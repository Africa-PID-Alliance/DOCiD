# DOCiD Flask API - Comprehensive Technical Documentation

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Integration Layer](#integration-layer)
3. [Storage & Data Model](#storage--data-model)
4. [Installation & Setup](#installation--setup)
5. [API Documentation](#api-documentation)
6. [Endpoints & Usage](#endpoints--usage)

## Architecture Overview

### System Architecture

The DOCiD (Document ID) system is a sophisticated Flask-based REST API designed to serve as a comprehensive publication and document identifier management platform. The system is architected with a focus on persistent identifier (PID) services, metadata management, and scholarly communication tools, specifically tailored for African academic and research institutions.

#### Core Architecture Components

**Application Layer**
- Flask application factory pattern with comprehensive extension integration
- Blueprint-based modular architecture with 20+ service-specific routes
- RESTful API design with JSON payload communication
- Swagger/OpenAPI documentation integration via Flasgger

**Service Layer**
- External service integration abstractions
- Background processing for batch operations
- Authentication and token management
- Error handling and fallback mechanisms

**Data Layer**
- SQLAlchemy ORM with PostgreSQL backend
- Complex relational model with cascading relationships
- Migration management via Alembic
- Reference data and controlled vocabularies

### Key Architectural Patterns

**Identifier Management Centralization**
The system implements a centralized approach to managing multiple persistent identifier types including DOIs, DocIDs, Handles, and other PIDs. This ensures consistency across all identifier operations and provides a unified interface for external systems.

**Hierarchical Data Structures**
Comments system implements a sophisticated tree structure allowing for threaded discussions with parent-child relationships, status management, and moderation capabilities.

**Service Integration Abstraction**
External service connectors are abstracted into dedicated service classes, providing consistent interfaces for interacting with Crossref, CSTR, CORDRA, ROR, ORCID, and Local Contexts APIs.

## Integration Layer

### External Service Integrations

#### CORDRA Digital Object Repository (`service_codra.py`)

**Purpose**: Integration with CORDRA (Content Organization and Repository Digital Archive) for digital object management and Handle identifier generation.

**Key Features**:
- Digital object creation and metadata deposit
- Handle identifier generation and management
- Authentication token management with automatic refresh
- Batch processing for bulk operations

**API Integration Pattern**:
```python
class CordraService:
    def authenticate(self) -> str
    def create_digital_object(self, metadata: dict, files: list) -> dict
    def update_digital_object(self, handle: str, metadata: dict) -> dict
    def get_digital_object(self, handle: str) -> dict
```

**Configuration Requirements**:
- CORDRA_BASE_URL: Repository base URL
- CORDRA_USERNAME: Authentication username
- CORDRA_PASSWORD: Authentication password

#### Crossref Services (`service_crossref.py`)

**Purpose**: Integration with Crossref for DOI metadata retrieval, validation, and registration.

**Key Features**:
- DOI metadata retrieval and validation
- XML submission for DOI registration
- Bulk DOI processing capabilities
- Search functionality across Crossref database

**API Integration Pattern**:
```python
class CrossrefService:
    def get_doi_metadata(self, doi: str) -> dict
    def submit_doi_registration(self, xml_data: str) -> dict
    def search_crossref(self, query: str, rows: int = 10) -> list
    def validate_doi(self, doi: str) -> bool
```

**Authentication**:
- Crossref Plus API token for enhanced access
- Email-based authentication for standard API access

#### CSTR Integration (`service_cstr.py`)

**Purpose**: Integration with China Science and Technology Resource platform for scientific data registration and metadata management.

**Key Features**:
- Scientific data registration with structured metadata
- Multi-language support (English/Chinese)
- Batch identifier assignment
- Status tracking and updates

**API Integration Pattern**:
```python
class CSTRService:
    def register_dataset(self, metadata: dict) -> str
    def update_dataset(self, cstr_id: str, metadata: dict) -> dict
    def get_dataset_status(self, cstr_id: str) -> dict
    def batch_register(self, datasets: list) -> list
```

**Background Processing**:
- Scheduled updates via cron jobs
- Batch processing for identifier assignment
- Status synchronization with local database

#### Research Organization Registry (ROR)

**Purpose**: Integration with ROR for organization identification and institutional metadata.

**Key Features**:
- Organization search and identification
- Institution metadata retrieval
- ROR ID validation and resolution
- Affiliation matching and verification

#### ORCID Services

**Purpose**: Integration with ORCID for researcher identification and profile management.

**Key Features**:
- Researcher identification and verification
- Profile metadata integration
- Authentication via ORCID OAuth
- Work submission to ORCID profiles

#### Local Contexts Integration

**Purpose**: Integration with Local Contexts for Indigenous knowledge protocols and cultural labels.

**Key Features**:
- Traditional Knowledge (TK) labels application
- Biocultural Community (BC) protocols
- Indigenous data sovereignty support
- Cultural metadata enhancement

### Authentication & Authorization

#### JWT-Based Authentication
- Flask-JWT-Extended implementation
- Access and refresh token management
- Role-based access control
- Social authentication integration

#### Social Authentication Providers
- Google OAuth 2.0
- ORCID OAuth 2.0
- GitHub OAuth 2.0
- Facebook OAuth 2.0

#### Permission Management
- User role hierarchy (user, admin, superadmin)
- Resource-based permissions
- Comment moderation permissions
- Publication ownership controls

## Storage & Data Model

### Database Architecture

The system utilizes PostgreSQL as the primary database, leveraging advanced features like JSON fields, full-text search, and complex indexing strategies.

#### Core Data Models

### User Management Schema

**UserAccount Model**
```python
class UserAccount(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    orcid_id = db.Column(db.String(19), unique=True)
    ror_id = db.Column(db.String(50))
    social_media_links = db.Column(db.JSON)
    google_id = db.Column(db.String(100), unique=True)
    github_id = db.Column(db.String(100), unique=True)
    facebook_id = db.Column(db.String(100), unique=True)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

**Key Features**:
- Multiple authentication provider support
- Rich profile information with social media integration
- ORCID and ROR ID integration for scholarly identification
- Role-based access control

### Publication Management Schema

**Publications Model**
```python
class Publications(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    docid = db.Column(db.String(50), unique=True)
    doi = db.Column(db.String(100), unique=True)
    resource_type_id = db.Column(db.Integer, db.ForeignKey('resource_types.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user_accounts.user_id'))
    metadata = db.Column(db.JSON)
    status = db.Column(db.String(20), default='draft')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

**Related Entities**:

**PublicationCreators** - Author/creator management with role assignment
```python
class PublicationCreators(db.Model):
    publication_id = db.Column(db.Integer, db.ForeignKey('publications.id'))
    creator_name = db.Column(db.String(255), nullable=False)
    orcid_id = db.Column(db.String(19))
    role_id = db.Column(db.Integer, db.ForeignKey('creators_roles.id'))
    affiliation = db.Column(db.String(500))
```

**PublicationOrganization** - Institutional affiliations with ROR integration
```python
class PublicationOrganization(db.Model):
    publication_id = db.Column(db.Integer, db.ForeignKey('publications.id'))
    organization_name = db.Column(db.String(255), nullable=False)
    ror_id = db.Column(db.String(50))
    organization_type = db.Column(db.String(100))
    country = db.Column(db.String(100))
```

**PublicationFunders** - Funding information with structured identifiers
```python
class PublicationFunders(db.Model):
    publication_id = db.Column(db.Integer, db.ForeignKey('publications.id'))
    funder_name = db.Column(db.String(255), nullable=False)
    funder_id = db.Column(db.String(100))
    grant_number = db.Column(db.String(100))
    award_amount = db.Column(db.Numeric(15, 2))
```

### Comments System Schema

**PublicationComments Model**
```python
class PublicationComments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    publication_id = db.Column(db.Integer, db.ForeignKey('publications.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user_accounts.user_id'))
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('publication_comments.id'))
    comment_text = db.Column(db.Text, nullable=False)
    comment_type = db.Column(db.String(50), default='general')
    status = db.Column(db.String(20), default='active')
    likes_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
```

**Key Features**:
- Hierarchical comment structure with parent-child relationships
- Comment type classification (general, review, question, suggestion)
- Status management (active, edited, deleted, flagged)
- Like/reaction system with count tracking
- Edit tracking and versioning

### Reference Data Models

**Controlled Vocabularies**:
- `ResourceTypes` - Publication resource classifications
- `CreatorsRoles` - Creator role taxonomies (author, editor, contributor, etc.)
- `FunderTypes` - Funding organization categories
- `PublicationTypes` - Document type classifications
- `PublicationIdentifierTypes` - Identifier scheme registry

### Database Relationships

**Key Relationship Patterns**:

1. **One-to-Many Relationships**:
   - UserAccount → Publications (user ownership)
   - Publications → PublicationComments (publication discussions)
   - PublicationComments → PublicationComments (comment replies)

2. **Many-to-Many Relationships**:
   - Publications ↔ PublicationCreators (multiple authors per publication)
   - Publications ↔ PublicationOrganization (multiple affiliations)
   - Publications ↔ PublicationFunders (multiple funding sources)

3. **Self-Referential Relationships**:
   - PublicationComments → PublicationComments (parent-child hierarchy)

### Data Integrity & Constraints

**Foreign Key Constraints**:
- Cascading deletes for dependent records
- Referential integrity across all relationships
- Proper indexing on foreign key columns

**Data Validation**:
- Email format validation
- ORCID ID format validation (xxxx-xxxx-xxxx-xxxx)
- DOI format validation
- URL validation for external links

## Installation & Setup

### System Requirements

**Server Environment**:
- Ubuntu 20.04 LTS or later
- Python 3.9 or later
- PostgreSQL 12 or later
- Redis (optional, for caching and rate limiting)
- Nginx (for production deployment)

**Development Environment**:
- Python 3.9+
- PostgreSQL 12+
- Git
- Node.js (for frontend development)

### Installation Process

#### 1. Environment Setup

**Clone Repository**:
```bash
git clone <repository-url>
cd DOCiD/backend
```

**Python Virtual Environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**Install Dependencies**:
```bash
pip install -r requirements.txt
```

#### 2. Database Configuration

**PostgreSQL Setup**:
```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE docid_db;
CREATE USER docid_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE docid_db TO docid_user;
```

**Environment Variables**:
Create `.env` file in the project root:
```bash
# Database Configuration
SQLALCHEMY_DATABASE_URI=postgresql://docid_user:your_password@localhost/docid_db

# Application Security
SECRET_KEY=your_very_secure_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here

# External Service API Keys
CSTR_CLIENT_ID=your_cstr_client_id
CSTR_SECRET=your_cstr_secret
CROSSREF_API_URL=https://api.crossref.org
CROSSREF_API_KEY=your_crossref_api_key
LC_API_KEY=your_local_contexts_api_key

# CORDRA Configuration
CORDRA_BASE_URL=https://your-cordra-instance.com
CORDRA_USERNAME=cordra_username
CORDRA_PASSWORD=cordra_password

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_email_password

# Social Authentication
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
ORCID_CLIENT_ID=your_orcid_client_id
ORCID_CLIENT_SECRET=your_orcid_client_secret
```

#### 3. Database Initialization

**Initialize Database**:
```bash
# Initialize migration repository
python run.py db init

# Create initial migration
python run.py db migrate -m "Initial migration"

# Apply migrations
python run.py db upgrade

# Seed reference data
python scripts/seed_db.py
```

#### 4. Development Server

**Start Development Server**:
```bash
python run.py
```

The server will start on `http://localhost:5001` (note: port 5001 to avoid conflicts with macOS AirPlay on port 5000).

### Production Deployment

## Detailed Production Setup Guide

### 1. Server Provisioning and OS Configuration

#### Initial Server Setup
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y python3 python3-pip python3-venv python-is-python3
sudo apt install -y git curl wget nginx supervisor
sudo apt install -y build-essential libssl-dev libffi-dev

# Check Python version (ensure 3.9+)
python3 --version

# Create application user
sudo useradd -m -s /bin/bash tcc-africa
sudo usermod -aG sudo tcc-africa

# Set up project directory
sudo mkdir -p /home/tcc-africa/docid_project
sudo chown -R tcc-africa:tcc-africa /home/tcc-africa/docid_project
```

#### System Security Configuration
```bash
# Configure firewall
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Update SSH configuration for security
sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh
```

### 2. PostgreSQL Database Installation and Configuration

#### PostgreSQL Installation
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Start and enable PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo systemctl status postgresql
```

#### Database Setup and User Configuration
```bash
# Switch to postgres user
sudo -i -u postgres

# Create database and user
psql << EOF
CREATE DATABASE docid;
CREATE USER usr_docid WITH PASSWORD '[SECURE_PASSWORD]';
GRANT ALL PRIVILEGES ON DATABASE docid TO usr_docid;
GRANT USAGE ON SCHEMA public TO usr_docid;
GRANT CREATE ON SCHEMA public TO usr_docid;
ALTER SCHEMA public OWNER TO usr_docid;
\q
EOF

# Exit postgres user
exit
```

#### Configure PostgreSQL Authentication
```bash
# Find PostgreSQL version and edit configuration
PG_VERSION=$(sudo -u postgres psql -c "SHOW server_version;" | grep PostgreSQL | sed 's/.*PostgreSQL \([0-9]*\).*/\1/')

# Update pg_hba.conf for password authentication
sudo sed -i "s/local   all             all                                     peer/local   all             all                                     md5/" /etc/postgresql/$PG_VERSION/main/pg_hba.conf

# Restart PostgreSQL
sudo systemctl restart postgresql

# Test database connection
psql -U usr_docid -d docid -h localhost -W
```

#### Create Development Database (Optional)
```bash
# Connect as database user and create dev database
psql -U usr_docid -d docid -h localhost << EOF
CREATE DATABASE docid_dev;
GRANT ALL PRIVILEGES ON DATABASE docid_dev TO usr_docid;
\q
EOF
```

### 3. Application Deployment with Gunicorn

#### Clone and Setup Application
```bash
# Switch to application user
sudo su - tcc-africa

# Clone repository (replace with your repository URL)
cd /home/tcc-africa/docid_project
git clone [REPOSITORY_URL] backend-v2
cd backend-v2

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

#### Environment Configuration
```bash
# Create environment file
cat > .env << EOF
# Database Configuration
SQLALCHEMY_DATABASE_URI=postgresql://usr_docid:[SECURE_PASSWORD]@localhost/docid

# Application Security
SECRET_KEY=[GENERATED_SECRET_KEY]
JWT_SECRET_KEY=[GENERATED_JWT_SECRET]

# External Service API Keys
CSTR_CLIENT_ID=[YOUR_CSTR_CLIENT_ID]
CSTR_SECRET=[YOUR_CSTR_SECRET]
CROSSREF_API_KEY=[YOUR_CROSSREF_KEY]

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=[YOUR_EMAIL]
MAIL_PASSWORD=[YOUR_EMAIL_PASSWORD]

# CORDRA Configuration
CORDRA_BASE_URL=https://cordra.kenet.or.ke
CORDRA_USERNAME=[CORDRA_USERNAME]
CORDRA_PASSWORD=[CORDRA_PASSWORD]
EOF

# Set appropriate permissions
chmod 600 .env
```

#### Database Initialization
```bash
# Initialize database
export FLASK_APP=app.py
source venv/bin/activate

# Run database migrations
python3 manage.py create-db
python3 manage.py seed-db
python3 manage.py generate-pids

# Test application startup
flask run --port=5001 --debug
```

#### Gunicorn Configuration
```bash
# Create Gunicorn configuration file
cat > gunicorn.conf.py << EOF
bind = "127.0.0.1:6000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
user = "tcc-africa"
group = "tcc-africa"
tmp_upload_dir = None
errorlog = "/home/tcc-africa/docid_project/backend-v2/logs/gunicorn.err.log"
accesslog = "/home/tcc-africa/docid_project/backend-v2/logs/gunicorn.out.log"
access_log_format = '%h %l %u %t "%r" %s %b "%{Referer}i" "%{User-Agent}i"'
EOF

# Create logs directory
mkdir -p logs

# Test Gunicorn
gunicorn --config gunicorn.conf.py wsgi:app
```

### 4. Nginx Reverse Proxy Configuration

#### Nginx Configuration for DOCiD
```bash
# Create Nginx site configuration
sudo tee /etc/nginx/sites-available/docid << EOF
server {
    listen 80;
    server_name docid.africapidalliance.org www.docid.africapidalliance.org;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Main application proxy
    location / {
        proxy_pass http://127.0.0.1:6000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files
    location /static/ {
        alias /home/tcc-africa/docid_project/backend-v2/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Uploads
    location /uploads/ {
        alias /home/tcc-africa/docid_project/backend-v2/uploads/;
        expires 1M;
        add_header Cache-Control "public";
    }

    # API documentation
    location /apidocs/ {
        proxy_pass http://127.0.0.1:6000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:6000;
        proxy_set_header Host \$host;
    }

    # Rate limiting for API endpoints
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:6000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

# Rate limiting configuration
http {
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
}
EOF

# Enable the site
sudo ln -s /etc/nginx/sites-available/docid /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 5. SSL Certificate Installation

#### Using Certbot for Let's Encrypt SSL
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain SSL certificate
sudo certbot --nginx -d docid.africapidalliance.org -d www.docid.africapidalliance.org

# Test certificate renewal
sudo certbot renew --dry-run

# Set up automatic renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

#### Manual SSL Certificate Configuration (Alternative)
```bash
# If using custom SSL certificates
sudo mkdir -p /etc/nginx/ssl

# Copy your SSL files (replace with actual file paths)
sudo cp /path/to/your/certificate.crt /etc/nginx/ssl/
sudo cp /path/to/your/private.key /etc/nginx/ssl/
sudo cp /path/to/your/ca-bundle.crt /etc/nginx/ssl/

# Set appropriate permissions
sudo chmod 600 /etc/nginx/ssl/private.key
sudo chmod 644 /etc/nginx/ssl/certificate.crt

# Update Nginx configuration for SSL
sudo tee -a /etc/nginx/sites-available/docid << EOF

server {
    listen 443 ssl http2;
    server_name docid.africapidalliance.org www.docid.africapidalliance.org;

    ssl_certificate /etc/nginx/ssl/certificate.crt;
    ssl_certificate_key /etc/nginx/ssl/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    # [Rest of server configuration same as HTTP version]
}
EOF
```

### 6. Supervisor Process Management Setup

#### Supervisor Configuration for DOCiD
```bash
# Create Supervisor configuration
sudo tee /etc/supervisor/conf.d/docid.conf << EOF
[program:docid]
command=/home/tcc-africa/docid_project/backend-v2/venv/bin/gunicorn --config /home/tcc-africa/docid_project/backend-v2/gunicorn.conf.py wsgi:app
directory=/home/tcc-africa/docid_project/backend-v2
user=tcc-africa
environment=PATH="/home/tcc-africa/docid_project/backend-v2/venv/bin"
autostart=true
autorestart=true
stderr_logfile=/home/tcc-africa/docid_project/backend-v2/logs/gunicorn.err.log
stdout_logfile=/home/tcc-africa/docid_project/backend-v2/logs/gunicorn.out.log
redirect_stderr=true
stopasgroup=true
killasgroup=true
EOF

# Update Supervisor configuration
sudo supervisorctl reread
sudo supervisorctl update

# Start the application
sudo supervisorctl start docid

# Check status
sudo supervisorctl status docid
```

#### Supervisor Management Commands
```bash
# Common Supervisor commands
sudo supervisorctl status                # Check all services
sudo supervisorctl start docid          # Start DOCiD service
sudo supervisorctl stop docid           # Stop DOCiD service
sudo supervisorctl restart docid        # Restart DOCiD service
sudo supervisorctl reload               # Reload configuration
sudo supervisorctl tail docid stderr    # View error logs
sudo supervisorctl tail docid stdout    # View access logs
```

### 7. Background Service Configuration

#### CORDRA Synchronization Service
```bash
# Create CORDRA push script
cat > /home/tcc-africa/docid_project/backend-v2/cordra_push.sh << EOF
#!/bin/bash
cd /home/tcc-africa/docid_project/backend-v2
source venv/bin/activate
export FLASK_APP=app.py

# Push recent publications to CORDRA
python push_recent_to_cordra.py >> logs/cordra_push.log 2>&1
EOF

chmod +x /home/tcc-africa/docid_project/backend-v2/cordra_push.sh
```

#### CSTR Update Service
```bash
# Create systemd service for CSTR updates
sudo tee /etc/systemd/system/docid-cstr.service << EOF
[Unit]
Description=DOCiD CSTR Update Service
After=network.target postgresql.service

[Service]
Type=simple
User=tcc-africa
WorkingDirectory=/home/tcc-africa/docid_project/backend-v2
Environment=PATH=/home/tcc-africa/docid_project/backend-v2/venv/bin
ExecStart=/home/tcc-africa/docid_project/backend-v2/venv/bin/python update_all_cstr_identifiers.py
Restart=always
RestartSec=3600

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable docid-cstr.service
sudo systemctl start docid-cstr.service
```

#### Cron Jobs for Scheduled Tasks
```bash
# Set up cron jobs
sudo su - tcc-africa
crontab -e

# Add the following lines:
# Push to CORDRA every minute
* * * * * /home/tcc-africa/docid_project/backend-v2/cordra_push.sh

# Update CSTR identifiers daily at 2 AM
0 2 * * * /home/tcc-africa/docid_project/backend-v2/run_check_null_identifiers.sh >> /home/tcc-africa/docid_project/backend-v2/logs/check_null_cron.log 2>&1

# Database backup daily at 3 AM
0 3 * * * pg_dump -U usr_docid -h localhost docid | gzip > /home/tcc-africa/backups/docid_$(date +\%Y\%m\%d).sql.gz

# Log rotation weekly
0 0 * * 0 find /home/tcc-africa/docid_project/backend-v2/logs -name "*.log" -mtime +7 -exec rm {} \;
```

### 8. Monitoring and Logging Setup

#### Log Directory Structure
```bash
# Create comprehensive logging structure
mkdir -p /home/tcc-africa/docid_project/backend-v2/logs/{app,nginx,supervisor,cordra,cstr}

# Set up log rotation
sudo tee /etc/logrotate.d/docid << EOF
/home/tcc-africa/docid_project/backend-v2/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 tcc-africa tcc-africa
    postrotate
        sudo supervisorctl signal HUP docid
    endscript
}
EOF
```

#### Application Monitoring Script
```bash
# Create monitoring script
cat > /home/tcc-africa/docid_project/backend-v2/monitor.sh << EOF
#!/bin/bash

# Check if application is responding
if ! curl -f http://localhost:6000/health > /dev/null 2>&1; then
    echo "$(date): Application not responding, restarting..." >> logs/monitor.log
    sudo supervisorctl restart docid
fi

# Check database connectivity
if ! psql -U usr_docid -d docid -h localhost -c "SELECT 1;" > /dev/null 2>&1; then
    echo "$(date): Database connection failed" >> logs/monitor.log
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 85 ]; then
    echo "$(date): Disk usage is $DISK_USAGE%" >> logs/monitor.log
fi
EOF

chmod +x /home/tcc-africa/docid_project/backend-v2/monitor.sh

# Add monitoring to cron
echo "*/5 * * * * /home/tcc-africa/docid_project/backend-v2/monitor.sh" | crontab -
```

#### System Resource Monitoring
```bash
# Install monitoring tools
sudo apt install htop iotop nethogs -y

# Create system status script
cat > /home/tcc-africa/docid_project/backend-v2/system_status.sh << EOF
#!/bin/bash
echo "=== System Status $(date) ==="
echo "CPU Usage:"
top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}'

echo "Memory Usage:"
free -h

echo "Disk Usage:"
df -h /

echo "Active Connections:"
netstat -an | grep :6000 | wc -l

echo "Application Status:"
sudo supervisorctl status docid
EOF

chmod +x /home/tcc-africa/docid_project/backend-v2/system_status.sh
```

### 9. Backup and Disaster Recovery Configuration

#### Database Backup Strategy
```bash
# Create backup directory
sudo mkdir -p /home/tcc-africa/backups/database
sudo chown tcc-africa:tcc-africa /home/tcc-africa/backups/database

# Create database backup script
cat > /home/tcc-africa/docid_project/backend-v2/backup_database.sh << EOF
#!/bin/bash

BACKUP_DIR="/home/tcc-africa/backups/database"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="docid"
DB_USER="usr_docid"

# Create backup
pg_dump -U $DB_USER -h localhost $DB_NAME | gzip > $BACKUP_DIR/docid_$DATE.sql.gz

# Keep only last 30 days of backups
find $BACKUP_DIR -name "docid_*.sql.gz" -mtime +30 -delete

# Log backup completion
echo "$(date): Database backup completed - docid_$DATE.sql.gz" >> /home/tcc-africa/docid_project/backend-v2/logs/backup.log
EOF

chmod +x /home/tcc-africa/docid_project/backend-v2/backup_database.sh
```

#### Application Backup Script
```bash
# Create full application backup script
cat > /home/tcc-africa/docid_project/backend-v2/backup_application.sh << EOF
#!/bin/bash

BACKUP_DIR="/home/tcc-africa/backups/application"
DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/home/tcc-africa/docid_project/backend-v2"

mkdir -p $BACKUP_DIR

# Backup application files (excluding venv and logs)
tar -czf $BACKUP_DIR/docid_app_$DATE.tar.gz \
    --exclude='venv' \
    --exclude='logs' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    -C $(dirname $APP_DIR) $(basename $APP_DIR)

# Backup uploads and static files
tar -czf $BACKUP_DIR/docid_files_$DATE.tar.gz \
    $APP_DIR/uploads \
    $APP_DIR/static

# Keep only last 7 days of application backups
find $BACKUP_DIR -name "docid_*.tar.gz" -mtime +7 -delete

echo "$(date): Application backup completed" >> $APP_DIR/logs/backup.log
EOF

chmod +x /home/tcc-africa/docid_project/backend-v2/backup_application.sh
```

#### Disaster Recovery Plan
```bash
# Create disaster recovery documentation
cat > /home/tcc-africa/docid_project/backend-v2/DISASTER_RECOVERY.md << EOF
# DOCiD Disaster Recovery Plan

## Quick Recovery Steps

### 1. Database Recovery
\`\`\`bash
# Restore from backup
gunzip < /home/tcc-africa/backups/database/docid_YYYYMMDD_HHMMSS.sql.gz | psql -U usr_docid -d docid
\`\`\`

### 2. Application Recovery
\`\`\`bash
# Stop services
sudo supervisorctl stop docid

# Restore application
cd /home/tcc-africa/docid_project
tar -xzf /home/tcc-africa/backups/application/docid_app_YYYYMMDD_HHMMSS.tar.gz

# Restore virtual environment
cd backend-v2
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Restart services
sudo supervisorctl start docid
\`\`\`

### 3. Configuration Files
- Database: /etc/postgresql/*/main/postgresql.conf
- Nginx: /etc/nginx/sites-available/docid
- Supervisor: /etc/supervisor/conf.d/docid.conf
- Environment: /home/tcc-africa/docid_project/backend-v2/.env
EOF
```

### 10. Performance Optimization and Tuning

#### Database Performance Tuning
```bash
# PostgreSQL optimization
sudo tee -a /etc/postgresql/*/main/postgresql.conf << EOF

# Performance tuning for DOCiD
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
EOF

# Restart PostgreSQL
sudo systemctl restart postgresql
```

#### Application Performance Optimization
```bash
# Create performance monitoring script
cat > /home/tcc-africa/docid_project/backend-v2/performance_check.sh << EOF
#!/bin/bash

echo "=== Performance Metrics $(date) ==="

# Application response time
curl -o /dev/null -s -w "Response time: %{time_total}s\n" http://localhost:6000/health

# Database query performance
psql -U usr_docid -d docid -c "
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;" 2>/dev/null || echo "pg_stat_statements not available"

# Memory usage
ps aux | grep gunicorn | awk '{sum+=$6} END {print "Total memory: " sum/1024 "MB"}'

# Active connections
netstat -an | grep :6000 | grep ESTABLISHED | wc -l | awk '{print "Active connections: " $1}'
EOF

chmod +x /home/tcc-africa/docid_project/backend-v2/performance_check.sh
```

#### Nginx Performance Optimization
```bash
# Update Nginx configuration for performance
sudo tee /etc/nginx/nginx.conf << EOF
user www-data;
worker_processes auto;
pid /run/nginx.pid;

events {
    worker_connections 2048;
    use epoll;
    multi_accept on;
}

http {
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    # Include sites
    include /etc/nginx/sites-enabled/*;
}
EOF

# Test and reload Nginx
sudo nginx -t && sudo systemctl reload nginx
```

#### System Performance Monitoring
```bash
# Set up performance alerts
cat > /home/tcc-africa/docid_project/backend-v2/performance_alerts.sh << EOF
#!/bin/bash

# CPU usage alert
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
    echo "$(date): High CPU usage: $CPU_USAGE%" >> logs/performance.log
fi

# Memory usage alert
MEM_USAGE=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100.0)}')
if (( $(echo "$MEM_USAGE > 85" | bc -l) )); then
    echo "$(date): High memory usage: $MEM_USAGE%" >> logs/performance.log
fi

# Response time check
RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:6000/health)
if (( $(echo "$RESPONSE_TIME > 2.0" | bc -l) )); then
    echo "$(date): Slow response time: ${RESPONSE_TIME}s" >> logs/performance.log
fi
EOF

chmod +x /home/tcc-africa/docid_project/backend-v2/performance_alerts.sh

# Add to cron for regular monitoring
echo "*/10 * * * * /home/tcc-africa/docid_project/backend-v2/performance_alerts.sh" | crontab -
```

## Production Deployment Verification

After completing all setup steps, verify the deployment:

```bash
# 1. Check all services are running
sudo systemctl status nginx
sudo systemctl status postgresql
sudo supervisorctl status docid

# 2. Test application endpoints
curl -I https://docid.africapidalliance.org/health
curl -I https://docid.africapidalliance.org/api/v1/publications/get-publications

# 3. Check SSL certificate
openssl s_client -connect docid.africapidalliance.org:443 -servername docid.africapidalliance.org

# 4. Monitor logs
tail -f /home/tcc-africa/docid_project/backend-v2/logs/gunicorn.out.log

# 5. Performance test
curl -o /dev/null -s -w "Total time: %{time_total}s\n" https://docid.africapidalliance.org/
```

This comprehensive deployment guide provides production-ready setup with monitoring, logging, backup, and performance optimization for the DOCiD Flask API system.

## API Documentation Access and Testing

### Accessing Swagger API Documentation

#### Local Development Environment
```bash
# Start the development server
cd /Users/ekariz/Projects/AMBAND/DOCiD/backend
source venv/bin/activate
export FLASK_APP=app.py
flask run --port=5001 --debug

# Access Swagger UI in browser
http://localhost:5001/apidocs/
```

#### Production Environment
```bash
# Access via domain
https://docid.africapidalliance.org/apidocs/

# Alternative port access (if needed)
https://docid.africapidalliance.org:6000/apidocs/
```

#### Swagger UI Features
The Swagger interface provides:
- **Interactive API testing** - Test endpoints directly from the browser
- **Request/response examples** - See sample data formats
- **Authentication testing** - Test JWT token authentication
- **Schema validation** - View data model requirements
- **Error response examples** - Understand error formats

### API Testing with Postman

#### Setting Up Postman Environment

**1. Create New Environment in Postman:**
```json
{
    "environment_name": "DOCiD API",
    "variables": [
        {
            "key": "base_url_dev",
            "value": "http://localhost:5001",
            "enabled": true
        },
        {
            "key": "base_url_prod",
            "value": "https://docid.africapidalliance.org",
            "enabled": true
        },
        {
            "key": "jwt_token",
            "value": "",
            "enabled": true
        }
    ]
}
```

**2. Import DOCiD API Collection:**
Create a new collection with the following structure:

#### Authentication Endpoints

**User Registration:**
```http
POST {{base_url_dev}}/api/v1/auth/register
Content-Type: application/json

{
    "user_name": "testuser",
    "full_name": "Test User",
    "email": "test@example.com",
    "password": "secure_password",
    "affiliation": "Test Organization",
    "orcid_id": "0000-0000-0000-0000"
}
```

**User Login:**
```http
POST {{base_url_dev}}/api/v1/auth/login
Content-Type: application/json

{
    "email": "test@example.com",
    "password": "secure_password"
}
```

**Test Script for Login (Postman Tests tab):**
```javascript
// Extract JWT token from response
if (pm.response.code === 200) {
    const responseJson = pm.response.json();
    if (responseJson.token) {
        pm.environment.set("jwt_token", responseJson.token);
        console.log("JWT token saved:", responseJson.token);
    }
}

// Test response structure
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has token", function () {
    const responseJson = pm.response.json();
    pm.expect(responseJson).to.have.property('token');
});
```

#### Publication Management Endpoints

**Create Publication:**
```http
POST {{base_url_dev}}/api/v1/publications/publish
Authorization: Bearer {{jwt_token}}
Content-Type: application/json

{
    "title": "Research Paper on AI",
    "description": "Comprehensive study on artificial intelligence applications",
    "resource_type_id": 1,
    "user_id": 1
}
```

**Get Publications:**
```http
GET {{base_url_dev}}/api/v1/publications/get-publications
Authorization: Bearer {{jwt_token}}
```

**Get Single Publication:**
```http
GET {{base_url_dev}}/api/v1/publications/get-publication/1
Authorization: Bearer {{jwt_token}}
```

#### Comments System Endpoints

**Get Comments for Publication:**
```http
GET {{base_url_dev}}/api/publications/1/comments?include_replies=true
```

**Add Comment:**
```http
POST {{base_url_dev}}/api/publications/1/comments
Authorization: Bearer {{jwt_token}}
Content-Type: application/json

{
    "user_id": 1,
    "comment_text": "This is an excellent research paper!",
    "comment_type": "review"
}
```

**Edit Comment:**
```http
PUT {{base_url_dev}}/api/comments/1
Authorization: Bearer {{jwt_token}}
Content-Type: application/json

{
    "user_id": 1,
    "comment_text": "Updated comment text"
}
```

**Delete Comment:**
```http
DELETE {{base_url_dev}}/api/comments/1
Authorization: Bearer {{jwt_token}}
Content-Type: application/json

{
    "user_id": 1
}
```

**Like Comment:**
```http
POST {{base_url_dev}}/api/comments/1/like
Authorization: Bearer {{jwt_token}}
```

**Get Comment Statistics:**
```http
GET {{base_url_dev}}/api/comments/stats/1
```

#### External Service Integration Endpoints

**Search ROR Organizations:**
```http
GET {{base_url_dev}}/api/v1/ror/search?query=university
Authorization: Bearer {{jwt_token}}
```

**Get DOI Metadata from Crossref:**
```http
GET {{base_url_dev}}/api/v1/crossref/doi/10.1000/182
Authorization: Bearer {{jwt_token}}
```

**Get ORCID Information:**
```http
GET {{base_url_dev}}/api/v1/orcid/0000-0002-1825-0097
Authorization: Bearer {{jwt_token}}
```

#### CORDRA Integration Endpoints

**Assign Handle Identifier:**
```http
POST {{base_url_dev}}/api/v1/cordoi/assign-identifier/apa-handle
Authorization: Bearer {{jwt_token}}
Content-Type: application/json

{}
```

### Postman Pre-request Scripts

**Global Authentication Setup:**
```javascript
// Add to Collection Pre-request Script
if (!pm.environment.get("jwt_token")) {
    console.log("No JWT token found, authentication required");
}
```

**Token Refresh Script:**
```javascript
// Check if token is expired and refresh if needed
const token = pm.environment.get("jwt_token");
if (token) {
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const currentTime = Math.floor(Date.now() / 1000);
        
        if (payload.exp < currentTime) {
            console.log("Token expired, please re-authenticate");
            pm.environment.unset("jwt_token");
        }
    } catch (e) {
        console.log("Invalid token format");
    }
}
```

### Postman Test Scripts

**Generic Response Validation:**
```javascript
// Add to Collection Tests tab
pm.test("Response time is less than 2000ms", function () {
    pm.expect(pm.response.responseTime).to.be.below(2000);
});

pm.test("Content-Type is application/json", function () {
    pm.expect(pm.response.headers.get("Content-Type")).to.include("application/json");
});

pm.test("Response should not have errors", function () {
    const responseJson = pm.response.json();
    pm.expect(responseJson).to.not.have.property('error');
});
```

**Publication Creation Validation:**
```javascript
pm.test("Publication created successfully", function () {
    pm.response.to.have.status(201);
    const responseJson = pm.response.json();
    pm.expect(responseJson).to.have.property('id');
    pm.expect(responseJson).to.have.property('title');
    pm.expect(responseJson).to.have.property('docid');
});
```

**Comments Validation:**
```javascript
pm.test("Comments retrieved successfully", function () {
    pm.response.to.have.status(200);
    const responseJson = pm.response.json();
    pm.expect(responseJson).to.have.property('publication_id');
    pm.expect(responseJson).to.have.property('total_comments');
    pm.expect(responseJson.comments).to.be.an('array');
});
```

### API Testing Scenarios

#### Complete User Registration and Publication Flow
```bash
# 1. Register new user
POST /api/v1/auth/register

# 2. Login to get JWT token  
POST /api/v1/auth/login

# 3. Create publication
POST /api/v1/publications/publish

# 4. Add creators to publication
POST /api/v1/publications/publication/{id}/creators

# 5. Add organizations
POST /api/v1/publications/publication/{id}/organizations

# 6. Add funders
POST /api/v1/publications/publication/{id}/funders

# 7. Add comment to publication
POST /api/publications/{id}/comments

# 8. Like the comment
POST /api/comments/{comment_id}/like

# 9. Get final publication with all data
GET /api/v1/publications/get-publication/{id}
```

#### Error Testing Scenarios
```bash
# Test invalid authentication
GET /api/v1/publications/get-publications
# (without Authorization header)

# Test invalid data
POST /api/v1/publications/publish
# (with missing required fields)

# Test non-existent resources
GET /api/v1/publications/get-publication/99999

# Test unauthorized operations
DELETE /api/comments/1
# (with different user's JWT token)
```

### Production API Testing

#### Health Check Endpoints
```bash
# Application health
curl -I https://docid.africapidalliance.org/health

# Database connectivity
curl -I https://docid.africapidalliance.org/api/v1/publications/get-resource-types

# External service integration
curl -I https://docid.africapidalliance.org/api/v1/ror/search?query=test
```

#### Load Testing with curl
```bash
# Test concurrent requests
for i in {1..10}; do
    curl -X GET "https://docid.africapidalliance.org/api/v1/publications/get-publications" \
         -H "Authorization: Bearer YOUR_JWT_TOKEN" &
done
wait

# Test publication creation load
for i in {1..5}; do
    curl -X POST "https://docid.africapidalliance.org/api/v1/publications/publish" \
         -H "Authorization: Bearer YOUR_JWT_TOKEN" \
         -H "Content-Type: application/json" \
         -d "{\"title\":\"Load Test $i\",\"description\":\"Test publication\",\"resource_type_id\":1,\"user_id\":1}" &
done
wait
```

### API Documentation Best Practices

1. **Always use HTTPS in production**
2. **Include proper Authorization headers**
3. **Validate response formats**
4. **Test error scenarios**
5. **Monitor response times**
6. **Use environment variables for different stages**
7. **Document all test cases**
8. **Implement automated testing pipelines**

### Troubleshooting API Issues

#### Common Issues and Solutions

**401 Unauthorized:**
```bash
# Check token validity
echo "YOUR_JWT_TOKEN" | cut -d'.' -f2 | base64 --decode

# Re-authenticate
curl -X POST "https://docid.africapidalliance.org/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"email":"your_email","password":"your_password"}'
```

**500 Internal Server Error:**
```bash
# Check server logs
sudo tail -f /home/tcc-africa/docid_project/backend-v2/logs/gunicorn.err.log

# Check application status
sudo supervisorctl status docid
```

**Connection Timeout:**
```bash
# Check if service is running
curl -I http://localhost:6000/health

# Check network connectivity
ping docid.africapidalliance.org
```

This comprehensive testing guide provides complete coverage for accessing and testing the DOCiD API through both Swagger UI and Postman, ensuring thorough validation of all system functionality.

#### 2. Process Management

**Supervisor Configuration** (`/etc/supervisor/conf.d/docid.conf`):
```ini
[program:docid]
command=/path/to/venv/bin/gunicorn -c gunicorn.conf.py wsgi:app
directory=/path/to/your/app
user=www-data
autostart=true
autorestart=true
stdout_logfile=/var/log/supervisor/docid.log
stderr_logfile=/var/log/supervisor/docid_error.log
```

**Gunicorn Configuration** (`gunicorn.conf.py`):
```python
bind = "127.0.0.1:5001"
workers = 4
worker_class = "sync"
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
```

#### 3. SSL Configuration

**Certbot SSL Setup**:
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

#### 4. Background Services

**CSTR Service** (`/etc/systemd/system/docid-cstr.service`):
```ini
[Unit]
Description=DOCiD CSTR Update Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/your/app
ExecStart=/path/to/venv/bin/python update_all_cstr_identifiers.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**Cron Jobs** for scheduled tasks:
```bash
# Update CSTR identifiers daily at 2 AM
0 2 * * * /path/to/venv/bin/python /path/to/app/update_all_cstr_identifiers.py

# Sync to CORDRA every 6 hours
0 */6 * * * /path/to/venv/bin/python /path/to/app/push_recent_to_cordra.py
```

### Monitoring & Logging

**Log Configuration**:
- Application logs: `/var/log/docid/app.log`
- Error logs: `/var/log/docid/error.log`
- Service-specific logs: `/var/log/docid/{service}.log`

**Log Rotation** (`/etc/logrotate.d/docid`):
```
/var/log/docid/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
}
```

## API Documentation

### API Design Principles

**RESTful Architecture**:
- Resource-oriented URLs
- HTTP verb semantics (GET, POST, PUT, DELETE)
- Status code conventions
- JSON payload communication

**Authentication**:
- JWT-based authentication
- Bearer token authorization
- Social OAuth integration
- Role-based access control

**Error Handling**:
- Consistent error response format
- HTTP status code compliance
- Detailed error messages
- Request validation

### API Response Format

**Success Response Structure**:
```json
{
    "status": "success",
    "data": {
        // Response data
    },
    "message": "Operation completed successfully"
}
```

**Error Response Structure**:
```json
{
    "status": "error",
    "error": "Error description",
    "code": "ERROR_CODE",
    "details": {
        // Additional error details
    }
}
```

### Authentication Flow

**JWT Authentication**:
```http
POST /api/v1/auth/login
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "password"
}
```

**Response**:
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "user_id": 1,
        "full_name": "John Doe",
        "email": "user@example.com",
        "role": "user"
    }
}
```

**Using JWT Token**:
```http
GET /api/v1/publications/get-publications
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Swagger/OpenAPI Documentation

The API includes comprehensive Swagger documentation accessible at `/apidocs/` when the server is running. This provides:

- Interactive API testing interface
- Request/response schema validation
- Example payloads and responses
- Authentication flow testing
- Endpoint discovery and exploration

## Endpoints & Usage

### Authentication Endpoints

#### User Registration
```http
POST /api/v1/auth/store-registration-token
Content-Type: application/json

{
    "email": "user@example.com",
    "full_name": "John Doe",
    "password": "secure_password",
    "orcid_id": "0000-0000-0000-0000",
    "affiliation": "University Name"
}
```

#### Complete Registration
```http
POST /api/v1/auth/complete-registration/{token}
Content-Type: application/json

{
    "token": "registration_token_from_email"
}
```

#### User Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "password"
}
```

#### Password Reset
```http
POST /api/v1/auth/request-password-reset
Content-Type: application/json

{
    "email": "user@example.com"
}
```

### Publication Management Endpoints

#### Create Publication
```http
POST /api/v1/publications/publish
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
    "title": "Research Paper Title",
    "abstract": "Paper abstract...",
    "resource_type_id": 1,
    "publication_type_id": 1,
    "creators": [
        {
            "creator_name": "John Doe",
            "orcid_id": "0000-0000-0000-0000",
            "role_id": 1,
            "affiliation": "University Name"
        }
    ],
    "organizations": [
        {
            "organization_name": "University Name",
            "ror_id": "ror_id_here",
            "country": "Country Name"
        }
    ],
    "funders": [
        {
            "funder_name": "Grant Agency",
            "grant_number": "GRANT-2023-001",
            "award_amount": 50000.00
        }
    ]
}
```

#### Get Publications List
```http
GET /api/v1/publications/get-publications?page=1&limit=10&resource_type=dataset
Authorization: Bearer {jwt_token}
```

**Response**:
```json
{
    "publications": [
        {
            "id": 1,
            "title": "Research Paper Title",
            "docid": "DOCID.001",
            "doi": "10.5555/example.doi",
            "resource_type": "dataset",
            "creators": [...],
            "organizations": [...],
            "created_at": "2023-01-01T00:00:00Z"
        }
    ],
    "pagination": {
        "page": 1,
        "pages": 5,
        "total": 50,
        "limit": 10
    }
}
```

#### Get Single Publication
```http
GET /api/v1/publications/get-publication/{id}
Authorization: Bearer {jwt_token}
```

#### Get Publication by DocID
```http
GET /api/v1/publications/docid/{docid}
```

### Comments System Endpoints

#### Get Publication Comments
```http
GET /api/publications/{publication_id}/comments?include_replies=true
```

**Response**:
```json
{
    "publication_id": 1,
    "total_comments": 5,
    "comments": [
        {
            "id": 1,
            "user_id": 1,
            "user_name": "John Doe",
            "comment_text": "Great research work!",
            "comment_type": "general",
            "status": "active",
            "likes_count": 3,
            "created_at": "2023-01-01T10:00:00Z",
            "replies": [
                {
                    "id": 2,
                    "user_id": 2,
                    "user_name": "Jane Smith",
                    "comment_text": "I agree, very insightful.",
                    "parent_comment_id": 1,
                    "created_at": "2023-01-01T11:00:00Z"
                }
            ]
        }
    ]
}
```

#### Add Comment
```http
POST /api/publications/{publication_id}/comments
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
    "user_id": 1,
    "comment_text": "This is a great contribution to the field.",
    "comment_type": "review"
}
```

#### Add Reply
```http
POST /api/publications/{publication_id}/comments
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
    "user_id": 1,
    "comment_text": "Thank you for the feedback!",
    "comment_type": "general",
    "parent_comment_id": 1
}
```

#### Edit Comment
```http
PUT /api/comments/{comment_id}
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
    "user_id": 1,
    "comment_text": "Updated comment text"
}
```

#### Delete Comment
```http
DELETE /api/comments/{comment_id}
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
    "user_id": 1
}
```

#### Like Comment
```http
POST /api/comments/{comment_id}/like
Authorization: Bearer {jwt_token}
```

#### Get Comment Statistics
```http
GET /api/comments/stats/{publication_id}
```

**Response**:
```json
{
    "publication_id": 1,
    "statistics": {
        "total_comments": 10,
        "top_level_comments": 7,
        "replies": 3,
        "unique_commenters": 5,
        "total_likes": 15,
        "comment_types": {
            "general": 6,
            "review": 3,
            "question": 1
        }
    }
}
```

### External Service Integration Endpoints

#### Crossref Integration
```http
GET /api/v1/crossref/doi/{doi}
Authorization: Bearer {jwt_token}
```

```http
POST /api/v1/crossref/search
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
    "query": "machine learning",
    "rows": 10,
    "sort": "relevance"
}
```

#### ROR Integration
```http
GET /api/v1/ror/search?query=university+name
Authorization: Bearer {jwt_token}
```

#### ORCID Integration
```http
GET /api/v1/orcid/{orcid_id}
Authorization: Bearer {jwt_token}
```

### File Upload Endpoints

#### Upload Publication Files
```http
POST /uploads
Authorization: Bearer {jwt_token}
Content-Type: multipart/form-data

file: [binary file data]
publication_id: 1
file_type: document
```

### Reference Data Endpoints

#### Get Resource Types
```http
GET /api/v1/publications/get-resource-types
```

#### Get Creator Roles
```http
GET /api/v1/publications/get-creators-roles
```

#### Get Publication Types
```http
GET /api/v1/publications/get-publication-types
```

### Rate Limiting

The API implements rate limiting on sensitive endpoints:

- Authentication endpoints: 5 requests per minute
- Publication creation: 10 requests per hour
- External service calls: 100 requests per hour
- Comment creation: 30 requests per hour

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

### Error Codes

**HTTP Status Codes**:
- `200 OK` - Successful request
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (e.g., duplicate email)
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

**Application Error Codes**:
- `INVALID_CREDENTIALS` - Login credentials incorrect
- `USER_NOT_FOUND` - User account does not exist
- `PUBLICATION_NOT_FOUND` - Publication does not exist
- `COMMENT_NOT_FOUND` - Comment does not exist
- `UNAUTHORIZED_ACCESS` - Insufficient permissions for operation
- `VALIDATION_ERROR` - Input validation failed
- `EXTERNAL_SERVICE_ERROR` - External API integration error
- `DATABASE_ERROR` - Database operation failed

This comprehensive documentation provides the foundation for developing, deploying, and maintaining the DOCiD Flask API system, with detailed coverage of all major components and integration patterns.