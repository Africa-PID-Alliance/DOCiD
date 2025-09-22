#!/bin/bash

# CORDRA Push Script for Local Testing

# Navigate to the backend directory
cd /Users/ekariz/Projects/AMBAND/DOCiD/backend/

# Set Flask environment
export FLASK_APP=app.py

# Set Python path to ensure imports work
export PYTHONPATH=/Users/ekariz/Projects/AMBAND/DOCiD/backend:$PYTHONPATH

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