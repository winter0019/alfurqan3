import sqlite3
import os
from flask import Flask, g, current_app
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect

bcrypt = Bcrypt()
csrf = CSRFProtect()

def get_db():
    """Establishes and returns a database connection."""
    if 'db' not in g:
        db_path = current_app.config['DATABASE']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db():
    """Initializes the database using schema.sql."""
    db = get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))
    db.commit()

def create_app(test_config=None):
    """The Flask application factory."""
    app = Flask(__name__, instance_relative_config=True)

    # Default config
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        DATABASE=os.path.join(app.instance_path, 'alfurqa_academy.db'),
        WTF_CSRF_ENABLED=True,
    )

    if test_config:
        app.config.update(test_config)
    else:
        # Load the instance config, if it exists
        app.config.from_pyfile('config.py', silent=True)

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Initialize extensions
    bcrypt.init_app(app)
    csrf.init_app(app)

    # Register blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)

    # Add CLI command to init DB
    @app.cli.command('init-db')
    def init_db_command():
        """Clear existing data and create new tables."""
        init_db()
        print('Initialized the database.')

    # Close DB on teardown
    @app.teardown_appcontext
    def close_db(error=None):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    return app
