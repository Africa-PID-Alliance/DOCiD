"""
CORE API v3 Client Service — open-access PDF discovery.
Stores open_access_url on Publications; never caches PDF bytes.
API docs: https://core.ac.uk/documentation/api-v3
"""
import time
import urllib.parse
import requests
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

from app.service_openalex import normalize_doi

CORE_API_BASE = 'https://api.core.ac.uk/v3'


class CoreClient:
    """Client for the CORE API v3."""

    def __init__(self, api_key: str, base_url: str = CORE_API_BASE):
        if not api_key:
            raise ValueError("CORE_API_KEY is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.rate_limit_delay = 0.5
        self._last_request_time = 0.0
        self.session = requests.Session()
        self.timeout = 15

    def _get_headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json',
        }

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()

        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, headers=self._get_headers(),
                                        params=params, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            if response.status_code == 401:
                logger.error("CORE API key invalid or expired (401)")
                return None
            if response.status_code == 429:
                raw_retry = response.headers.get('Retry-After', '30')
                try:
                    retry_seconds = int(raw_retry)
                except ValueError:
                    retry_seconds = 30
                logger.warning("CORE rate-limited; retrying after %ds", retry_seconds)
                time.sleep(retry_seconds)
                self._last_request_time = time.time()
                response = self.session.get(url, headers=self._get_headers(),
                                            params=params, timeout=self.timeout)
                if response.status_code == 200:
                    return response.json()
                return None
            if response.status_code == 404:
                return None
            if response.status_code >= 500:
                logger.error("CORE server error: %d", response.status_code)
                return None
            logger.error("Unexpected CORE response: %d %s", response.status_code, response.text[:200])
            return None
        except requests.exceptions.Timeout:
            logger.error("Timeout calling CORE: %s", url)
            return None
        except requests.exceptions.RequestException as exc:
            logger.error("Network error calling CORE: %s", exc)
            return None

    def get_work_by_doi(self, doi: str) -> Optional[Dict]:
        normalized = normalize_doi(doi)
        if not normalized:
            return None
        # CORE search uses a query string, not path segment, so plain encoding is safe.
        resp = self._make_request(
            '/search/works',
            params={'q': f'doi:"{normalized}"', 'limit': 1},
        )
        if not resp:
            return None
        results = resp.get('results') or []
        if not results:
            return None
        # Verify the returned DOI matches to guard against false positives.
        result = results[0]
        returned_doi = normalize_doi(result.get('doi') or '')
        if returned_doi and returned_doi.lower() != normalized.lower():
            logger.warning("CORE returned mismatched DOI: got %s expected %s",
                           returned_doi, normalized)
            return None
        return result

    def search_works_by_title(self, title: str, limit: int = 5) -> List[Dict]:
        if not title or not title.strip():
            return []
        resp = self._make_request(
            '/search/works',
            params={'q': f'title:"{title.strip()}"', 'limit': limit},
        )
        if not resp:
            return []
        return resp.get('results') or []

    def get_work_by_core_id(self, core_id: str) -> Optional[Dict]:
        return self._make_request(f'/works/{core_id}')


class CoreEnrichmentMapper:
    """Maps CORE work data to DOCiD enrichment fields."""

    @classmethod
    def extract_work_enrichment(cls, work: Dict) -> Optional[Dict]:
        if not work or not isinstance(work, dict):
            return None
        data_providers = work.get('dataProviders') or []
        repository_name = data_providers[0].get('name') if data_providers else None
        language = (work.get('language') or {}).get('code')
        return {
            'core_id':          work.get('id'),
            'full_text_url':    work.get('fullTextIdentifier') or work.get('downloadUrl'),
            'core_download_url':work.get('downloadUrl'),
            'language':         language,
            'repository_name':  repository_name,
            'publisher':        work.get('publisher'),
            'abstract':         work.get('abstract'),
        }


# ---------------------------------------------------------------------------
# Fetch / apply / snapshot chain
# ---------------------------------------------------------------------------

# open_access_url is only set from CORE when it's currently NULL;
# CORE never overwrites a value set by OpenAlex or Unpaywall.
CORE_APPLIED_COLUMNS = ('open_access_url', 'abstract_text')


def snapshot_publication_core_fields(publication) -> Dict:
    return {col: getattr(publication, col, None) for col in CORE_APPLIED_COLUMNS}


def restore_publication_from_snapshot(publication, snapshot: Dict) -> None:
    if not isinstance(snapshot, dict):
        return
    for col in CORE_APPLIED_COLUMNS:
        if col in snapshot:
            setattr(publication, col, snapshot[col])


def fetch_core_candidate(
    publication,
    client: CoreClient,
    mapper: CoreEnrichmentMapper,
    performed_by: str = "system",
    allow_title_fallback: bool = False,
) -> Tuple[str, Optional[str], Optional[Dict]]:
    """
    Look up CORE metadata for a publication without mutating it.

    Returns (status, error_message, payload).
    """
    doi = getattr(publication, 'doi', None)
    normalized_doi = normalize_doi(doi) if doi else None
    work = None
    match_method = None

    if normalized_doi and normalized_doi.startswith('10.'):
        try:
            work = client.get_work_by_doi(normalized_doi)
            if work:
                match_method = 'doi'
        except Exception as exc:
            logger.error("Transient error fetching CORE by DOI: %s", exc)
            return 'transient_error', str(exc), None

    if not work and allow_title_fallback and getattr(publication, 'document_title', None):
        try:
            results = client.search_works_by_title(publication.document_title, limit=1)
            if results:
                work = results[0]
                match_method = 'title_search'
        except Exception as exc:
            logger.error("Transient error in CORE title search: %s", exc)
            return 'transient_error', str(exc), None

    if not work:
        if not normalized_doi:
            return 'skipped', 'no_valid_doi', None
        return 'not_found', None, None

    try:
        enrichment_data = mapper.extract_work_enrichment(work)
    except Exception as exc:
        return 'malformed_response', str(exc), None

    if not enrichment_data:
        return 'malformed_response', 'mapper returned None', None

    retrieved_at = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    confidence = 'high' if match_method == 'doi' else 'review_required'
    provenance = {
        "eventType":   "external_metadata_enrichment",
        "source":      "CORE",
        "sourceUrl":   enrichment_data.get('full_text_url') or '',
        "retrievedAt": retrieved_at,
        "matchedBy":   match_method,
        "confidence":  confidence,
        "performedBy": performed_by,
        "status":      'accepted' if confidence == 'high' else 'pending_review',
    }

    payload = {
        "work":         work,
        "enrichment":   enrichment_data,
        "provenance":   provenance,
        "match_method": match_method,
    }
    return 'enriched', None, payload


def apply_core_enrichment_to_publication(publication, payload: Dict) -> None:
    """Apply fetched CORE candidate. Never overwrites an existing open_access_url."""
    if not payload:
        return
    enrichment = payload.get("enrichment") or {}
    # Only set open_access_url when the column is currently empty.
    if enrichment.get('full_text_url') and not getattr(publication, 'open_access_url', None):
        publication.open_access_url = enrichment['full_text_url']
    if enrichment.get('abstract') and not getattr(publication, 'abstract_text', None):
        publication.abstract_text = enrichment['abstract']


def enrich_publication_core(
    publication,
    client: CoreClient,
    mapper: CoreEnrichmentMapper,
    performed_by: str = "system",
    allow_title_fallback: bool = False,
) -> Tuple[str, Optional[str], Optional[Dict]]:
    """CLI-friendly wrapper: fetch + auto-apply."""
    status, error_message, payload = fetch_core_candidate(
        publication, client, mapper,
        performed_by=performed_by,
        allow_title_fallback=allow_title_fallback,
    )
    if status == 'enriched' and payload:
        apply_core_enrichment_to_publication(publication, payload)
    return status, error_message, payload
