#!/bin/bash

# ROR Organization Enrichment Cron Script
# Runs the ROR enrichment for newly synced publications
# Safe to re-run: skips publications that already have organization records

# Lockfile to prevent overlapping runs
LOCKFILE="/tmp/enrich_ror.lock"
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
echo "========================================" >> logs/enrich_ror.log
echo "Starting ROR enrichment at $(date)" >> logs/enrich_ror.log
echo "========================================" >> logs/enrich_ror.log

# Run the enrichment script
python3 enrich_ror_organizations.py >> logs/enrich_ror.log 2>&1

# Check exit code
if [ $? -eq 0 ]; then
    echo "ROR enrichment completed successfully at $(date)" >> logs/enrich_ror.log
else
    echo "ROR enrichment failed at $(date)" >> logs/enrich_ror.log
fi

echo "" >> logs/enrich_ror.log

# Deactivate virtual environment
deactivate
