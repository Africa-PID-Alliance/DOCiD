"""
Semantic Scholar API Client Service
Handles communication with Semantic Scholar for retrieving paper metadata,
citation counts, and enrichment data for DOCiD publications.
"""

import time
import requests
import logging
from typing import Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def normalize_doi(doi_string: str) -> Optional[str]:
    """
    Normalize a DOI string by stripping common URL prefixes.

    Args:
        doi_string: Raw DOI string, possibly with URL prefix

    Returns:
        Cleaned DOI string or None if input is empty/invalid
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
        'DOI:',
    ]:
        if doi.startswith(prefix):
            doi = doi[len(prefix):]

    return doi.strip() if doi else None


class SemanticScholarClient:
    """Client for interacting with the Semantic Scholar Academic Graph API"""

    # Default fields to request when fetching paper details
    PAPER_DETAIL_FIELDS = (
        'citationCount,influentialCitationCount,abstract,tldr,'
        'externalIds,title,year,referenceCount,fieldsOfStudy'
    )

    # Fields to request when searching by title
    PAPER_SEARCH_FIELDS = (
        'citationCount,influentialCitationCount,abstract,externalIds,title'
    )

    def __init__(self, api_key: str = None):
        """
        Initialize Semantic Scholar client.

        Args:
            api_key: Optional API key for higher rate limits.
                     Without a key: ~100 requests per 5 minutes.
                     With a key: ~1,000 requests per 5 minutes.
        """
        self.base_url = 'https://api.semanticscholar.org/graph/v1'
        self.api_key = api_key
        self.rate_limit_delay = 1.1 if api_key else 3.1
        self.session = requests.Session()
        self.timeout = 15  # Request timeout in seconds

    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for API requests.

        Returns:
            Dictionary of HTTP headers including API key if configured
        """
        headers = {
            'Accept': 'application/json',
        }
        if self.api_key:
            headers['x-api-key'] = self.api_key
        return headers

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Make HTTP GET request to Semantic Scholar API with rate limiting.

        Implements polite rate limiting via time.sleep between requests,
        handles 429 (Too Many Requests) with Retry-After, 404, and 5xx errors.

        Args:
            endpoint: API endpoint path (e.g., /paper/DOI:10.1234/example)
            params: Optional query parameters

        Returns:
            Response JSON as dictionary, or None if request fails
        """
        url = f"{self.base_url}{endpoint}"

        # Rate limiting: wait between requests to respect API limits
        time.sleep(self.rate_limit_delay)

        try:
            logger.info(f"Making GET request to {url}")

            response = self.session.get(
                url=url,
                headers=self._get_headers(),
                params=params,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()

            elif response.status_code == 429:
                retry_after_seconds = int(response.headers.get('Retry-After', 30))
                logger.warning(
                    f"Rate limited by Semantic Scholar. "
                    f"Retrying after {retry_after_seconds} seconds."
                )
                time.sleep(retry_after_seconds)
                # Retry the request once after waiting
                response = self.session.get(
                    url=url,
                    headers=self._get_headers(),
                    params=params,
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    return response.json()
                logger.error(
                    f"Request failed after rate-limit retry: "
                    f"{response.status_code} - {response.text[:500]}"
                )
                return None

            elif response.status_code == 404:
                logger.info(f"Paper not found on Semantic Scholar: {url}")
                return None

            elif response.status_code >= 500:
                logger.error(
                    f"Semantic Scholar server error: "
                    f"{response.status_code} - {response.text[:500]}"
                )
                return None

            else:
                logger.error(
                    f"Unexpected response from Semantic Scholar: "
                    f"{response.status_code} - {response.text[:500]}"
                )
                return None

        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for Semantic Scholar: {url}")
            return None
        except requests.exceptions.RequestException as network_error:
            logger.error(f"Network error calling Semantic Scholar: {str(network_error)}")
            return None

    def get_paper_by_doi(self, doi: str) -> Optional[Dict]:
        """
        Retrieve paper metadata from Semantic Scholar using a DOI.

        Normalizes the DOI (strips URL prefixes) before querying. Requests
        citation counts, abstract, external IDs, and fields of study.

        Args:
            doi: DOI string (may include URL prefix like https://doi.org/)

        Returns:
            Paper metadata dictionary or None if not found
        """
        normalized_doi = normalize_doi(doi)
        if not normalized_doi:
            logger.warning(f"Invalid or empty DOI provided: {doi}")
            return None

        endpoint = f"/paper/DOI:{normalized_doi}"
        params = {'fields': self.PAPER_DETAIL_FIELDS}

        return self._make_request(endpoint, params=params)

    def get_paper_by_title(self, title: str) -> Optional[Dict]:
        """
        Search for a paper on Semantic Scholar by title.

        Returns the first (best) match from the search results. Useful when
        no DOI is available for a publication.

        Args:
            title: Paper title to search for

        Returns:
            Paper metadata dictionary for the best match, or None if no results
        """
        if not title or not title.strip():
            logger.warning("Empty title provided for Semantic Scholar search")
            return None

        endpoint = "/paper/search"
        params = {
            'query': title.strip(),
            'limit': 1,
            'fields': self.PAPER_SEARCH_FIELDS,
        }

        search_response = self._make_request(endpoint, params=params)

        if not search_response:
            return None

        search_results = search_response.get('data', [])
        if not search_results:
            logger.info(f"No Semantic Scholar results for title: {title[:80]}")
            return None

        return search_results[0]


class SemanticScholarEnrichmentMapper:
    """
    Maps Semantic Scholar paper data to DOCiD enrichment fields.

    Extracts citation metrics, abstract, and Semantic Scholar identifiers
    from raw API responses into a standardized enrichment dictionary.
    """

    @classmethod
    def extract_enrichment(cls, paper_data: Dict) -> Optional[Dict]:
        """
        Extract enrichment fields from a Semantic Scholar paper response.

        Args:
            paper_data: Raw paper data dictionary from Semantic Scholar API

        Returns:
            Dictionary with enrichment fields:
                - citation_count: Total citation count
                - influential_citation_count: Count of influential citations
                - abstract: Paper abstract (plain text)
                - semantic_scholar_id: Semantic Scholar paper ID
            Returns None if paper_data is empty or invalid.
        """
        if not paper_data or not isinstance(paper_data, dict):
            logger.warning("Invalid or empty paper data for enrichment extraction")
            return None

        enrichment_data = {
            'citation_count': paper_data.get('citationCount'),
            'influential_citation_count': paper_data.get('influentialCitationCount'),
            'abstract': paper_data.get('abstract'),
            'semantic_scholar_id': paper_data.get('paperId'),
        }

        logger.info(
            "Extracted Semantic Scholar enrichment: "
            f"citations={enrichment_data['citation_count']}, "
            f"influential={enrichment_data['influential_citation_count']}, "
            f"id={enrichment_data['semantic_scholar_id']}"
        )

        return enrichment_data
