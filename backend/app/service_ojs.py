"""
OJS (Open Journal Systems) REST API Client Service
Handles communication with OJS repositories for journal submissions and articles
"""

import requests
import logging
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class OJSClient:
    """Client for interacting with OJS REST API (OJS 3.x)"""

    def __init__(self, base_url: str, api_key: str = None):
        """
        Initialize OJS client

        Args:
            base_url: OJS API base URL (e.g., https://your-journal.org/api/v1)
            api_key: API key for authenticated requests
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.timeout = 30  # Request timeout in seconds

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        return headers

    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Optional[Dict]:
        """
        Make HTTP request to OJS API

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., /submissions)
            params: Query parameters
            data: Request body data

        Returns:
            Response JSON or None if request fails
        """
        url = f"{self.base_url}{endpoint}"

        try:
            logger.info(f"Making {method} request to {url}")

            response = self.session.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                params=params,
                json=data,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                logger.error("OJS API authentication failed - check API key")
                return None
            elif response.status_code == 403:
                logger.error("OJS API access forbidden - insufficient permissions")
                return None
            elif response.status_code == 404:
                logger.warning(f"Resource not found: {url}")
                return None
            else:
                logger.error(f"Request failed: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {url}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for {url} - OJS instance may be unavailable")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return None

    # ==================== Submissions Endpoints ====================

    def get_submissions(self, status: str = None, page: int = 1, per_page: int = 20,
                        search_phrase: str = None, is_incomplete: bool = None) -> Dict:
        """
        Get list of submissions (requires authentication)

        Args:
            status: Filter by status (1=queued, 3=scheduled, 4=published, 5=declined)
            page: Page number (1-indexed)
            per_page: Results per page (max 100)
            search_phrase: Search in title and authors
            is_incomplete: Filter incomplete submissions

        Returns:
            Dictionary containing submissions list and pagination info
        """
        if not self.api_key:
            logger.warning("API key required for submissions endpoint")
            return {'items': [], 'error': 'API key required'}

        params = {
            'offset': (page - 1) * per_page,
            'count': min(per_page, 100)
        }

        if status:
            params['status'] = status
        if search_phrase:
            params['searchPhrase'] = search_phrase
        if is_incomplete is not None:
            params['isIncomplete'] = is_incomplete

        result = self._make_request('GET', '/submissions', params=params)

        return {
            'items': result.get('items', []) if result else [],
            'itemsMax': result.get('itemsMax', 0) if result else 0,
            'page': page,
            'per_page': per_page
        }

    def get_submission(self, submission_id: int) -> Optional[Dict]:
        """
        Get details of a specific submission

        Args:
            submission_id: OJS submission ID

        Returns:
            Submission data dictionary or None if not found
        """
        if not self.api_key:
            logger.warning("API key required for submission details")
            return None

        return self._make_request('GET', f'/submissions/{submission_id}')

    def search_submissions(self, query: str, page: int = 1, per_page: int = 20) -> Dict:
        """
        Search submissions by title and authors

        Args:
            query: Search query string
            page: Page number (1-indexed)
            per_page: Results per page

        Returns:
            Dictionary containing search results
        """
        return self.get_submissions(search_phrase=query, page=page, per_page=per_page)

    # ==================== Issues Endpoints ====================

    def get_issues(self, page: int = 1, per_page: int = 20, is_published: bool = True) -> Dict:
        """
        Get list of journal issues

        Args:
            page: Page number (1-indexed)
            per_page: Results per page
            is_published: Filter by published status

        Returns:
            Dictionary containing issues list and pagination info
        """
        params = {
            'offset': (page - 1) * per_page,
            'count': min(per_page, 100),
            'isPublished': is_published
        }

        result = self._make_request('GET', '/issues', params=params)

        return {
            'items': result.get('items', []) if result else [],
            'itemsMax': result.get('itemsMax', 0) if result else 0,
            'page': page,
            'per_page': per_page
        }

    def get_issue(self, issue_id: int) -> Optional[Dict]:
        """
        Get details of a specific issue

        Args:
            issue_id: OJS issue ID

        Returns:
            Issue data dictionary or None if not found
        """
        return self._make_request('GET', f'/issues/{issue_id}')

    def get_current_issue(self) -> Optional[Dict]:
        """
        Get the current (most recent published) issue

        Returns:
            Current issue data or None if not found
        """
        return self._make_request('GET', '/issues/current')

    # ==================== Announcements Endpoints ====================

    def get_announcements(self, page: int = 1, per_page: int = 20) -> Dict:
        """
        Get list of announcements

        Args:
            page: Page number (1-indexed)
            per_page: Results per page

        Returns:
            Dictionary containing announcements list
        """
        params = {
            'offset': (page - 1) * per_page,
            'count': min(per_page, 100)
        }

        result = self._make_request('GET', '/announcements', params=params)

        return {
            'items': result.get('items', []) if result else [],
            'itemsMax': result.get('itemsMax', 0) if result else 0,
            'page': page,
            'per_page': per_page
        }

    # ==================== Context (Journal) Info ====================

    def get_context(self) -> Optional[Dict]:
        """
        Get journal/context information

        Returns:
            Journal context data or None if not found
        """
        return self._make_request('GET', '/contexts')

    # ==================== Utility Methods ====================

    def is_configured(self) -> bool:
        """Check if client has API key configured"""
        return bool(self.api_key)

    def test_connection(self) -> Dict:
        """
        Test connection to OJS API

        Returns:
            Dictionary with connection status and details
        """
        if not self.base_url or self.base_url == 'https://your-ojs-instance.com/api/v1':
            return {
                'status': 'not_configured',
                'message': 'OJS base URL not configured',
                'base_url': self.base_url
            }

        try:
            # Try to get issues (public endpoint)
            response = self.session.get(
                f"{self.base_url}/issues",
                headers=self._get_headers(),
                params={'count': 1},
                timeout=10
            )

            if response.status_code == 200:
                return {
                    'status': 'connected',
                    'authenticated': self.is_configured(),
                    'base_url': self.base_url
                }
            elif response.status_code == 401:
                return {
                    'status': 'auth_error',
                    'error': 'Authentication failed',
                    'base_url': self.base_url
                }
            else:
                return {
                    'status': 'error',
                    'error': f'HTTP {response.status_code}',
                    'base_url': self.base_url
                }

        except requests.exceptions.ConnectionError:
            return {
                'status': 'unreachable',
                'error': 'Could not connect to OJS instance',
                'base_url': self.base_url
            }
        except requests.exceptions.RequestException as e:
            return {
                'status': 'error',
                'error': str(e),
                'base_url': self.base_url
            }


class OJSMetadataMapper:
    """
    Maps OJS submission/article metadata to DOCiD publication format
    """

    @classmethod
    def ojs_to_docid(cls, ojs_submission: Dict, user_id: int) -> Dict:
        """
        Transform OJS submission to DOCiD publication format

        Args:
            ojs_submission: OJS submission data
            user_id: DOCiD user ID who will own the publication

        Returns:
            Dictionary ready for Publications model creation
        """
        # Extract publication info (multilingual support - get primary locale)
        publication = ojs_submission.get('publications', [{}])[0] if ojs_submission.get('publications') else {}

        # Extract title (handle multilingual)
        title_data = publication.get('title', {})
        title = cls._get_localized_value(title_data) or ojs_submission.get('title', 'Untitled')

        # Extract abstract/description
        abstract_data = publication.get('abstract', {})
        description = cls._get_localized_value(abstract_data) or ''

        # Extract DOI if available
        doi = publication.get('doi', '') or ''

        # Build OJS identifiers
        ojs_submission_id = str(ojs_submission.get('id', ''))
        ojs_url = publication.get('urlPublished', '') or ''

        # Build publication data
        publication_data = {
            'user_id': user_id,
            'document_title': title,
            'document_description': description,
            'resource_type': 'Text',  # OJS is primarily for articles
            'doi': doi,
            'ojs_submission_id': ojs_submission_id,
            'ojs_url': ojs_url,
        }

        # Extract creators/authors
        creators = []
        for author in publication.get('authors', []):
            given_name = cls._get_localized_value(author.get('givenName', {}))
            family_name = cls._get_localized_value(author.get('familyName', {}))
            full_name = f"{given_name} {family_name}".strip()

            creators.append({
                'creator_name': full_name,
                'creator_role': 'Author',
                'orcid_id': author.get('orcid'),
                'affiliation': cls._get_localized_value(author.get('affiliation', {})),
            })

        # Extract keywords
        keywords_data = publication.get('keywords', {})
        keywords = cls._get_localized_value(keywords_data) or []

        # Extract subjects/categories
        subjects_data = publication.get('subjects', {})
        subjects = cls._get_localized_value(subjects_data) or []

        return {
            'publication': publication_data,
            'creators': creators,
            'keywords': keywords if isinstance(keywords, list) else [],
            'subjects': subjects if isinstance(subjects, list) else [],
            'extended_metadata': {
                'ojs_submission_id': ojs_submission_id,
                'ojs_url': ojs_url,
                'status': ojs_submission.get('status'),
                'stage_id': ojs_submission.get('stageId'),
                'date_submitted': ojs_submission.get('dateSubmitted'),
                'date_published': publication.get('datePublished'),
                'issue_id': publication.get('issueId'),
                'section_id': publication.get('sectionId'),
                'pages': publication.get('pages'),
                'license_url': publication.get('licenseUrl'),
            }
        }

    @staticmethod
    def _get_localized_value(data: Dict, locale: str = 'en') -> Optional[str]:
        """
        Get value from OJS multilingual field

        Args:
            data: Dictionary with locale keys (e.g., {'en': 'value', 'fr': 'valeur'})
            locale: Preferred locale (default: 'en')

        Returns:
            String value for the locale or first available value
        """
        if not data or not isinstance(data, dict):
            return data if isinstance(data, str) else None

        # Try preferred locale first
        if locale in data:
            return data[locale]

        # Try English as fallback
        if 'en' in data:
            return data['en']

        # Return first available value
        for value in data.values():
            if value:
                return value

        return None
