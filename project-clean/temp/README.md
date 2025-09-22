# DOCiD Backend Setup and Deployment Guide

This document provides comprehensive instructions for setting up, running, and maintaining the DOCiD backend application.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Database Setup](#database-setup)
4. [Running Migrations](#running-migrations)
5. [Running the Application](#running-the-application)
6. [Service Configuration](#service-configuration)
   - [CSTR Identifier Update Service](#cstr-identifier-update-service)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.9+ 
- PostgreSQL database
- pip (Python package installer)
- virtualenv or venv for Python environment management

## Initial Setup

### 1. Clone the Repository (if you haven't already)

```bash
git clone <repository-url>
cd DOCiD/backend
```

### 2. Create and Activate Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# For minimal installation (production only)
pip install -r requirements_minimal.txt
```

### 4. Environment Configuration

Create a `.env` file in the backend directory with the following variables:

```
# Database configuration
SQLALCHEMY_DATABASE_URI=postgresql://username:password@localhost/docid_db

# Security configuration
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here

# API configuration
CSTR_CLIENT_ID=your_cstr_client_id
CSTR_SECRET=your_cstr_secret
CSTR_PREFIX=your_cstr_prefix

# Email configuration (if using email features)
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_email_password
MAIL_USE_TLS=True

# Debug mode (set to False in production)
DEBUG=True
```

## Database Setup

### 1. Create the PostgreSQL Database

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE docid_db;
CREATE USER docid_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE docid_db TO docid_user;
```

### 2. Initialize the Database

```bash
# From the backend directory, with virtual environment activated
python manage.py create-db
python manage.py seed-db    # Optional: Seed with initial data
```

## Running Migrations

The DOCiD project uses Flask-Migrate for database migrations. The `run_migrations.sh` script provides a convenient way to manage migrations.

### Basic Migration Commands

```bash
# Initialize migrations (if not already initialized)
./run_migrations.sh init

# Generate a new migration
./run_migrations.sh migrate -m "Updates"

# Apply migrations to the database
./run_migrations.sh upgrade

# Downgrade to previous migration version
./run_migrations.sh downgrade

# Show current migration version
./run_migrations.sh current

# Show migration history
./run_migrations.sh history
```

### Migration Tips

- Always backup your database before running migrations in production
- Review the generated migration files before applying them
- Test migrations in a development environment first

## Running the Application

### Development Mode

```bash
# Set environment variables
export FLASK_APP=run.py
export FLASK_ENV=development
export FLASK_DEBUG=1

# Run the application
flask run --host=0.0.0.0 --port=5000
```

### Production Mode with Gunicorn

```bash
# Run with gunicorn (adjust workers as needed)
gunicorn --config gunicorn.conf.py wsgi:app
```

### Restart Application (if using Supervisor)

```bash
./restart.sh
```

## Service Configuration

### CSTR Identifier Update Service

The CSTR identifier update service processes publication documents and registers them with the CSTR API. This service should run regularly in production.

#### Setup as Systemd Service (Recommended for Production)

1. **Update the service unit file**:

   Edit `update_cstr_identifiers.service` to update paths and user:

   ```bash
   sudo nano /etc/systemd/system/update_cstr_identifiers.service
   ```

   Configuration should look like:

   ```ini
   [Unit]
   Description=CSTR Identifier Update Service
   After=network.target

   [Service]
   User=www-data  # Change to appropriate user
   Group=www-data  # Change to appropriate group
   WorkingDirectory=/path/to/DOCiD/backend
   ExecStart=/path/to/DOCiD/backend/update_all_cstr_identifiers.py
   Restart=always
   RestartSec=60
   StandardOutput=append:/path/to/DOCiD/backend/logs/cstr_update.log
   StandardError=append:/path/to/DOCiD/backend/logs/cstr_update.log

   [Install]
   WantedBy=multi-user.target
   ```

2. **Enable and start the service**:

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable update_cstr_identifiers.service
   sudo systemctl start update_cstr_identifiers.service
   ```

3. **Check service status**:

   ```bash
   sudo systemctl status update_cstr_identifiers.service
   ```

#### Alternative: Manual Cron Setup

1. **Open crontab for editing**:

   ```bash
   crontab -e
   ```

2. **Add the following entry**:

   ```
   # Run CSTR identifier update every minute
   * * * * * cd /path/to/DOCiD/backend && ./update_all_cstr_identifiers.py >> /path/to/DOCiD/backend/logs/cstr_update.log 2>&1
   ```

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL service status
sudo systemctl status postgresql

# Check database connection
psql -U docid_user -h localhost -d docid_db
```

### Application Startup Issues

1. **Check logs for errors**:

   ```bash
   tail -f logs/app.log
   ```

2. **Verify environment variables**:

   ```bash
   printenv | grep FLASK
   ```

3. **Check Python dependencies**:

   ```bash
   pip freeze | grep Flask
   ```

### Migration Issues

If you encounter errors during migrations:

1. **Module not found errors**:

   If you see errors like `ModuleNotFoundError: No module named 'flask'`, ensure all dependencies are installed:

   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

   Or install the specific missing package:

   ```bash
   pip install flask flask-migrate
   ```

2. **Check the migration repository**:

   ```bash
   ls -la migrations/versions/
   ```

3. **Verify database schema**:

   ```bash
   psql -U docid_user -d docid_db -c "\d"
   ```

4. **Reset migrations** (last resort, development only):

   ```bash
   rm -rf migrations/
   ./run_migrations.sh init
   ```

### CSTR Update Service Issues

1. **Check service logs**:

   ```bash
   sudo journalctl -u update_cstr_identifiers.service
   ```

2. **Manually run the script to test**:

   ```bash
   cd /path/to/DOCiD/backend
   ./update_all_cstr_identifiers.py
   ```

3. **Check permissions**:

   ```bash
   ls -la update_all_cstr_identifiers.py
   ls -la logs/
   ```

### Permission Issues

If you encounter "Permission denied" errors when running scripts:

1. **Set executable permissions for all scripts**:

   ```bash
   ./setup_permissions.sh
   ```

2. **Or manually set permissions for specific scripts**:

   ```bash
   chmod +x run_migrations.sh
   chmod +x update_all_cstr_identifiers.py
   ```

3. **Check current permissions**:

   ```bash
   ls -la *.sh *.py
   ```

### Database Management

Additional database management commands:

1. **Clear user data while preserving seeded lookup data**:

   ```bash
   ./clear_non_seeded_tables.py
   ```

2. **Truncate non-seeded tables** (alternative method, may require superuser privileges):

   ```bash
   ./truncate_non_seeded_tables.py
   ```

3. **Truncate all tables** (complete reset):

   ```bash
   ./truncate_all_tables.py
   ```

4. **Reseed lookup data**:

   ```bash
   python scripts/seed_db.py
   ```

## Additional Resources

- Flask Documentation: [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/)
- Flask-Migrate Documentation: [https://flask-migrate.readthedocs.io/](https://flask-migrate.readthedocs.io/)
- Gunicorn Documentation: [https://gunicorn.org/](https://gunicorn.org/)
- Supervisor Documentation: [http://supervisord.org/](http://supervisord.org/)
