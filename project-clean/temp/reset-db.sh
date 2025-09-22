cd /Users/ekariz/Projects/AMBAND/DOCiD/backend/
export FLASK_APP=app.py
python3 -m venv venv
source venv/bin/activate

python3 manage.py drop-db
python3 manage.py create-db
python3 manage.py seed-db
python3 manage.py generate-pids
