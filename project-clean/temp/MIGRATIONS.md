# DOCiD Database Migrations

This document provides instructions for working with database migrations using Flask-Migrate in the DOCiD project.

## Prerequisites

1. Make sure you have installed all requirements:
   ```
   pip install -r requirements.txt
   ```

2. Ensure your database configuration is correct in `config.py`

## Available Migration Commands

### Using run_migrations.sh Script (Recommended)

The `run_migrations.sh` script provides a convenient way to manage migrations:

```bash
# Initialize migration repository (first-time setup)
./run_migrations.sh init

# Create a new migration
./run_migrations.sh migrate "description of changes"

# Apply migrations to the database
./run_migrations.sh upgrade

# Roll back migrations
./run_migrations.sh downgrade

# Check current migration version
./run_migrations.sh current

# View migration history
./run_migrations.sh history
```

### Using Flask CLI

You can also use Flask CLI commands directly:

```bash
# First, set up environment variables
source setup_flask_env.sh

# Initialize migration repository
flask db-init

# Create a new migration
flask db-migrate -m "description of changes"

# Apply migrations to the database
flask db-upgrade

# Roll back migrations
flask db-downgrade -r revision_id_or_relative_revision
```

### Using init_migrations.py

For an interactive experience:

```bash
python init_migrations.py
```

This will guide you through the available migration commands with a user-friendly menu interface.

## Migration Workflow

1. **Make changes to your models** in `app/models.py`
2. **Create a migration** to record these changes
3. **Review the generated migration file** in the `migrations/versions/` directory
4. **Apply the migration** to update your database schema
5. **Commit both your model changes and migration files** to version control

## Troubleshooting

- If you encounter errors during migration, check your database connection and ensure you have proper permissions.
- After significant schema changes, it might be easier to delete the migrations folder and start fresh with `flask db-init`.
- Always back up your database before applying migrations in production.

## Additional Resources

- [Flask-Migrate Documentation](https://flask-migrate.readthedocs.io/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
