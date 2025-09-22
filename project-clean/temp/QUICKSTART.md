# DOCiD Backend Quick Start Guide

This quick start guide provides the essential commands and steps to get the DOCiD backend up and running for development or basic testing purposes.

## Setup Environment

### 1. Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Create a `.env` file in the backend directory with:

```
SQLALCHEMY_DATABASE_URI=postgresql://username:password@localhost/docid_db
SECRET_KEY=dev_secret_key
JWT_SECRET_KEY=dev_jwt_secret
DEBUG=True
```

## Database Setup

### Create and initialize database

```bash
# Create PostgreSQL database
sudo -u postgres psql -c "CREATE DATABASE docid_db;"
sudo -u postgres psql -c "CREATE USER docid_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE docid_db TO docid_user;"

# Initialize database
python manage.py create-db
python manage.py seed-db
```

## Run Database Migrations

```bash
# Run all migrations
./run_migrations.sh upgrade
```

## Run Application (Development Mode)

```bash
# Set environment variables
export FLASK_APP=run.py
export FLASK_ENV=development
export FLASK_DEBUG=1

# Start application
flask run
```

## Key Services

### CSTR Identifier Update

Run the CSTR identifier update script manually:

```bash
# Process all publication documents with NULL identifier_cstr
./update_all_cstr_identifiers.py
```

## Common Commands

```bash
# Check current migration version
./run_migrations.sh current

# Create new migration
./run_migrations.sh migrate -m "Description of changes"

# Run tests
pytest

# Check application logs
tail -f logs/app.log

# Reset database (development only)
python manage.py drop-db
python manage.py create-db
python manage.py seed-db

# Generate PIDs for documents
python manage.py generate-pids
```
