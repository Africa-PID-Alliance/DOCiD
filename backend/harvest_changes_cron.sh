#!/bin/bash

# Every-minute check of watched DSpace collections (Indigenous Knowledge,
# Cultural Heritage): harvests the records changed since the last check, gives
# new ones a DOCiD and writes the DOCiD link back into DSpace. Writes nothing
# to the log when nothing changed.
#
# harvest_cron.sh still runs the daily full pass, which is what notices records
# DSpace has restricted, hidden or deleted.
#
# Crontab:
#   * * * * * /home/tcc-africa/docid_project/backend-v2/harvest_changes_cron.sh
#
# No lock file here: each source has its own lock inside the harvester, so a
# slow repository is skipped by the next check instead of holding up the rest,
# and a check never harvests a record the daily pass is harvesting.

cd /home/tcc-africa/docid_project/backend-v2/ || exit 1

export FLASK_APP=app.py
source venv/bin/activate
export PYTHONPATH=/home/tcc-africa/docid_project/backend-v2:$PYTHONPATH

mkdir -p logs
python3 harvest_repositories.py --changes-only >> logs/harvest_changes.log 2>&1
