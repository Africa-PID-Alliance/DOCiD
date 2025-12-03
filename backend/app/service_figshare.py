"""
Figshare REST API Client Service
Handles communication with Figshare repository for searching and retrieving articles/datasets
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


class FigshareClient:
    """Client for interacting with Figshare REST API (read-only operations)"""

    def __init__(self, base_url: str, api_token: str = None):
        """
        Initialize Figshare client

        Args:
            base_url: Figshare API base URL (e.g., https://api.figshare.com/v2)
            api_token: Optional personal access token for authenticated requests
        """
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.session = requests.Session()
        self.timeout = 30  # Request timeout in seconds

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        if self.api_token:
            headers['Authorization'] = f'token {self.api_token}'
        return headers

    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Optional[Dict]:
        """
        Make HTTP request to Figshare API

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., /articles)
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
            elif response.status_code == 404:
                logger.warning(f"Resource not found: {url}")
                return None
            else:
                logger.error(f"Request failed: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return None

    # ==================== Public Endpoints (No Auth Required) ====================

    def search_articles(self, query: str, page: int = 1, page_size: int = 10,
                        item_type: str = None, order: str = 'published_date',
                        order_direction: str = 'desc') -> Dict:
        """
        Search for public articles/datasets on Figshare

        Args:
            query: Search query string
            page: Page number (1-indexed)
            page_size: Number of results per page (max 1000)
            item_type: Filter by type (1=figure, 2=media, 3=dataset, 4=fileset,
                       5=poster, 6=journal contribution, 7=presentation,
                       8=thesis, 9=software, 11=online resource, 12=preprint,
                       13=book, 14=conference contribution, 15=chapter,
                       16=peer review, 17=educational resource)
            order: Sort field (published_date, modified_date, views, shares, downloads, cites)
            order_direction: Sort direction (asc, desc)

        Returns:
            Dictionary containing search results and pagination info
        """
        params = {
            'search_for': query,
            'page': page,
            'page_size': min(page_size, 1000),  # Figshare max is 1000
            'order': order,
            'order_direction': order_direction
        }

        if item_type:
            params['item_type'] = item_type

        result = self._make_request('GET', '/articles', params=params)

        return {
            'articles': result if result else [],
            'page': page,
            'page_size': page_size,
            'query': query
        }

    def get_article(self, article_id: int) -> Optional[Dict]:
        """
        Get details of a public article by ID

        Args:
            article_id: Figshare article ID

        Returns:
            Article data dictionary or None if not found
        """
        return self._make_request('GET', f'/articles/{article_id}')

    def get_article_files(self, article_id: int) -> List[Dict]:
        """
        Get files associated with a public article

        Args:
            article_id: Figshare article ID

        Returns:
            List of file dictionaries
        """
        result = self._make_request('GET', f'/articles/{article_id}/files')
        return result if result else []

    def get_article_versions(self, article_id: int) -> List[Dict]:
        """
        Get version history of a public article

        Args:
            article_id: Figshare article ID

        Returns:
            List of version dictionaries
        """
        result = self._make_request('GET', f'/articles/{article_id}/versions')
        return result if result else []

    def get_article_version(self, article_id: int, version_id: int) -> Optional[Dict]:
        """
        Get specific version of an article

        Args:
            article_id: Figshare article ID
            version_id: Version number

        Returns:
            Article version data or None if not found
        """
        return self._make_request('GET', f'/articles/{article_id}/versions/{version_id}')

    # ==================== Private Endpoints (Auth Required) ====================

    def get_my_articles(self, page: int = 1, page_size: int = 10) -> Dict:
        """
        Get authenticated user's articles (requires API token)

        Args:
            page: Page number (1-indexed)
            page_size: Number of results per page

        Returns:
            Dictionary containing user's articles and pagination info
        """
        if not self.api_token:
            logger.warning("API token required for private endpoints")
            return {'articles': [], 'error': 'API token required'}

        params = {
            'page': page,
            'page_size': min(page_size, 1000)
        }

        result = self._make_request('GET', '/account/articles', params=params)

        return {
            'articles': result if result else [],
            'page': page,
            'page_size': page_size
        }

    def get_private_article(self, article_id: int) -> Optional[Dict]:
        """
        Get details of user's private article (requires API token)

        Args:
            article_id: Figshare article ID

        Returns:
            Article data dictionary or None if not found
        """
        if not self.api_token:
            logger.warning("API token required for private endpoints")
            return None

        return self._make_request('GET', f'/account/articles/{article_id}')

    # ==================== Utility Methods ====================

    def is_configured(self) -> bool:
        """Check if client has API token configured"""
        return bool(self.api_token)

    def test_connection(self) -> Dict:
        """
        Test connection to Figshare API

        Returns:
            Dictionary with connection status and details
        """
        try:
            # Test with a simple public search
            response = self.session.get(
                f"{self.base_url}/articles",
                headers=self._get_headers(),
                params={'page_size': 1},
                timeout=10
            )

            if response.status_code == 200:
                return {
                    'status': 'connected',
                    'authenticated': self.is_configured(),
                    'base_url': self.base_url
                }
            else:
                return {
                    'status': 'error',
                    'error': f'HTTP {response.status_code}',
                    'base_url': self.base_url
                }

        except requests.exceptions.RequestException as e:
            return {
                'status': 'error',
                'error': str(e),
                'base_url': self.base_url
            }


class FigshareMetadataMapper:
    """
    Maps Figshare article metadata to DOCiD publication format
    """

    # Figshare item type mapping to DOCiD ResourceType
    TYPE_MAPPING = {
        1: 'Image',           # figure
        2: 'Audiovisual',     # media
        3: 'Dataset',         # dataset
        4: 'Collection',      # fileset
        5: 'Image',           # poster
        6: 'Text',            # journal contribution
        7: 'Text',            # presentation
        8: 'Text',            # thesis
        9: 'Software',        # software
        11: 'Other',          # online resource
        12: 'Text',           # preprint
        13: 'Text',           # book
        14: 'Text',           # conference contribution
        15: 'Text',           # chapter
        16: 'Text',           # peer review
        17: 'Text',           # educational resource
    }

    @classmethod
    def figshare_to_docid(cls, figshare_article: Dict, user_id: int) -> Dict:
        """
        Transform Figshare article to DOCiD publication format

        Args:
            figshare_article: Figshare article data
            user_id: DOCiD user ID who will own the publication

        Returns:
            Dictionary ready for Publications model creation
        """
        # Extract basic metadata
        title = figshare_article.get('title', 'Untitled')
        description = figshare_article.get('description', '')

        # Get resource type
        defined_type = figshare_article.get('defined_type', 3)  # Default to dataset
        resource_type = cls.TYPE_MAPPING.get(defined_type, 'Other')

        # Extract DOI
        doi = figshare_article.get('doi', '')

        # Extract Figshare identifiers
        figshare_article_id = str(figshare_article.get('id', ''))
        figshare_url = figshare_article.get('url_public_html', '')

        # Build publication data
        publication_data = {
            'user_id': user_id,
            'document_title': title,
            'document_description': description,
            'resource_type': resource_type,
            'doi': doi,
            'figshare_article_id': figshare_article_id,
            'figshare_url': figshare_url,
        }

        # Extract creators/authors
        creators = []
        for author in figshare_article.get('authors', []):
            creators.append({
                'creator_name': author.get('full_name', ''),
                'creator_role': 'Author',
                'orcid_id': author.get('orcid_id'),
            })

        # Extract categories/subjects
        categories = [cat.get('title', '') for cat in figshare_article.get('categories', [])]

        # Extract tags/keywords
        tags = figshare_article.get('tags', [])

        # Extract license
        license_info = figshare_article.get('license', {})

        return {
            'publication': publication_data,
            'creators': creators,
            'categories': categories,
            'tags': tags,
            'license': license_info,
            'extended_metadata': {
                'figshare_id': figshare_article_id,
                'figshare_url': figshare_url,
                'defined_type': defined_type,
                'defined_type_name': figshare_article.get('defined_type_name', ''),
                'published_date': figshare_article.get('published_date'),
                'created_date': figshare_article.get('created_date'),
                'modified_date': figshare_article.get('modified_date'),
                'version': figshare_article.get('version'),
                'citation': figshare_article.get('citation'),
            }
        }
