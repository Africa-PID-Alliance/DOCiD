# service_codra.py
import requests
import json
from typing import Dict, Any, List
import logging
import time
import uuid

# Configure logging with file and console handlers
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for more detailed logs
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/cordra_service.log"),  # Save logs to a file
        logging.StreamHandler()  # Print logs to console
    ]
)
logger = logging.getLogger(__name__)

# Initialize CordraService with the necessary credentials
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CORDRA_BASE_URL = os.getenv("CORDRA_BASE_URL", "https://cordra.kenet.or.ke/cordra")
CORDRA_USERNAME = os.getenv("CORDRA_USERNAME", "admin")
CORDRA_PASSWORD = os.getenv("CORDRA_PASSWORD")

class CordraService:
    
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.access_token = None
        self.authenticate(username, password)
        logger.info("Initialized CordraService with base URL: %s", self.base_url)
    
    def _generate_request_id(self) -> str:
        """Generate a unique request identifier."""
        return str(uuid.uuid4())
    
    def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate and log the process with performance tracking.
        
        Args:
            username (str): Authentication username
            password (str): Authentication password
        
        Returns:
            bool: Authentication success status
        """
        request_id = self._generate_request_id()
        start_time = time.time()
        
        try:
            auth_url = f"{self.base_url}/doip/20.DOIP/Op.Auth.Token?targetId=service"
            auth_data = {
                "grant_type": "password",
                "username": username,
                "password": password
            }
            
            logger.info(f"Request {request_id}: Authenticating user {username}")
            
            response = requests.post(
                auth_url, 
                json=auth_data, 
                headers={"Content-Type": "application/json"}
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                access_token = response.json().get("access_token")
                if not access_token:
                    logger.error(f"Request {request_id}: No access token received")
                    return False
                
                self.access_token = access_token
                logger.info(f"Request {request_id} completed in {duration:.2f}s: Authentication successful {access_token}")
                return True
            else:
                logger.error(
                    f"Request {request_id} failed in {duration:.2f}s: "
                    f"Authentication error - {response.status_code}: {response.text}"
                )
                return False
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request {request_id} failed in {duration:.2f}s: "
                f"Authentication exception - {str(e)}"
            )
            return False

    def _headers(self) -> Dict[str, str]:
        """Headers for authenticated requests."""
        # Re-authenticate for every request to get a fresh token
        self.authenticate(self.username, self.password)
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def set_type_public(self, type_name: str) -> Dict[str, Any]:
        """
        Update the Authorization settings to make all objects of a specific type public.
        
        Args:
            type_name (str): The name of the type to make public
            
        Returns:
            Dict[str, Any]: Response from the Cordra API
        """
        request_id = self._generate_request_id()
        
        try:
            # First, get the current design object
            design_url = f"{self.base_url}/doip"
            get_design_data = {
                "operationId": "20.DOIP/Op.Retrieve",
                "targetId": "design"
            }
            
            get_response = requests.post(
                design_url, 
                json=get_design_data, 
                headers=self._headers()
            )
            
            if get_response.status_code != 200:
                return {"error": "Failed to retrieve design object", "status_code": get_response.status_code}
            
            design_obj = get_response.json()
            
            # Modify the authorization config
            auth_config = design_obj.get('content', {}).get('authConfig', {})
            
            # Create or update the type ACL
            schema_acls = auth_config.get('schemaAcls', {})
            
            # Set or update the specific type ACL
            schema_acls[type_name] = {
                "defaultAclRead": ["public"],
                "defaultAclWrite": ["creator"],
                "aclCreate": ["authenticated"]
            }
            
            # Update the design object
            auth_config['schemaAcls'] = schema_acls
            design_obj['content']['authConfig'] = auth_config
            
            update_url = f"{self.base_url}/doip"
            update_data = {
                "operationId": "20.DOIP/Op.Update",
                "targetId": "design",
                "attributes": design_obj
            }
            
            update_response = requests.post(
                update_url, 
                json=update_data, 
                headers=self._headers()
            )
            
            if update_response.status_code == 200:
                return {"success": True, "message": f"Type {type_name} is now public"}
            else:
                return {"error": "Failed to update design object", "status_code": update_response.status_code}
                
        except Exception as e:
            return {"error": str(e)}
    
    def deposit_metadata(self, metadata: Dict[str, Any], target_id: str) -> Dict[str, Any]:
        """
        Deposit metadata with comprehensive logging and performance tracking.
        
        Args:
            metadata (Dict[str, Any]): Metadata to deposit
            target_id (str): Target identifier for deposit
        
        Returns:
            Dict[str, Any]: Deposit operation result
        """
        request_id = self._generate_request_id()
        start_time = time.time()
        
        try:
            deposit_url = f"{self.base_url}/doip"
            data = {
                "operationId": "20.DOIP/Op.Create",
                "targetId": target_id,
                "attributes": metadata
            }
            
            logger.info(
                f"Request {request_id}: Depositing metadata for target {target_id}. "
                f"Metadata keys: {list(metadata.keys())}"
            )
            
            response = requests.post(
                deposit_url, 
                json=data, 
                headers=self._headers()  # Fresh token for every request
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                logger.info(
                    f"Request {request_id} completed in {duration:.2f}s: "
                    f"Metadata deposit successful. Result: {result}"
                )
                return result
            else:
                logger.error(
                    f"Request {request_id} failed in {duration:.2f}s: "
                    f"Metadata deposit error - {response.status_code}: {response.text}"
                )
                return {"error": response.text, "status_code": response.status_code}
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request {request_id} failed in {duration:.2f}s: "
                f"Metadata deposit exception - {str(e)}"
            )
            return {"error": str(e)}

    def batch_upload(self, metadata_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Batch upload multiple metadata records."""
        batch_url = f"{self.base_url}/doip"
        data = {
            "operationId": "20.DOIP/Op.BatchUpload",
            "attributes": metadata_list
        }
        
        response = requests.post(batch_url, json=data, headers=self._headers())
        if response.status_code == 200:
            return response.json()
        else:
            print("Failed to batch upload:", response.json())
            return response.json()
 
    def get_object(self, object_id: str) -> Dict[str, Any]:
        """Retrieve a digital object by ID."""
        get_url = f"{self.base_url}/doip?operationId=20.DOIP/Op.Retrieve&targetId={object_id}"
        response = requests.get(get_url, headers=self._headers())
        if response.status_code == 200:
            return response.json()
        else:
            print("Failed to retrieve object:", response.json())
            return response.json()

    def update_metadata(self, object_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Update metadata for an existing digital object."""
        update_url = f"{self.base_url}/doip"
        data = {
            "operationId": "0.DOIP/Op.Update",
            "targetId": object_id,
            "attributes": metadata
        }
        
        response = requests.post(update_url, json=data, headers=self._headers())
        if response.status_code == 200:
            return response.json()
        else:
            print("Failed to update metadata:", response.json())
            return response.json()

    def update_object(self, object_id, object_data) -> Dict[str, Any]:
        """Update an object using DOIP operation endpoint."""
        # Use operationId and targetId in query parameters as shown in the example
        url = f"{self.base_url}/doip"
        querystring = {
            "operationId": "0.DOIP/Op.Update",
            "targetId": object_id
        }
        
        # The payload should match the format with attributes wrapper
        payload = object_data
        
        logger.info(f"update_object called with object_id: {object_id}")
        logger.info(f"URL: {url}")
        logger.info(f"Query params: {querystring}")
        logger.info(f"Payload being sent: {json.dumps(payload, indent=2)}")

        try:
            # Make the POST request with query parameters
            response = requests.post(url, json=payload, headers=self._headers(), params=querystring)
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response text: {response.text}")
            
            if response.status_code == 200:
                return response.json()  # or response.text if not JSON
            else:
                print(f"Error updating object: {response.status_code} {response.text}")
                return {"error": f"Failed to update object: {response.status_code} {response.text}", "status_code": response.status_code}
        except Exception as e:
            print(f"Exception updating object: {str(e)}")
            return {"error": str(e)}
            
    def delete_object(self, object_id: str) -> Dict[str, Any]:
        """Delete a digital object by ID."""
        delete_url = f"{self.base_url}/doip"
        data = {
            "operationId": "20.DOIP/Op.Delete",
            "targetId": object_id
        }
        
        response = requests.post(delete_url, json=data, headers=self._headers())
        if response.status_code == 200:
            return response.json()
        else:
            print("Failed to delete object:", response.json())
            return response.json()

    def query_objects(
        self, 
        query: Dict[str, Any], 
        page_size: int = 10, 
        page_number: int = 0
    ) -> Dict[str, Any]:
        """
        Query digital objects with advanced logging and performance tracking.
        
        Args:
            query (Dict[str, Any]): Search query parameters
            page_size (int, optional): Number of results per page. Defaults to 10.
            page_number (int, optional): Page number for pagination. Defaults to 0.
        
        Returns:
            Dict[str, Any]: Query results with detailed logging
        """
        request_id = self._generate_request_id()
        start_time = time.time()
        
        try:
            query_url = f"{self.base_url}/doip"
            data = {
                "operationId": "20.DOIP/Op.Query",
                "attributes": {
                    "query": query,
                    "pageSize": page_size,
                    "pageNumber": page_number
                }
            }
            
            logger.info(
                f"Request {request_id}: Querying objects. "
                f"Query: {query}, Page Size: {page_size}, Page Number: {page_number}"
            )
            
            response = requests.post(
                query_url, 
                json=data, 
                headers=self._headers()
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                logger.info(
                    f"Request {request_id} completed in {duration:.2f}s: "
                    f"Query successful. Results count: {len(result.get('results', []))}"
                )
                return result
            else:
                logger.error(
                    f"Request {request_id} failed in {duration:.2f}s: "
                    f"Query error - {response.status_code}: {response.text}"
                )
                return {"error": response.text, "status_code": response.status_code}
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request {request_id} failed in {duration:.2f}s: "
                f"Query exception - {str(e)}"
            )
            return {"error": str(e)}


    def list_dois(self) -> Dict[str, Any]:
        """List all DOIs assigned in Cordra."""
        list_dois_url = f"{self.base_url}/doip?operationId=20.DOIP/Op.ListDOIs"
        response = requests.get(list_dois_url, headers=self._headers())
        if response.status_code == 200:
            return response.json()
        else:
            print("Failed to list DOIs:", response.json())
            return response.json()

    def check_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """Check the status of a batch operation."""
        status_url = f"{self.base_url}/doip?operationId=20.DOIP/Op.BatchStatus&targetId={batch_id}"
        response = requests.get(status_url, headers=self._headers())
        if response.status_code == 200:
            return response.json()
        else:
            print("Failed to check batch status:", response.json())
            return response.json()

    def refresh_token(self) -> bool:
        """Refresh access token."""
        self.access_token = None
        return self.authenticate(self.username, self.password)
    
    def list_operations(self) -> Dict[str, Any]:
        """
        Retrieve the list of available operations from the Cordra API.

        Returns:
            Dict[str, Any]: Response from the Cordra API.
        """
        request_id = self._generate_request_id()
        start_time = time.time()

        try:
            url = f"{self.base_url}/doip/0.DOIP/Op.ListOperations"
            querystring = {"targetId": "service"}

            headers = self._headers()  # Retrieve headers, including authorization

            logger.info(f"Request {request_id}: Listing operations from Cordra")

            response = requests.post(url, headers=headers, params=querystring)

            duration = time.time() - start_time

            if response.status_code == 200:
                response_data = response.json()
                logger.info(
                    f"Request {request_id} completed in {duration:.2f}s: Operations listed successfully. Response: {response_data}"
                )
                return {"success": True, "data": response_data}
            else:
                logger.error(
                    f"Request {request_id} failed in {duration:.2f}s: Failed to list operations - {response.status_code}: {response.text}"
                )
                return {
                    "success": False,
                    "message": response.json().get('message', 'Failed to list operations'),
                    "status_code": response.status_code,
                }

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request {request_id} failed in {duration:.2f}s: Exception occurred - {str(e)}"
            )
            return {"success": False, "message": str(e)}
        
    def _assign_doi_generic(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generic method to create a digital object using the DOIP Create operation.

        Args:
            payload (Dict[str, Any]): The pre-constructed payload to send to the Cordra API.

        Returns:
            Dict[str, Any]: Response from the Cordra API.
        """
        request_id = self._generate_request_id()
        start_time = time.time()

        try:
            # Log input payload for debugging
            logger.info(f"Request {request_id}: Attempting to create object")
            logger.debug(f"Request {request_id}: Payload - {json.dumps(payload, indent=2)}")

            url = f"{self.base_url}/doip/0.DOIP/Op.Create"
            querystring = {"targetId": "service"}

            headers = self._headers()

            # Log request details
            logger.info(f"Request {request_id}: Sending POST to {url}")
            logger.info(f"Request {request_id}: Query String - {querystring}")

            # Send the request
            response = requests.post(url, json=payload, headers=headers, params=querystring)

            duration = time.time() - start_time

            # Log response details
            logger.info(f"Request {request_id}: Response received in {duration:.2f}s")
            logger.info(f"Response Status Code: {response.status_code}")

            if response.status_code == 200:
                response_data = response.json()
                logger.info(
                    f"Request {request_id} completed in {duration:.2f}s: "
                    f"Object created successfully. Response: {response_data}"
                )
                return {
                    "success": True,
                    "message": "Object created successfully",
                    "data": response_data
                }
            else:
                # Detailed error logging
                logger.error(
                    f"Request {request_id} failed in {duration:.2f}s: "
                    f"Object creation error - {response.status_code}: {response.text}"
                )
                
                try:
                    # Try to parse error message from response
                    error_message = response.json().get('message', 'Failed to create object')
                except ValueError:
                    # Fallback if response is not JSON
                    error_message = response.text or 'Unknown error occurred'
                
                return {
                    "success": False,
                    "message": error_message,
                    "status_code": response.status_code,
                    "response_text": response.text
                }

        except requests.RequestException as req_exc:
            # Specific handling for request-related exceptions
            duration = time.time() - start_time
            logger.error(
                f"Request {request_id} failed in {duration:.2f}s: "
                f"Network/Request Exception - {str(req_exc)}"
            )
            return {
                "success": False,
                "message": f"Request failed: {str(req_exc)}",
                "exception_type": type(req_exc).__name__
            }

        except Exception as e:
            # Catch-all for any other unexpected exceptions
            duration = time.time() - start_time
            logger.error(
                f"Request {request_id} failed in {duration:.2f}s: "
                f"Unexpected Exception - {str(e)}"
            )
            logger.exception("Full exception traceback:")

            return {
                "success": False,
                "message": str(e),
                "exception_type": type(e).__name__
            }
     
    def assign_identifier_apa_handle(self) -> Dict[str, Any]:
        """
        Assign an identifier to an object in the APA_Handle_ID schema.

        Returns:
            Dict[str, Any]: Response from the Cordra API, including the generated ID.
        """
        request_id = self._generate_request_id()
        start_time = time.time()

        try:
            logger.info(f"[{request_id}] - Starting APA_Handle_ID object creation")

            # Ensure attributes contain a valid object
            payload = {
                "type": "APA_Handle_ID",
                "attributes": {
                    "content": {}  # Ensure attributes is always a valid object
                }
            }

            logger.debug(f"[{request_id}] - Payload constructed: {json.dumps(payload, indent=2)}")

            url = f"{self.base_url}/doip/0.DOIP/Op.Create"
            querystring = {"targetId": "service"}

            headers = self._headers()  # Get fresh authentication headers

            logger.info(f"[{request_id}] - Sending POST request to Cordra API at {url}")
            logger.debug(f"[{request_id}] - Headers: {headers}")

            # Send the request to Cordra
            response = requests.post(url, json=payload, headers=headers, params=querystring)

            duration = time.time() - start_time

            logger.info(f"[{request_id}] - Received response in {duration:.2f}s with status code {response.status_code}")

            # Process response
            if response.status_code == 200:
                response_data = response.json()
                generated_id = response_data.get("id", "Unknown ID")
                logger.info(f"[{request_id}] - Object created successfully with ID {generated_id}")
                logger.debug(f"[{request_id}] - Response data: {json.dumps(response_data, indent=2)}")

                return {
                    "success": True, 
                    "message": "Object created successfully",
                    "id": generated_id,
                    # "data": response_data
                }
            else:
                logger.error(f"[{request_id}] - Object creation failed - {response.status_code}: {response.text}")

                return {
                    "success": False,
                    "message": response.json().get('message', 'Failed to create object'),
                    "status_code": response.status_code,
                    "response_text": response.text
                }

        except requests.RequestException as req_exc:
            duration = time.time() - start_time
            logger.error(f"[{request_id}] - Network error after {duration:.2f}s: {str(req_exc)}")
            return {"success": False, "message": f"Request failed: {str(req_exc)}"}

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"[{request_id}] - Unexpected Exception after {duration:.2f}s: {str(e)}", exc_info=True)
            return {"success": False, "message": str(e)}

    def  push_apa_metadata(self, metadata: Dict[str, Any], schema_type: str = "APA_Handle_ID") -> Dict[str, Any]:

        """
        Assign an identifier to an object in the APA_Handle_ID schema, with custom metadata.

        Args:
            metadata (Dict[str, Any]): Key-value metadata to include in the object content.

        Returns:
            Dict[str, Any]: Response from the Cordra API, including the generated ID.
        """
        request_id = self._generate_request_id()
        start_time = time.time()

        try:
            logger.info(f"[{request_id}] - Starting APA_Handle_ID object creation")

            payload = {
                "type": schema_type,
                "attributes": {
                    "content": metadata or {},
                    "acl": {
                        "read": ["public"]  # Make this object publicly readable
                    }
                }
            }

            # Safely log the payload with datetime handling
            try:
                logger.debug(f"[{request_id}] - Payload constructed: {json.dumps(payload, indent=2, default=str)}")
            except Exception as log_e:
                logger.debug(f"[{request_id}] - Payload constructed (unable to serialize for logging): {str(log_e)}")

            url = f"{self.base_url}/doip/0.DOIP/Op.Create"
            querystring = {"targetId": "service"}

            headers = self._headers()  # Fresh authentication

            logger.info(f"[{request_id}] - Sending POST request to Cordra API at {url}")
            logger.debug(f"[{request_id}] - Headers: {headers}")

            response = requests.post(url, json=payload, headers=headers, params=querystring)

            duration = time.time() - start_time
            logger.info(f"[{request_id}] - Received response in {duration:.2f}s with status code {response.status_code}")

            if response.status_code == 200:
                response_data = response.json()
                generated_id = response_data.get("id", "Unknown ID")
                logger.info(f"[{request_id}] - Object created successfully with ID {generated_id}")
                return {
                    "success": True,
                    "message": "Object created successfully",
                    "id": generated_id
                }
            else:
                logger.error(f"[{request_id}] - Object creation failed - {response.status_code}: {response.text}")
                return {
                    "success": False,
                    "message": response.json().get('message', 'Failed to create object'),
                    "status_code": response.status_code,
                    "response_text": response.text
                }

        except requests.RequestException as req_exc:
            duration = time.time() - start_time
            logger.error(f"[{request_id}] - Network error after {duration:.2f}s: {str(req_exc)}")
            return {"success": False, "message": f"Request failed: {str(req_exc)}"}

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"[{request_id}] - Unexpected Exception after {duration:.2f}s: {str(e)}", exc_info=True)
            return {"success": False, "message": str(e)}
        
# Singleton instance to use for all service functions
cordra_service = CordraService(CORDRA_BASE_URL, CORDRA_USERNAME, CORDRA_PASSWORD)

# Functions using the singleton instance
# Functions to be imported and used in routes

def list_operations() -> Dict[str, Any]:
    return cordra_service.list_operations()

def deposit_metadata(metadata: Dict[str, Any], target_id: str) -> Dict[str, Any]:
    return cordra_service.deposit_metadata(metadata, target_id)

def batch_upload(metadata_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    return cordra_service.batch_upload(metadata_list)

def get_object(object_id: str) -> Dict[str, Any]:
    return cordra_service.get_object(object_id)

def update_metadata(object_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    return cordra_service.update_metadata(object_id, metadata)

def update_object(object_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    return cordra_service.update_object(object_id, metadata)

def delete_object(object_id: str) -> Dict[str, Any]:
    return cordra_service.delete_object(object_id)

def query_objects(query: Dict[str, Any], page_size: int = 10) -> Dict[str, Any]:
    return cordra_service.query_objects(query, page_size)

def list_dois() -> Dict[str, Any]:
    return cordra_service.list_dois()

def check_batch_status(batch_id: str) -> Dict[str, Any]:
    return cordra_service.check_batch_status(batch_id)

def refresh_token() -> bool:
    return cordra_service.refresh_token()

def assign_identifier_apa_handle() -> Dict[str, Any]:
    return cordra_service.assign_identifier_apa_handle()

def push_apa_metadata(metadata: Dict) -> Dict[str, Any]:
    return cordra_service.push_apa_metadata(metadata, schema_type="APA_Handle_ID")

def create_or_update_semantic_object(object_type: str, handle_id: str, content_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create or update a semantic object in CORDRA (for Creators, Organizations, Funders, Projects)"""
    # First try to create
    payload = {
        "id": handle_id,
        "type": object_type,
        "attributes": {
            "content": content_data
        }
    }
    result = cordra_service._assign_doi_generic(payload)
    
    # If object already exists (409 error), try to update it
    if not result.get('success') and result.get('status_code') == 409:
        update_payload = {
            "attributes": {
                "content": content_data
            }
        }
        return update_object(handle_id, update_payload)
    
    return result

# Indigenous Knowledge example

def assign_doi_indigenous_knowledge(doi: str, name: str, description: str, description2: str = "") -> Dict[str, Any]:
    payload = {
        "type": "Indigenous Knowledge",
        "attributes": {
            "content": {
                "doi": doi,
                "name": name,
                "description": description,
                "description2": description2
            }
        }
    }
    return cordra_service._assign_doi_generic(payload)

# Container iD
def assign_doi_container_id( title: str, description: str) -> Dict[str, Any]:
    payload = {
        "type": "Container iD",
        "attributes": {
            "content": {
                "groupName": title,
                "description": description
            }
        },
        "acl": {
            "readers": ["public"],  # Make this object publicly readable
            "writers": [],
            "payloadReaders": ["public"]
        }
    }
    return cordra_service._assign_doi_generic(payload)

# Patent
def assign_doi_patent(
    doi: str,
    name: str,
    description: str,
    title: str,
    inventor: str,
    assignee: str,
    date: str,
    application_date: str,
    grant_date: str,
    classification_code: str,
    classification_date: str = "",
    abstract: str = "",
    owner: str = ""
) -> Dict[str, Any]:
    """
    Construct the payload for assigning a DOI to a Patent object and send the request.

    Args:
        doi (str): The DOI to assign.
        name (str): The name of the patent.
        description (str): The description of the patent.
        title (str): The title of the patent.
        inventor (str): The name of the inventor.
        assignee (str): The name of the assignee.
        date (str): The date associated with the patent.
        application_date (str): The application date of the patent.
        grant_date (str): The grant date of the patent.
        classification_code (str): The classification code for the patent.
        classification_date (str, optional): The classification date of the patent. Defaults to "".
        abstract (str, optional): An abstract of the patent. Defaults to "".
        owner (str, optional): The owner of the patent. Defaults to "".

    Returns:
        Dict[str, Any]: The response from the Cordra service.
    """
    content = {
        "doi": doi,
        "name": name,
        "description": description,
        "title": title,
        "inventor": inventor,
        "assignee": assignee,
        "date": date,
        "application date": application_date,
        "grant date": grant_date,
        "classification code": classification_code,
        "abstract": abstract,
        "owner": owner,
    }

    # Include classification_date only if provided
    if classification_date:
        content["classification_date"] = classification_date

    payload = {
        "type": "Patent",
        "attributes": {
            "content": content
        }
    }

    return cordra_service._assign_doi_generic(payload)
 

# User
def assign_doi_user(username: str,password: str, email: str, role: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "type": "User",
        "attributes": {
            "content": {
                "username": username,
                "password": password,
                "email": email,
                "role": role,
                "metadata": metadata
            }
        }
    }
    return cordra_service._assign_doi_generic(payload)
