#!/bin/bash

# Script to run update_publication_identifiers.py using the virtual environment

# Define script directory
SCRIPT_PATH="scripts/update_publication_identifiers.py"
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FULL_SCRIPT_PATH="${BASE_DIR}/${SCRIPT_PATH}"

# Check if the virtual environment exists
if [ -d "${BASE_DIR}/venv" ]; then
    echo "Using existing virtual environment..."
    # Activate the virtual environment
    source "${BASE_DIR}/venv/bin/activate"
else
    echo "Virtual environment not found. Creating a new one..."
    python3 -m venv "${BASE_DIR}/venv"
    source "${BASE_DIR}/venv/bin/activate"
    
    # Install requirements if they exist
    if [ -f "${BASE_DIR}/requirements.txt" ]; then
        echo "Installing requirements..."
        pip install -r "${BASE_DIR}/requirements.txt"
    fi
fi

# Run the script
echo "Running update_publication_identifiers.py..."
python "${FULL_SCRIPT_PATH}"

# Check the exit status
if [ $? -eq 0 ]; then
    echo "Script completed successfully!"
else
    echo "Script failed with error code $?"
fi

# Deactivate the virtual environment
deactivate

echo "Done!"
