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
    Asynchronously push publication to CORDRA after a delay
    """
    try:
        logger.info(f"Starting CORDRA push for publication {publication_id}")
        
        # Run the update and push script
        result = subprocess.run(
            [sys.executable, 'update_and_push_to_cordra.py', '--publication-id', str(publication_id)],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        if result.returncode == 0:
            logger.info(f"Successfully pushed publication {publication_id} to CORDRA")
        else:
            logger.error(f"Failed to push publication {publication_id}: {result.stderr}")
            
        return result.returncode == 0
        
    except Exception as e:
        logger.error(f"Error pushing publication {publication_id} to CORDRA: {str(e)}")
        return False