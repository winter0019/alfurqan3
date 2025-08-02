# main.py
import os
import sqlite3
from flask import Flask, g
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from firebase_functions import https_fn
from werkzeug.security import generate_password_hash, check_password_hash

# IMPORTANT:
# We need to change the database to Firestore for Firebase deployment.
# SQLite is not suitable for a serverless environment.
# For now, we will comment out the SQLite code, but the database logic
# will need to be re-written using Firestore in the next steps.

# Initialize extensions outside of the app factory
bcrypt = Bcrypt()
csrf = CSRFProtect()

def create_app(test_config=None):
    """
    The Flask app factory function.
    """
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        # DATABASE is no longer used for Firebase deployment.
        # It's kept here for local testing.
        DATABASE='alfurqa_academy.db',
    )
    
    # Initialize extensions with the app
    bcrypt.init_app(app)
    csrf.init_app(app)

    # We will need to re-implement the database logic with Firestore.
    # The current SQLite logic is not compatible with Cloud Functions.
    # For now, we will add simple routes without database access
    # to demonstrate a working Firebase function.
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app

# Initialize the Flask app
app = create_app()

# This is the entry point for Firebase Cloud Functions
@https_fn.on_request()
def alfurqa_academy_app(req: https_fn.Request) -> https_fn.Response:
    """
    Handles HTTP requests to the Flask application.
    """
    with app.app_context():
        # This will set up the Flask request context
        return app.wsgi_app(req.environ, https_fn.start_response)

