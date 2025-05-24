from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager # Import JWTManager

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # Configuration settings
    # TODO: Move these to a configuration file or environment variables for production
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:bronco_racing@127.0.0.1/bronco_parts' # Changed to pymysql
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this in your application!
    # TODO: Consider using environment variables for JWT_SECRET_KEY

    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, resources={r"/api/*": {"origins": "*"}})  # More specific CORS config
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
