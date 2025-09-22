# CSTR Update Service Deployment Guide

This document explains how to deploy the CSTR identifier update service on an Ubuntu server.

## Overview

The CSTR identifier update service processes all publication documents that have NULL/blank `identifier_cstr` values and registers them with the CSTR API using their existing `generated_identifier + CSTR_PREFIX`. The script runs at regular intervals to ensure all new documents are processed.

## Deployment Options

There are two ways to deploy the service:

1. **Systemd Service**: Runs continuously and processes records every minute
2. **Cron Job**: Executes the script every minute via cron scheduler

## Prerequisites

- Ubuntu server with the DOCiD application deployed
- Python environment with all requirements installed
- Proper permissions to create systemd services or cron jobs

## Option 1: Deploy as Systemd Service

Systemd is the recommended method as it provides better logging, automatic restarts, and proper dependency management.

1. SSH into your Ubuntu server

2. Copy the `setup_cstr_service.sh` script to your server

3. Edit the script to update the configuration variables:
   ```bash
   APP_DIR="/path/to/DOCiD/backend"  # Change to your actual path
   SERVICE_USER="www-data"           # Change to the appropriate user
   PYTHON_ENV="$APP_DIR/venv/bin/python"  # Path to your venv's Python
   ```

4. Run the setup script:
   ```bash
   sudo bash setup_cstr_service.sh
   ```

5. Verify the service is running:
   ```bash
   sudo systemctl status update_cstr_identifiers.service
   ```

## Option 2: Deploy as Cron Job

If systemd is not preferred, you can use the cron scheduler:

1. SSH into your Ubuntu server

2. Copy the `setup_cstr_cron.sh` script to your server

3. Edit the script to update the configuration variables:
   ```bash
   APP_DIR="/path/to/DOCiD/backend"  # Change to your actual path
   SERVICE_USER="www-data"           # Change to the appropriate user
   PYTHON_ENV="$APP_DIR/venv/bin/python"  # Path to your venv's Python
   FREQUENCY="* * * * *"            # Default: every minute
   ```

4. Run the setup script:
   ```bash
   sudo bash setup_cstr_cron.sh
   ```

5. Verify the cron job is installed:
   ```bash
   sudo -u www-data crontab -l
   ```

## Logging

Both methods will log output to `logs/cstr_update.log` in your application directory. You can monitor this file to ensure the service is functioning correctly:

```bash
tail -f /path/to/DOCiD/backend/logs/cstr_update.log
```

## Troubleshooting

### Service not starting

Check the service status:
```bash
sudo systemctl status update_cstr_identifiers.service
```

View the logs:
```bash
sudo journalctl -u update_cstr_identifiers.service
```

### Script not executing with cron

Check if cron is running:
```bash
systemctl status cron
```

Check cron logs:
```bash
grep CRON /var/log/syslog
```

### Permissions issues

Ensure the script is executable:
```bash
chmod +x /path/to/DOCiD/backend/update_all_cstr_identifiers.py
```

Ensure the service user has appropriate permissions:
```bash
chown -R www-data:www-data /path/to/DOCiD/backend/logs
```

## Manual Testing

To manually test the script:
```bash
cd /path/to/DOCiD/backend
./update_all_cstr_identifiers.py
```

This should process any publication documents with NULL CSTR identifiers and update the database.
