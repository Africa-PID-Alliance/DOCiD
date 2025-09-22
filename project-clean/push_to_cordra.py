#!/usr/bin/env python3
"""
Script to push all publication data and semantics to CORDRA

This script runs after update_all_cstr_identifiers.py and pushes:
- Publications
- PublicationFiles  
- PublicationDocuments
- PublicationCreators
- PublicationOrganizations
- PublicationFunders
- PublicationProjects
"""

import os
import sys
import json
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add the parent directory to system path to import from app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from config import Config
    from app.service_codra import update_object, create_or_update_semantic_object
    from app.models import (
        Publications, PublicationFiles, PublicationDocuments,
        PublicationCreators, PublicationOrganization, PublicationFunders,
        PublicationProjects, PublicationTypes, PublicationIdentifierTypes,
        CreatorsRoles, FunderTypes, UserAccount
    )
    from app import db, create_app
except ImportError as e:
    print(f"Error: Could not import required modules: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/push_to_cordra.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Always use the production domain for CORDRA
APPLICATION_DOMAIN = 'https://docid.africapidalliance.org'

def fix_file_url(url):
    """Fix file URLs to use the correct domain instead of localhost or any other domain"""
    if not url:
        return url
    
    # Extract just the path part after /uploads/
    if '/uploads/' in url:
        # Get everything after /uploads/
        parts = url.split('/uploads/')
        if len(parts) > 1:
            # Return with the correct domain
            return f"{APPLICATION_DOMAIN}/uploads/{parts[1]}"
    
    # If it's already using the correct domain, return as is
    if url.startswith(APPLICATION_DOMAIN):
        return url
    
    # For any other URL format, try to extract the filename and rebuild
    if 'localhost' in url or 'http://' in url or 'https://' in url:
        # Try to extract just the filename
        filename = url.split('/')[-1] if '/' in url else url
        if filename:
            return f"{APPLICATION_DOMAIN}/uploads/{filename}"
    
    return url

def push_publication_to_cordra(publication):
    """Push main publication metadata to CORDRA"""
    try:
        if not publication.doi:
            logger.warning(f"Publication {publication.id} has no DOI, skipping CORDRA push")
            return False
            
        metadata = {
            "id": str(publication.id),
            "docid": f"https://docid.africapidalliance.org/docid/{publication.document_docid}",
            "title": publication.document_title,
            "description": publication.document_description,
            "doi": publication.doi,
            "owner": publication.owner,
            "user_id": publication.user_id,
            "resource_type_id": publication.resource_type_id,
            "avatar": publication.avatar,
            "poster_url": fix_file_url(publication.publication_poster_url),
            "groupName": publication.document_title,  # Container iD requires groupName
            "created_on": int(publication.published.timestamp()) if publication.published else None
        }
        
        object_data = {
            "attributes": {
                "content": metadata
            }
        }
        
        logger.info(f"Pushing Publication {publication.id} to CORDRA with DOI: {publication.doi}")
        response = update_object(publication.doi, object_data)
        
        # If object doesn't exist (404), try to create it
        if isinstance(response, dict) and response.get('status_code') == 404:
            logger.info(f"Publication {publication.doi} not found in CORDRA, attempting to create it")
            response = create_or_update_semantic_object("Container iD", publication.doi, metadata)
            logger.info(f"CORDRA create response for Publication {publication.id}: {response}")
        else:
            logger.info(f"CORDRA response for Publication {publication.id}: {response}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to push Publication {publication.id} to CORDRA: {str(e)}")
        return False

def push_publication_files_to_cordra(publication):
    """Push all publication files to CORDRA"""
    try:
        files = PublicationFiles.query.filter_by(publication_id=publication.id).all()
        count = 0
        
        for file in files:
            if not file.handle_identifier:
                logger.warning(f"PublicationFile {file.id} has no handle, skipping")
                continue
                
            # Get publication type name
            pub_type = PublicationTypes.query.filter_by(id=file.publication_type_id).first()
            pub_type_name = pub_type.publication_type_name if pub_type else "Unknown"
            
            metadata = {
                "title": file.title,
                "description": file.description,
                "fileUrl": fix_file_url(file.file_url),
                "fileType": file.file_type,
                "fileName": file.file_name,
                "publicationType": pub_type_name,
                "parentId": publication.doi,
                "createdOn": int(datetime.now().timestamp())
            }
            
            if file.external_identifier:
                metadata["externalIdentifier"] = file.external_identifier
                metadata["externalIdentifierType"] = file.external_identifier_type
                if file.external_identifier_type:
                    metadata[file.external_identifier_type.lower()] = file.external_identifier
            
            object_data = {
                "attributes": {
                    "content": metadata
                }
            }
            
            logger.info(f"Pushing PublicationFile {file.id} to CORDRA with handle: {file.handle_identifier}")
            response = update_object(file.handle_identifier, object_data)
            
            # If object doesn't exist (404), try to create it
            if isinstance(response, dict) and response.get('status_code') == 404:
                logger.info(f"File {file.handle_identifier} not found in CORDRA, attempting to create it")
                response = create_or_update_semantic_object("APA_Handle_ID", file.handle_identifier, metadata)
                logger.info(f"CORDRA create response for PublicationFile {file.id}: {response}")
            else:
                logger.info(f"CORDRA response for PublicationFile {file.id}: {response}")
            
            count += 1
            
        logger.info(f"Pushed {count} PublicationFiles for Publication {publication.id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to push PublicationFiles for Publication {publication.id}: {str(e)}")
        return False

def push_publication_documents_to_cordra(publication):
    """Push all publication documents to CORDRA"""
    try:
        documents = PublicationDocuments.query.filter_by(publication_id=publication.id).all()
        count = 0
        
        for doc in documents:
            if not doc.handle_identifier:
                logger.warning(f"PublicationDocument {doc.id} has no handle, skipping")
                continue
                
            # Get publication type name
            pub_type = PublicationTypes.query.filter_by(id=doc.publication_type_id).first()
            pub_type_name = pub_type.publication_type_name if pub_type else "Unknown"
            
            # Get identifier type name if available
            identifier_type_name = None
            if doc.identifier_type_id:
                id_type = PublicationIdentifierTypes.query.filter_by(id=doc.identifier_type_id).first()
                identifier_type_name = id_type.identifier_type_name if id_type else None
            
            # Construct CSTR full resolvable URL if identifier_cstr exists
            identifier_cstr_url = None
            if doc.identifier_cstr:
                # If it's already a full URL, use as is
                if doc.identifier_cstr.startswith('http'):
                    identifier_cstr_url = doc.identifier_cstr
                # Otherwise, construct the CSTR URL with correct format
                else:
                    identifier_cstr_url = f"https://www.cstr.cn/detail?identifier={doc.identifier_cstr}"
            
            metadata = {
                "title": doc.title,
                "description": doc.description,
                "fileUrl": fix_file_url(doc.file_url),
                "publicationType": pub_type_name,
                "identifierType": identifier_type_name,
                "identifierCstr": identifier_cstr_url,  # Full resolvable CSTR URL
                "parentId": publication.doi,
                "createdOn": int(datetime.now().timestamp())
            }
            
            if doc.external_identifier:
                metadata["externalIdentifier"] = doc.external_identifier
                metadata["externalIdentifierType"] = doc.external_identifier_type
                if doc.external_identifier_type:
                    metadata[doc.external_identifier_type.lower()] = doc.external_identifier
            
            object_data = {
                "attributes": {
                    "content": metadata
                }
            }
            
            logger.info(f"Pushing PublicationDocument {doc.id} to CORDRA with handle: {doc.handle_identifier}")
            response = update_object(doc.handle_identifier, object_data)
            
            # If object doesn't exist (404), try to create it
            if isinstance(response, dict) and response.get('status_code') == 404:
                logger.info(f"Document {doc.handle_identifier} not found in CORDRA, attempting to create it")
                response = create_or_update_semantic_object("APA_Handle_ID", doc.handle_identifier, metadata)
                logger.info(f"CORDRA create response for PublicationDocument {doc.id}: {response}")
            else:
                logger.info(f"CORDRA response for PublicationDocument {doc.id}: {response}")
            
            count += 1
            
        logger.info(f"Pushed {count} PublicationDocuments for Publication {publication.id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to push PublicationDocuments for Publication {publication.id}: {str(e)}")
        return False

def push_publication_creators_to_cordra(publication):
    """Push all publication creators to CORDRA"""
    try:
        creators = PublicationCreators.query.filter_by(publication_id=publication.id).all()
        
        if not creators:
            logger.info(f"No creators found for Publication {publication.id}")
            return True
            
        # Prepare creators list for CORDRA
        creators_list = []
        for creator in creators:
            # Get role name
            role = CreatorsRoles.query.filter_by(role_id=creator.role_id).first()
            role_name = role.role_name if role else "Author"
            
            creator_data = {
                "familyName": creator.family_name,
                "givenName": creator.given_name,
                "fullName": f"{creator.given_name} {creator.family_name}",
                "identifier": creator.identifier,  # This now contains the full resolvable URL
                "identifierType": creator.identifier_type,  # e.g., 'orcid', 'isni', 'viaf'
                "role": role_name,
                "parentId": publication.doi
            }
            
            # Add specific identifier field for easier access
            if creator.identifier_type and creator.identifier:
                creator_data[creator.identifier_type.lower()] = creator.identifier
            creators_list.append(creator_data)
        
        # Update publication metadata with creators
        metadata = {
            "creators": creators_list,
            "creatorsCount": len(creators_list)
        }
        
        # Create a synthetic handle for creators collection
        creators_handle = f"{publication.doi}/creators"
        
        content_data = {
            "parentId": publication.doi,
            "publicationId": str(publication.id),
            "creators": creators_list,
            "createdOn": int(datetime.now().timestamp())
        }
        
        logger.info(f"Creating/Updating {len(creators)} PublicationCreators for Publication {publication.id}")
        # Use APA_Handle_ID type which exists in CORDRA
        response = create_or_update_semantic_object("APA_Handle_ID", creators_handle, content_data)
        logger.info(f"CORDRA response for PublicationCreators: {response}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to push PublicationCreators for Publication {publication.id}: {str(e)}")
        return False

def push_publication_organizations_to_cordra(publication):
    """Push all publication organizations to CORDRA"""
    try:
        organizations = PublicationOrganization.query.filter_by(publication_id=publication.id).all()
        
        if not organizations:
            logger.info(f"No organizations found for Publication {publication.id}")
            return True
            
        # Prepare organizations list for CORDRA
        orgs_list = []
        for org in organizations:
            org_data = {
                "name": org.name,
                "type": org.type,
                "otherName": org.other_name,
                "country": org.country,
                "parentId": publication.doi
            }
            
            # Add identifier fields (now that organization identifiers are supported)
            if org.identifier:
                org_data["identifier"] = org.identifier  # Full resolvable URL (e.g., https://ror.org/02qv1aw94)
                if org.identifier_type:
                    org_data["identifierType"] = org.identifier_type  # e.g., 'ror', 'grid', 'isni'
                    org_data[org.identifier_type.lower()] = org.identifier
            orgs_list.append(org_data)
        
        # Create a synthetic handle for organizations collection
        orgs_handle = f"{publication.doi}/organizations"
        
        content_data = {
            "parentId": publication.doi,
            "publicationId": str(publication.id),
            "organizations": orgs_list,
            "organizationsCount": len(orgs_list),
            "createdOn": int(datetime.now().timestamp())
        }
        
        logger.info(f"Creating/Updating {len(organizations)} PublicationOrganizations for Publication {publication.id}")
        # Use APA_Handle_ID type which exists in CORDRA
        response = create_or_update_semantic_object("APA_Handle_ID", orgs_handle, content_data)
        logger.info(f"CORDRA response for PublicationOrganizations: {response}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to push PublicationOrganizations for Publication {publication.id}: {str(e)}")
        return False

def push_publication_funders_to_cordra(publication):
    """Push all publication funders to CORDRA"""
    try:
        funders = PublicationFunders.query.filter_by(publication_id=publication.id).all()
        
        if not funders:
            logger.info(f"No funders found for Publication {publication.id}")
            return True
            
        # Prepare funders list for CORDRA
        funders_list = []
        for funder in funders:
            # Get funder type name
            funder_type = FunderTypes.query.filter_by(id=funder.funder_type_id).first()
            funder_type_name = funder_type.funder_type_name if funder_type else "Unknown"
            
            funder_data = {
                "name": funder.name,
                "type": funder.type,
                "funderType": funder_type_name,
                "otherName": funder.other_name,
                "country": funder.country,
                "identifier": funder.identifier,  # This now contains the full resolvable URL (e.g., https://ror.org/01bj3aw27)
                "identifierType": funder.identifier_type,  # e.g., 'ror', 'fundref', 'isni'
                "parentId": publication.doi
            }
            
            # Add specific identifier field for easier access
            if funder.identifier_type and funder.identifier:
                funder_data[funder.identifier_type.lower()] = funder.identifier
            funders_list.append(funder_data)
        
        # Create a synthetic handle for funders collection
        funders_handle = f"{publication.doi}/funders"
        
        content_data = {
            "parentId": publication.doi,
            "publicationId": str(publication.id),
            "funders": funders_list,
            "fundersCount": len(funders_list),
            "createdOn": int(datetime.now().timestamp())
        }
        
        logger.info(f"Creating/Updating {len(funders)} PublicationFunders for Publication {publication.id}")
        # Use APA_Handle_ID type which exists in CORDRA
        response = create_or_update_semantic_object("APA_Handle_ID", funders_handle, content_data)
        logger.info(f"CORDRA response for PublicationFunders: {response}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to push PublicationFunders for Publication {publication.id}: {str(e)}")
        return False

def push_publication_projects_to_cordra(publication):
    """Push all publication projects to CORDRA"""
    try:
        projects = PublicationProjects.query.filter_by(publication_id=publication.id).all()
        
        if not projects:
            logger.info(f"No projects found for Publication {publication.id}")
            return True
            
        # Prepare projects list for CORDRA
        projects_list = []
        for project in projects:
            project_data = {
                "title": project.title,
                "raidId": project.raid_id,  # Keep for backward compatibility
                "description": project.description,
                "identifier": project.identifier,  # Full resolvable URL (e.g., https://app.demo.raid.org.au/raids/10.80368/b1adfb3a)
                "identifierType": project.identifier_type,  # Will be 'raid'
                "parentId": publication.doi
            }
            
            # Add dynamic field for easier access
            if project.identifier_type and project.identifier:
                project_data[project.identifier_type.lower()] = project.identifier
            projects_list.append(project_data)
        
        # Create a synthetic handle for projects collection
        projects_handle = f"{publication.doi}/projects"
        
        content_data = {
            "parentId": publication.doi,
            "publicationId": str(publication.id),
            "projects": projects_list,
            "projectsCount": len(projects_list),
            "createdOn": int(datetime.now().timestamp())
        }
        
        logger.info(f"Creating/Updating {len(projects)} PublicationProjects for Publication {publication.id}")
        # Use APA_Handle_ID type which exists in CORDRA
        response = create_or_update_semantic_object("APA_Handle_ID", projects_handle, content_data)
        logger.info(f"CORDRA response for PublicationProjects: {response}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to push PublicationProjects for Publication {publication.id}: {str(e)}")
        return False

def main():
    """Main function to push all publications and their semantics to CORDRA"""
    
    import argparse
    parser = argparse.ArgumentParser(description='Push publications to CORDRA')
    parser.add_argument('--publication-id', type=int, help='Push only a specific publication ID')
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("Starting CORDRA push process")
    logger.info(f"Application domain: {APPLICATION_DOMAIN}")
    if args.publication_id:
        logger.info(f"Processing only publication ID: {args.publication_id}")
    logger.info("=" * 80)
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        try:
            # Get publications to process
            if args.publication_id:
                # Process single publication
                publication = Publications.query.get(args.publication_id)
                if not publication:
                    logger.error(f"Publication {args.publication_id} not found")
                    return 1
                publications = [publication]
            else:
                # Get all publications
                publications = Publications.query.all()
            
            total_publications = len(publications)
            
            logger.info(f"Found {total_publications} publications to process")
            
            success_count = 0
            failed_count = 0
            
            for idx, publication in enumerate(publications, 1):
                logger.info(f"\nProcessing Publication {idx}/{total_publications}: ID={publication.id}, DOI={publication.doi}")
                
                try:
                    # Push main publication
                    if push_publication_to_cordra(publication):
                        # Push all related data
                        push_publication_files_to_cordra(publication)
                        push_publication_documents_to_cordra(publication)
                        push_publication_creators_to_cordra(publication)
                        push_publication_organizations_to_cordra(publication)
                        push_publication_funders_to_cordra(publication)
                        push_publication_projects_to_cordra(publication)
                        
                        success_count += 1
                        logger.info(f"✓ Successfully pushed Publication {publication.id} and all semantics")
                    else:
                        failed_count += 1
                        logger.error(f"✗ Failed to push Publication {publication.id}")
                        
                except Exception as e:
                    failed_count += 1
                    logger.error(f"✗ Error processing Publication {publication.id}: {str(e)}")
                    continue
            
            # Summary
            logger.info("\n" + "=" * 80)
            logger.info("CORDRA Push Summary:")
            logger.info(f"  Total publications: {total_publications}")
            logger.info(f"  Successful: {success_count}")
            logger.info(f"  Failed: {failed_count}")
            logger.info("=" * 80)
            
            return 0 if failed_count == 0 else 1
            
        except Exception as e:
            logger.error(f"Fatal error in main process: {str(e)}")
            return 1

if __name__ == "__main__":
    sys.exit(main())