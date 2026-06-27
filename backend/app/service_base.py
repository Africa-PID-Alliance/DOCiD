"""
BASE (Bielefeld Academic Search Engine) enrichment service.
Provides abstract text, subjects, language, and publisher metadata
from BASE's 300M+ open-access document index.

Auth: token passed as a query parameter (?token=<BASE_API_KEY>).
Quota: free-tier allows reasonable academic usage; no published hard limit.

NOTE: Store only metadata URLs and text. Never cache BASE full-text binaries.
"""
import logging
import time
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import requests

from app.service_openalex import normalize_doi

logger = logging.getLogger(__name__)

BASE_API_BASE_URL = 'https://api.base-search.net/cgi-bin/BaseHttpSearchInterface.fcgi'

# Columns this service writes to Publications on accept.
BASE_APPLIED_COLUMNS = ('abstract_text',)


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class BaseSearchClient:
    """HTTP client for the BASE Bielefeld Academic Search Engine API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = BASE_API_BASE_URL,
        rate_limit_delay: float = 1.0,
        timeout: int = 15,
    ):
        if not api_key:
            raise ValueError(
                "BASE_API_KEY is required. Apply at https://www.base-search.net/about/en/contact.php "
                "(approval typically takes 1-4 weeks)."
            )
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.rate_limit_delay = rate_limit_delay
        self.timeout = timeout
        self._last_request_time: float = 0.0
        self.session = requests.Session()
        self.session.headers.update({'Accept': 'application/json'})

    def _make_request(self, params: dict) -> Optional[dict]:
        elapsed = time.time() - self._last_request_time
        remaining_delay = self.rate_limit_delay - elapsed
        if remaining_delay > 0:
            time.sleep(remaining_delay)

        params['token'] = self.api_key
        params['format'] = 'json'

        try:
            response = self.session.get(self.base_url, params=params, timeout=self.timeout)
            self._last_request_time = time.time()

            if response.status_code == 401 or response.status_code == 403:
                logger.error("BASE auth error: %s", response.status_code)
                return None
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning("BASE rate-limited; sleeping %ss", retry_after)
                time.sleep(retry_after)
                return None
            if response.status_code >= 500:
                logger.warning("BASE server error %s", response.status_code)
                return None
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.warning("BASE request timed out")
            return None
        except requests.exceptions.RequestException as exc:
            logger.warning("BASE request failed: %s", exc)
            return None
        except ValueError as exc:
            logger.warning("BASE JSON decode error: %s", exc)
            return None

    def search_by_doi(self, doi: str) -> Optional[dict]:
        """Search BASE by DOI. Returns the first matching document or None."""
        normalised = normalize_doi(doi)
        if not normalised:
            return None
        query = f'dcdoi:"{urllib.parse.quote(normalised, safe="")}"'
        data = self._make_request({'func': 'PerformSearch', 'query': query, 'hits': 1})
        return self._first_doc(data)

    def search_by_title(self, title: str, limit: int = 5) -> List[dict]:
        """Search BASE by title. Returns up to `limit` document dicts."""
        if not title or len(title.strip()) < 5:
            return []
        safe_title = title.replace('"', ' ')
        query = f'dctitle:"{safe_title}"'
        data = self._make_request({'func': 'PerformSearch', 'query': query, 'hits': limit})
        docs = (data or {}).get('response', {}).get('docs') or []
        return docs

    @staticmethod
    def _first_doc(data: Optional[dict]) -> Optional[dict]:
        if not data:
            return None
        docs = data.get('response', {}).get('docs') or []
        return docs[0] if docs else None


# ---------------------------------------------------------------------------
# Mapper
# ---------------------------------------------------------------------------

class BaseEnrichmentMapper:

    @classmethod
    def extract_doc_enrichment(cls, doc: dict) -> dict:
        """Map a BASE document dict to enrichment fields."""
        abstract_candidates = doc.get('dcabstract') or []
        if isinstance(abstract_candidates, str):
            abstract_candidates = [abstract_candidates]
        abstract_text = abstract_candidates[0] if abstract_candidates else None

        subjects = doc.get('dcsubject') or []
        if isinstance(subjects, str):
            subjects = [subjects]

        languages = doc.get('dclanguage') or []
        if isinstance(languages, str):
            languages = [languages]

        oa_links = doc.get('dclink') or []
        if isinstance(oa_links, str):
            oa_links = [oa_links]

        return {
            'base_id':       doc.get('dcidentifier') or doc.get('id'),
            'abstract_text': abstract_text,
            'subjects':      subjects,
            'language':      languages[0] if languages else None,
            'publisher':     doc.get('dcpublisher'),
            'oa_links':      oa_links,
            'doc_type':      doc.get('dctype'),
            'date':          doc.get('dcdate'),
            'source':        doc.get('dcsource'),
        }

    @classmethod
    def extract_enrichment(cls, doc: dict) -> dict:
        return cls.extract_doc_enrichment(doc)


# ---------------------------------------------------------------------------
# Fetch / apply / snapshot / restore chain
# ---------------------------------------------------------------------------

def snapshot_publication_base_fields(publication) -> dict:
    return {'abstract_text': publication.abstract_text}


def restore_publication_from_snapshot(publication, snapshot: dict) -> None:
    if 'abstract_text' in snapshot:
        publication.abstract_text = snapshot['abstract_text']


def apply_base_enrichment_to_publication(publication, payload: dict) -> None:
    enrichment = payload.get('enrichment') or {}
    if enrichment.get('abstract_text') and not publication.abstract_text:
        publication.abstract_text = enrichment['abstract_text']


def fetch_base_candidate(
    publication,
    client: BaseSearchClient,
    mapper: BaseEnrichmentMapper,
    performed_by: str = 'system',
    allow_title_fallback: bool = False,
) -> Tuple[str, Optional[str], Optional[dict]]:
    """
    Fetch a BASE enrichment candidate for publication.

    Returns (status, error_message, payload).
    status values: enriched | not_found | skipped | transient_error | auth_error |
                   quota_exhausted | malformed_response
    """
    doi = getattr(publication, 'doi', None)
    title = getattr(publication, 'title', None)

    if not doi and not allow_title_fallback:
        return 'skipped', 'No DOI and title_fallback disabled', None
    if not doi and (not title or len(title.strip()) < 5):
        return 'skipped', 'No DOI and title too short for reliable title search', None

    doc = None
    match_method = None

    if doi:
        try:
            doc = client.search_by_doi(doi)
            if doc:
                match_method = 'doi'
        except Exception as exc:
            logger.warning("BASE DOI lookup failed: %s", exc)
            return 'transient_error', str(exc), None

    if doc is None and allow_title_fallback and title:
        try:
            candidates = client.search_by_title(title, limit=5)
            if candidates:
                doc = candidates[0]
                match_method = 'title_search'
        except Exception as exc:
            logger.warning("BASE title search failed: %s", exc)
            return 'transient_error', str(exc), None

    if doc is None:
        return 'not_found', None, None

    try:
        enrichment = mapper.extract_doc_enrichment(doc)
    except Exception as exc:
        logger.warning("BASE mapper error: %s", exc)
        return 'malformed_response', f'Mapper error: {exc}', None

    if not any(enrichment.values()):
        return 'not_found', 'BASE returned an empty document', None

    retrieved_at = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    provenance = {
        'eventType':   'external_metadata_enrichment',
        'source':      'BASE',
        'sourceUrl':   f'{client.base_url}?func=PerformSearch&query=dcdoi:{doi}',
        'retrievedAt': retrieved_at,
        'matchedBy':   match_method,
        'confidence':  'high' if match_method == 'doi' else 'review_required',
        'performedBy': performed_by,
        'status':      'pending_review',
    }

    return 'enriched', None, {
        'match_method': match_method,
        'enrichment':   enrichment,
        'provenance':   provenance,
    }


def enrich_publication_base(
    publication,
    client: BaseSearchClient,
    mapper: BaseEnrichmentMapper,
    performed_by: str = 'system',
) -> Tuple[str, Optional[str], Optional[dict]]:
    """CLI-friendly wrapper — fetch + apply in one call (no DB persistence)."""
    status, error_message, payload = fetch_base_candidate(
        publication, client, mapper, performed_by=performed_by
    )
    if status == 'enriched' and payload:
        payload['pre_apply_snapshot'] = snapshot_publication_base_fields(publication)
        apply_base_enrichment_to_publication(publication, payload)
    return status, error_message, payload
