from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from flask_user import UserManager
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_babel import Babel
from flask_mail import Mail

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_class=Config):
    """Create a Flask application.
    """
    # Set the version of the overall framework?
    __version__ = '0.1'

    # Instantiate Flask
    app = Flask(__name__)

    # Load environment variables
    app.config.from_object(config_class)

    # Enable CSRF protection globally
    csrf.init_app(app)

    # Initialize Flask-BabelEx
    babel.init_app(app)

    # Setup Flask-SQLAlchemy
    db.init_app(app)

    # Setup Flask-Migrate
    migrate.init_app(app, db)

    # Register blueprints
    from app.routes.main import main
    app.register_blueprint(main)

    from app.routes.api.services import api_v1 as services_api
    app.register_blueprint(services_api, url_prefix='/api/v1')

    return app


from models import main, auth, gradebook
from models.auth import User

