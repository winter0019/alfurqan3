import sqlite3
import os
from flask import Flask, g, current_app
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect

# Create a Bcrypt instance and CSRF instance outside of the app factory
bcrypt = Bcrypt()
csrf = CSRFProtect()

def get_db():
    """Establishes and returns a database connection."""
    db = getattr(g, '_database', None)
    if db is None:
        db_path = current_app.config['DATABASE']
        db = g._database = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initializes the database from the schema file."""
    with current_app.app_context():
        db = get_db()
        with current_app.open_resource('schema.sql', mode='r') as f:
            script = f.read()
        db.cursor().executescript(script)
        db.commit()

def create_app(test_config=None):
    """The Flask app factory function."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        DATABASE=os.path.join(app.instance_path, 'alfurqa_academy.db'),
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize extensions with the app
    bcrypt.init_app(app)
    csrf.init_app(app)

    # Moved the database teardown function here
    @app.teardown_appcontext
    def close_db(e=None):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
