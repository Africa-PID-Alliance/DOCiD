"""
DSpace REST API Client Service
Handles communication with DSpace repositories and metadata transformation
"""

import requests
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class DSpaceClient:
    """Client for interacting with DSpace REST API"""

    def __init__(self, base_url: str, username: str = None, password: str = None):
        """
        Initialize DSpace client

        Args:
            base_url: DSpace server base URL (e.g., https://demo.dspace.org/server)
            username: Optional username for authentication
            password: Optional password for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api"
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.auth_token = None
        self.csrf_token = None

    def authenticate(self) -> bool:
        """
        Authenticate with DSpace and get JWT token

        Returns:
            True if authentication successful, False otherwise
        """
        if not self.username or not self.password:
            return False

        try:
            # Step 1: Get CSRF token
            status_response = self.session.get(f"{self.api_url}/authn/status")
            self.csrf_token = status_response.headers.get('DSPACE-XSRF-TOKEN')

            if not self.csrf_token:
                print("Failed to get CSRF token")
                return False

            # Step 2: Login
            headers = {'X-XSRF-TOKEN': self.csrf_token}
            response = self.session.post(
                f"{self.api_url}/authn/login",
                data={'user': self.username, 'password': self.password},
                headers=headers
            )

            if response.status_code == 200:
                self.auth_token = response.headers.get('Authorization')
                new_csrf = response.headers.get('DSPACE-XSRF-TOKEN')
                if new_csrf:
                    self.csrf_token = new_csrf
                return True
            else:
                print(f"Login failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"Authentication error: {e}")
            return False

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for authenticated requests"""
        headers = {}
        if self.auth_token:
            headers['Authorization'] = self.auth_token
        if self.csrf_token:
            headers['X-XSRF-TOKEN'] = self.csrf_token
        return headers

    def get_items(self, page: int = 0, size: int = 20) -> Dict:
        """
        Get items from DSpace repository

        Args:
            page: Page number (0-indexed)
            size: Number of items per page

        Returns:
            Dictionary containing items and pagination info
        """
        try:
            url = f"{self.api_url}/core/items?page={page}&size={size}"
            response = self.session.get(url, headers=self._get_headers())

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get items: {response.status_code}")
                return {}
        except Exception as e:
            print(f"Error getting items: {e}")
            return {}

    def get_item(self, uuid: str) -> Optional[Dict]:
        """
        Get single item by UUID

        Args:
            uuid: Item UUID

        Returns:
            Item data or None if not found
        """
        try:
            url = f"{self.api_url}/core/items/{uuid}"
            response = self.session.get(url, headers=self._get_headers())

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get item {uuid}: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error getting item {uuid}: {e}")
            return None

    def get_item_by_handle(self, handle: str) -> Optional[Dict]:
        """
        Get item by Handle identifier

        Args:
            handle: DSpace handle (e.g., "123456789/1")

        Returns:
            Item data or None if not found
        """
        try:
            # DSpace API allows searching by handle
            url = f"{self.api_url}/core/items/search/findByHandle?handle={handle}"
            response = self.session.get(url, headers=self._get_headers())

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get item by handle {handle}: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error getting item by handle {handle}: {e}")
            return None

    def get_communities(self, page: int = 0, size: int = 20) -> Dict:
        """Get communities from DSpace"""
        try:
            url = f"{self.api_url}/core/communities?page={page}&size={size}"
            response = self.session.get(url, headers=self._get_headers())

            if response.status_code == 200:
                return response.json()
            else:
                return {}
        except Exception as e:
            print(f"Error getting communities: {e}")
            return {}

    def get_collections(self, page: int = 0, size: int = 20) -> Dict:
        """Get collections from DSpace"""
        try:
            url = f"{self.api_url}/core/collections?page={page}&size={size}"
            response = self.session.get(url, headers=self._get_headers())

            if response.status_code == 200:
                return response.json()
            else:
                return {}
        except Exception as e:
            print(f"Error getting collections: {e}")
            return {}

    @staticmethod
    def calculate_metadata_hash(metadata: Dict) -> str:
        """
        Calculate MD5 hash of metadata for change detection

        Args:
            metadata: Metadata dictionary

        Returns:
            MD5 hash string
        """
        # Convert to JSON and hash
        metadata_str = json.dumps(metadata, sort_keys=True)
        return hashlib.md5(metadata_str.encode()).hexdigest()


class DSpaceMetadataMapper:
    """
    Maps DSpace Dublin Core metadata to DOCiD publication format
    """

    # DSpace type to DOCiD ResourceType mapping
    TYPE_MAPPING = {
        'Article': 'Text',
        'Book': 'Text',
        'Book chapter': 'Text',
        'Conference paper': 'Text',
        'Dataset': 'Dataset',
        'Image': 'Image',
        'Software': 'Software',
        'Thesis': 'Text',
        'Technical Report': 'Text',
        'Working Paper': 'Text',
    }

    @classmethod
    def dspace_to_docid(cls, dspace_item: Dict, user_id: int) -> Dict:
        """
        Transform DSpace item to DOCiD publication format

        Args:
            dspace_item: DSpace item data
            user_id: DOCiD user ID who will own the publication

        Returns:
            Dictionary ready for Publications model creation
        """
        metadata = dspace_item.get('metadata', {})

        # Extract title
        title = cls._get_metadata_value(metadata, 'dc.title')
        if not title:
            title = dspace_item.get('name', 'Untitled')

        # Extract description
        description = (
            cls._get_metadata_value(metadata, 'dc.description.abstract') or
            cls._get_metadata_value(metadata, 'dc.description') or
            ''
        )

        # Extract dates
        date_issued = cls._get_metadata_value(metadata, 'dc.date.issued')
        date_accessioned = cls._get_metadata_value(metadata, 'dc.date.accessioned')
        date_available = cls._get_metadata_value(metadata, 'dc.date.available')

        # Extract identifiers
        identifier_uri = cls._get_metadata_value(metadata, 'dc.identifier.uri')

        # Extract language
        language = cls._get_metadata_value(metadata, 'dc.language')
        language_iso = cls._get_metadata_value(metadata, 'dc.language.iso')
        final_language = language_iso or language or 'en'

        # Extract type
        dspace_type = cls._get_metadata_value(metadata, 'dc.type', 'Article')
        dspace_entity_type = cls._get_metadata_value(metadata, 'dspace.entity.type')
        resource_type = cls.TYPE_MAPPING.get(dspace_type, 'Text')

        # Build publication data
        publication_data = {
            'user_id': user_id,
            'document_title': title,
            'document_description': description,
            'published_date': cls._parse_date(date_issued),
            'resource_type': resource_type,
            'dspace_handle': dspace_item.get('handle'),
            'dspace_uuid': dspace_item.get('uuid'),
        }

        # Extract creators
        creators = cls._extract_creators(metadata)

        # Extract subjects/keywords
        subjects = cls._get_metadata_values(metadata, 'dc.subject')

        # Extract publisher
        publisher = cls._get_metadata_value(metadata, 'dc.publisher')

        # Extract author relations
        author_relations = cls._get_metadata_values(metadata, 'relation.isAuthorOfPublication')
        author_relations_latest = cls._get_metadata_values(metadata, 'relation.isAuthorOfPublication.latestForDiscovery')

        # Extract organizations (corporate contributors, affiliations)
        organizations = []
        corporate_contributors = cls._get_metadata_values(metadata, 'dc.contributor.corporate')
        organizations.extend(corporate_contributors)

        # Extract affiliations from various possible fields
        affiliations = cls._get_metadata_values(metadata, 'dc.contributor.affiliation')
        organizations.extend(affiliations)

        # Extract funders
        funders = []
        funder_names = cls._get_metadata_values(metadata, 'dc.contributor.funder')
        funders.extend(funder_names)

        # Also check sponsorship field
        sponsorships = cls._get_metadata_values(metadata, 'dc.description.sponsorship')
        funders.extend(sponsorships)

        # Extract projects
        projects = []
        project_names = cls._get_metadata_values(metadata, 'dc.relation.ispartof')
        projects.extend(project_names)

        # Also check project field
        project_refs = cls._get_metadata_values(metadata, 'dc.relation.project')
        projects.extend(project_refs)

        # Build comprehensive metadata object
        extended_metadata = {
            'dates': {
                'issued': date_issued,
                'accessioned': date_accessioned,
                'available': date_available
            },
            'identifiers': {
                'uri': identifier_uri,
                'handle': dspace_item.get('handle'),
                'uuid': dspace_item.get('uuid')
            },
            'language': final_language,
            'types': {
                'dc_type': dspace_type,
                'entity_type': dspace_entity_type
            },
            'relations': {
                'author_publications': author_relations,
                'author_publications_latest': author_relations_latest
            }
        }

        return {
            'publication': publication_data,
            'creators': creators,
            'subjects': subjects,
            'publisher': publisher,
            'organizations': organizations,
            'funders': funders,
            'projects': projects,
            'extended_metadata': extended_metadata
        }

    @staticmethod
    def _get_metadata_value(metadata: Dict, field: str, default: str = None) -> Optional[str]:
        """Get first value from metadata field"""
        values = metadata.get(field, [])
        if values and len(values) > 0:
            return values[0].get('value', default)
        return default

    @staticmethod
    def _get_metadata_values(metadata: Dict, field: str) -> List[str]:
        """Get all values from metadata field"""
        values = metadata.get(field, [])
        return [v.get('value') for v in values if v.get('value')]

    @classmethod
    def _extract_creators(cls, metadata: Dict) -> List[Dict]:
        """
        Extract creators/authors from metadata

        Returns:
            List of creator dictionaries with name and role
        """
        creators = []

        # Get authors
        authors = cls._get_metadata_values(metadata, 'dc.contributor.author')
        for author in authors:
            creators.append({
                'creator_name': author,
                'creator_role': 'Author',  # Will map to CreatorsRoles table
                'orcid_id': None,  # Can be enhanced later
                'affiliation': None
            })

        # Get other contributors
        contributors = cls._get_metadata_values(metadata, 'dc.contributor')
        for contributor in contributors:
            if contributor not in authors:  # Avoid duplicates
                creators.append({
                    'creator_name': contributor,
                    'creator_role': 'Contributor',
                    'orcid_id': None,
                    'affiliation': None
                })

        return creators

    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[str]:
        """
        Parse DSpace date to ISO format

        Args:
            date_str: Date string (various formats: YYYY, YYYY-MM-DD, etc.)

        Returns:
            ISO formatted date or None
        """
        if not date_str:
            return None

        # Try different date formats
        formats = [
            '%Y-%m-%d',
            '%Y-%m',
            '%Y',
            '%Y-%m-%dT%H:%M:%SZ',
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue

        # If all formats fail, return as-is if it looks like a year
        if date_str.isdigit() and len(date_str) == 4:
            return f"{date_str}-01-01"

        return None
