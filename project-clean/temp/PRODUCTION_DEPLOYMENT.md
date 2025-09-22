# DOCiD Production Deployment Guide

This guide provides instructions for deploying the DOCiD backend application to a production Ubuntu server environment.

## Server Requirements

- Ubuntu 20.04 LTS or newer
- Python 3.9+
- PostgreSQL 12+
- Nginx
- Supervisor
- SSL certificate (Let's Encrypt recommended)

## Step 1: Server Preparation

### Update system packages

```bash
sudo apt update
sudo apt upgrade -y
```

### Install required packages

```bash
sudo apt install -y python3-pip python3-venv postgresql nginx supervisor git certbot python3-certbot-nginx
```

## Step 2: Create Application User

```bash
# Create a user for the application
sudo useradd -m -s /bin/bash docid

# Add user to www-data group
sudo usermod -a -G www-data docid
```

## Step 3: Database Setup

### Configure PostgreSQL

```bash
# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Switch to postgres user
sudo -i -u postgres

# Create database and user
psql -c "CREATE DATABASE docid_db;"
psql -c "CREATE USER docid_user WITH PASSWORD 'secure_password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE docid_db TO docid_user;"

# Exit postgres user
exit
```

## Step 4: Application Setup

### Clone the repository

```bash
# Switch to application user
sudo -i -u docid

# Clone the repository
cd /home/docid
git clone <repository-url> DOCiD
cd DOCiD/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements_minimal.txt
pip install gunicorn
```

### Configure environment variables

```bash
# Create .env file
cat > .env << EOL
# Database configuration
SQLALCHEMY_DATABASE_URI=postgresql://docid_user:secure_password@localhost/docid_db

# Security configuration
SECRET_KEY=your_secure_secret_key
JWT_SECRET_KEY=your_secure_jwt_key

# API configuration
CSTR_CLIENT_ID=your_cstr_client_id
CSTR_SECRET=your_cstr_secret
CSTR_PREFIX=your_cstr_prefix

# Debug mode (disable for production)
DEBUG=False

# Set max file upload size (16MB)
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=/home/tcc-africa/docid_project/backend-v2/uploads

# Email configuration
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_email_password
MAIL_USE_TLS=True
EOL

# Create logs directory
mkdir -p logs
chmod 755 logs

# Set proper file permissions
./setup_permissions.sh

# Exit docid user
exit
```

## Step 5: Run Database Migrations

```bash
# Switch to docid user
sudo -i -u docid
cd /home/tcc-africa/docid_project/backend-v2
source venv/bin/activate

# Run migrations
./run_migrations.sh upgrade

# Exit docid user
exit
```

## Step 6: Configure Supervisor

### Create supervisor configuration

```bash
sudo nano /etc/supervisor/conf.d/docid.conf
```

Add the following content:

```ini
[program:docid]
directory=/home/tcc-africa/docid_project/backend-v2
command=/home/tcc-africa/docid_project/backend-v2/venv/bin/gunicorn --config gunicorn.conf.py wsgi:app
user=docid
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/home/tcc-africa/docid_project/backend-v2/logs/supervisor-err.log
stdout_logfile=/home/tcc-africa/docid_project/backend-v2/logs/supervisor-out.log
environment=PYTHONUNBUFFERED=1
```

### Update supervisor

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start docid
```

## Step 7: Configure Nginx

### Create Nginx server block

```bash
sudo nano /etc/nginx/sites-available/docid
```

Add the following content:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    access_log /var/log/nginx/docid.access.log;
    error_log /var/log/nginx/docid.error.log;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /home/tcc-africa/docid_project/backend-v2/app/static;
    }

    location /uploads {
        alias /home/tcc-africa/docid_project/backend-v2/uploads;
    }

    client_max_body_size 16M;
}
```

### Enable the site and restart Nginx

```bash
sudo ln -s /etc/nginx/sites-available/docid /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

## Step 8: SSL Configuration

### Obtain SSL certificate with Let's Encrypt

```bash
sudo certbot --nginx -d your-domain.com
```

Follow the prompts to complete the SSL configuration.

## Step 9: Set Up CSTR Identifier Update Service

### Create systemd service file

```bash
sudo nano /etc/systemd/system/update_cstr_identifiers.service
```

Add the following content:

```ini
[Unit]
Description=CSTR Identifier Update Service
After=network.target

[Service]
User=docid
Group=www-data
WorkingDirectory=/home/tcc-africa/docid_project/backend-v2
ExecStart=/home/tcc-africa/docid_project/backend-v2/update_all_cstr_identifiers.py
Restart=always
RestartSec=60
StandardOutput=append:/home/tcc-africa/docid_project/backend-v2/logs/cstr_update.log
StandardError=append:/home/tcc-africa/docid_project/backend-v2/logs/cstr_update.log

[Install]
WantedBy=multi-user.target
```

### Enable and start the service

```bash
# Make the script executable
sudo chmod +x /home/tcc-africa/docid_project/backend-v2/update_all_cstr_identifiers.py

# Reload systemd and enable the service
sudo systemctl daemon-reload
sudo systemctl enable update_cstr_identifiers.service
sudo systemctl start update_cstr_identifiers.service

# Check status
sudo systemctl status update_cstr_identifiers.service
```

## Step 10: Server Security

### Configure firewall

```bash
sudo apt install ufw
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

### Setup automatic updates

```bash
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
```

## Step 11: Monitoring and Maintenance

### Configure log rotation

```bash
sudo nano /etc/logrotate.d/docid
```

Add the following content:

```
/home/tcc-africa/docid_project/backend-v2/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 docid www-data
    sharedscripts
    postrotate
        supervisorctl restart docid >/dev/null 2>&1 || true
    endscript
}
```

### Restart application

```bash
# Use the provided restart script
sudo -i -u docid
cd /home/tcc-africa/docid_project/backend-v2
./restart.sh
exit

# Or use supervisor directly
sudo supervisorctl restart docid
```

## Troubleshooting

### Application not starting

Check supervisor logs:
```bash
sudo supervisorctl status docid
tail -f /home/tcc-africa/docid_project/backend-v2/logs/supervisor-*.log
```

### Database connection issues

Verify PostgreSQL is running:
```bash
sudo systemctl status postgresql
```

### Nginx configuration issues

Check Nginx error logs:
```bash
tail -f /var/log/nginx/error.log
```

### CSTR service issues

Check service status and logs:
```bash
sudo systemctl status update_cstr_identifiers.service
tail -f /home/tcc-africa/docid_project/backend-v2/logs/cstr_update.log
```
