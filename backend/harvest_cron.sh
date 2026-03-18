#!/bin/bash

# Repository Harvest Cron Script
# Pulls new records from configured institutional repositories (DSpace, Figshare, OJS)
# Safe to re-run: uses UUID/handle deduplication to skip existing records

# Lockfile to prevent overlapping runs
LOCKFILE="/tmp/harvest_repos.lock"
if [ -f "$LOCKFILE" ]; then
    OLD_PID=$(cat "$LOCKFILE" 2>/dev/null || true)
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
        exit 0
    fi
    rm -f "$LOCKFILE"
fi
echo $$ > "$LOCKFILE"
trap 'rm -f "$LOCKFILE"' EXIT

# Navigate to the backend directory
cd /home/tcc-africa/docid_project/backend-v2/

# Set Flask environment
export FLASK_APP=app.py

# Activate virtual environment
source venv/bin/activate

# Set Python path
export PYTHONPATH=/home/tcc-africa/docid_project/backend-v2:$PYTHONPATH

# Create logs directory if it doesn't exist
mkdir -p logs

# Log start time
echo "========================================" >> logs/harvest_repos.log
echo "Starting repository harvest at $(date)" >> logs/harvest_repos.log
echo "========================================" >> logs/harvest_repos.log

# Harvest from all configured sources
python3 harvest_repositories.py --source all >> logs/harvest_repos.log 2>&1

# Check exit code
if [ $? -eq 0 ]; then
    echo "Repository harvest completed successfully at $(date)" >> logs/harvest_repos.log
else
    echo "Repository harvest failed at $(date)" >> logs/harvest_repos.log
fi

echo "" >> logs/harvest_repos.log

# Deactivate virtual environment
deactivate
