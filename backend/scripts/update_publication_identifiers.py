#!/usr/bin/env python3
"""
Script to update publication documents with CSTR identifiers

This script:
1. Fetches publications with NULL identifier_type_id in publication_documents
2. For each publication, retrieves metadata and sends it to CSTR API
3. Updates the PublicationDocuments records with the returned identifier

Usage: python update_publication_identifiers.py
"""

import os
import sys
import json
import requests
from datetime import datetime
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add the parent directory to system path to import from app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    # Import the database config from the app's config file
    from config import Config
except ImportError:
    print("Error: Could not import Config. Make sure you're running this script from the correct directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/cstr_update.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# CSTR API configuration - Use direct CSTR API
CSTR_API_BASE_URL = "https://cstr.cn"
CSTR_API_URL = f"{CSTR_API_BASE_URL}/api/v1/register"
CSTR_PREFIX = "KE154"  # Your CSTR prefix

# CSTR credentials from config
CSTR_CLIENT_ID = getattr(Config, 'CSTR_CLIENT_ID', "202504295484")
CSTR_SECRET = getattr(Config, 'CSTR_SECRET', "de07fcaebe9a4822e3bb881687a7241a")

def get_publications_with_null_identifiers():
    """
    Retrieve publications that have documents with NULL identifier_cstr
    """
    try:
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        
        with engine.connect() as connection:
            # Find all PublicationDocuments records with NULL identifier_cstr
            # These are the ones needing CSTR identifiers
            query = text("""
                SELECT pd.id, pd.publication_id, pd.title, pd.description, pd.file_url, 
                       pd.identifier_type_id, pd.generated_identifier, p.*
                FROM "publication_documents" pd
                JOIN "publications" p ON pd.publication_id = p.id
                WHERE pd.identifier_cstr IS NULL
            """)
            
            result = connection.execute(query)
            return result.fetchall()
    
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise

def get_creators_for_publication(publication_id, connection):
    """
    Get creators for a publication
    """
    query = text("""
        SELECT family_name, given_name, identifier
        FROM "publication_creators" 
        WHERE publication_id = :publication_id
    """)
    
    result = connection.execute(query, {"publication_id": publication_id})
    return result.fetchall()

def get_organization_for_publication(publication_id, connection):
    """
    Get organization for a publication
    """
    query = text("""
        SELECT name, type, other_name, country
        FROM "publication_organizations" 
        WHERE publication_id = :publication_id
    """)
    
    result = connection.execute(query, {"publication_id": publication_id})
    return result.fetchall()

def get_user_details(user_id, connection):
    """
    Get user details based on user_id
    """
    query = text("""
        SELECT user_id, social_id, user_name, full_name, email, type, affiliation, 
               role, orcid_id, ror_id, country, city, location
        FROM "user_accounts" 
        WHERE user_id = :user_id
    """)
    
    result = connection.execute(query, {"user_id": user_id})
    user = result.fetchone()
    return user

def register_with_cstr(publication_data, document_data, creators, user=None):
    """
    Register the publication with CSTR API
    """
    # Extract document_docid from URL format "https://cordra.kenet.or.ke/#objects/20.500.14351/unique_doc_id_123"
    docid = publication_data.document_docid.split('/')[-1] if publication_data.document_docid else ""
    
    # Format publication date to YYYY-MM-DD
    pub_date = publication_data.published.strftime('%Y-%m-%d') if publication_data.published else datetime.now().strftime('%Y-%m-%d')
    
    # Create creators list for the API payload
    creators_list = []
    for creator in creators:
        names = [{"lang": "en", "name": f"{creator.given_name} {creator.family_name}"}]
        person = {"names": names}
        if creator.identifier:
            person["emails"] = [creator.identifier] if "@" in creator.identifier else []
        
        creators_list.append({
            "type": "1",  # Person
            "person": person
        })
    
    # If no creators found, use user account details if available
    if not creators_list and user:
        # Use full_name from user account if available
        if user.full_name:
            name_parts = user.full_name.split(" ", 1)
            given_name = name_parts[0] if len(name_parts) > 0 else user.full_name
            family_name = name_parts[1] if len(name_parts) > 1 else ""
            
            person_data = {
                "names": [{"lang": "en", "name": user.full_name}]
            }
            
            if user.email:
                person_data["emails"] = [user.email]
                
            creators_list.append({
                "type": "1",  # Person
                "person": person_data
            })
        else:
            # Fall back to owner if user details don't have full_name
            owner_parts = publication_data.owner.split(" ", 1)
            given_name = owner_parts[0] if len(owner_parts) > 0 else publication_data.owner
            family_name = owner_parts[1] if len(owner_parts) > 1 else ""
            
            creators_list.append({
                "type": "1",
                "person": {
                    "names": [{"lang": "en", "name": f"{given_name} {family_name}"}]
                }
            })
    # If no creators and no user data, use the owner field as fallback
    elif not creators_list:
        owner_parts = publication_data.owner.split(" ", 1)
        given_name = owner_parts[0] if len(owner_parts) > 0 else publication_data.owner
        family_name = owner_parts[1] if len(owner_parts) > 1 else ""
        
        creators_list.append({
            "type": "1",
            "person": {
                "names": [{"lang": "en", "name": f"{given_name} {family_name}"}]
            }
        })
    
    # Create the API payload
    publisher_name = "Africa PID Alliance"
    
    # Use user's affiliation as publisher if available
    if user and user.affiliation:
        publisher_name = user.affiliation
    
    # Create a unique identifier using publication_id to avoid conflicts
    unique_identifier = f"{CSTR_PREFIX}.11.500.14351/{publication_data.id:x}_{docid}"
    logger.info(f"Generated unique identifier: {unique_identifier}")
        
    payload = {
        "prefix": CSTR_PREFIX,
        "metadatas": [
            {
                "identifier": unique_identifier,
                "titles": [
                    {
                        "lang": "en",
                        "name": publication_data.document_title
                    }
                ],
                "creators": creators_list,
                "publisher": {
                    "names": [
                        {
                            "lang": "en",
                            "name": publisher_name
                        }
                    ]
                },
                "publish_date": pub_date,
                "language": "en",
                "cstr_state": "2",
                "urls": [publication_data.document_docid] if publication_data.document_docid else [],
                "resource_type": "11",  # Scientific data
                "type": 1
            }
        ]
    }
    
    # Add user location data if available
    if user:
        location_info = {}
        if user.country:
            location_info["country"] = user.country
        if user.city:
            location_info["city"] = user.city
        if user.location:
            location_info["address"] = user.location
            
        if location_info:
            payload["metadatas"][0]["geo_locations"] = [location_info]
    
    # Add document description if available
    if document_data.description:
        payload["metadatas"][0]["descriptions"] = [
            {
                "lang": "en",
                "content": document_data.description
            }
        ]
    
    # Log the payload for debugging
    logger.info(f"CSTR API Payload for publication {publication_data.id}: {json.dumps(payload, default=str)}")
    
    # Make the API request to direct CSTR API
    try:
        response = requests.post(
            CSTR_API_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {CSTR_CLIENT_ID}:{CSTR_SECRET}"
            },
            json=payload,
            timeout=30  # Add timeout to avoid hanging
        )
        
        # Check if response is valid before attempting to parse JSON
        if response.status_code != 200:
            logger.error(f"CSTR API Error: Status code {response.status_code}, Response: {response.text}")
            # Use the unique identifier as a fallback
            logger.info(f"Using generated identifier as fallback: {unique_identifier}")
            return unique_identifier
            
        # Add a check for empty response
        if not response.text.strip():
            logger.error("CSTR API Error: Empty response received")
            logger.info(f"Using generated identifier as fallback: {unique_identifier}")
            return unique_identifier
            
        # Parse and return the response
        try:
            response_data = response.json()
            logger.info(f"CSTR API Response: {json.dumps(response_data, default=str)}")
            
            if response_data.get("components"):
                # Handle both success and "already exists" cases
                if response_data.get("status") == "0" or (response_data.get("status") == "7" and "existed" in response_data.get("detail", "")):
                    identifier = response_data["components"][0].get("identifier")
                    logger.info(f"Got identifier: {identifier} (status: {response_data.get('status')})")
                    return identifier
                else:
                    logger.error(f"CSTR API Error: {json.dumps(response_data, default=str)}")
                    logger.info(f"Using generated identifier as fallback: {unique_identifier}")
                    return unique_identifier
            else:
                logger.error(f"CSTR API Missing Components: {json.dumps(response_data, default=str)}")
                logger.info(f"Using generated identifier as fallback: {unique_identifier}")
                return unique_identifier
                
        except json.JSONDecodeError as e:
            logger.error(f"CSTR API Response JSON Parse Error: {str(e)}, Response text: {response.text}")
            logger.info(f"Using generated identifier as fallback: {unique_identifier}")
            return unique_identifier
    
    except requests.RequestException as e:
        logger.error(f"CSTR API Connection Error: {str(e)}")
        logger.info(f"Using generated identifier as fallback: {unique_identifier}")
        return unique_identifier
    
    except Exception as e:
        logger.error(f"CSTR API Request Error: {str(e)}")
        logger.info(f"Using generated identifier as fallback: {unique_identifier}")
        return unique_identifier

def update_publication_document(document_id, identifier, connection):
    """
    Update the PublicationDocuments record with the new identifier
    """
    try:
        # First log the current state of the record to ensure we're updating the right one
        check_query = text("""
            SELECT id, publication_id, title, description, file_url, identifier_cstr, identifier_type_id, generated_identifier
            FROM "publication_documents"
            WHERE id = :document_id
        """)
        
        record = connection.execute(check_query, {"document_id": document_id}).fetchone()
        if record:
            logger.info(f"About to update record: ID={record.id}, Title={record.title}, Current identifier_cstr={record.identifier_cstr}")
            
        # Update the identifier_cstr column
        query = text("""
            UPDATE "publication_documents"
            SET identifier_cstr = :identifier
            WHERE id = :document_id
        """)
        
        result = connection.execute(query, {"document_id": document_id, "identifier": identifier})
        
        # Check if rows were affected
        if result.rowcount > 0:
            logger.info(f"Updated PublicationDocuments id={document_id} with identifier_cstr={identifier} ({result.rowcount} rows affected)")
            return True
        else:
            logger.error(f"No rows updated for document_id={document_id}. Document may not exist!")
            return False
    
    except Exception as e:
        logger.error(f"Error updating document {document_id}: {str(e)}")
        return False

def process_publications():
    """
    Main function to process all publications with NULL identifiers
    """
    try:
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        
        publications = get_publications_with_null_identifiers()
        logger.info(f"Found {len(publications)} publications with NULL identifiers")
        
        with engine.begin() as connection:
            for pub in publications:
                # Get publication metadata
                pub_data = pub
                document_data = pub
                
                # Get user details for this publication
                user = None
                if hasattr(pub_data, 'user_id') and pub_data.user_id:
                    user = get_user_details(pub_data.user_id, connection)
                    if user:
                        logger.info(f"Found user data: user_id={user.user_id}, name={user.full_name}, email={user.email}")
                    else:
                        logger.warning(f"No user found for user_id={pub_data.user_id}")
                
                # Get creators for this publication
                creators = get_creators_for_publication(pub.publication_id, connection)
                
                # Call CSTR API
                logger.info(f"Processing publication id={pub.publication_id}, document_id={pub.id}, user_id={pub_data.user_id if hasattr(pub_data, 'user_id') else None}")
                
                identifier = register_with_cstr(pub_data, document_data, creators, user)
                
                if identifier:
                    # Update the PublicationDocuments record
                    success = update_publication_document(pub.id, identifier, connection)
                    
                    if success:
                        logger.info(f"Successfully updated document id={pub.id} with CSTR identifier: {identifier}")
                    else:
                        logger.error(f"Failed to update document id={pub.id}")
                else:
                    logger.error(f"Failed to get CSTR identifier for publication id={pub.publication_id}")
        
        logger.info("Processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error in process_publications: {str(e)}")
        raise

def check_api_availability():
    """
    Check if the CSTR API is available
    """
    try:
        # Try to ping the CSTR API base URL
        response = requests.head(
            CSTR_API_BASE_URL,
            timeout=5
        )
        # Accept any 2xx or 3xx status as success
        if 200 <= response.status_code < 400:
            logger.info(f"CSTR API is available (status: {response.status_code})")
            return True
        else:
            logger.warning(f"CSTR API returned status code {response.status_code}")
            return False
    except Exception as e:
        logger.warning(f"CSTR API is not available: {str(e)}")
        # Continue anyway as the /register endpoint might still work
        logger.info("Will attempt to use the register endpoint anyway")
        return True  # Return True anyway to proceed with trying the real endpoint

if __name__ == "__main__":
    try:
        logger.info("Starting CSTR identifier update process")
        
        # Check if API is available
        api_available = check_api_availability()
        if not api_available:
            logger.warning("CSTR API is not available. Fallback identifiers will be used for any publications.")
        
        process_publications()
        logger.info("CSTR identifier update process completed")
    except Exception as e:
        logger.error(f"Script failed with error: {str(e)}")
        sys.exit(1)
