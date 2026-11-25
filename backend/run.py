from app import create_app, db
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

# Migrations: use Flask-Migrate's own group, e.g. `flask --app run.py db upgrade`.

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(__import__('os').getenv('FLASK_PORT', 5001)),
        debug=__import__('os').getenv('FLASK_ENV', 'development') == 'development'
    )
