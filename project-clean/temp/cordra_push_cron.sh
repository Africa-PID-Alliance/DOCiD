#!/bin/bash

# CORDRA Push Script for Cronjob
# This script runs every minute to push recent publications to CORDRA

# Navigate to the backend directory
cd /home/tcc-africa/docid_project/backend-v2/

# Set Flask environment
export FLASK_APP=app.py

# Activate virtual environment
source venv/bin/activate

# Set Python path to ensure imports work
export PYTHONPATH=/home/tcc-africa/docid_project/backend-v2:$PYTHONPATH

# Create logs directory if it doesn't exist
mkdir -p logs

# Log start time
echo "========================================" >> logs/cordra_sync.log
echo "Starting CORDRA sync at $(date)" >> logs/cordra_sync.log
echo "========================================" >> logs/cordra_sync.log

# Run the push recent script
python3 push_recent_to_cordra.py >> logs/cordra_sync.log 2>&1

# Check exit code
if [ $? -eq 0 ]; then
    echo "CORDRA sync completed successfully at $(date)" >> logs/cordra_sync.log
else
    echo "CORDRA sync failed at $(date)" >> logs/cordra_sync.log
fi

echo "" >> logs/cordra_sync.log

# Deactivate virtual environment
deactivate