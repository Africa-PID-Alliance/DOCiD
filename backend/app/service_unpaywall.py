"""
Unpaywall API Client Service
Handles communication with Unpaywall for open access status and PDF availability lookups
"""

import time
import requests
import logging
from typing import Dict, Optional

from app.service_openalex import normalize_doi

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class UnpaywallClient:
    """Client for interacting with the Unpaywall REST API (read-only operations)"""

    def __init__(self, contact_email: str):
        """
        Initialize Unpaywall client

        Args:
            contact_email: Email address required by Unpaywall for API access
                           (all requests must include an email parameter)
        """
        self.base_url = "https://api.unpaywall.org"
        self.contact_email = contact_email
        self.rate_limit_delay = 0.01  # 100 requests per second max
        self._last_request_time = None
        self.session = requests.Session()
        self.timeout = 15  # Request timeout in seconds

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Make HTTP GET request to Unpaywall API with rate limiting

        Args:
            endpoint: API endpoint (e.g., /v2/10.1234/foo)
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

        # Always include email for API access
        request_params = params.copy() if params else {}
        request_params['email'] = self.contact_email

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
                    f"Rate limited by Unpaywall. Retrying after {retry_after_seconds}s"
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
                    f"Unpaywall server error: {response.status_code} - {response.text}"
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

    # ==================== OA Status Endpoint ====================

    def get_oa_status(self, doi: str) -> Optional[Dict]:
        """
        Look up open access status and best available PDF for a given DOI

        Args:
            doi: DOI string (with or without URL prefix)

        Returns:
            Full Unpaywall response dict or None if not found
        """
        normalized_doi = normalize_doi(doi)
        if not normalized_doi:
            logger.warning("Cannot look up OA status: DOI is empty after normalization")
            return None

        return self._make_request(f"/v2/{normalized_doi}")


class UnpaywallEnrichmentMapper:
    """
    Maps Unpaywall API responses to DOCiD enrichment fields.
    All methods are static/class methods — no instance state required.
    """

    @classmethod
    def extract_enrichment(cls, unpaywall_response: Dict) -> Dict:
        """
        Extract enrichment fields from an Unpaywall response

        Args:
            unpaywall_response: Full Unpaywall API response dict

        Returns:
            Dictionary with enrichment fields:
                open_access_status, open_access_url
        """
        if not unpaywall_response:
            return {
                'open_access_status': None,
                'open_access_url': None,
            }

        # Determine open access status
        is_open_access = unpaywall_response.get('is_oa', False)
        if not is_open_access:
            open_access_status = 'closed'
        else:
            open_access_status = unpaywall_response.get('oa_status', 'closed')

        # Best available open access URL — prefer PDF, fall back to landing page
        best_oa_location = unpaywall_response.get('best_oa_location', {}) or {}
        open_access_url = best_oa_location.get('url_for_pdf')
        if not open_access_url:
            open_access_url = best_oa_location.get('url')

        return {
            'open_access_status': open_access_status,
            'open_access_url': open_access_url,
        }
