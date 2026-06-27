#!/bin/bash

# OAI-PMH Harvest Cron Script
# Triggers incremental harvests for ScienceOpen and CiteSeerX.
# Each run fetches only records newer than the last successful checkpoint
# (stored in the harvest_state table).
#
# Schedule suggestion: daily, offset from enrich_metadata_cron.sh
# Example crontab:
#   0 2 * * * /home/tcc-africa/docid_project/backend-v2/harvest_oai_pmh_cron.sh
#
# To test CiteSeerX endpoint liveness before enabling:
#   curl "https://citeseerx.ist.psu.edu/oai2?verb=Identify"

LOCKFILE="/tmp/harvest_oai_pmh.lock"
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

LOG=logs/harvest_oai_pmh.log
echo "========================================" >> "$LOG"
echo "Starting OAI-PMH harvest at $(date)"     >> "$LOG"
echo "========================================" >> "$LOG"

# Inline Python runner — calls service_*.harvest() directly so no HTTP
# round-trip through the Flask dev server is needed.
python3 - <<'PYEOF' >> "$LOG" 2>&1
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) or '.'))
from app import create_app, db

app = create_app()
with app.app_context():

    # ── ScienceOpen ──────────────────────────────────────────────────────
    try:
        from app.service_scienceopen import harvest as scienceopen_harvest
        result = scienceopen_harvest(db.session, page_limit=0)
        print(f"[scienceopen] {result}")
    except Exception as exc:
        print(f"[scienceopen] ERROR: {exc}")

    # ── CiteSeerX (disabled by default — endpoint unreliable since 2022) ─
    # Uncomment once you have verified the endpoint is alive:
    #   curl "https://citeseerx.ist.psu.edu/oai2?verb=Identify"
    #
    # try:
    #     from app.service_citeseerx import harvest as citeseerx_harvest
    #     result = citeseerx_harvest(db.session, page_limit=0)
    #     print(f"[citeseerx] {result}")
    # except Exception as exc:
    #     print(f"[citeseerx] ERROR: {exc}")

PYEOF

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "OAI-PMH harvest completed successfully at $(date)" >> "$LOG"
else
    echo "OAI-PMH harvest failed (exit $EXIT_CODE) at $(date)" >> "$LOG"
fi
echo "" >> "$LOG"

deactivate
