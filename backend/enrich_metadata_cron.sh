#!/bin/bash

# Metadata Enrichment Cron Script
# Runs enrichment sources sequentially; each is individually resumable.
# Add a provider to ENRICHMENT_SOURCES in .env (not here) to activate it.
# Safe to re-run: skips publications already in a terminal status per source.

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

cd /home/tcc-africa/docid_project/backend-v2/

export FLASK_APP=app.py
source venv/bin/activate
export PYTHONPATH=/home/tcc-africa/docid_project/backend-v2:$PYTHONPATH

mkdir -p logs

LOG=logs/enrich_metadata.log
echo "========================================" >> "$LOG"
echo "Starting metadata enrichment at $(date)" >> "$LOG"
echo "========================================" >> "$LOG"

# ── Wave 0 (original providers) ───────────────────────────────────────────
python3 enrich_metadata.py --source openalex          --batch-size 100 >> "$LOG" 2>&1
python3 enrich_metadata.py --source unpaywall         --batch-size 100 >> "$LOG" 2>&1

# ── Wave 1 ────────────────────────────────────────────────────────────────
# Semantic Scholar: free-tier rate limit ~1 req/s — keep batch small
python3 enrich_metadata.py --source semantic_scholar  --batch-size  50 >> "$LOG" 2>&1
python3 enrich_metadata.py --source openaire          --batch-size 100 >> "$LOG" 2>&1

# CORE: free tier ~10k req/day — enable once CORE_API_KEY is in .env
# python3 enrich_metadata.py --source core             --batch-size  50 >> "$LOG" 2>&1

# OpenCitations: no hard quota; rate limit 1 req/s default
python3 enrich_metadata.py --source opencitations    --batch-size  50 >> "$LOG" 2>&1

# ── Wave 2 ────────────────────────────────────────────────────────────────
# Lens.org: enable once LENS_SCHOLAR_API_KEY + LENS_PATENT_API_KEY are in .env
# python3 enrich_metadata.py --source lens_org         --batch-size  30 >> "$LOG" 2>&1

# ── Wave 4 ────────────────────────────────────────────────────────────────
# BASE: enable once BASE_API_KEY is in .env (requires approved application)
# python3 enrich_metadata.py --source base             --batch-size  50 >> "$LOG" 2>&1

# WorldCat: enable once WORLDCAT_CLIENT_ID + WORLDCAT_CLIENT_SECRET are in .env
# python3 enrich_metadata.py --source worldcat         --batch-size  30 >> "$LOG" 2>&1

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "Metadata enrichment completed successfully at $(date)" >> "$LOG"
else
    echo "Metadata enrichment failed (exit $EXIT_CODE) at $(date)" >> "$LOG"
fi
echo "" >> "$LOG"

deactivate
