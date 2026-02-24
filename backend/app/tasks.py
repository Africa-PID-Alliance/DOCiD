"""
Celery tasks for asynchronous processing
"""
from celery import Celery
import subprocess
import logging
from datetime import datetime
import os
import sys

# Add the parent directory to system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config

# Configure Celery
celery = Celery('tasks', broker=Config.CELERY_BROKER_URL or 'redis://localhost:6379/0')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@celery.task
def push_to_cordra_async(publication_id):
    """
    Asynchronously push publication to CORDRA after a delay.
    Idempotent: skips minting if publication already has a DOI or is already minted.
    """
    try:
        logger.info(f"Starting CORDRA push for publication {publication_id}")

        # Idempotency guard: reload publication and check if minting should be skipped
        try:
            from app import create_app, db
            from app.models import Publications
            app = create_app()
            with app.app_context():
                publication = Publications.query.get(publication_id)
                if not publication:
                    logger.error(f"Publication {publication_id} not found, skipping CORDRA push")
                    return False

                # Skip if DOI exists (Figshare provided one)
                if publication.doi and publication.doi.strip():
                    logger.info(f"Publication {publication_id} has DOI '{publication.doi}', skipping CORDRA mint")
                    publication.cordra_synced = True
                    publication.cordra_status = 'SKIPPED'
                    db.session.commit()
                    return True

                # Skip if already minted (document_docid starts with 'DOCiD:')
                if publication.document_docid and publication.document_docid.startswith('DOCiD:'):
                    logger.info(f"Publication {publication_id} already minted: {publication.document_docid}")
                    publication.cordra_synced = True
                    publication.cordra_status = 'MINTED'
                    db.session.commit()
                    return True
        except ImportError:
            logger.warning("Could not import app for idempotency check, proceeding with CORDRA push")

        # Run the update and push script
        result = subprocess.run(
            [sys.executable, 'scripts/update_and_push_to_cordra.py', '--publication-id', str(publication_id)],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        if result.returncode == 0:
            logger.info(f"Successfully pushed publication {publication_id} to CORDRA")
            # Update cordra_status on success
            try:
                from app import create_app, db
                from app.models import Publications
                app = create_app()
                with app.app_context():
                    publication = Publications.query.get(publication_id)
                    if publication:
                        publication.cordra_synced = True
                        publication.cordra_status = 'MINTED'
                        publication.cordra_synced_at = datetime.utcnow()
                        db.session.commit()
            except Exception:
                pass
        else:
            logger.error(f"Failed to push publication {publication_id}: {result.stderr}")
            # Record failure
            try:
                from app import create_app, db
                from app.models import Publications
                app = create_app()
                with app.app_context():
                    publication = Publications.query.get(publication_id)
                    if publication:
                        publication.cordra_status = 'FAILED'
                        publication.cordra_error = result.stderr[:500] if result.stderr else 'Unknown error'
                        db.session.commit()
            except Exception:
                pass

        return result.returncode == 0

    except Exception as e:
        logger.error(f"Error pushing publication {publication_id} to CORDRA: {str(e)}")
        # Record failure
        try:
            from app import create_app, db
            from app.models import Publications
            app = create_app()
            with app.app_context():
                publication = Publications.query.get(publication_id)
                if publication:
                    publication.cordra_status = 'FAILED'
                    publication.cordra_error = str(e)[:500]
                    db.session.commit()
        except Exception:
            pass
        return False