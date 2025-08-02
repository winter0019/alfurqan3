import os
import sqlite3
from flask import Flask, g
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from flask.cli import with_appcontext
import click

bcrypt = Bcrypt()
csrf = CSRFProtect()

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            os.path.join(os.getcwd(), 'instance', 'database.db'),
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db():
    db = get_db()
    with open(os.path.join(os.path.dirname(__file__), 'schema.sql'), 'rb') as f:
        db.executescript(f.read().decode('utf8'))

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    click.echo('✅ Initialized the database.')

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'database.db'),
    )

    if test_config:
        app.config.from_mapping(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    bcrypt.init_app(app)
    csrf.init_app(app)

    # Register blueprint
    from .routes import main_bp
    app.register_blueprint(main_bp)

    # Register CLI command
    app.cli.add_command(init_db_command)

    # Close db connection
    @app.teardown_appcontext
    def close_db(error=None):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    return app
