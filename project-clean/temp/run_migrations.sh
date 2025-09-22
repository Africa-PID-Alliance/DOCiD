#!/bin/bash

# Script to run Flask-Migrate commands
# Usage: ./run_migrations.sh [command]
# Available commands: init, migrate, upgrade, downgrade, current, history

# Set up working directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR" || exit 1

# Check if virtual environment exists and activate it
if [ -d "venv_new" ]; then
    echo "Activating virtual environment..."
    source venv_new/bin/activate
elif [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Warning: Virtual environment not found. Using system Python."
fi

# Define functions for each migration command
run_init() {
    echo "Initializing migration repository..."
    python -c "
from init_migrations import *
app = create_app()
with app.app_context():
    from flask_migrate import init
    init()
    print('✅ Migration repository initialized!')
"
}

run_migrate() {
    local message="$1"
    if [ -z "$message" ]; then
        read -p "Enter migration message: " message
    fi
    
    echo "Creating migration with message: ${message:-'Auto-generated migration'}"
    python -c "
from init_migrations import *
app = create_app()
with app.app_context():
    from flask_migrate import migrate
    migrate(message='${message:-Auto-generated migration}')
    print('✅ Migration created successfully!')
"
}

run_upgrade() {
    echo "Upgrading database..."
    python -c "
from init_migrations import *
app = create_app()
with app.app_context():
    from flask_migrate import upgrade
    upgrade()
    print('✅ Database upgraded successfully!')
"
}

run_downgrade() {
    local revision="$1"
    
    if [ -z "$revision" ]; then
        read -p "Enter revision to downgrade to (default: -1): " revision
        revision=${revision:-"-1"}
    fi
    
    echo "Downgrading database to revision $revision..."
    python -c "
from init_migrations import *
app = create_app()
with app.app_context():
    from flask_migrate import downgrade
    downgrade('$revision')
    print('✅ Database downgraded successfully!')
"
}

run_current() {
    echo "Current revision:"
    python -c "
from init_migrations import *
app = create_app()
with app.app_context():
    from flask_migrate import current
    current()
"
}

run_history() {
    echo "Migration history:"
    python -c "
from init_migrations import *
app = create_app()
with app.app_context():
    from flask_migrate import history
    history()
"
}

# Check which command to run
case "$1" in
    init)
        run_init
        ;;
    migrate)
        run_migrate "$2"
        ;;
    upgrade)
        run_upgrade
        ;;
    downgrade)
        run_downgrade "$2"
        ;;
    current)
        run_current
        ;;
    history)
        run_history
        ;;
    *)
        echo "Usage: $0 [command] [options]"
        echo "Available commands:"
        echo "  init      Initialize migration repository"
        echo "  migrate   Create a new migration (optionally with message)"
        echo "  upgrade   Upgrade database to latest migration"
        echo "  downgrade Downgrade database (optionally specify revision)"
        echo "  current   Show current revision"
        echo "  history   Show migration history"
        echo ""
        echo "Examples:"
        echo "  $0 init"
        echo "  $0 migrate 'add user roles'"
        echo "  $0 downgrade abc123"
        exit 1
        ;;
esac

echo "Done."
