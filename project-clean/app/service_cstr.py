import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class CSTRResourceType(Enum):
    """Resource types supported by CSTR"""
    SCIENTIFIC_DATA = "11"


class CSTRDataType(Enum):
    """Data types supported by CSTR"""
    DATASET = "1"
    VIDEO = "2"
    AUDIO = "3"


class CSTRIdentifierState(Enum):
    """Identifier states"""
    RESOLVABLE_NOT_RETRIEVABLE = "1"
    RESOLVABLE_AND_RETRIEVABLE = "2"


class CSTRLanguage(Enum):
    """Common languages"""
    ENGLISH = "en"
    CHINESE = "zh"


class CSTRAPIHelper:
    """
    Helper class for interacting with CSTR REST API v1.0
    
    This class provides methods to register, update, and query scientific data
    in the CSTR (China Science and Technology Resource) system.
    """
    
    def __init__(self, client_id: str, secret: str, app_name: str = "FlaskApp"):
        """
        Initialize CSTR API Helper
        
        Args:
            client_id: Application ID assigned by CSTR platform
            secret: Secret key provided by CSTR platform (32 characters)
            app_name: Name of your application (optional)
        """
        self.base_url = "https://www.cstr.cn/openapi/v3"
        self.client_id = client_id
        self.secret = secret
        self.app_name = app_name
        self.headers = {
            "clientId": self.client_id,
            "secret": self.secret,
            "app_name": self.app_name,
            "Content-Type": "application/json"
        }
    
    def _build_metadata(self, 
                       identifier: str,
                       title: str,
                       creators: List[Dict],
                       publisher: Dict,
                       publish_date: str,
                       data_type: str,
                       urls: List[str],
                       descriptions: Optional[List[Dict]] = None,
                       keywords: Optional[List[Dict]] = None,
                       subjects: Optional[List[Dict]] = None,
                       language: str = "en",
                       version: Optional[str] = None,
                       contributors: Optional[List[Dict]] = None,
                       alternative_identifiers: Optional[List[Dict]] = None,
                       related_identifiers: Optional[List[Dict]] = None,
                       share_method: Optional[Dict] = None,
                       rights: Optional[List[Dict]] = None,
                       funders: Optional[List[Dict]] = None) -> Dict:
        """
        Build metadata dictionary for CSTR registration/update
        
        Args:
            identifier: CSTR identifier
            title: Title of the resource
            creators: List of creators
            publisher: Publishing institution
            publish_date: Publication date
            data_type: Type of data (Dataset, Video, Audio)
            urls: Resource links
            ... (other optional parameters)
            
        Returns:
            Dictionary containing formatted metadata
        """
        metadata = {
            "identifier": identifier,
            "titles": [{"lang": language, "name": title}],
            "creators": creators,
            "publisher": publisher,
            "publish_date": publish_date,
            "type": data_type,
            "cstr_state": CSTRIdentifierState.RESOLVABLE_AND_RETRIEVABLE.value,
            "urls": urls,
            "resource_type": CSTRResourceType.SCIENTIFIC_DATA.value
        }
        
        # Add optional fields if provided
        if descriptions:
            metadata["descriptions"] = descriptions
        if keywords:
            metadata["keywords"] = keywords
        if subjects:
            metadata["subjects"] = subjects
        if language:
            metadata["language"] = language
        if version:
            metadata["version"] = version
        if contributors:
            metadata["contributors"] = contributors
        if alternative_identifiers:
            metadata["alternative_identifiers"] = alternative_identifiers
        if related_identifiers:
            metadata["related_identifiers"] = related_identifiers
        if share_method:
            metadata["share_method"] = share_method
        if rights:
            metadata["rights"] = rights
        if funders:
            metadata["funders"] = funders
            
        return metadata
    
    def register(self, prefix: str, metadatas: List[Dict], res_name: str = "v3_scientific_data") -> Dict:
        """
        Register new CSTR identifiers
        
        Args:
            prefix: CSTR prefix (5 characters)
            metadatas: List of metadata dictionaries (max 100)
            res_name: Resource name (default: v3_scientific_data)
            
        Returns:
            API response as dictionary
        """
        url = f"{self.base_url}/api/register"
        params = {"res_name": res_name}
        
        data = {
            "prefix": prefix,
            "metadatas": metadatas
        }
        
        try:
            response = requests.post(url, 
                                   headers=self.headers, 
                                   params=params,
                                   json=data)
            return response.json()
        except Exception as e:
            return {"error": str(e), "code": 500}
    
    def update(self, prefix: str, metadatas: List[Dict], res_name: str = "v3_scientific_data") -> Dict:
        """
        Update existing CSTR identifiers
        
        Args:
            prefix: CSTR prefix (5 characters)
            metadatas: List of metadata dictionaries (max 100)
            res_name: Resource name (default: v3_scientific_data)
            
        Returns:
            API response as dictionary
        """
        url = f"{self.base_url}/api/update"
        params = {"res_name": res_name}
        
        data = {
            "prefix": prefix,
            "metadatas": metadatas
        }
        
        try:
            response = requests.post(url, 
                                   headers=self.headers, 
                                   params=params,
                                   json=data)
            return response.json()
        except Exception as e:
            return {"error": str(e), "code": 500}
    
    def get_task_details(self, task_id: str) -> Dict:
        """
        Get details of a batch registration/update task
        
        Args:
            task_id: Batch task ID
            
        Returns:
            Task details as dictionary
        """
        url = f"{self.base_url}/md/task/detail"
        params = {"task_id": task_id}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            return response.json()
        except Exception as e:
            return {"error": str(e), "code": 500}
    
    def get_cstr_details(self, identifier: str) -> Dict:
        """
        Get details of a registered CSTR identifier
        
        Args:
            identifier: CSTR identifier
            
        Returns:
            CSTR details as dictionary
        """
        url = f"{self.base_url}/portal/api/detail"
        params = {"identifier": identifier}
        
        # Note: This endpoint doesn't require authentication headers
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            return response.json()
        except Exception as e:
            return {"error": str(e), "code": 500}
    
    def create_person_creator(self, name: str, email: Optional[str] = None, 
                            affiliations: Optional[List[Dict]] = None,
                            language: str = "en") -> Dict:
        """
        Helper method to create a person creator object
        
        Args:
            name: Person's name
            email: Person's email (optional)
            affiliations: List of affiliations (optional)
            language: Language code (default: en)
            
        Returns:
            Creator dictionary
        """
        person = {
            "names": [{"lang": language, "name": name}]
        }
        
        if email:
            person["emails"] = [email]  # Email should be a string in array, not an object
        if affiliations:
            person["affiliations"] = affiliations
            
        return {
            "type": "1",  # Person type
            "person": person
        }
    
    def create_organization_creator(self, name: str, language: str = "en", 
                                  identifiers: Optional[List[Dict]] = None) -> Dict:
        """
        Helper method to create an organization creator object
        
        Args:
            name: Organization name
            language: Language code (default: en)
            identifiers: List of organization identifiers (optional)
            
        Returns:
            Creator dictionary
        """
        affiliation = {
            "names": [{"lang": language, "name": name}]
        }
        
        if identifiers:
            affiliation["identifiers"] = identifiers
            
        return {
            "type": "2",  # Organization type
            "affiliation": affiliation
        }
    
    def create_description(self, description: str, language: str = "en") -> Dict:
        """
        Helper method to create a description object
        
        Args:
            description: Description text
            language: Language code (default: en)
            
        Returns:
            Description dictionary
        """
        return {
            "lang": language,
            "description": description
        }
    
    def create_keywords(self, words: List[str], language: str = "en") -> Dict:
        """
        Helper method to create keywords object
        
        Args:
            words: List of keywords
            language: Language code (default: en)
            
        Returns:
            Keywords dictionary
        """
        return {
            "lang": language,
            "words": words
        }
    
    def create_share_method(self, channel: str = "1", range_type: str = "2") -> Dict:
        """
        Helper method to create share method object
        
        Args:
            channel: Sharing channel (1=online, 2=offline, 3=other)
            range_type: Sharing range (1=conditional, 2=full)
            
        Returns:
            Share method dictionary
        """
        return {
            "channel": channel,
            "range": range_type
        }
    
    def create_funder(self, name: str, proj_type: Optional[str] = None,
                     proj_num: Optional[str] = None, proj_name: Optional[str] = None) -> Dict:
        """
        Helper method to create funder object
        
        Args:
            name: Funder name
            proj_type: Project type (optional)
            proj_num: Project number (optional)
            proj_name: Project name (optional)
            
        Returns:
            Funder dictionary
        """
        funder = {"name": name}
        
        if proj_type:
            funder["proj_type"] = proj_type
        if proj_num:
            funder["proj_num"] = proj_num
        if proj_name:
            funder["proj_name"] = proj_name
            
        return funder


# Example usage in Flask application
if __name__ == "__main__":
    # Initialize the helper
    cstr = CSTRAPIHelper(
        client_id="YOUR_CLIENT_ID",
        secret="YOUR_32_CHAR_SECRET",
        app_name="MyFlaskApp"
    )
    
    # Example: Register a new dataset
    # Create metadata
    creators = [
        cstr.create_person_creator(
            name="John Doe",
            email="john.doe@example.com",
            affiliations=[{
                "names": [{"lang": "en", "name": "Example University"}]
            }]
        )
    ]
    
    publisher = {
        "names": [{"lang": "en", "name": "Example Research Institute"}]
    }
    
    descriptions = [
        cstr.create_description("This is a sample scientific dataset for demonstration.")
    ]
    
    keywords = [
        cstr.create_keywords(["science", "data", "example"])
    ]
    
    metadata = cstr._build_metadata(
        identifier="14804.11.TEST.IDENTIFIER.001.v3",
        title="Sample Scientific Dataset",
        creators=creators,
        publisher=publisher,
        publish_date="2025-05-29",
        data_type=CSTRDataType.DATASET.value,
        urls=["https://example.com/dataset"],
        descriptions=descriptions,
        keywords=keywords,
        share_method=cstr.create_share_method(channel="1", range_type="2")
    )
    
    # Register the dataset
    result = cstr.register(prefix="14804", metadatas=[metadata])
    print(json.dumps(result, indent=2))
    
    # Check task status if batch registration
    if "task_id" in result:
        task_details = cstr.get_task_details(result["task_id"])
        print(json.dumps(task_details, indent=2))
    
    # Get details of a registered CSTR
    details = cstr.get_cstr_details("14804.11.TEST.IDENTIFIER.001.v3")
    print(json.dumps(details, indent=2))