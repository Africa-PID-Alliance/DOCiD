#!/usr/bin/env python3
"""
Script to push recently created publications to CORDRA
Runs every minute via cron and processes publications created in the last 2 minutes
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# Add the parent directory to system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from config import Config
    from app import db, create_app
    from app.models import Publications
    import subprocess
except ImportError as e:
    print(f"Error: Could not import required modules: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/push_recent_cordra.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Process publications created in the last 2 minutes"""
    
    logger.info("Checking for recent publications to push to CORDRA...")
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        try:
            # Get publications created in the last 2 minutes
            two_minutes_ago = datetime.now() - timedelta(minutes=2)
            
            recent_publications = Publications.query.filter(
                Publications.published >= two_minutes_ago
            ).all()
            
            if not recent_publications:
                logger.info("No recent publications found")
                return 0
            
            logger.info(f"Found {len(recent_publications)} recent publications")
            
            for publication in recent_publications:
                logger.info(f"Processing publication {publication.id} created at {publication.published}")
                
                # Run the push script for this specific publication
                result = subprocess.run(
                    [sys.executable, 'push_to_cordra.py', '--publication-id', str(publication.id)],
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(os.path.abspath(__file__))
                )
                
                if result.returncode == 0:
                    logger.info(f"✓ Successfully pushed publication {publication.id}")
                else:
                    logger.error(f"✗ Failed to push publication {publication.id}: {result.stderr}")
            
            return 0
            
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return 1

if __name__ == "__main__":
    sys.exit(main())