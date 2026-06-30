"""
Application Factory Module
============================
Creates and configures the Flask application using the factory pattern.
Initializes extensions, registers blueprints, and sets up logging.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from config import get_config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config_name: Optional configuration name override.

    Returns:
        Flask: Configured Flask application instance.
    """
    app = Flask(__name__,
                instance_relative_config=True,
                static_folder='static',
                template_folder='templates')

    # Load configuration
    config = get_config()
    app.config.from_object(config)

    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Ensure required directories exist
    _create_directories(app)

    # Initialize extensions
    _init_extensions(app)

    # Register blueprints
    _register_blueprints(app)

    # Setup logging
    _setup_logging(app)

    # Register error handlers
    _register_error_handlers(app)

    # Register context processors
    _register_context_processors(app)

    return app


def _create_directories(app: Flask) -> None:
    """Create required directories if they don't exist.

    Args:
        app: Flask application instance.
    """
    directories = [
        'logs',
        'data/raw',
        'data/processed',
        'data/models',
        os.path.join(app.static_folder, 'images', 'charts'),
        os.path.join(app.static_folder, 'images', 'posters'),
    ]
    for directory in directories:
        path = os.path.join(app.config.get('BASE_DIR', ''), directory)
        os.makedirs(path, exist_ok=True)


def _init_extensions(app: Flask) -> None:
    """Initialize Flask extensions.

    Args:
        app: Flask application instance.
    """
    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        from app.models import user, movie  # noqa: F401
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if not inspector.get_table_names():
            db.create_all()


def _register_blueprints(app: Flask) -> None:

    from app.routes.main_routes import main_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.movie_routes import movie_bp
    from app.routes.recommendation_routes import recommendation_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.api_routes import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(movie_bp, url_prefix='/movies')
    app.register_blueprint(recommendation_bp, url_prefix='/recommend')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')


def _setup_logging(app: Flask) -> None:
    """Configure application logging.

    Args:
        app: Flask application instance.
    """
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'DEBUG'))
    log_file = os.path.join(
        app.config.get('BASE_DIR', ''),
        app.config.get('LOG_FILE', 'logs/app.log')
    )

    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))

    app.logger.addHandler(file_handler)
    app.logger.setLevel(log_level)
    app.logger.info('AI Movie Recommendation System starting up...')


def _register_error_handlers(app: Flask) -> None:
    """Register custom error handlers.

    Args:
        app: Flask application instance.
    """
    from flask import render_template, jsonify, request

    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Resource not found', 'status': 404}), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error', 'status': 500}), 500
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Forbidden', 'status': 403}), 403
        return render_template('errors/403.html'), 403


def _register_context_processors(app: Flask) -> None:
    """Register template context processors.

    Args:
        app: Flask application instance.
    """
    @app.context_processor
    def inject_globals():
        return {
            'app_name': 'CineAI',
            'app_version': '1.0.0',
            'current_year': 2026,
        }
