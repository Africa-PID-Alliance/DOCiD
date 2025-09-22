import click
from flask.cli import FlaskGroup
from app import create_app, db, migrate
from app.models import Publications,PublicationFiles,PublicationDocuments,PublicationCreators,PublicationOrganization,PublicationFunders,PublicationProjects
from app.models import ResourceTypes,FunderTypes,CreatorsRoles,creatorsIdentifiers,PublicationIdentifierTypes,PublicationTypes,UserAccount

from scripts.seed_db import seed, generate_pids

# Create a FlaskGroup to manage the application
def create_my_app():
    return create_app()

@click.group(cls=FlaskGroup, create_app=create_my_app)
def cli():
    """Management script for the Flask application."""

@cli.command('create-db')
def create_db():
    """Create the database tables."""
    try:
     db.create_all()
     click.echo('Database created.')
    except Exception as e:
     db.session.rollback()
     print(f"Error occurred: {e}")

@cli.command('recreate-db')
def create_db():
    """Create the database tables."""
    try:
     db.create_all()
     click.echo('Database re created.')
    except Exception as e:
     db.session.rollback()
     print(f"Error occurred: {e}")


@cli.command('upgrade-db')
def upgrade_db():
    """Upgrade the database to the latest migration."""
    try:
        migrate.upgrade()
        click.echo('Database upgraded to latest migration.')
    except Exception as e:
        print(f"Error occurred: {e}")


@cli.command('drop-db')
def drop_db():
    """Drop the database tables."""
    
@cli.command('db-migrate')
@click.option('--message', '-m', default=None, help='Migration message')
def db_migrate(message):
    """Generate a new migration."""
    try:
        migrate.migrate(message=message)
        click.echo('Migration script created.')
    except Exception as e:
        print(f"Error creating migration: {e}")
        
@cli.command('db-downgrade')
@click.option('--revision', '-r', default='-1', help='Revision to downgrade to (default: -1)')
def db_downgrade(revision):
    """Downgrade the database."""
    try:
        migrate.downgrade(revision)
        click.echo(f'Database downgraded to {revision}.')
    except Exception as e:
        print(f"Error occurred during downgrade: {e}")
        
@cli.command('db-init')
def db_init():
    """Initialize migration repository."""
    try:
        migrate.init()
        click.echo('Migration repository initialized.')
    except Exception as e:
        print(f"Error initializing migrations: {e}")
        
@cli.command('db-current')
def db_current():
    """Show current migration revision."""
    try:
        migrate.current()
        # Output is printed by the migrate.current() function
    except Exception as e:
        print(f"Error getting current migration: {e}")
        
@cli.command('db-history')
def db_history():
    """Show migration history."""
    try:
        migrate.history()
        # Output is printed by the migrate.history() function
    except Exception as e:
        print(f"Error getting migration history: {e}")
    try:
     db.drop_all()
     click.echo('Database dropped.')
    except Exception as e:
     db.session.rollback()
     print(f"Error occurred: {e}")

@cli.command('seed-db')
def seed_db():
    seed()

    # """Seed the database with initial data."""
    # example = ExampleModel(name='Initial Example')
    # db.session.add(example)
    # db.session.commit()
    # click.echo('Database seeded.')

    # test = TestModel(name='Data Test 2')
    # db.session.add(test)
    # db.session.commit()
    # click.echo('Database seeded.')

@cli.command('generate-pids')
def gen_pids():
    generate_pids()

if __name__ == '__main__':
    cli()
