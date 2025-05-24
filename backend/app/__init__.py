from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager # Import JWTManager
import os # Import os module

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # Configuration settings
    # Read from environment variables, with fallbacks for local development if appropriate
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 
        'mysql+pymysql://root:bronco_racing@127.0.0.1/bronco_parts'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    jwt_secret_key = os.environ.get('JWT_SECRET_KEY')
    if not jwt_secret_key and app.config['ENV'] == 'production':
        raise ValueError("No JWT_SECRET_KEY set for Flask application in production environment.")
    app.config['JWT_SECRET_KEY'] = jwt_secret_key or 'super-secret-dev-key' # Fallback for dev only

    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)

    # CORS configuration
    # For production, set CORS_ALLOWED_ORIGINS to your frontend's domain e.g., "http://localhost:3000,https://yourdomain.com"
    # The current "*" is permissive.
    allowed_origins = os.environ.get('CORS_ALLOWED_ORIGINS')
    if allowed_origins:
        origins = [origin.strip() for origin in allowed_origins.split(',')]
    else:
        origins = "*" # Default to all if not specified (consider changing for production)
    
    CORS(app, resources={r"/api/*": {"origins": origins}})
    jwt = JWTManager(app) # Initialize JWTManager

    # Configure logging
    if not app.debug:
        import logging
        from logging.handlers import RotatingFileHandler
        # TODO: Consider a more robust logging setup for production
        # For now, basic console logging might be sufficient if app.debug is True
        # If app.debug is False, this will log to 'app.log'
        file_handler = RotatingFileHandler('app.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
    
    app.logger.setLevel(logging.INFO) # Ensure logger level is set for app.logger
    app.logger.info('BroncoPartsV2 application starting up')

    with app.app_context():
        from . import routes
        from . import models # Import models here to ensure they are registered with SQLAlchemy

        # Register blueprints if you decide to use them later
        # app.register_blueprint(routes.main_bp)

    return app
