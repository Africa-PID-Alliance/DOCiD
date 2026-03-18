"""
OpenAIRE API Client Service
Handles communication with the OpenAIRE Research Graph API for retrieving
publication metadata, project/funding information, and enrichment data
for DOCiD publications.
"""

import time
import requests
import logging
from typing import Dict, List, Optional

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


class OpenAIREClient:
    """Client for interacting with the OpenAIRE Research Graph API"""

    def __init__(self):
        """
        Initialize OpenAIRE client.

        OpenAIRE's public API does not require authentication but enforces
        rate limits. A polite delay of 0.6 seconds is applied between requests.
        """
        self.base_url = 'https://api.openaire.eu'
        self.rate_limit_delay = 0.6
        self.session = requests.Session()
        self.timeout = 15  # Request timeout in seconds

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Make HTTP GET request to OpenAIRE API with rate limiting.

        Implements polite rate limiting via time.sleep between requests,
        handles 429 (Too Many Requests) with Retry-After, 404, and 5xx errors.

        Args:
            endpoint: API endpoint path (e.g., /search/publications)
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
                headers={'Accept': 'application/json'},
                params=params,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()

            elif response.status_code == 429:
                retry_after_seconds = int(response.headers.get('Retry-After', 30))
                logger.warning(
                    f"Rate limited by OpenAIRE. "
                    f"Retrying after {retry_after_seconds} seconds."
                )
                time.sleep(retry_after_seconds)
                # Retry the request once after waiting
                response = self.session.get(
                    url=url,
                    headers={'Accept': 'application/json'},
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
                logger.info(f"Resource not found on OpenAIRE: {url}")
                return None

            elif response.status_code >= 500:
                logger.error(
                    f"OpenAIRE server error: "
                    f"{response.status_code} - {response.text[:500]}"
                )
                return None

            else:
                logger.error(
                    f"Unexpected response from OpenAIRE: "
                    f"{response.status_code} - {response.text[:500]}"
                )
                return None

        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for OpenAIRE: {url}")
            return None
        except requests.exceptions.RequestException as network_error:
            logger.error(f"Network error calling OpenAIRE: {str(network_error)}")
            return None

    def search_by_doi(self, doi: str) -> Optional[Dict]:
        """
        Search for a publication on OpenAIRE by DOI.

        Normalizes the DOI (strips URL prefixes) before querying.
        The response uses a deeply nested JSON structure; the first
        matching result is returned.

        Args:
            doi: DOI string (may include URL prefix like https://doi.org/)

        Returns:
            Publication result dictionary or None if not found
        """
        normalized_doi = normalize_doi(doi)
        if not normalized_doi:
            logger.warning(f"Invalid or empty DOI provided: {doi}")
            return None

        endpoint = "/search/publications"
        params = {
            'doi': normalized_doi,
            'format': 'json',
        }

        search_response = self._make_request(endpoint, params=params)

        if not search_response:
            return None

        # Navigate the deeply nested OpenAIRE response structure
        # Expected path: response -> results -> result -> [0]
        response_wrapper = search_response.get('response', {})
        response_header = response_wrapper.get('header', {})
        total_results_found = response_header.get('numFound', 0)

        if isinstance(total_results_found, str):
            try:
                total_results_found = int(total_results_found)
            except (ValueError, TypeError):
                total_results_found = 0

        if total_results_found == 0:
            logger.info(f"No OpenAIRE results for DOI: {normalized_doi}")
            return None

        results_container = response_wrapper.get('results', {})
        result_list = results_container.get('result', [])

        if not result_list:
            logger.info(f"Empty result list from OpenAIRE for DOI: {normalized_doi}")
            return None

        # Return the first matching result
        first_result = result_list[0] if isinstance(result_list, list) else result_list

        logger.info(f"Found OpenAIRE publication for DOI: {normalized_doi}")
        return first_result

    def get_projects_for_doi(self, doi: str) -> List[Dict]:
        """
        Extract project/funding information from an OpenAIRE publication result.

        Note: The OpenAIRE /search/projects endpoint does NOT support DOI
        as a query parameter. Instead, project info is embedded within the
        publication result's metadata (rels/rel entries).

        This method is kept for API compatibility but returns an empty list.
        Project data should be extracted from the publication result itself
        via the OpenAIREEnrichmentMapper.

        Args:
            doi: DOI string (unused — kept for interface compatibility)

        Returns:
            Empty list (project data comes from publication metadata)
        """
        # OpenAIRE /search/projects does not support DOI parameter
        # Project links are embedded in publication results instead
        return []


class OpenAIREEnrichmentMapper:
    """
    Maps OpenAIRE publication and project data to DOCiD enrichment fields.

    Handles the deeply nested OpenAIRE JSON response structure, using
    defensive .get() chains to gracefully handle missing or unexpected data.
    """

    @classmethod
    def extract_enrichment(
        cls,
        openaire_publication: Dict,
        projects: List[Dict] = None
    ) -> Optional[Dict]:
        """
        Extract enrichment fields from an OpenAIRE publication and its projects.

        Navigates the nested OpenAIRE response structure to extract the
        OpenAIRE identifier and linked project/funding information.

        Args:
            openaire_publication: Raw publication result dict from OpenAIRE API.
                Expected structure:
                    {
                      "header": {"dri:objIdentifier": "dedup_wf_001::..."},
                      "metadata": {"oaf:entity": {"oaf:result": {...}}}
                    }
            projects: Optional list of raw project result dicts from OpenAIRE API.

        Returns:
            Dictionary with enrichment fields:
                - openaire_id: The OpenAIRE deduplication identifier
                - projects: List of project dicts with title, acronym,
                            funder_name, and grant_id
            Returns None if openaire_publication is empty or invalid.
        """
        if not openaire_publication or not isinstance(openaire_publication, dict):
            logger.warning("Invalid or empty OpenAIRE publication data for enrichment")
            return None

        # --- Extract OpenAIRE identifier ---
        # Try direct path: header -> dri:objIdentifier
        openaire_identifier = None

        publication_header = openaire_publication.get('header', {})
        if isinstance(publication_header, dict):
            openaire_identifier = publication_header.get('dri:objIdentifier')

        # Fallback: result -> header -> dri:objIdentifier
        if not openaire_identifier:
            result_wrapper = openaire_publication.get('result', {})
            if isinstance(result_wrapper, dict):
                nested_header = result_wrapper.get('header', {})
                if isinstance(nested_header, dict):
                    openaire_identifier = nested_header.get('dri:objIdentifier')

        if openaire_identifier:
            logger.info(f"Extracted OpenAIRE ID: {openaire_identifier}")
        else:
            logger.warning("Could not extract OpenAIRE identifier from publication data")

        # --- Extract project/funding information ---
        extracted_projects = []

        if projects:
            for project_result in projects:
                extracted_project = cls._extract_single_project(project_result)
                if extracted_project:
                    extracted_projects.append(extracted_project)

        enrichment_data = {
            'openaire_id': openaire_identifier,
            'projects': extracted_projects,
        }

        logger.info(
            f"Extracted OpenAIRE enrichment: "
            f"id={openaire_identifier}, "
            f"projects={len(extracted_projects)}"
        )

        return enrichment_data

    @classmethod
    def _extract_single_project(cls, project_result: Dict) -> Optional[Dict]:
        """
        Extract structured project information from a single OpenAIRE project result.

        Navigates the nested project structure to pull out title, acronym,
        funder name, and grant ID.

        Args:
            project_result: Raw project result dict from OpenAIRE API

        Returns:
            Dictionary with project fields, or None if extraction fails
        """
        if not project_result or not isinstance(project_result, dict):
            return None

        # Navigate to the project metadata
        # Path: metadata -> oaf:entity -> oaf:project
        metadata_container = project_result.get('metadata', {})
        if not isinstance(metadata_container, dict):
            metadata_container = {}

        oaf_entity = metadata_container.get('oaf:entity', {})
        if not isinstance(oaf_entity, dict):
            oaf_entity = {}

        oaf_project = oaf_entity.get('oaf:project', {})
        if not isinstance(oaf_project, dict):
            oaf_project = {}

        project_title = oaf_project.get('title', {})
        # Title may be a dict with '$' key or a plain string
        if isinstance(project_title, dict):
            project_title = project_title.get('$', '')
        elif not isinstance(project_title, str):
            project_title = str(project_title) if project_title else ''

        project_acronym = oaf_project.get('acronym', {})
        if isinstance(project_acronym, dict):
            project_acronym = project_acronym.get('$', '')
        elif not isinstance(project_acronym, str):
            project_acronym = str(project_acronym) if project_acronym else ''

        # Funder information is typically nested under fundingtree
        funder_name = ''
        grant_identifier = ''

        funding_tree = oaf_project.get('fundingtree', {})
        if isinstance(funding_tree, list) and funding_tree:
            funding_tree = funding_tree[0]

        if isinstance(funding_tree, dict):
            funder_element = funding_tree.get('funder', {})
            if isinstance(funder_element, dict):
                funder_name_value = funder_element.get('name', {})
                if isinstance(funder_name_value, dict):
                    funder_name = funder_name_value.get('$', '')
                elif isinstance(funder_name_value, str):
                    funder_name = funder_name_value

        # Grant ID from the code field
        grant_code = oaf_project.get('code', {})
        if isinstance(grant_code, dict):
            grant_identifier = grant_code.get('$', '')
        elif isinstance(grant_code, str):
            grant_identifier = grant_code

        # Only return if we have at least a title or acronym
        if not project_title and not project_acronym:
            logger.info("Skipping project with no title or acronym")
            return None

        return {
            'title': project_title,
            'acronym': project_acronym,
            'funder_name': funder_name,
            'grant_id': grant_identifier,
        }
