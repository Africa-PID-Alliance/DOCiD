"""
Lens.org API Client Service — patents + scholar-patent cross-citations.

Two separate API keys are required (both arrive in the same Cambia approval email):
  LENS_SCHOLAR_API_KEY  — for /scholarly/search
  LENS_PATENT_API_KEY   — for /patent/search and /patent/family/search

Emits edge dicts for publication_external_edges (patent_family_member,
patent_cites_paper, paper_cited_by_patent). Does NOT cache PDF or full-text
content — stores URLs only per Cambia's non-commercial terms.

NOTE: Lens.org v2 POST body schema verified against https://docs.api.lens.org
at implementation time (2026-06-10). Re-verify if queries return unexpected 400s.
"""
import time
import requests
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

from app.service_openalex import normalize_doi

LENS_BASE_URL = 'https://api.lens.org'


class LensClient:
    """Client for the Lens.org Scholar and Patent APIs (v2, POST-based)."""

    def __init__(
        self,
        scholar_api_key: str = '',
        patent_api_key: str = '',
        base_url: str = LENS_BASE_URL,
    ):
        self.scholar_api_key = scholar_api_key
        self.patent_api_key = patent_api_key
        self.base_url = base_url.rstrip('/')
        self.rate_limit_delay = 1.0
        self._last_request_time = 0.0
        self.session = requests.Session()
        self.timeout = 20

    def _make_post_request(self, endpoint: str, body: Dict, api_key: str) -> Optional[Dict]:
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()

        url = f"{self.base_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        try:
            response = self.session.post(url, json=body, headers=headers, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            if response.status_code == 401:
                logger.error("Lens.org auth error (401) — check API key")
                return None
            if response.status_code == 403:
                logger.error("Lens.org forbidden (403) — check non-commercial terms compliance")
                return None
            if response.status_code == 429:
                raw_retry = response.headers.get('Retry-After', '60')
                try:
                    retry_seconds = int(raw_retry)
                except ValueError:
                    retry_seconds = 60
                logger.warning("Lens.org rate-limited; retrying after %ds", retry_seconds)
                time.sleep(retry_seconds)
                self._last_request_time = time.time()
                response = self.session.post(url, json=body, headers=headers, timeout=self.timeout)
                if response.status_code == 200:
                    return response.json()
                return None
            if response.status_code >= 500:
                logger.error("Lens.org server error: %d", response.status_code)
                return None
            logger.error("Unexpected Lens.org response: %d — %s", response.status_code, response.text[:300])
            return None
        except requests.exceptions.Timeout:
            logger.error("Timeout calling Lens.org: %s", url)
            return None
        except requests.exceptions.RequestException as exc:
            logger.error("Network error calling Lens.org: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Scholar API
    # ------------------------------------------------------------------

    def get_scholar_by_doi(self, doi: str) -> Optional[Dict]:
        """Look up a scholarly work by DOI."""
        if not self.scholar_api_key:
            logger.warning("LENS_SCHOLAR_API_KEY not set — skipping scholar lookup")
            return None
        normalized = normalize_doi(doi)
        if not normalized:
            return None
        body = {
            "query": {
                "match": {"external_ids": {"value": normalized, "type": "doi"}}
            },
            "size": 1,
            "include": ["lens_id", "external_ids", "scholarly_citations_count",
                        "patent_citations", "title"],
        }
        resp = self._make_post_request('/scholarly/search', body, self.scholar_api_key)
        if not resp:
            return None
        results = resp.get('data') or []
        return results[0] if results else None

    def get_scholar_patent_citations(self, lens_scholar_id: str) -> List[Dict]:
        """Return patents that cite this scholarly work."""
        if not self.patent_api_key:
            return []
        body = {
            "query": {
                "match": {"npl_citations.lens_id": lens_scholar_id}
            },
            "size": 50,
            "include": ["lens_id", "doc_number", "jurisdiction", "kind",
                        "publication_date", "title"],
        }
        resp = self._make_post_request('/patent/search', body, self.patent_api_key)
        if not resp:
            return []
        return resp.get('data') or []

    # ------------------------------------------------------------------
    # Patent API
    # ------------------------------------------------------------------

    def get_patent_by_doi(self, doi: str) -> Optional[Dict]:
        """Look up a patent record by DOI (patents sometimes have DOIs)."""
        if not self.patent_api_key:
            return None
        normalized = normalize_doi(doi)
        if not normalized:
            return None
        body = {
            "query": {"match": {"external_ids": {"value": normalized, "type": "doi"}}},
            "size": 1,
            "include": ["lens_id", "doc_number", "jurisdiction", "kind",
                        "publication_date", "families", "title"],
        }
        resp = self._make_post_request('/patent/search', body, self.patent_api_key)
        if not resp:
            return None
        results = resp.get('data') or []
        return results[0] if results else None

    def get_patent_family(self, lens_id: str) -> List[Dict]:
        """Return all family members for a patent lens_id."""
        if not self.patent_api_key:
            return []
        body = {
            "query": {"match": {"family_id": lens_id}},
            "size": 50,
            "include": ["lens_id", "doc_number", "jurisdiction", "kind",
                        "publication_date", "title"],
        }
        resp = self._make_post_request('/patent/search', body, self.patent_api_key)
        if not resp:
            return []
        return resp.get('data') or []


class LensEnrichmentMapper:
    """Maps Lens.org API responses to DOCiD enrichment fields and edge dicts."""

    @classmethod
    def extract_scholar_enrichment(cls, scholar: Dict) -> Optional[Dict]:
        if not scholar or not isinstance(scholar, dict):
            return None
        return {
            'lens_scholar_id':        scholar.get('lens_id'),
            'scholarly_citation_count': scholar.get('scholarly_citations_count'),
        }

    @classmethod
    def extract_patent_enrichment(cls, patent: Dict) -> Optional[Dict]:
        if not patent or not isinstance(patent, dict):
            return None
        return {
            'lens_patent_id': patent.get('lens_id'),
        }

    @classmethod
    def extract_patent_family_edges(cls, source_lens_id: str, family_members: List[Dict]) -> List[Dict]:
        """Each family member becomes a patent_family_member edge."""
        edges = []
        for member in family_members:
            member_lens_id = member.get('lens_id')
            if not member_lens_id or member_lens_id == source_lens_id:
                continue
            edges.append({
                'object_id_kind': 'lens_patent_id',
                'object_id':      member_lens_id,
                'object_label':   (member.get('title') or [{}])[0].get('text') if isinstance(member.get('title'), list) else member.get('title'),
                'relation':       'patent_family_member',
                'source_name':    'lens_org',
                'confidence':     'high',
                'raw_metadata':   {
                    'jurisdiction':     member.get('jurisdiction'),
                    'doc_number':       member.get('doc_number'),
                    'kind':             member.get('kind'),
                    'publication_date': member.get('publication_date'),
                },
            })
        return edges

    @classmethod
    def extract_paper_cited_by_patent_edges(cls, citing_patents: List[Dict]) -> List[Dict]:
        """Each patent that cites this scholarly work becomes a paper_cited_by_patent edge."""
        edges = []
        for patent in citing_patents:
            lens_id = patent.get('lens_id')
            if not lens_id:
                continue
            edges.append({
                'object_id_kind': 'lens_patent_id',
                'object_id':      lens_id,
                'object_label':   (patent.get('title') or [{}])[0].get('text') if isinstance(patent.get('title'), list) else patent.get('title'),
                'relation':       'paper_cited_by_patent',
                'source_name':    'lens_org',
                'confidence':     'high',
                'raw_metadata':   {
                    'jurisdiction':     patent.get('jurisdiction'),
                    'doc_number':       patent.get('doc_number'),
                    'kind':             patent.get('kind'),
                    'publication_date': patent.get('publication_date'),
                },
            })
        return edges


# ---------------------------------------------------------------------------
# Fetch / apply / snapshot chain
# ---------------------------------------------------------------------------

LENS_APPLIED_COLUMNS = ('lens_scholar_id', 'lens_patent_id')


def snapshot_publication_lens_fields(publication) -> Dict:
    return {col: getattr(publication, col, None) for col in LENS_APPLIED_COLUMNS}


def restore_publication_from_snapshot(publication, snapshot: Dict) -> None:
    if not isinstance(snapshot, dict):
        return
    for col in LENS_APPLIED_COLUMNS:
        if col in snapshot:
            setattr(publication, col, snapshot[col])


def fetch_lens_candidate(
    publication,
    client: LensClient,
    mapper: LensEnrichmentMapper,
    performed_by: str = "system",
    fetch_family: bool = True,
    fetch_patent_citations: bool = True,
) -> Tuple[str, Optional[str], Optional[Dict]]:
    """
    Look up Lens.org metadata for a publication without mutating it.

    Returns (status, error_message, payload).
    payload on success:
        {
          "scholar":      <raw Lens scholar dict or None>,
          "patent":       <raw Lens patent dict or None>,
          "enrichment":   <dict with lens_scholar_id / lens_patent_id>,
          "edges":        [<edge dicts>],
          "provenance":   <dict>,
          "match_method": "doi",
        }
    """
    doi = getattr(publication, 'doi', None)
    normalized_doi = normalize_doi(doi) if doi else None
    if not normalized_doi or not normalized_doi.startswith('10.'):
        return 'skipped', 'no_valid_doi', None

    if not client.scholar_api_key and not client.patent_api_key:
        return 'auth_error', 'no_lens_api_keys_configured', None

    scholar = None
    patent = None
    enrichment: Dict = {}
    edges: List[Dict] = []

    # Scholar lookup
    try:
        scholar = client.get_scholar_by_doi(normalized_doi)
        if scholar:
            scholar_enr = mapper.extract_scholar_enrichment(scholar)
            if scholar_enr:
                enrichment.update(scholar_enr)
    except Exception as exc:
        logger.error("Transient error in Lens scholar lookup: %s", exc)
        return 'transient_error', str(exc), None

    # Patent lookup (for publications that are patents — lens_patent_id on the record)
    try:
        patent = client.get_patent_by_doi(normalized_doi)
        if patent:
            patent_enr = mapper.extract_patent_enrichment(patent)
            if patent_enr:
                enrichment.update(patent_enr)
    except Exception as exc:
        logger.error("Transient error in Lens patent lookup: %s", exc)
        return 'transient_error', str(exc), None

    if not scholar and not patent:
        return 'not_found', None, None

    # Patent family edges
    if fetch_family and patent and patent.get('lens_id'):
        try:
            family_members = client.get_patent_family(patent['lens_id'])
            edges.extend(mapper.extract_patent_family_edges(patent['lens_id'], family_members))
        except Exception as exc:
            logger.warning("Could not fetch Lens patent family (non-fatal): %s", exc)

    # Scholar-patent cross-citation edges (papers cited by patents)
    if fetch_patent_citations and scholar and scholar.get('lens_id'):
        try:
            citing_patents = client.get_scholar_patent_citations(scholar['lens_id'])
            edges.extend(mapper.extract_paper_cited_by_patent_edges(citing_patents))
        except Exception as exc:
            logger.warning("Could not fetch Lens scholar-patent citations (non-fatal): %s", exc)

    retrieved_at = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    source_url = ''
    if scholar and scholar.get('lens_id'):
        source_url = f"https://www.lens.org/lens/scholar/article/{scholar['lens_id']}"
    elif patent and patent.get('lens_id'):
        source_url = f"https://www.lens.org/lens/patent/{patent['lens_id']}"

    provenance = {
        "eventType":   "external_metadata_enrichment",
        "source":      "Lens.org",
        "sourceUrl":   source_url,
        "retrievedAt": retrieved_at,
        "matchedBy":   "doi",
        "confidence":  "high",
        "performedBy": performed_by,
        "status":      "accepted",
    }

    payload = {
        "scholar":      scholar,
        "patent":       patent,
        "enrichment":   enrichment,
        "edges":        edges,
        "provenance":   provenance,
        "match_method": "doi",
    }
    return 'enriched', None, payload


def apply_lens_enrichment_to_publication(publication, payload: Dict) -> None:
    """Apply fetched Lens candidate to Publication columns (no DB commit)."""
    if not payload:
        return
    enrichment = payload.get("enrichment") or {}
    if enrichment.get('lens_scholar_id'):
        publication.lens_scholar_id = enrichment['lens_scholar_id']
    if enrichment.get('lens_patent_id'):
        publication.lens_patent_id = enrichment['lens_patent_id']


def enrich_publication_lens(
    publication,
    client: LensClient,
    mapper: LensEnrichmentMapper,
    performed_by: str = "system",
) -> Tuple[str, Optional[str], Optional[Dict]]:
    """CLI-friendly wrapper: fetch + auto-apply."""
    status, error_message, payload = fetch_lens_candidate(
        publication, client, mapper, performed_by=performed_by,
    )
    if status == 'enriched' and payload:
        apply_lens_enrichment_to_publication(publication, payload)
    return status, error_message, payload
