"""
WorldCat (OCLC Metadata API v2) enrichment service.
Provides OCLC numbers, ISBNs, holdings counts, and edition information
for books and serials registered with OCLC.

Auth: OAuth 2.0 Client Credentials (OCLC member agreement required).
Token endpoint: https://oauth.oclc.org/token
Token lifetime: 3600s; refreshed automatically with a 100s safety margin.

Scope: WorldCatMetadataAPI

NOTE: Requires an active OCLC membership contract. No code runs until
WORLDCAT_CLIENT_ID + WORLDCAT_CLIENT_SECRET are both configured.

IMPORTANT: Publication columns for OCLC number and ISBN (oclc_number, isbn)
are deferred until the OCLC contract is signed. Until then,
WORLDCAT_APPLIED_COLUMNS is empty — all enrichment data is stored in
raw_response only and can be promoted to columns via a later migration.
"""
import logging
import time
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import requests

from app.service_openalex import normalize_doi

logger = logging.getLogger(__name__)

WORLDCAT_TOKEN_URL      = 'https://oauth.oclc.org/token'
WORLDCAT_SEARCH_BASE_URL = 'https://americas.discovery.api.oclc.org/worldcat/search/v2'
WORLDCAT_METADATA_BASE_URL = 'https://metadata.api.oclc.org'

# Deferred: oclc_number and isbn columns don't exist yet on Publications.
# Flip to ('oclc_number', 'isbn') once the migration ships.
WORLDCAT_APPLIED_COLUMNS: tuple = ()


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class WorldCatClient:
    """
    HTTP client for the OCLC WorldCat Metadata + Search APIs.
    Uses OAuth 2.0 Client Credentials with automatic token refresh.
    Token pattern follows service_codra.CordraService._is_token_expired().
    """

    _TOKEN_SAFETY_MARGIN = 100  # seconds before expiry to pre-refresh

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        search_base_url: str = WORLDCAT_SEARCH_BASE_URL,
        metadata_base_url: str = WORLDCAT_METADATA_BASE_URL,
        rate_limit_delay: float = 0.5,
        timeout: int = 15,
    ):
        if not client_id or not client_secret:
            raise ValueError(
                "WORLDCAT_CLIENT_ID and WORLDCAT_CLIENT_SECRET are both required. "
                "Obtain them from https://platform.worldcat.org/wskey/ once the "
                "OCLC membership contract is in place."
            )
        self.client_id = client_id
        self.client_secret = client_secret
        self.search_base_url = search_base_url.rstrip('/')
        self.metadata_base_url = metadata_base_url.rstrip('/')
        self.rate_limit_delay = rate_limit_delay
        self.timeout = timeout
        self._last_request_time: float = 0.0
        self._access_token: Optional[str] = None
        self._token_acquired_at: Optional[float] = None
        self._token_lifetime: int = 3600
        self.session = requests.Session()

    # ---- Token management ----

    def _is_token_expired(self) -> bool:
        if self._token_acquired_at is None or self._access_token is None:
            return True
        age = time.time() - self._token_acquired_at
        return age >= (self._token_lifetime - self._TOKEN_SAFETY_MARGIN)

    def _fetch_token(self) -> bool:
        """Request a new OAuth token via Client Credentials grant."""
        try:
            response = requests.post(
                WORLDCAT_TOKEN_URL,
                data={
                    'grant_type': 'client_credentials',
                    'scope':      'WorldCatMetadataAPI',
                },
                auth=(self.client_id, self.client_secret),
                timeout=10,
            )
            if response.status_code == 401:
                logger.error("WorldCat OAuth: invalid client credentials")
                return False
            if not response.ok:
                logger.error("WorldCat token fetch failed: %s %s", response.status_code, response.text[:200])
                return False
            token_data = response.json()
            self._access_token = token_data.get('access_token')
            self._token_lifetime = int(token_data.get('expires_in', 3600))
            self._token_acquired_at = time.time()
            return bool(self._access_token)
        except Exception as exc:
            logger.error("WorldCat token fetch exception: %s", exc)
            return False

    def _auth_headers(self) -> Optional[dict]:
        if self._is_token_expired():
            if not self._fetch_token():
                return None
        return {
            'Authorization': f'Bearer {self._access_token}',
            'Accept':        'application/json',
        }

    # ---- Request helper ----

    def _get(self, url: str, params: Optional[dict] = None) -> Optional[dict]:
        elapsed = time.time() - self._last_request_time
        remaining_delay = self.rate_limit_delay - elapsed
        if remaining_delay > 0:
            time.sleep(remaining_delay)

        headers = self._auth_headers()
        if headers is None:
            return None

        try:
            response = self.session.get(url, headers=headers, params=params, timeout=self.timeout)
            self._last_request_time = time.time()

            if response.status_code in (401, 403):
                logger.error("WorldCat auth error %s — token may have been invalidated", response.status_code)
                self._access_token = None  # force re-fetch on next call
                return None
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning("WorldCat rate-limited; sleeping %ss", retry_after)
                time.sleep(retry_after)
                return None
            if response.status_code == 404:
                return {}  # distinct from None (network error)
            if response.status_code >= 500:
                logger.warning("WorldCat server error %s", response.status_code)
                return None
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.warning("WorldCat request timed out")
            return None
        except requests.exceptions.RequestException as exc:
            logger.warning("WorldCat request failed: %s", exc)
            return None
        except ValueError as exc:
            logger.warning("WorldCat JSON decode error: %s", exc)
            return None

    # ---- Public search methods ----

    def search_by_isbn(self, isbn: str) -> Optional[dict]:
        """Search WorldCat by ISBN-13 or ISBN-10. Returns first bib record or None."""
        clean_isbn = isbn.replace('-', '').replace(' ', '')
        url = f'{self.search_base_url}/bibs'
        data = self._get(url, params={'q': f'bn:{clean_isbn}', 'limit': 1})
        return self._first_bib(data)

    def search_by_doi(self, doi: str) -> Optional[dict]:
        """Search WorldCat by DOI. Returns first matching bib record or None."""
        normalised = normalize_doi(doi)
        if not normalised:
            return None
        url = f'{self.search_base_url}/bibs'
        data = self._get(url, params={'q': f'sn:"{normalised}"', 'limit': 1})
        return self._first_bib(data)

    def search_by_title(self, title: str, limit: int = 5) -> List[dict]:
        """Search WorldCat by title. Returns up to `limit` bib record dicts."""
        if not title or len(title.strip()) < 5:
            return []
        url = f'{self.search_base_url}/bibs'
        data = self._get(url, params={'q': f'ti:"{title}"', 'limit': limit})
        bibs = (data or {}).get('bibRecords') or []
        return bibs

    def get_bib_by_oclc_number(self, oclc_number: str) -> Optional[dict]:
        """Retrieve a specific bib record by OCLC control number."""
        url = f'{self.metadata_base_url}/worldcat/manage/bibs/{urllib.parse.quote(oclc_number)}'
        data = self._get(url)
        return data if data else None

    @staticmethod
    def _first_bib(data: Optional[dict]) -> Optional[dict]:
        if not data:
            return None
        bibs = data.get('bibRecords') or []
        return bibs[0] if bibs else None


# ---------------------------------------------------------------------------
# Mapper
# ---------------------------------------------------------------------------

class WorldCatEnrichmentMapper:

    @classmethod
    def extract_bib_enrichment(cls, bib: dict) -> dict:
        """Map a WorldCat bibRecord dict to enrichment fields."""
        identifier = bib.get('identifier') or {}
        oclc_number = identifier.get('oclcNumber') or identifier.get('oclcNumbers', [None])[0]

        isbns = []
        for id_entry in (bib.get('identifiers') or []):
            if id_entry.get('type') in ('isbn', 'ISBN'):
                isbns.append(id_entry.get('value', ''))
        # Also look in the flat shape
        if not isbns:
            raw_isbns = bib.get('isbn') or []
            if isinstance(raw_isbns, str):
                raw_isbns = [raw_isbns]
            isbns = raw_isbns

        title_info = bib.get('title') or {}
        main_title = title_info.get('mainTitles', [{}])[0].get('text') if title_info.get('mainTitles') else None

        contributors = []
        for contributor in (bib.get('contributors') or []):
            name = contributor.get('nonPersonName', {}).get('text') or contributor.get('firstName', {}).get('text', '')
            surname = contributor.get('secondName', {}).get('text', '')
            full_name = f"{name} {surname}".strip()
            if full_name:
                contributors.append(full_name)

        language_info = (bib.get('languages') or [{}])[0]
        language = language_info.get('itemLanguage')

        dates = bib.get('date') or {}
        publisher_info = (bib.get('publishers') or [{}])[0]

        holdings = bib.get('holdingsCount') or bib.get('numberOfHoldings') or 0

        return {
            'oclc_number':    oclc_number,
            'isbns':          isbns,
            'isbn':           isbns[0] if isbns else None,
            'title':          main_title,
            'contributors':   contributors,
            'language':       language,
            'publish_date':   dates.get('publicationDate'),
            'publisher':      publisher_info.get('publisherName', {}).get('text'),
            'edition':        bib.get('edition'),
            'holdings_count': holdings,
            'record_type':    bib.get('recordType'),
            'material_type':  (bib.get('materialType') or {}).get('generalFormat'),
        }

    @classmethod
    def extract_enrichment(cls, bib: dict) -> dict:
        return cls.extract_bib_enrichment(bib)


# ---------------------------------------------------------------------------
# Fetch / apply / snapshot / restore chain
# ---------------------------------------------------------------------------

def snapshot_publication_worldcat_fields(publication) -> dict:
    """Snapshot current columns that WorldCat might eventually write to."""
    # oclc_number and isbn columns don't exist yet; snapshot what we have.
    return {}


def restore_publication_from_snapshot(publication, snapshot: dict) -> None:
    """Restore columns from a pre-apply snapshot dict."""
    # Nothing to restore until the oclc_number / isbn migration ships.
    pass


def apply_worldcat_enrichment_to_publication(publication, payload: dict) -> None:
    """
    Apply accepted WorldCat enrichment to a Publications row.
    Currently a no-op because the oclc_number / isbn columns are deferred.
    Once migration a1b2c3d4e5f6_add_worldcat_columns ships, enable:

        enrichment = payload.get('enrichment') or {}
        if enrichment.get('oclc_number') and not getattr(publication, 'oclc_number', None):
            publication.oclc_number = enrichment['oclc_number']
        if enrichment.get('isbn') and not getattr(publication, 'isbn', None):
            publication.isbn = enrichment['isbn']
    """
    pass


def fetch_worldcat_candidate(
    publication,
    client: WorldCatClient,
    mapper: WorldCatEnrichmentMapper,
    performed_by: str = 'system',
    allow_title_fallback: bool = False,
) -> Tuple[str, Optional[str], Optional[dict]]:
    """
    Fetch a WorldCat enrichment candidate for publication.

    Returns (status, error_message, payload).
    status values: enriched | not_found | skipped | transient_error | auth_error |
                   quota_exhausted | malformed_response
    """
    doi   = getattr(publication, 'doi', None)
    isbn  = getattr(publication, 'isbn', None) if hasattr(publication, 'isbn') else None
    title = getattr(publication, 'title', None)

    if not doi and not isbn and not allow_title_fallback:
        return 'skipped', 'No DOI, no ISBN, and title_fallback disabled', None
    if not doi and not isbn and (not title or len(title.strip()) < 5):
        return 'skipped', 'No match keys and title too short for reliable search', None

    bib = None
    match_method = None

    if isbn:
        try:
            bib = client.search_by_isbn(isbn)
            if bib:
                match_method = 'isbn'
        except Exception as exc:
            logger.warning("WorldCat ISBN lookup failed: %s", exc)
            return 'transient_error', str(exc), None

    if bib is None and doi:
        try:
            bib = client.search_by_doi(doi)
            if bib:
                match_method = 'doi'
        except Exception as exc:
            logger.warning("WorldCat DOI lookup failed: %s", exc)
            return 'transient_error', str(exc), None

    if bib is None and allow_title_fallback and title:
        try:
            candidates = client.search_by_title(title, limit=5)
            if candidates:
                bib = candidates[0]
                match_method = 'title_search'
        except Exception as exc:
            logger.warning("WorldCat title search failed: %s", exc)
            return 'transient_error', str(exc), None

    if bib is None:
        return 'not_found', None, None

    try:
        enrichment = mapper.extract_bib_enrichment(bib)
    except Exception as exc:
        logger.warning("WorldCat mapper error: %s", exc)
        return 'malformed_response', f'Mapper error: {exc}', None

    if not any(enrichment.values()):
        return 'not_found', 'WorldCat returned an empty bib record', None

    retrieved_at = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    oclc_url = (
        f'https://www.worldcat.org/oclc/{enrichment["oclc_number"]}'
        if enrichment.get('oclc_number') else None
    )
    provenance = {
        'eventType':   'external_metadata_enrichment',
        'source':      'WorldCat',
        'sourceUrl':   oclc_url,
        'retrievedAt': retrieved_at,
        'matchedBy':   match_method,
        'confidence':  'high' if match_method in ('doi', 'isbn') else 'review_required',
        'performedBy': performed_by,
        'status':      'pending_review',
    }

    return 'enriched', None, {
        'match_method': match_method,
        'enrichment':   enrichment,
        'provenance':   provenance,
    }


def enrich_publication_worldcat(
    publication,
    client: WorldCatClient,
    mapper: WorldCatEnrichmentMapper,
    performed_by: str = 'system',
) -> Tuple[str, Optional[str], Optional[dict]]:
    """CLI-friendly wrapper — fetch + apply in one call (no DB persistence)."""
    status, error_message, payload = fetch_worldcat_candidate(
        publication, client, mapper, performed_by=performed_by
    )
    if status == 'enriched' and payload:
        payload['pre_apply_snapshot'] = snapshot_publication_worldcat_fields(publication)
        apply_worldcat_enrichment_to_publication(publication, payload)
    return status, error_message, payload
