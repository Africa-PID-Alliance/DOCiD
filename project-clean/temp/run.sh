#!/bin/bash

# Navigate to project directory
cd /Users/ekariz/Projects/AMBAND/DOCiD/backend/

# Kill any process running on port 5001
lsof -ti:5001 | xargs -r kill -9 2>/dev/null || true

# Set Flask app
export FLASK_APP=app.py

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Run Flask app in debug mode on port 5001
flask run --debug --port=5001