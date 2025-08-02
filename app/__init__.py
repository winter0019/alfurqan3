# ... existing imports
from flask.cli import with_appcontext
import click

# ... rest of your code (create_app, get_db, etc.)

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    # ... your config code

    # Initialize extensions
    bcrypt.init_app(app)
    csrf.init_app(app)

    # Register blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)

    # Register CLI commands
    app.cli.add_command(init_db_command)

    # DB teardown
    @app.teardown_appcontext
    def close_db(error=None):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    return app
