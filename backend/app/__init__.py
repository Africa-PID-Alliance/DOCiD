# app/__init__.py

import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_mailman import Mail
from config import Config
from flasgger import Swagger
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
jwt = JWTManager()
limiter = Limiter(get_remote_address)

# Create the cache object
cache = Cache()

def create_app():
    
    swagger_config = Swagger.DEFAULT_CONFIG

    # Set a descriptive title for your API documentation
    swagger_config['openapi_version'] = '0.1.2'
    swagger_config['title'] = 'TCC DocID API'
    swagger_config['swagger_ui_bundle_js'] = '//unpkg.com/swagger-ui-dist@3/swagger-ui-bundle.js'
    swagger_config['swagger_ui_standalone_preset_js'] = '//unpkg.com/swagger-ui-dist@3/swagger-ui-standalone-preset.js'
    swagger_config['jquery_js'] = '//unpkg.com/jquery@2.2.4/dist/jquery.min.js'
    swagger_config['swagger_ui_css'] = '//unpkg.com/swagger-ui-dist@3/swagger-ui.css'
    swagger_config['static_url_path'] = '/flasgger_static'
    swagger_config['static_folder'] = '/flasgger_static'
    swagger_config['swagger_ui'] =  True
    
    app = Flask(__name__)

    # Load configurations from config.py
    app.config.from_object(Config)

    # JWT Configuration from environment
    from datetime import timedelta
    app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET_KEY
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(seconds=Config.JWT_REFRESH_TOKEN_EXPIRES)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    # Configure CORS to allow local development
    CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://docid.africapidalliance.org"])
    jwt.init_app(app)
    limiter.init_app(app)
    
    
    # Cache configuration
    app.config['CACHE_TYPE'] = 'simple'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 minutes timeout
    
    # Initialize cache
    cache.init_app(app)
    
    # Set up Swagger
    Swagger(app)

    # Define a basic route
    @app.route('/api/v1')
    def index():
        return jsonify("Welcome to the DOCID Integration API :)")

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.datacite import datacite_bp
    from app.routes.docid import docid_bp
    from app.routes.crossref import crossref_bp
    from app.routes.ror import ror_bp
    from app.routes.raid import raid_bp
    from app.routes.cordoi import cordoi_bp
    from app.routes.orcid import orcid_bp
    from app.routes.publications import publications_bp
    from app.routes.arks import arks_bp
    from app.routes.cstr import cstr_bp
    from app.routes.smtp import smtp_bp
    from app.routes.uploads import uploads_bp
    from app.routes.doi import doi_bp
    from app.routes.localcontexts import localcontexts_bp
    from app.routes.docs import docs_bp
    from app.routes.comments import comments_bp
    from app.routes.user_profile import user_profile_bp
    from app.routes.analytics import analytics_bp
    from app.routes.isni import isni_bp
    from app.routes.ringgold import ringgold_bp
    from app.routes.dspace import dspace_bp
    from app.routes.dspace_legacy import dspace_legacy_bp

    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(datacite_bp, url_prefix='/api/v1/datacite')
    app.register_blueprint(docid_bp, url_prefix='/api/v1/docid')
    app.register_blueprint(crossref_bp, url_prefix='/api/v1/crossref')
    app.register_blueprint(ror_bp, url_prefix='/api/v1/ror')
    app.register_blueprint(raid_bp, url_prefix='/api/v1/raid')
    app.register_blueprint(orcid_bp, url_prefix='/api/v1/orcid')
    app.register_blueprint(cordoi_bp, url_prefix='/api/v1/cordoi')
    app.register_blueprint(publications_bp, url_prefix='/api/v1/publications')
    app.register_blueprint(arks_bp, url_prefix='/api/v1/arks')
    app.register_blueprint(cstr_bp, url_prefix='/api/v1/cstr')
    app.register_blueprint(smtp_bp, url_prefix='/api/v1/smtp')
    app.register_blueprint(uploads_bp, url_prefix='/uploads')
    app.register_blueprint(doi_bp, url_prefix='/doi')
    app.register_blueprint(localcontexts_bp,url_prefix='/api/v1/localcontexts')
    app.register_blueprint(docs_bp,url_prefix='/docs')
    app.register_blueprint(comments_bp)
    app.register_blueprint(user_profile_bp, url_prefix='/api/v1/user-profile')
    app.register_blueprint(analytics_bp)
    app.register_blueprint(isni_bp, url_prefix='/api/v1/isni')
    app.register_blueprint(ringgold_bp, url_prefix='/api/v1/ringgold')
    app.register_blueprint(dspace_bp)  # DSpace 7+ integration
    app.register_blueprint(dspace_legacy_bp)  # DSpace 6.x Legacy integration

    # Add root-level DocID route
    from app.routes.docid_root import setup_docid_root_route
    setup_docid_root_route(app)

    # Set up logging
    setup_logging(app)

    # Log requests and responses
    @app.before_request
    def log_request_info():
        if request.method in ['GET', 'POST']:
            app.logger.info("-----------------------------------------------------------------\r\n")
            app.logger.info(f"Request: {request.method} {request.url} - Body: {request.get_data()}")

    @app.after_request
    def log_response_info(response):
        if request.method in ['GET', 'POST']:
            app.logger.info(f"Response: {response.status} - Body: {request.get_data(as_text=True)}")

        # Only log the response body if direct_passthrough is not set
        if not response.direct_passthrough:
            app.logger.info(f"Response: {response.status} - Body: {response.get_data(as_text=True)}")
        else:
            app.logger.info(f"Response: {response.status} - Direct passthrough enabled")

        app.logger.info("-----------------------------------------------------------------\r\n")
        return response

    return app

def setup_logging(app):
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('App startup')
