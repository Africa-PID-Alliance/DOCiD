#!/bin/bash

# Metadata Enrichment Cron Script
# Runs all enrichment sources sequentially with rate-limit-aware batch sizes
# Safe to re-run: skips publications already enriched by each source

# Lockfile to prevent overlapping runs
LOCKFILE="/tmp/enrich_metadata.lock"
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
echo "========================================" >> logs/enrich_metadata.log
echo "Starting metadata enrichment at $(date)" >> logs/enrich_metadata.log
echo "========================================" >> logs/enrich_metadata.log

# Run each source sequentially — each is individually resumable
python3 enrich_metadata.py --source openalex --batch-size 100 >> logs/enrich_metadata.log 2>&1
python3 enrich_metadata.py --source unpaywall --batch-size 100 >> logs/enrich_metadata.log 2>&1
python3 enrich_metadata.py --source semantic_scholar --batch-size 50 >> logs/enrich_metadata.log 2>&1
python3 enrich_metadata.py --source openaire --batch-size 100 >> logs/enrich_metadata.log 2>&1

# Check exit code
if [ $? -eq 0 ]; then
    echo "Metadata enrichment completed successfully at $(date)" >> logs/enrich_metadata.log
else
    echo "Metadata enrichment failed at $(date)" >> logs/enrich_metadata.log
fi

echo "" >> logs/enrich_metadata.log

# Deactivate virtual environment
deactivate
