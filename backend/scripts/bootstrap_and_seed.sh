#!/usr/bin/env sh
set -eu

echo "Waiting for database connectivity..."
python - <<'PY'
import os
import time
import psycopg2

dsn = os.getenv("DATABASE_URL")
if not dsn:
    raise RuntimeError("DATABASE_URL must be set")

for _ in range(60):
    try:
        conn = psycopg2.connect(dsn)
        conn.close()
        print("Database is reachable.")
        break
    except Exception:
        time.sleep(2)
else:
    raise RuntimeError("Database did not become ready in time")
PY

echo "Creating schema from models..."
flask create-db
echo "Stamping alembic head..."
flask db stamp head

echo "Seeding core reference data..."
python fix_alembic_state.py
python seed_reference_data.py
python seed_harvest_sources.py

echo "Bootstrap and seed completed."
