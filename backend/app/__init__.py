from flask import Flask, jsonify
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
    # FLASK_ENV (and thus app.env) is set by the environment variable.
    # If you need to explicitly put it in app.config, do it after app creation:
    app.config['ENV'] = os.environ.get('FLASK_ENV', 'production') # Ensure it matches FLASK_ENV

    # Read from environment variables, with fallbacks for local development if appropriate
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 
        'mysql+pymysql://bp_prod_user:your_very_strong_db_password_here@127.0.0.1/broncoparts_production'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    jwt_secret_key = os.environ.get('JWT_SECRET_KEY')
    # Check environment for production
    flask_env = os.environ.get('FLASK_ENV', 'production')
    if not jwt_secret_key and flask_env == 'production':
        raise ValueError("No JWT_SECRET_KEY set for Flask application in production environment.")
    app.config['JWT_SECRET_KEY'] = jwt_secret_key or 'super-secret-dev-key' # Fallback for dev only

    from datetime import timedelta
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8) 
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)  

    # Airtable Configuration
    app.config['AIRTABLE_API_KEY'] = os.environ.get('AIRTABLE_API_KEY') # Removed default
    app.config['AIRTABLE_BASE_ID'] = os.environ.get('AIRTABLE_BASE_ID') # Removed default
    app.config['AIRTABLE_TABLE_ID'] = os.environ.get('AIRTABLE_TABLE_ID') # Removed default
    
    # Ensure API key is set in production
    if not app.config['AIRTABLE_API_KEY'] and flask_env == 'production':
        raise ValueError("Airtable API Key not set for production environment.")
    elif not app.config['AIRTABLE_API_KEY'] and flask_env != 'production':
        app.logger.warning("Airtable API Key is not set. Airtable integration will not work.")

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

    # Register error handlers
    @app.errorhandler(400)
    def handle_bad_request(e):
        """Handle bad request errors, including JSON parsing errors."""
        return jsonify(message="Error: Malformed request"), 400
    
    @app.errorhandler(404)
    def handle_not_found(e):
        """Handle not found errors with JSON response."""
        return jsonify(message="Error: Resource not found"), 404
    
    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        """Handle method not allowed errors with JSON response."""
        return jsonify(message="Error: Method not allowed"), 405

    with app.app_context():
        from . import routes
        from . import models # Import models here to ensure they are registered with SQLAlchemy

        # Register blueprints if you decide to use them later
        # app.register_blueprint(routes.main_bp)

    return app
