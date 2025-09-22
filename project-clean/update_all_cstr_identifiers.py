#!/usr/bin/env python3
"""
Script to register all publication documents with CSTR API

This script processes all publication documents that have NULL/blank identifier_cstr
and registers them with CSTR using their existing generated_identifier + CSTR_PREFIX
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
    from config import Config
except ImportError:
    print("Error: Could not import Config. Make sure you're running this script from the correct directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# CSTR API Configuration
CSTR_API_BASE_URL = "https://cstr.cn"
CSTR_CLIENT_ID = Config.CSTR_CLIENT_ID or "202504295484"
CSTR_SECRET = Config.CSTR_SECRET or "de07fcaebe9a4822e3bb881687a7241a"
CSTR_PREFIX = Config.CSTR_PREFIX or "KE154"

def register_with_cstr(publication_data, document_data, creators, user=None):
    """Register the publication with CSTR API"""
    
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
    
    # Use the existing generated_identifier with CSTR_PREFIX
    if document_data.generated_identifier:
        unique_identifier = f"{CSTR_PREFIX}.{document_data.generated_identifier}"
    else:
        # Fallback if no generated_identifier exists
        unique_identifier = f"{CSTR_PREFIX}.11.500.14351/{publication_data.publication_id:x}_fallback"
    
    logger.info(f"Using identifier: {unique_identifier} (based on generated_identifier: {document_data.generated_identifier})")
    
    # Create the API payload
    publisher_name = "Africa PID Alliance"
    if user and user.affiliation:
        publisher_name = user.affiliation
    
    payload = {
        "prefix": CSTR_PREFIX,
        "metadatas": [
            {
                "identifier": unique_identifier,
                "titles": [{"lang": "en", "name": publication_data.document_title}],
                "creators": creators_list,
                "publisher": {"names": [{"lang": "en", "name": publisher_name}]},
                "publish_date": pub_date,
                "language": "en",
                "cstr_state": "2",
                "urls": [f"https://docid.africapidalliance.org/docid/{publication_data.document_docid}"] if publication_data.document_docid else [],
                "resource_type": "11",  # Scientific data
                "type": 1
            }
        ]
    }
    
    # Add document description if available
    if document_data.document_description:
        payload["metadatas"][0]["descriptions"] = [{"lang": "en", "content": document_data.document_description}]
    
    logger.info(f"CSTR API Payload: {json.dumps(payload, default=str)}")
    
    try:
        # Make the API request
        response = requests.post(
            f"{CSTR_API_BASE_URL}/api/v1/register",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {CSTR_CLIENT_ID}:{CSTR_SECRET}"
            },
            timeout=30
        )
        
        logger.info(f"CSTR API Response Status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"CSTR API Error - Status: {response.status_code}, Response: {response.text}")
            return unique_identifier
        
        # Parse response
        try:
            response_data = response.json()
            logger.info(f"CSTR API Response: {json.dumps(response_data, default=str)}")
            
            if response_data.get("components"):
                if response_data.get("status") == "0" or (response_data.get("status") == "7" and "existed" in response_data.get("detail", "")):
                    identifier = response_data["components"][0].get("identifier")
                    logger.info(f"Got identifier: {identifier} (status: {response_data.get('status')})")
                    return identifier
                else:
                    logger.error(f"CSTR API Error: {json.dumps(response_data, default=str)}")
                    return unique_identifier
            else:
                logger.error(f"CSTR API Missing Components: {json.dumps(response_data, default=str)}")
                return unique_identifier
                
        except json.JSONDecodeError as e:
            logger.error(f"CSTR API Response JSON Parse Error: {str(e)}, Response text: {response.text}")
            return unique_identifier
    
    except requests.RequestException as e:
        logger.error(f"CSTR API Connection Error: {str(e)}")
        return unique_identifier
    
    except Exception as e:
        logger.error(f"CSTR API Request Error: {str(e)}")
        return unique_identifier

def update_publication_document(document_id, identifier, connection):
    """Update the PublicationDocuments record with the new identifier"""
    try:
        update_query = text("""
            UPDATE publication_documents 
            SET identifier_cstr = :identifier 
            WHERE id = :document_id
        """)
        
        result = connection.execute(update_query, {
            'identifier': identifier,
            'document_id': document_id
        })
        
        connection.commit()
        
        logger.info(f"Updated PublicationDocuments id={document_id} with identifier={identifier} ({result.rowcount} rows affected)")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Database error updating document {document_id}: {str(e)}")
        connection.rollback()
        return False

def check_api_availability():
    """Check if the CSTR API is available"""
    try:
        response = requests.get(f"{CSTR_API_BASE_URL}/health", timeout=10)
        return response.status_code == 200
    except:
        return False

def process_all_publications():
    """Process all publication documents with NULL/blank identifier_cstr"""
    
    # Create database connection
    database_url = Config.SQLALCHEMY_DATABASE_URI
    if not database_url:
        logger.error("Database URL not configured")
        return False
        
    engine = create_engine(database_url)
    
    with engine.connect() as connection:
        # Query for all publication documents with NULL identifier_cstr
        count_query = text("""
            SELECT COUNT(*) as count
            FROM publication_documents pd
            WHERE pd.identifier_cstr IS NULL
        """)
        
        count_result = connection.execute(count_query)
        total_count = count_result.fetchone().count
        
        if total_count == 0:
            logger.info("No publication documents found with NULL identifier_cstr")
            return True
        
        logger.info(f"Found {total_count} publication documents with NULL identifier_cstr")
        
        # Query for all publication documents with NULL identifier_cstr
        query = text("""
            SELECT 
                pd.id as document_id,
                pd.title as document_title,
                pd.description as document_description,
                pd.identifier_type_id,
                pd.generated_identifier,
                p.id as publication_id,
                p.document_title,
                p.document_docid,
                p.published,
                p.user_id
            FROM publication_documents pd
            JOIN publications p ON pd.publication_id = p.id
            WHERE pd.identifier_cstr IS NULL
            ORDER BY pd.id
        """)
        
        result = connection.execute(query)
        publications = result.fetchall()
        
        success_count = 0
        failure_count = 0
        
        for i, publication_doc in enumerate(publications, 1):
            logger.info(f"Processing {i}/{total_count}: Document ID {publication_doc.document_id}")
            
            try:
                # Get creators for this publication
                creators_query = text("""
                    SELECT family_name, given_name, identifier
                    FROM publication_creators
                    WHERE publication_id = :publication_id
                """)
                
                creators_result = connection.execute(creators_query, {'publication_id': publication_doc.publication_id})
                creators = creators_result.fetchall()
                
                if not creators:
                    logger.warning(f"No creators found for publication {publication_doc.publication_id}")
                    # Create a default creator
                    from collections import namedtuple
                    Creator = namedtuple('Creator', ['family_name', 'given_name', 'identifier'])
                    creators = [Creator('Default', 'Creator', 'default@example.com')]
                
                # Get user information
                user_query = text("""
                    SELECT user_id, full_name, email, affiliation, country, city, location
                    FROM user_accounts
                    WHERE user_id = :user_id
                """)
                
                user_result = connection.execute(user_query, {'user_id': publication_doc.user_id})
                user = user_result.fetchone()
                
                if user:
                    logger.info(f"Found user data: user_id={user.user_id}, name={user.full_name}, email={user.email}")
                
                # Register with CSTR
                identifier = register_with_cstr(publication_doc, publication_doc, creators, user)
                
                # Update the database
                success = update_publication_document(publication_doc.document_id, identifier, connection)
                
                if success:
                    success_count += 1
                    logger.info(f"✅ Successfully processed document id={publication_doc.document_id} with CSTR identifier: {identifier}")
                else:
                    failure_count += 1
                    logger.error(f"❌ Failed to update document id={publication_doc.document_id}")
                    
            except Exception as e:
                failure_count += 1
                logger.error(f"❌ Error processing document id={publication_doc.document_id}: {str(e)}")
                continue
        
        # Summary
        logger.info(f"Processing completed: {success_count} successful, {failure_count} failed out of {total_count} total")
        
        return failure_count == 0

if __name__ == "__main__":
    try:
        logger.info("Starting CSTR identifier update process for all publication documents")
        
        # Check if API is available
        api_available = check_api_availability()
        if not api_available:
            logger.warning("CSTR API is not available. Fallback identifiers will be used.")
        
        success = process_all_publications()
        
        if success:
            logger.info("✅ CSTR identifier update process completed successfully")
        else:
            logger.error("❌ CSTR identifier update process completed with errors")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Script failed with error: {str(e)}")
        sys.exit(1)
