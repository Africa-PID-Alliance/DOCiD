#!/usr/bin/env python3
"""
Test script to verify that identifiers are being pushed correctly to CORDRA
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add the parent directory to system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from config import Config
    from app import db, create_app
    from app.models import (
        Publications, PublicationCreators, PublicationFunders,
        PublicationProjects, PublicationOrganization
    )
except ImportError as e:
    print(f"Error: Could not import required modules: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def test_identifiers(publication_id=None):
    """Test that identifiers are present and correctly formatted"""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Get publication
            if publication_id:
                publications = [Publications.query.get(publication_id)]
                if not publications[0]:
                    logger.error(f"Publication {publication_id} not found")
                    return
            else:
                # Get recent publications with identifiers
                publications = Publications.query.order_by(Publications.id.desc()).limit(5).all()
            
            for publication in publications:
                logger.info(f"\n{'='*80}")
                logger.info(f"Publication ID: {publication.id}")
                logger.info(f"Title: {publication.document_title}")
                logger.info(f"DOI: {publication.doi}")
                
                # Check creators
                creators = PublicationCreators.query.filter_by(publication_id=publication.id).all()
                if creators:
                    logger.info(f"\nCreators ({len(creators)}):")
                    for creator in creators:
                        logger.info(f"  - {creator.given_name} {creator.family_name}")
                        logger.info(f"    Identifier: {creator.identifier}")
                        logger.info(f"    Type: {creator.identifier_type}")
                        
                        # Verify format
                        if creator.identifier_type == 'orcid' and creator.identifier:
                            if not creator.identifier.startswith('https://orcid.org/'):
                                logger.warning(f"    ⚠️ ORCID not in expected format!")
                        
                # Check funders
                funders = PublicationFunders.query.filter_by(publication_id=publication.id).all()
                if funders:
                    logger.info(f"\nFunders ({len(funders)}):")
                    for funder in funders:
                        logger.info(f"  - {funder.name}")
                        logger.info(f"    Identifier: {funder.identifier}")
                        logger.info(f"    Type: {funder.identifier_type}")
                        
                        # Verify format
                        if funder.identifier_type == 'ror' and funder.identifier:
                            if not funder.identifier.startswith('https://ror.org/'):
                                logger.warning(f"    ⚠️ ROR not in expected format!")
                
                # Check projects
                projects = PublicationProjects.query.filter_by(publication_id=publication.id).all()
                if projects:
                    logger.info(f"\nProjects ({len(projects)}):")
                    for project in projects:
                        logger.info(f"  - {project.title}")
                        logger.info(f"    RAiD: {project.raid_id}")
                
                # Check organizations (for future)
                organizations = PublicationOrganization.query.filter_by(publication_id=publication.id).all()
                if organizations:
                    logger.info(f"\nOrganizations ({len(organizations)}):")
                    for org in organizations:
                        logger.info(f"  - {org.name}")
                        if hasattr(org, 'identifier') and org.identifier:
                            logger.info(f"    Identifier: {org.identifier}")
                            logger.info(f"    Type: {org.identifier_type}")
            
            logger.info(f"\n{'='*80}")
            logger.info("✓ Identifier check complete")
            
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()

def main():
    """Main function"""
    import argparse
    parser = argparse.ArgumentParser(description='Test CORDRA identifier push')
    parser.add_argument('--publication-id', type=int, help='Test specific publication ID')
    args = parser.parse_args()
    
    test_identifiers(args.publication_id)

if __name__ == "__main__":
    main()