#!/usr/bin/env python3
"""
Script to push recently created publications to CORDRA
Runs every minute via cron and processes publications created in the last 2 minutes
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text, func

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
    """Process publications that haven't been synced to CORDRA yet"""

    logger.info("Checking for unsynced publications to push to CORDRA...")

    # Create Flask app context
    app = create_app()

    with app.app_context():
        try:
            # CORDRA object id is the docid handle, NOT the DOI — most DOCiD
            # records are created without a DOI. Codex review: do NOT gate on
            # `published`; that's often the source paper's original publication
            # date (e.g. 2003 for a harvested record), so a freshness window on
            # `published` strands every backfilled / harvested publication
            # forever. Instead just pick up the newest unsynced rows by id
            # DESC and cap the per-tick batch so a backlog can't overwhelm
            # CORDRA. Retired (deleted_at) records are excluded — they should
            # not be pushed to CORDRA per the soft-delete plan.
            recent_publications = (
                Publications.query.filter(
                    (Publications.cordra_synced == False) | (Publications.cordra_synced == None),
                    Publications.document_docid.isnot(None),
                    func.trim(Publications.document_docid) != '',
                    Publications.deleted_at.is_(None),
                )
                # Drain oldest-first so a sudden burst of new docids can't
                # permanently starve earlier unsynced rows that just happen
                # to fall outside the per-tick LIMIT. Keep LIMIT small —
                # each row makes multiple CORDRA HTTPS calls (creators,
                # orgs, funders, files, projects) at 2-15s each, so a
                # high LIMIT combined with a 1-minute cron schedule caused
                # process pile-up that starved the docker host (see
                # 2026-06-24 incident — 502s on prod, SSH banner timeout).
                .order_by(Publications.id.asc())
                .limit(10)
                .all()
            )
            
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