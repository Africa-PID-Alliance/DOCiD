"""
DSpace Legacy (6.x and earlier) Integration Service

This module provides integration with DSpace 6.x and earlier versions,
which use the older REST API structure (/rest/) instead of the newer
DSpace 7+ REST API (/server/api/).

Key Differences from DSpace 7+:
- Uses /rest/ endpoints instead of /server/api/
- Different authentication mechanism (login endpoint)
- Different response structure
- Items accessed via /rest/items/{id} instead of UUID
- Collections and communities have different structure
"""

import requests
import hashlib
import json
from typing import Optional, Dict, List, Any
from datetime import datetime


class DSpaceLegacyClient:
    """Client for DSpace 6.x REST API"""

    def __init__(self, base_url: str, email: str = None, password: str = None):
        """
        Initialize DSpace Legacy client

        Args:
            base_url: Base URL of DSpace instance (e.g., https://dspace.example.org)
            email: User email for authentication
            password: User password for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.rest_url = f"{self.base_url}/rest"
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        self.token = None

    def authenticate(self) -> bool:
        """
        Authenticate with DSpace Legacy API

        Returns:
            bool: True if authentication successful
        """
        if not self.email or not self.password:
            return False

        try:
            url = f"{self.rest_url}/login"
            response = self.session.post(url, json={
                'email': self.email,
                'password': self.password
            })

            if response.status_code == 200:
                self.token = response.text  # Token is returned as plain text
                self.session.headers.update({
                    'rest-dspace-token': self.token
                })
                return True
            return False
        except Exception as e:
            print(f"Authentication error: {e}")
            return False

    def logout(self) -> bool:
        """Logout and invalidate token"""
        if not self.token:
            return True

        try:
            url = f"{self.rest_url}/logout"
            response = self.session.post(url)
            self.token = None
            if 'rest-dspace-token' in self.session.headers:
                del self.session.headers['rest-dspace-token']
            return response.status_code == 200
        except Exception as e:
            print(f"Logout error: {e}")
            return False

    def test_connection(self) -> bool:
        """Test connection to DSpace Legacy instance"""
        try:
            url = f"{self.rest_url}/status"
            response = self.session.get(url)
            return response.status_code == 200
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

    def get_items(self, limit: int = 20, offset: int = 0) -> Optional[List[Dict]]:
        """
        Get items from DSpace Legacy

        Args:
            limit: Number of items to retrieve
            offset: Offset for pagination

        Returns:
            List of item dictionaries or None
        """
        try:
            url = f"{self.rest_url}/items"
            params = {
                'limit': limit,
                'offset': offset,
                'expand': 'metadata,parentCollection'
            }
            response = self.session.get(url, params=params)

            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error fetching items: {e}")
            return None

    def get_item(self, item_id: int) -> Optional[Dict]:
        """
        Get single item by ID

        Args:
            item_id: Item ID (not UUID - Legacy uses numeric IDs)

        Returns:
            Item dictionary or None
        """
        try:
            url = f"{self.rest_url}/items/{item_id}"
            params = {'expand': 'metadata,parentCollection,bitstreams'}
            response = self.session.get(url, params=params)

            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error fetching item {item_id}: {e}")
            return None

    def find_item_by_handle(self, handle: str) -> Optional[Dict]:
        """
        Find item by handle

        Args:
            handle: Item handle (e.g., "123456789/1")

        Returns:
            Item dictionary or None
        """
        try:
            url = f"{self.rest_url}/handle/{handle}"
            params = {'expand': 'metadata,parentCollection,bitstreams'}
            response = self.session.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                # Legacy API returns object with 'handle', 'type', 'link'
                if data.get('type') == 'item':
                    # Extract item ID from link and fetch full item
                    item_id = data.get('id')
                    if item_id:
                        return self.get_item(item_id)
            return None
        except Exception as e:
            print(f"Error finding item by handle {handle}: {e}")
            return None

    def get_collections(self, limit: int = 100, offset: int = 0) -> Optional[List[Dict]]:
        """Get collections from DSpace Legacy"""
        try:
            url = f"{self.rest_url}/collections"
            params = {
                'limit': limit,
                'offset': offset,
                'expand': 'parentCommunity'
            }
            response = self.session.get(url, params=params)

            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error fetching collections: {e}")
            return None

    def get_collection_items(self, collection_id: int, limit: int = 20, offset: int = 0) -> Optional[List[Dict]]:
        """Get items from a specific collection"""
        try:
            url = f"{self.rest_url}/collections/{collection_id}/items"
            params = {
                'limit': limit,
                'offset': offset,
                'expand': 'metadata'
            }
            response = self.session.get(url, params=params)

            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error fetching collection items: {e}")
            return None

    def search_items(self, query: str, limit: int = 20, offset: int = 0) -> Optional[List[Dict]]:
        """
        Search for items

        Args:
            query: Search query
            limit: Number of results
            offset: Offset for pagination

        Returns:
            List of items or None
        """
        try:
            url = f"{self.rest_url}/filtered-items"
            params = {
                'query_field[]': 'title',
                'query_op[]': 'contains',
                'query_val[]': query,
                'limit': limit,
                'offset': offset,
                'expand': 'metadata'
            }
            response = self.session.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                return data.get('items', [])
            return None
        except Exception as e:
            print(f"Error searching items: {e}")
            return None

    @staticmethod
    def calculate_metadata_hash(metadata: List[Dict]) -> str:
        """
        Calculate hash of metadata for change detection

        Args:
            metadata: Metadata list from DSpace Legacy

        Returns:
            MD5 hash string
        """
        metadata_str = json.dumps(metadata, sort_keys=True)
        return hashlib.md5(metadata_str.encode()).hexdigest()


class DSpaceLegacyMetadataMapper:
    """Maps DSpace Legacy metadata to DOCiD format"""

    @classmethod
    def dspace_to_docid(cls, dspace_item: Dict, user_id: int) -> Dict:
        """
        Transform DSpace Legacy item metadata to DOCiD format

        Args:
            dspace_item: Item from DSpace Legacy API
            user_id: DOCiD user ID to assign publication to

        Returns:
            Dictionary with publication data, creators, and extended metadata
        """
        metadata = dspace_item.get('metadata', [])

        # Extract basic fields
        title = cls._get_metadata_value(metadata, 'dc.title')
        description = cls._get_metadata_value(metadata, 'dc.description.abstract')
        dc_type = cls._get_metadata_value(metadata, 'dc.type')
        date_issued = cls._get_metadata_value(metadata, 'dc.date.issued')

        # Map DC type to resource type
        resource_type = cls._map_dc_type_to_resource_type(dc_type)

        # Publication data
        publication_data = {
            'user_id': user_id,
            'document_title': title or 'Untitled',
            'document_description': description or '',
            'resource_type': resource_type,
            'published_date': date_issued,
        }

        # Extract creators/authors
        creators = cls._extract_creators(metadata)

        # Extract subjects
        subjects = cls._get_metadata_values(metadata, 'dc.subject')

        # Extract publisher
        publisher = cls._get_metadata_value(metadata, 'dc.publisher')

        # Extract organizations
        organizations = []
        corporate_contributors = cls._get_metadata_values(metadata, 'dc.contributor.corporate')
        affiliations = cls._get_metadata_values(metadata, 'dc.contributor.affiliation')
        organizations.extend(corporate_contributors + affiliations)

        # Extract funders
        funders = []
        funder_names = cls._get_metadata_values(metadata, 'dc.contributor.funder')
        sponsorships = cls._get_metadata_values(metadata, 'dc.description.sponsorship')
        funders.extend(funder_names + sponsorships)

        # Extract projects
        projects = []
        project_names = cls._get_metadata_values(metadata, 'dc.relation.ispartof')
        project_refs = cls._get_metadata_values(metadata, 'dc.relation.project')
        projects.extend(project_names + project_refs)

        # Extended metadata
        extended_metadata = {
            'dates': {
                'issued': cls._get_metadata_value(metadata, 'dc.date.issued'),
                'accessioned': cls._get_metadata_value(metadata, 'dc.date.accessioned'),
                'available': cls._get_metadata_value(metadata, 'dc.date.available'),
            },
            'identifiers': {
                'uri': cls._get_metadata_value(metadata, 'dc.identifier.uri'),
                'handle': dspace_item.get('handle'),
                'item_id': dspace_item.get('id'),
            },
            'language': cls._extract_language(metadata),
            'types': {
                'dc_type': dc_type,
                'type': dspace_item.get('type'),
            },
            'rights': cls._get_metadata_value(metadata, 'dc.rights'),
            'citation': cls._get_metadata_value(metadata, 'dc.identifier.citation'),
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
    def _get_metadata_value(metadata: List[Dict], key: str) -> Optional[str]:
        """
        Get single metadata value by key

        Args:
            metadata: List of metadata dictionaries
            key: Metadata key (e.g., 'dc.title')

        Returns:
            First value or None
        """
        for item in metadata:
            if item.get('key') == key:
                return item.get('value')
        return None

    @staticmethod
    def _get_metadata_values(metadata: List[Dict], key: str) -> List[str]:
        """
        Get all metadata values for a key

        Args:
            metadata: List of metadata dictionaries
            key: Metadata key

        Returns:
            List of values
        """
        values = []
        for item in metadata:
            if item.get('key') == key:
                value = item.get('value')
                if value:
                    values.append(value)
        return values

    @classmethod
    def _extract_creators(cls, metadata: List[Dict]) -> List[Dict]:
        """Extract creators/authors from metadata"""
        creators = []

        # Get authors
        authors = cls._get_metadata_values(metadata, 'dc.contributor.author')
        for author in authors:
            creators.append({
                'creator_name': author,
                'creator_role': 'Author',
                'orcid_id': None,
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

        # Get creators
        dc_creators = cls._get_metadata_values(metadata, 'dc.creator')
        for creator in dc_creators:
            if creator not in authors and creator not in contributors:
                creators.append({
                    'creator_name': creator,
                    'creator_role': 'Creator',
                    'orcid_id': None,
                    'affiliation': None
                })

        return creators

    @classmethod
    def _extract_language(cls, metadata: List[Dict]) -> str:
        """Extract language with fallback"""
        language_iso = cls._get_metadata_value(metadata, 'dc.language.iso')
        if language_iso:
            return language_iso

        language = cls._get_metadata_value(metadata, 'dc.language')
        if language:
            return language

        return 'en'  # Default to English

    @staticmethod
    def _map_dc_type_to_resource_type(dc_type: Optional[str]) -> str:
        """Map Dublin Core type to DOCiD resource type"""
        if not dc_type:
            return 'Text'

        dc_type_lower = dc_type.lower()

        # Common mappings
        type_mapping = {
            'article': 'Article',
            'journal article': 'Article',
            'book': 'Book',
            'book chapter': 'Book Chapter',
            'conference paper': 'Conference Paper',
            'thesis': 'Thesis',
            'dissertation': 'Thesis',
            'dataset': 'Dataset',
            'image': 'Image',
            'video': 'Video',
            'audio': 'Audio',
            'software': 'Software',
            'presentation': 'Presentation',
            'poster': 'Poster',
            'report': 'Report',
            'technical report': 'Report',
            'working paper': 'Working Paper',
            'preprint': 'Preprint',
        }

        for key, value in type_mapping.items():
            if key in dc_type_lower:
                return value

        return 'Text'  # Default
