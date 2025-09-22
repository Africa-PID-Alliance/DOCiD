# DOCiD Development Environment Setup

This guide provides detailed instructions for setting up a development environment for the DOCiD backend application.

## System Requirements

- Python 3.9+ (recommended: Python 3.10)
- PostgreSQL 12+
- Git
- pip and virtualenv

## Step 1: Clone the Repository

```bash
git clone <repository-url>
cd DOCiD/backend
```

## Step 2: Set Up Python Environment

### Create a virtual environment

```bash
python3 -m venv venv
```

### Activate the virtual environment

```bash
# On macOS/Linux
source venv/bin/activate

# On Windows
venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

## Step 3: Set Up PostgreSQL Database

### Install PostgreSQL (if not already installed)

```bash
# On macOS with Homebrew
brew install postgresql
brew services start postgresql

# On Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### Create a database for development

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# In PostgreSQL command line
CREATE DATABASE docid_db;
CREATE USER docid_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE docid_db TO docid_user;
ALTER USER docid_user CREATEDB;  # Needed for test database creation
\q
```

## Step 4: Configure Environment Variables

### Create a `.env` file in the project root

```
# Database configuration
SQLALCHEMY_DATABASE_URI=postgresql://docid_user:your_password@localhost/docid_db

# Security configuration
SECRET_KEY=dev_secret_key
JWT_SECRET_KEY=dev_jwt_secret

# API configuration
CSTR_CLIENT_ID=test_client_id
CSTR_SECRET=test_secret
CSTR_PREFIX=TEST

# Debug mode (enable for development)
DEBUG=True

# File storage configuration
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216  # 16MB in bytes
```

## Step 5: Initialize the Database

### Run database migrations

```bash
./run_migrations.sh upgrade
```

### Seed the database with sample data

```bash
python manage.py seed-db
```

## Step 6: Run the Development Server

### Set Flask environment variables

```bash
export FLASK_APP=run.py
export FLASK_ENV=development
export FLASK_DEBUG=1
```

### Start the development server

```bash
flask run
```

The application will be available at `http://localhost:5000`

## Step 7: Development Workflow

### Making database changes

1. Modify models in `app/models.py`
2. Create a migration:
   ```bash
   ./run_migrations.sh migrate -m "Description of changes"
   ```
3. Apply the migration:
   ```bash
   ./run_migrations.sh upgrade
   ```

### Running tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_specific_feature.py
```

### Testing CSTR identifier updates

```bash
# Test updating a single record
python test_single_cstr.py

# Test updating all records with NULL identifier_cstr
./update_all_cstr_identifiers.py
```

## Step 8: IDE Setup (Optional)

### VSCode Configuration

1. Install the Python extension
2. Configure `.vscode/settings.json`:
   ```json
   {
     "python.pythonPath": "venv/bin/python",
     "python.linting.enabled": true,
     "python.linting.pylintEnabled": true,
     "python.formatting.provider": "black",
     "editor.formatOnSave": true
   }
   ```

### PyCharm Configuration

1. Set the project interpreter to the virtualenv
2. Enable Flask integration in run configurations
3. Set environment variables in run configuration

## Troubleshooting

### Database connection errors

Verify PostgreSQL is running:
```bash
# macOS
brew services list

# Ubuntu
sudo systemctl status postgresql
```

### Missing dependencies

If you encounter import errors, install the missing package:
```bash
pip install package_name
```

### Migration issues

If migrations fail, check the current state:
```bash
./run_migrations.sh current
```

To reset migrations (development only):
```bash
rm -rf migrations/
./run_migrations.sh init
```
