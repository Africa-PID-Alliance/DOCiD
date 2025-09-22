from app import create_app, db, migrate
from app.models import UserAccount
from flask.cli import with_appcontext
import click

app = create_app()

@app.cli.command('create-db')
def create_db():
    db.create_all()
    print('Database created.')

@app.cli.command('drop-db')
def drop_db():
    db.drop_all()
    print('Database dropped.')

# Migration commands
@app.cli.command('db-init')
def db_init():
    """Initialize migrations."""
    migrate.init()
    print('Migration repository initialized.')

@app.cli.command('db-migrate')
@click.option('--message', '-m', help='Migration message')
def db_migrate(message=None):
    """Create a new migration."""
    migrate.migrate(message=message)
    print('Migration script created.')

@app.cli.command('db-upgrade')
def db_upgrade():
    """Upgrade to the latest migration."""
    migrate.upgrade()
    print('Database upgraded to latest migration.')

@app.cli.command('db-downgrade')
@click.option('--revision', '-r', default='-1', help='Revision to downgrade to')
def db_downgrade(revision):
    """Downgrade the database."""
    migrate.downgrade(revision)
    print(f'Database downgraded to {revision}.')

if __name__ == '__main__':
    # app.run(debug=False, port=5001)
    app.run(debug=True, port=5001)  # Start the server on port 50001
