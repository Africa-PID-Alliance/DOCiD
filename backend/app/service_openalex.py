"""
OpenAlex API Client Service
Handles communication with OpenAlex for scholarly metadata enrichment (works, authors, institutions)
"""

import time
import requests
import logging
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def normalize_doi(doi_string: str) -> Optional[str]:
    """
    Strip common DOI prefixes to get bare DOI like 10.1234/foo

    Args:
        doi_string: Raw DOI string that may include URL prefixes

    Returns:
        Normalized DOI string or None if input is empty/invalid
    """
    if not doi_string:
        return None
    doi = doi_string.strip()
    for prefix in [
        'https://doi.org/',
        'http://doi.org/',
        'https://dx.doi.org/',
        'http://dx.doi.org/',
        'doi:',
        'DOI:'
    ]:
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
    return doi.strip() if doi else None


class OpenAlexClient:
    """Client for interacting with the OpenAlex REST API (read-only operations)"""

    def __init__(self, contact_email: str):
        """
        Initialize OpenAlex client

        Args:
            contact_email: Email address for the OpenAlex polite pool
                           (requests with mailto get faster, more reliable access)
        """
        self.base_url = "https://api.openalex.org"
        self.contact_email = contact_email
        self.rate_limit_delay = 0.12  # 10 requests per second max
        self._last_request_time = None
        self.session = requests.Session()
        self.timeout = 15  # Request timeout in seconds

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Make HTTP GET request to OpenAlex API with rate limiting

        Args:
            endpoint: API endpoint (e.g., /works/doi:10.1234/foo)
            params: Query parameters

        Returns:
            Response JSON or None if request fails
        """
        # Enforce rate limiting
        if self._last_request_time is not None:
            elapsed_since_last_request = time.time() - self._last_request_time
            remaining_delay = self.rate_limit_delay - elapsed_since_last_request
            if remaining_delay > 0:
                time.sleep(remaining_delay)

        url = f"{self.base_url}{endpoint}"

        # Always include mailto for the polite pool
        request_params = params.copy() if params else {}
        request_params['mailto'] = self.contact_email

        try:
            logger.info(f"Making GET request to {url}")
            self._last_request_time = time.time()

            response = self.session.get(
                url=url,
                params=request_params,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                retry_after_seconds = int(response.headers.get('Retry-After', 1))
                logger.warning(
                    f"Rate limited by OpenAlex. Retrying after {retry_after_seconds}s"
                )
                time.sleep(retry_after_seconds)
                # Retry the request once
                self._last_request_time = time.time()
                retry_response = self.session.get(
                    url=url,
                    params=request_params,
                    timeout=self.timeout
                )
                if retry_response.status_code == 200:
                    return retry_response.json()
                else:
                    logger.error(
                        f"Retry failed: {retry_response.status_code} - {retry_response.text}"
                    )
                    return None
            elif response.status_code == 404:
                logger.warning(f"Resource not found: {url}")
                return None
            elif response.status_code >= 500:
                logger.error(
                    f"OpenAlex server error: {response.status_code} - {response.text}"
                )
                return None
            else:
                logger.error(f"Request failed: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {url}")
            return None
        except requests.exceptions.RequestException as network_error:
            logger.error(f"Request error: {str(network_error)}")
            return None

    # ==================== Work Endpoints ====================

    def get_work_by_doi(self, doi: str) -> Optional[Dict]:
        """
        Look up an OpenAlex Work by its DOI

        Args:
            doi: DOI string (with or without URL prefix)

        Returns:
            Full OpenAlex Work response dict or None if not found
        """
        normalized_doi = normalize_doi(doi)
        if not normalized_doi:
            logger.warning("Cannot look up work: DOI is empty after normalization")
            return None

        return self._make_request(f"/works/doi:{normalized_doi}")

    # ==================== Author Endpoints ====================

    def get_author_by_orcid(self, orcid_id: str) -> Optional[Dict]:
        """
        Look up an OpenAlex Author by their ORCID iD

        Args:
            orcid_id: ORCID identifier (e.g., 0000-0002-1234-5678)

        Returns:
            Full OpenAlex Author response dict or None if not found
        """
        if not orcid_id:
            logger.warning("Cannot look up author: ORCID iD is empty")
            return None

        return self._make_request(f"/authors/https://orcid.org/{orcid_id}")

    # ==================== Institution Endpoints ====================

    def get_institution_by_ror(self, ror_id: str) -> Optional[Dict]:
        """
        Look up an OpenAlex Institution by its ROR ID

        Args:
            ror_id: ROR identifier (e.g., 03czfpz43)

        Returns:
            Full OpenAlex Institution response dict or None if not found
        """
        if not ror_id:
            logger.warning("Cannot look up institution: ROR ID is empty")
            return None

        return self._make_request(f"/institutions/https://ror.org/{ror_id}")


class OpenAlexEnrichmentMapper:
    """
    Maps OpenAlex API responses to DOCiD enrichment fields.
    All methods are static/class methods — no instance state required.
    """

    @classmethod
    def extract_work_enrichment(cls, openalex_work: Dict) -> Dict:
        """
        Extract enrichment fields from an OpenAlex Work response

        Args:
            openalex_work: Full OpenAlex Work response dict

        Returns:
            Dictionary with enrichment fields:
                citation_count, open_access_status, open_access_url,
                openalex_id, topics, abstract
        """
        if not openalex_work:
            return {
                'citation_count': None,
                'open_access_status': None,
                'open_access_url': None,
                'openalex_id': None,
                'topics': None,
                'abstract': None,
            }

        # Citation count
        citation_count = openalex_work.get('cited_by_count')

        # Open access information
        open_access_data = openalex_work.get('open_access', {}) or {}
        open_access_status = open_access_data.get('oa_status')
        open_access_url = open_access_data.get('oa_url')

        # OpenAlex ID — strip the URL prefix to get just the ID (e.g., W1234567)
        raw_openalex_id = openalex_work.get('id')
        openalex_id = None
        if raw_openalex_id:
            openalex_id = raw_openalex_id.replace('https://openalex.org/', '')

        # Topics — extract top 5 as list of {name, score} dicts
        raw_topics = openalex_work.get('topics', []) or []
        topics = [
            {
                'name': topic.get('display_name'),
                'score': topic.get('score'),
            }
            for topic in raw_topics[:5]
        ]
        if not topics:
            topics = None

        # Abstract — reconstruct from inverted index
        abstract_inverted_index = openalex_work.get('abstract_inverted_index')
        abstract_text = cls._reconstruct_abstract(abstract_inverted_index)

        return {
            'citation_count': citation_count,
            'open_access_status': open_access_status,
            'open_access_url': open_access_url,
            'openalex_id': openalex_id,
            'topics': topics,
            'abstract': abstract_text,
        }

    @classmethod
    def extract_author_enrichment(cls, openalex_author: Dict) -> Dict:
        """
        Extract enrichment fields from an OpenAlex Author response

        Args:
            openalex_author: Full OpenAlex Author response dict

        Returns:
            Dictionary with enrichment fields:
                h_index, works_count, display_name, last_known_institutions
        """
        if not openalex_author:
            return {
                'h_index': None,
                'works_count': None,
                'display_name': None,
                'last_known_institutions': None,
            }

        # Summary metrics
        summary_stats = openalex_author.get('summary_stats', {}) or {}
        h_index = summary_stats.get('h_index')

        works_count = openalex_author.get('works_count')
        display_name = openalex_author.get('display_name')

        # Last known institutions
        raw_institutions = openalex_author.get('last_known_institutions', []) or []
        last_known_institutions = [
            {
                'display_name': institution.get('display_name'),
                'ror': institution.get('ror'),
                'country_code': institution.get('country_code'),
            }
            for institution in raw_institutions
        ]
        if not last_known_institutions:
            last_known_institutions = None

        return {
            'h_index': h_index,
            'works_count': works_count,
            'display_name': display_name,
            'last_known_institutions': last_known_institutions,
        }

    # ==================== Internal Helpers ====================

    @staticmethod
    def _reconstruct_abstract(abstract_inverted_index: Optional[Dict]) -> Optional[str]:
        """
        Reconstruct plain text abstract from OpenAlex inverted index format.

        OpenAlex stores abstracts as inverted indexes: {"word": [position1, position2], ...}
        To reconstruct: create (position, word) tuples, sort by position, join with spaces.

        Args:
            abstract_inverted_index: Inverted index dict from OpenAlex or None

        Returns:
            Reconstructed abstract string or None if index is missing
        """
        if not abstract_inverted_index:
            return None

        position_word_pairs: List[Tuple[int, str]] = []
        for word, positions in abstract_inverted_index.items():
            for position in positions:
                position_word_pairs.append((position, word))

        if not position_word_pairs:
            return None

        position_word_pairs.sort(key=lambda pair: pair[0])
        reconstructed_text = ' '.join(word for _, word in position_word_pairs)

        return reconstructed_text if reconstructed_text else None
