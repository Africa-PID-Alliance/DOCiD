#!/usr/bin/env python3
"""
Wrapper script to run identifier updates and CORDRA push in sequence

This script:
1. First runs update_all_cstr_identifiers.py to ensure all documents have identifiers
2. Then runs push_to_cordra.py to push all data to CORDRA
"""

import os
import sys
import subprocess
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/update_and_push.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_script(script_name):
    """Run a Python script and return its exit code"""
    logger.info(f"Starting execution of {script_name}")
    start_time = datetime.now()
    
    try:
        # Run the script
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        if result.returncode == 0:
            logger.info(f"✓ {script_name} completed successfully in {duration:.2f} seconds")
            if result.stdout:
                logger.info(f"Output from {script_name}:\n{result.stdout}")
            return 0
        else:
            logger.error(f"✗ {script_name} failed with exit code {result.returncode} after {duration:.2f} seconds")
            if result.stderr:
                logger.error(f"Error output:\n{result.stderr}")
            if result.stdout:
                logger.info(f"Standard output:\n{result.stdout}")
            return result.returncode
            
    except Exception as e:
        logger.error(f"✗ Failed to run {script_name}: {str(e)}")
        return 1

def main():
    """Main function to run both scripts in sequence"""
    
    logger.info("=" * 80)
    logger.info("Starting identifier update and CORDRA push process")
    logger.info("=" * 80)
    
    # Step 1: Run identifier update script
    logger.info("\n--- Step 1: Updating CSTR identifiers ---")
    ret_code = run_script("update_all_cstr_identifiers.py")
    
    if ret_code != 0:
        logger.error("Identifier update failed. Aborting CORDRA push.")
        return ret_code
    
    # Step 2: Run CORDRA push script
    logger.info("\n--- Step 2: Pushing data to CORDRA ---")
    ret_code = run_script("push_to_cordra.py")
    
    if ret_code != 0:
        logger.error("CORDRA push failed.")
        return ret_code
    
    # Success
    logger.info("\n" + "=" * 80)
    logger.info("✓ Both scripts completed successfully!")
    logger.info("  1. All identifiers have been updated")
    logger.info("  2. All data has been pushed to CORDRA")
    logger.info("=" * 80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())