"""
OpenCitations COCI API Client Service — DOI-to-DOI citation edges.
Emits edge dicts for publication_external_edges; does NOT mutate Publications.
API docs: https://opencitations.net/index/coci/api/v1
"""
import time
import urllib.parse
import requests
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

from app.service_openalex import normalize_doi

OPENCITATIONS_BASE = 'https://opencitations.net/index/coci/api/v1'


class OpenCitationsClient:
    """Client for the OpenCitations COCI API."""

    def __init__(self, access_token: str = '', base_url: str = OPENCITATIONS_BASE):
        self.access_token = access_token
        self.base_url = base_url.rstrip('/')
        self.rate_limit_delay = 0.3
        self._last_request_time = 0.0
        self.session = requests.Session()
        self.timeout = 15

    def _get_headers(self) -> Dict[str, str]:
        # OpenCitations uses lowercase 'authorization' header.
        headers = {'Accept': 'application/json'}
        if self.access_token:
            headers['authorization'] = self.access_token
        return headers

    def _make_request(self, endpoint: str) -> Optional[List]:
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()

        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, headers=self._get_headers(), timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                return data if isinstance(data, list) else []
            if response.status_code == 404:
                return []
            if response.status_code == 429:
                raw_retry = response.headers.get('Retry-After', '30')
                try:
                    retry_seconds = int(raw_retry)
                except ValueError:
                    retry_seconds = 30
                logger.warning("OpenCitations rate-limited; retrying after %ds", retry_seconds)
                time.sleep(retry_seconds)
                self._last_request_time = time.time()
                response = self.session.get(url, headers=self._get_headers(), timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    return data if isinstance(data, list) else []
                return []
            if response.status_code >= 500:
                logger.error("OpenCitations server error: %d", response.status_code)
                return None  # None = transient; [] = truly empty
            logger.error("Unexpected OpenCitations response: %d", response.status_code)
            return None
        except requests.exceptions.Timeout:
            logger.error("Timeout calling OpenCitations: %s", url)
            return None
        except requests.exceptions.RequestException as exc:
            logger.error("Network error calling OpenCitations: %s", exc)
            return None

    def get_references(self, doi: str) -> Optional[List[Dict]]:
        """Return papers that `doi` cites (outgoing references)."""
        normalized = normalize_doi(doi)
        if not normalized:
            return []
        encoded = urllib.parse.quote(normalized, safe='')
        return self._make_request(f'/references/{encoded}')

    def get_citations(self, doi: str) -> Optional[List[Dict]]:
        """Return papers that cite `doi` (incoming citations)."""
        normalized = normalize_doi(doi)
        if not normalized:
            return []
        encoded = urllib.parse.quote(normalized, safe='')
        return self._make_request(f'/citations/{encoded}')

    def get_metadata(self, doi: str) -> Optional[List[Dict]]:
        """Return citation metadata for a DOI."""
        normalized = normalize_doi(doi)
        if not normalized:
            return []
        encoded = urllib.parse.quote(normalized, safe='')
        return self._make_request(f'/metadata/{encoded}')


class OpenCitationsMapper:
    """Converts COCI reference/citation records into edge dicts."""

    @classmethod
    def extract_reference_edges(cls, source_doi: str, references: List[Dict]) -> List[Dict]:
        """
        Each item in `references` is a COCI reference record.
        The cited DOI is in item['cited'].
        Produces relation='cites' edges.
        """
        edges = []
        for item in (references or []):
            cited_raw = item.get('cited') or ''
            cited_doi = normalize_doi(cited_raw)
            if not cited_doi:
                continue
            edges.append({
                'object_id_kind': 'doi',
                'object_id':      cited_doi,
                'object_label':   None,
                'relation':       'cites',
                'source_name':    'opencitations',
                'confidence':     'high',
                'raw_metadata':   {
                    'oci':            item.get('oci'),
                    'creation':       item.get('creation'),
                    'journal_sc':     item.get('journal_sc'),
                    'author_sc':      item.get('author_sc'),
                },
            })
        return edges

    @classmethod
    def extract_citation_edges(cls, source_doi: str, citations: List[Dict]) -> List[Dict]:
        """
        Each item in `citations` is a COCI citation record.
        The citing DOI is in item['citing'].
        Produces relation='cited_by' edges.
        """
        edges = []
        for item in (citations or []):
            citing_raw = item.get('citing') or ''
            citing_doi = normalize_doi(citing_raw)
            if not citing_doi:
                continue
            edges.append({
                'object_id_kind': 'doi',
                'object_id':      citing_doi,
                'object_label':   None,
                'relation':       'cited_by',
                'source_name':    'opencitations',
                'confidence':     'high',
                'raw_metadata':   {
                    'oci':        item.get('oci'),
                    'creation':   item.get('creation'),
                    'journal_sc': item.get('journal_sc'),
                    'author_sc':  item.get('author_sc'),
                },
            })
        return edges


# ---------------------------------------------------------------------------
# Fetch edges — no Publications mutation for this provider
# ---------------------------------------------------------------------------

OPENCITATIONS_APPLIED_COLUMNS = ()  # no Publications columns mutated


def fetch_opencitations_edges(
    publication,
    client: OpenCitationsClient,
    mapper: OpenCitationsMapper,
    performed_by: str = "system",
    include_references: bool = True,
    include_citations: bool = True,
) -> Tuple[str, Optional[str], Optional[Dict]]:
    """
    Fetch citation edges for a publication without mutating any columns.

    Returns (status, error_message, payload).
    payload['edges'] contains the typed edge dicts for publication_external_edges.
    The route layer is responsible for upserting them.

    status values: enriched | not_found | skipped | transient_error
    """
    doi = getattr(publication, 'doi', None)
    normalized_doi = normalize_doi(doi) if doi else None
    if not normalized_doi or not normalized_doi.startswith('10.'):
        return 'skipped', 'no_valid_doi', None

    edges = []
    found_any = False

    if include_references:
        try:
            refs = client.get_references(normalized_doi)
            if refs is None:
                return 'transient_error', 'opencitations server error on references', None
            ref_edges = mapper.extract_reference_edges(normalized_doi, refs)
            edges.extend(ref_edges)
            if ref_edges:
                found_any = True
        except Exception as exc:
            logger.error("Transient error fetching OpenCitations references: %s", exc)
            return 'transient_error', str(exc), None

    if include_citations:
        try:
            cits = client.get_citations(normalized_doi)
            if cits is None:
                return 'transient_error', 'opencitations server error on citations', None
            cit_edges = mapper.extract_citation_edges(normalized_doi, cits)
            edges.extend(cit_edges)
            if cit_edges:
                found_any = True
        except Exception as exc:
            logger.error("Transient error fetching OpenCitations citations: %s", exc)
            return 'transient_error', str(exc), None

    if not found_any and not edges:
        return 'not_found', None, None

    retrieved_at = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    provenance = {
        "eventType":   "citation_edges_harvest",
        "source":      "OpenCitations",
        "sourceUrl":   f"https://opencitations.net/index/coci/api/v1/metadata/{normalized_doi}",
        "retrievedAt": retrieved_at,
        "matchedBy":   "doi",
        "confidence":  "high",
        "performedBy": performed_by,
        "status":      "accepted",
    }

    payload = {
        "edges":        edges,
        "provenance":   provenance,
        "match_method": "doi",
    }
    return 'enriched', None, payload
