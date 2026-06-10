"""
OpenAIRE Graph API Client Service.
Uses the current Graph API at graph.openaire.eu/api (NOT the deprecated
api.openaire.eu/search/* endpoint which was shut down in 2023).
"""
import time
import urllib.parse
import requests
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

from app.service_openalex import normalize_doi

_DEPRECATED_URL_FRAGMENT = 'api.openaire.eu'


class OpenAIREClient:
    """Client for the OpenAIRE Graph API (graph.openaire.eu/api)."""

    def __init__(self, base_url: str = 'https://graph.openaire.eu/api'):
        if _DEPRECATED_URL_FRAGMENT in base_url:
            raise ValueError(
                f"OpenAIRE base_url '{base_url}' points at the deprecated Search API "
                f"(api.openaire.eu). Use 'https://graph.openaire.eu/api' instead."
            )
        self.base_url = base_url.rstrip('/')
        self.rate_limit_delay = 0.6
        self._last_request_time = 0.0
        self.session = requests.Session()
        self.timeout = 15

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()

        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(
                url, headers={'Accept': 'application/json'},
                params=params, timeout=self.timeout,
            )
            if response.status_code == 200:
                return response.json()
            if response.status_code == 429:
                raw_retry = response.headers.get('Retry-After', '30')
                try:
                    retry_seconds = int(raw_retry)
                except ValueError:
                    retry_seconds = 30
                logger.warning("OpenAIRE rate-limited; retrying after %ds", retry_seconds)
                time.sleep(retry_seconds)
                self._last_request_time = time.time()
                response = self.session.get(
                    url, headers={'Accept': 'application/json'},
                    params=params, timeout=self.timeout,
                )
                if response.status_code == 200:
                    return response.json()
                return None
            if response.status_code == 404:
                return None
            if response.status_code >= 500:
                logger.error("OpenAIRE server error: %d", response.status_code)
                return None
            logger.error("Unexpected OpenAIRE response: %d", response.status_code)
            return None
        except requests.exceptions.Timeout:
            logger.error("Timeout calling OpenAIRE: %s", url)
            return None
        except requests.exceptions.RequestException as exc:
            logger.error("Network error calling OpenAIRE: %s", exc)
            return None

    def search_by_doi(self, doi: str) -> Optional[Dict]:
        """Look up a research product by DOI using the Graph API."""
        normalized = normalize_doi(doi)
        if not normalized:
            return None
        encoded = urllib.parse.quote(normalized, safe='')
        resp = self._make_request(
            '/researchProducts',
            params={'pid': normalized, 'format': 'json', 'pageSize': 1},
        )
        if not resp:
            return None
        results = resp.get('results') or []
        if not results:
            return None
        return results[0]

    def get_projects_for_doi(self, doi: str) -> List[Dict]:
        """Projects are embedded in the publication result; this is a no-op stub."""
        return []


class OpenAIREEnrichmentMapper:
    """Maps OpenAIRE Graph API results to DOCiD enrichment fields."""

    @classmethod
    def extract_enrichment(cls, result: Dict, projects: List[Dict] = None) -> Optional[Dict]:
        if not result or not isinstance(result, dict):
            return None

        # Graph API returns a flat-ish structure compared to the old Search API.
        openaire_id = result.get('id') or result.get('originalId')
        if not openaire_id and isinstance(result.get('originalIds'), list):
            openaire_id = result['originalIds'][0] if result['originalIds'] else None

        # Extract project links from the result itself (Graph API embeds them).
        extracted_projects = []
        for rel in (result.get('projects') or []):
            project_item = cls._extract_project(rel)
            if project_item:
                extracted_projects.append(project_item)

        return {
            'openaire_id': openaire_id,
            'projects':    extracted_projects,
        }

    @classmethod
    def _extract_project(cls, project_rel: Dict) -> Optional[Dict]:
        if not project_rel or not isinstance(project_rel, dict):
            return None
        title = project_rel.get('title') or project_rel.get('projectTitle') or ''
        acronym = project_rel.get('acronym') or ''
        funder_name = (project_rel.get('funding') or {}).get('name') or ''
        grant_id = project_rel.get('grantId') or project_rel.get('id') or ''
        if not title and not acronym:
            return None
        return {
            'title':       title,
            'acronym':     acronym,
            'funder_name': funder_name,
            'grant_id':    grant_id,
        }

    @classmethod
    def _extract_single_project(cls, project_result: Dict) -> Optional[Dict]:
        """Legacy alias kept for callers that used the old search-API mapper."""
        return cls._extract_project(project_result)


# ---------------------------------------------------------------------------
# Fetch / apply / snapshot chain
# ---------------------------------------------------------------------------

OPENAIRE_APPLIED_COLUMNS = ('openaire_id',)


def snapshot_publication_openaire_fields(publication) -> Dict:
    return {col: getattr(publication, col, None) for col in OPENAIRE_APPLIED_COLUMNS}


def restore_publication_from_snapshot(publication, snapshot: Dict) -> None:
    if not isinstance(snapshot, dict):
        return
    for col in OPENAIRE_APPLIED_COLUMNS:
        if col in snapshot:
            setattr(publication, col, snapshot[col])


def fetch_openaire_candidate(
    publication,
    client: OpenAIREClient,
    mapper: OpenAIREEnrichmentMapper,
    performed_by: str = "system",
) -> Tuple[str, Optional[str], Optional[Dict]]:
    """
    Look up OpenAIRE metadata for a publication without mutating it.

    Returns (status, error_message, payload).
    Requires a real DOI (10. prefix) — skips handle-shaped identifiers.
    """
    doi = getattr(publication, 'doi', None)
    normalized_doi = normalize_doi(doi) if doi else None
    if not normalized_doi or not normalized_doi.startswith('10.'):
        return 'skipped', 'no_valid_doi', None

    try:
        result = client.search_by_doi(normalized_doi)
    except Exception as exc:
        logger.error("Transient error fetching OpenAIRE: %s", exc)
        return 'transient_error', str(exc), None

    if not result:
        return 'not_found', None, None

    try:
        enrichment_data = mapper.extract_enrichment(result)
    except Exception as exc:
        logger.error("Malformed OpenAIRE response: %s", exc)
        return 'malformed_response', str(exc), None

    if not enrichment_data:
        return 'malformed_response', 'mapper returned None', None

    retrieved_at = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    provenance = {
        "eventType":   "external_metadata_enrichment",
        "source":      "OpenAIRE",
        "sourceUrl":   result.get('id') or result.get('landingPage') or '',
        "retrievedAt": retrieved_at,
        "matchedBy":   "doi",
        "confidence":  "high",
        "performedBy": performed_by,
        "status":      "accepted",
    }

    payload = {
        "result":       result,
        "enrichment":   enrichment_data,
        "provenance":   provenance,
        "match_method": "doi",
    }
    return 'enriched', None, payload


def apply_openaire_enrichment_to_publication(publication, payload: Dict) -> None:
    """Apply fetched OpenAIRE candidate to Publication columns (no DB commit)."""
    if not payload:
        return
    enrichment = payload.get("enrichment") or {}
    if enrichment.get('openaire_id'):
        publication.openaire_id = enrichment['openaire_id']


def enrich_publication_openaire(
    publication,
    client: OpenAIREClient,
    mapper: OpenAIREEnrichmentMapper,
    performed_by: str = "system",
) -> Tuple[str, Optional[str], Optional[Dict]]:
    """CLI-friendly wrapper: fetch + auto-apply."""
    status, error_message, payload = fetch_openaire_candidate(
        publication, client, mapper, performed_by=performed_by,
    )
    if status == 'enriched' and payload:
        apply_openaire_enrichment_to_publication(publication, payload)
    return status, error_message, payload
