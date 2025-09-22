#!/bin/bash

# setup_permissions.sh
# Script to set proper permissions for all executable files in the DOCiD backend project
# Run this script after deploying to a server to ensure all scripts are executable

echo "Setting up file permissions for DOCiD backend..."

# Get the absolute path of the backend directory
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BACKEND_DIR" || exit 1

# Make shell scripts executable
echo "Setting permissions for shell scripts..."
chmod +x run_migrations.sh
chmod +x run_update_identifiers.sh
chmod +x restart.sh
chmod +x cleanup.sh
chmod +x cleanup_scripts.sh

# Make Python scripts executable
echo "Setting permissions for Python scripts..."
chmod +x init_migrations.py
chmod +x update_all_cstr_identifiers.py
chmod +x test_single_cstr.py
chmod +x truncate_non_seeded_tables.py
chmod +x truncate_all_tables.py

# Make sure the main application files are readable
echo "Setting permissions for application files..."
chmod 644 run.py
chmod 644 wsgi.py
chmod 644 config.py
chmod 644 requirements.txt
chmod 644 requirements_minimal.txt

# Set directory permissions
echo "Setting directory permissions..."
chmod 755 app/
chmod 755 migrations/
chmod 755 scripts/
chmod 755 logs/
chmod 755 uploads/
chmod 755 temp/

echo "✅ File permissions set successfully!"
echo ""
echo "Executable files:"
echo "  - run_migrations.sh"
echo "  - run_update_identifiers.sh" 
echo "  - restart.sh"
echo "  - init_migrations.py"
echo "  - update_all_cstr_identifiers.py"
echo "  - test_single_cstr.py"
echo "  - truncate_non_seeded_tables.py"
echo "  - truncate_all_tables.py"
echo ""
echo "You can now run migration commands like:"
echo "  ./run_migrations.sh init"
echo "  ./run_migrations.sh current"
