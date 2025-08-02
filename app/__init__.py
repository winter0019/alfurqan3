from flask import Flask
from flask_wtf.csrf import CSRFProtect
from .db import init_db  # Make sure this exists

csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    csrf.init_app(app)

    # Import and register blueprints
    from .views.auth import auth_bp
    from .views.admin import admin_bp
    from .views.exam import exam_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(exam_bp)

    # Add CLI command
    import click

    @app.cli.command("init-db")
    def init_db_command():
        """Clear existing data and create new tables."""
        init_db()
        click.echo("✅ Initialized the database.")

    return app
