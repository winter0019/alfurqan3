import os
import sqlite3
from flask import Flask, g, current_app
from flask.cli import with_appcontext
import click

# --- Database helpers ---

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            os.path.join(current_app.instance_path, 'database.db'),
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    click.echo('✅ Database initialized.')

# --- Flask App Factory ---

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'database.db'),
    )

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Register CLI command and teardown
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

    # A simple route for testing
    @app.route('/hello')
    def hello():
        return 'Hello, Flask is working!'

    return app
