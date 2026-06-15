"""
Semantic Scholar API Client Service — extends client + mapper with the
fetch/apply/snapshot chain and reference/citation edge emission.
"""
import time
import urllib.parse
import requests
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Import shared normalizer so we don't redefine it.
from app.service_openalex import normalize_doi


class SemanticScholarClient:
    """Client for the Semantic Scholar Academic Graph API v1."""

    PAPER_DETAIL_FIELDS = (
        'paperId,citationCount,influentialCitationCount,abstract,tldr,'
        'externalIds,title,year,referenceCount,fieldsOfStudy'
    )
    PAPER_SEARCH_FIELDS = (
        'paperId,citationCount,influentialCitationCount,abstract,externalIds,title'
    )
    REFERENCE_FIELDS = 'paperId,externalIds,title,year'
    CITATION_FIELDS  = 'paperId,externalIds,title,year'

    def __init__(self, api_key: str = None):
        self.base_url = 'https://api.semanticscholar.org/graph/v1'
        self.api_key = api_key
        self.rate_limit_delay = 1.1 if api_key else 3.1
        self._last_request_time = 0.0
        self.session = requests.Session()
        self.timeout = 15

    def _get_headers(self) -> Dict[str, str]:
        headers = {'Accept': 'application/json'}
        if self.api_key:
            headers['x-api-key'] = self.api_key
        return headers

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
            if response.status_code == 429:
                raw_retry = response.headers.get('Retry-After', '30')
                try:
                    retry_seconds = int(raw_retry)
                except ValueError:
                    retry_seconds = 30
                logger.warning("Semantic Scholar rate-limited; retrying after %ds", retry_seconds)
                time.sleep(retry_seconds)
                self._last_request_time = time.time()
                response = self.session.get(url, headers=self._get_headers(),
                                            params=params, timeout=self.timeout)
                if response.status_code == 200:
                    return response.json()
                logger.error("Retry failed: %d", response.status_code)
                return None
            if response.status_code == 404:
                return None
            if response.status_code in (401, 403):
                logger.error("Semantic Scholar auth error: %d", response.status_code)
                return None
            if response.status_code >= 500:
                logger.error("Semantic Scholar server error: %d", response.status_code)
                return None
            logger.error("Unexpected Semantic Scholar response: %d", response.status_code)
            return None
        except requests.exceptions.Timeout:
            logger.error("Timeout calling Semantic Scholar: %s", url)
            return None
        except requests.exceptions.RequestException as exc:
            logger.error("Network error calling Semantic Scholar: %s", exc)
            return None

    def get_paper_by_doi(self, doi: str) -> Optional[Dict]:
        normalized = normalize_doi(doi)
        if not normalized:
            return None
        encoded = urllib.parse.quote(normalized, safe='')
        return self._make_request(f"/paper/DOI:{encoded}",
                                  params={'fields': self.PAPER_DETAIL_FIELDS})

    def get_paper_by_id(self, paper_id: str) -> Optional[Dict]:
        return self._make_request(f"/paper/{paper_id}",
                                  params={'fields': self.PAPER_DETAIL_FIELDS})

    def search_papers_by_title(self, title: str, limit: int = 1) -> List[Dict]:
        if not title or not title.strip():
            return []
        resp = self._make_request('/paper/search',
                                  params={'query': title.strip(), 'limit': limit,
                                          'fields': self.PAPER_SEARCH_FIELDS})
        if not resp:
            return []
        return resp.get('data', [])

    def get_paper_references(self, paper_id: str, limit: int = 100) -> List[Dict]:
        """Return up to `limit` papers that this paper cites."""
        result = []
        offset = 0
        while len(result) < limit:
            batch_size = min(100, limit - len(result))
            resp = self._make_request(
                f"/paper/{paper_id}/references",
                params={'fields': self.REFERENCE_FIELDS, 'limit': batch_size, 'offset': offset},
            )
            if not resp:
                break
            batch = [item.get('citedPaper', {}) for item in resp.get('data', [])]
            result.extend(batch)
            if len(resp.get('data', [])) < batch_size:
                break
            offset += batch_size
        return result[:limit]

    def get_paper_citations(self, paper_id: str, limit: int = 100) -> List[Dict]:
        """Return up to `limit` papers that cite this paper."""
        result = []
        offset = 0
        while len(result) < limit:
            batch_size = min(100, limit - len(result))
            resp = self._make_request(
                f"/paper/{paper_id}/citations",
                params={'fields': self.CITATION_FIELDS, 'limit': batch_size, 'offset': offset},
            )
            if not resp:
                break
            batch = [item.get('citingPaper', {}) for item in resp.get('data', [])]
            result.extend(batch)
            if len(resp.get('data', [])) < batch_size:
                break
            offset += batch_size
        return result[:limit]


class SemanticScholarEnrichmentMapper:
    """Maps Semantic Scholar paper data to DOCiD enrichment fields and edge dicts."""

    @classmethod
    def extract_paper_enrichment(cls, paper: Dict) -> Optional[Dict]:
        if not paper or not isinstance(paper, dict):
            return None
        abstract_text = paper.get('abstract')
        if not abstract_text:
            tldr = paper.get('tldr') or {}
            abstract_text = tldr.get('text')
        return {
            'citation_count':             paper.get('citationCount'),
            'influential_citation_count': paper.get('influentialCitationCount'),
            'semantic_scholar_id':        paper.get('paperId'),
            'abstract':                   abstract_text,
            'fields_of_study':            paper.get('fieldsOfStudy') or [],
        }

    # Legacy alias so existing callers (enrich_metadata.py) keep working.
    @classmethod
    def extract_enrichment(cls, paper: Dict) -> Optional[Dict]:
        return cls.extract_paper_enrichment(paper)

    @classmethod
    def extract_reference_edges(cls, paper_id: str, references: List[Dict]) -> List[Dict]:
        """
        Convert a list of referenced papers into edge dicts for publication_external_edges.
        relation='cites', object is the cited paper.
        """
        edges = []
        for ref in references:
            doi = (ref.get('externalIds') or {}).get('DOI')
            ss_id = ref.get('paperId')
            if doi:
                object_id_kind = 'doi'
                object_id = normalize_doi(doi)
            elif ss_id:
                object_id_kind = 'semantic_scholar_id'
                object_id = ss_id
            else:
                continue
            edges.append({
                'object_id_kind': object_id_kind,
                'object_id':      object_id,
                'object_label':   ref.get('title'),
                'relation':       'cites',
                'source_name':    'semantic_scholar',
                'confidence':     'high',
                'raw_metadata':   {'year': ref.get('year'), 'ss_paper_id': ss_id},
            })
        return edges

    @classmethod
    def extract_citation_edges(cls, paper_id: str, citations: List[Dict]) -> List[Dict]:
        """
        Convert a list of citing papers into edge dicts.
        relation='cited_by', object is the citing paper.
        """
        edges = []
        for cit in citations:
            doi = (cit.get('externalIds') or {}).get('DOI')
            ss_id = cit.get('paperId')
            if doi:
                object_id_kind = 'doi'
                object_id = normalize_doi(doi)
            elif ss_id:
                object_id_kind = 'semantic_scholar_id'
                object_id = ss_id
            else:
                continue
            edges.append({
                'object_id_kind': object_id_kind,
                'object_id':      object_id,
                'object_label':   cit.get('title'),
                'relation':       'cited_by',
                'source_name':    'semantic_scholar',
                'confidence':     'high',
                'raw_metadata':   {'year': cit.get('year'), 'ss_paper_id': ss_id},
            })
        return edges


# ---------------------------------------------------------------------------
# Fetch / apply / snapshot chain
# ---------------------------------------------------------------------------

SEMANTIC_SCHOLAR_APPLIED_COLUMNS = (
    'citation_count',
    'semantic_scholar_id',
    'abstract_text',
)


def snapshot_publication_semantic_scholar_fields(publication) -> Dict:
    return {col: getattr(publication, col, None) for col in SEMANTIC_SCHOLAR_APPLIED_COLUMNS}


def restore_publication_from_snapshot(publication, snapshot: Dict) -> None:
    if not isinstance(snapshot, dict):
        return
    for col in SEMANTIC_SCHOLAR_APPLIED_COLUMNS:
        if col in snapshot:
            setattr(publication, col, snapshot[col])


def fetch_semantic_scholar_candidate(
    publication,
    client: SemanticScholarClient,
    mapper: SemanticScholarEnrichmentMapper,
    performed_by: str = "system",
    allow_title_fallback: bool = False,
    fetch_edges: bool = True,
    edge_limit: int = 100,
) -> Tuple[str, Optional[str], Optional[Dict]]:
    """
    Look up Semantic Scholar metadata for a publication without mutating it.

    Returns (status, error_message, payload).
    payload on success:
        {
          "paper":       <raw SS paper dict>,
          "enrichment":  <mapper.extract_paper_enrichment output>,
          "edges":       [<edge dicts for publication_external_edges>],
          "provenance":  <dict>,
          "match_method": "doi" | "title_search",
        }
    status values follow the 7-way enum: enriched | not_found | skipped |
    transient_error | auth_error | quota_exhausted | malformed_response
    """
    from app.service_openalex import normalize_doi as _norm_doi
    normalized_doi = _norm_doi(publication.doi) if getattr(publication, 'doi', None) else None
    paper = None
    match_method = None

    if normalized_doi:
        try:
            paper = client.get_paper_by_doi(normalized_doi)
            if paper:
                match_method = 'doi'
        except Exception as exc:
            logger.error("Transient error fetching Semantic Scholar by DOI: %s", exc)
            return 'transient_error', str(exc), None

    if not paper and allow_title_fallback and getattr(publication, 'document_title', None):
        try:
            results = client.search_papers_by_title(publication.document_title, limit=1)
            if results:
                paper = results[0]
                match_method = 'title_search'
        except Exception as exc:
            logger.error("Transient error in Semantic Scholar title search: %s", exc)
            return 'transient_error', str(exc), None

    if not paper:
        if not normalized_doi and not allow_title_fallback:
            return 'skipped', 'no_valid_doi', None
        return 'not_found', None, None

    try:
        enrichment_data = mapper.extract_paper_enrichment(paper)
    except Exception as exc:
        logger.error("Malformed Semantic Scholar response: %s", exc)
        return 'malformed_response', str(exc), None

    if not enrichment_data:
        return 'malformed_response', 'mapper returned None', None

    edges = []
    paper_id = paper.get('paperId')
    if fetch_edges and paper_id:
        try:
            refs = client.get_paper_references(paper_id, limit=edge_limit)
            edges.extend(mapper.extract_reference_edges(paper_id, refs))
            cits = client.get_paper_citations(paper_id, limit=edge_limit)
            edges.extend(mapper.extract_citation_edges(paper_id, cits))
        except Exception as exc:
            logger.warning("Could not fetch SS edges (non-fatal): %s", exc)

    retrieved_at = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    confidence = 'high' if match_method == 'doi' else 'review_required'
    provenance = {
        "eventType":   "external_metadata_enrichment",
        "source":      "Semantic Scholar",
        "sourceUrl":   f"https://www.semanticscholar.org/paper/{paper.get('paperId', '')}",
        "retrievedAt": retrieved_at,
        "matchedBy":   match_method,
        "confidence":  confidence,
        "performedBy": performed_by,
        "status":      'accepted' if confidence == 'high' else 'pending_review',
    }

    payload = {
        "paper":        paper,
        "enrichment":   enrichment_data,
        "edges":        edges,
        "provenance":   provenance,
        "match_method": match_method,
    }
    return 'enriched', None, payload


def apply_semantic_scholar_enrichment_to_publication(publication, payload: Dict) -> None:
    """Apply a fetched Semantic Scholar candidate to Publication columns (no DB commit)."""
    if not payload:
        return
    enrichment = payload.get("enrichment") or {}
    if enrichment.get('citation_count') is not None:
        publication.citation_count = enrichment['citation_count']
    if enrichment.get('semantic_scholar_id'):
        publication.semantic_scholar_id = enrichment['semantic_scholar_id']
    if enrichment.get('abstract') and not getattr(publication, 'abstract_text', None):
        publication.abstract_text = enrichment['abstract']


def enrich_publication_semantic_scholar(
    publication,
    client: SemanticScholarClient,
    mapper: SemanticScholarEnrichmentMapper,
    performed_by: str = "system",
    allow_title_fallback: bool = False,
) -> Tuple[str, Optional[str], Optional[Dict]]:
    """CLI-friendly wrapper: fetch + auto-apply."""
    status, error_message, payload = fetch_semantic_scholar_candidate(
        publication, client, mapper,
        performed_by=performed_by,
        allow_title_fallback=allow_title_fallback,
    )
    if status == 'enriched' and payload:
        apply_semantic_scholar_enrichment_to_publication(publication, payload)
    return status, error_message, payload
