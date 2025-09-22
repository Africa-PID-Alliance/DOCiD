#!/bin/bash

# setup_cstr_service.sh
# Script to set up CSTR identifier update service on Ubuntu server
# This script should be run on the Ubuntu server, not on your local machine

# Exit on error
set -e

# Configuration variables - MODIFY THESE
APP_DIR="/path/to/DOCiD/backend"  # Change this to your actual app directory path
SERVICE_USER="www-data"           # Change to the user that should run the service
PYTHON_ENV="$APP_DIR/venv/bin/python"  # Path to your virtual environment's Python
LOG_DIR="$APP_DIR/logs"           # Path to your logs directory
LOG_FILE="$LOG_DIR/cstr_update.log"

echo "Setting up CSTR identifier update service..."

# Create log directory if it doesn't exist
if [ ! -d "$LOG_DIR" ]; then
    echo "Creating log directory: $LOG_DIR"
    mkdir -p "$LOG_DIR"
    chown $SERVICE_USER:$SERVICE_USER "$LOG_DIR"
fi

# Update the script's shebang to use the virtual environment's Python
if [ -f "$APP_DIR/update_all_cstr_identifiers.py" ]; then
    echo "Updating the script to use the virtual environment's Python"
    sed -i "1s:#\!/usr/bin/env python3:#\!$PYTHON_ENV:" "$APP_DIR/update_all_cstr_identifiers.py"
    chmod +x "$APP_DIR/update_all_cstr_identifiers.py"
else
    echo "ERROR: The script file $APP_DIR/update_all_cstr_identifiers.py doesn't exist."
    exit 1
fi

# Create the systemd service file
cat > /tmp/update_cstr_identifiers.service << EOL
[Unit]
Description=CSTR Identifier Update Service
After=network.target

[Service]
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/update_all_cstr_identifiers.py
Restart=always
RestartSec=60
StandardOutput=append:$LOG_FILE
StandardError=append:$LOG_FILE

[Install]
WantedBy=multi-user.target
EOL

# Install the service
echo "Installing systemd service..."
sudo mv /tmp/update_cstr_identifiers.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable update_cstr_identifiers.service
sudo systemctl start update_cstr_identifiers.service

# Check service status
echo "Service status:"
sudo systemctl status update_cstr_identifiers.service

echo "Setup complete. The CSTR identifier update service is now running."
echo "You can check the logs at: $LOG_FILE"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status update_cstr_identifiers.service  # Check status"
echo "  sudo systemctl stop update_cstr_identifiers.service    # Stop service"
echo "  sudo systemctl start update_cstr_identifiers.service   # Start service"
echo "  sudo systemctl restart update_cstr_identifiers.service # Restart service"
echo "  sudo journalctl -u update_cstr_identifiers.service     # View logs"
