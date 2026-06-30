"""
Application Configuration Module
==================================
Provides configuration classes for different environments.
Uses environment variables with sensible defaults.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration class with shared settings."""

    # Flask Core
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-fallback-secret-key')
    FLASK_APP: str = os.getenv('FLASK_APP', 'run.py')

    # Database
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'movie_recommender.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # OMDb API
    OMDB_API_KEY: str = os.getenv('OMDB_API_KEY', '')
    OMDB_BASE_URL: str = os.getenv('OMDB_BASE_URL', 'http://www.omdbapi.com/')

    # ML Paths
    ML_MODEL_PATH: str = os.getenv('ML_MODEL_PATH', 'data/models/')
    ML_DATA_PATH: str = os.getenv('ML_DATA_PATH', 'data/raw/')
    ML_PROCESSED_PATH: str = os.getenv('ML_PROCESSED_PATH', 'data/processed/')

    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'DEBUG')
    LOG_FILE: str = os.getenv('LOG_FILE', 'logs/app.log')

    # Pagination
    MOVIES_PER_PAGE: int = 20
    USERS_PER_PAGE: int = 20

    # Upload
    MAX_CONTENT_LENGTH: int = 50 * 1024 * 1024  # 50MB max upload

    # Base directory
    BASE_DIR: str = os.path.abspath(os.path.dirname(__file__))


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG: bool = True
    TESTING: bool = False


class TestingConfig(Config):
    """Testing environment configuration."""

    DEBUG: bool = True
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = 'sqlite:///test_movie_recommender.db'
    WTF_CSRF_ENABLED: bool = False


class ProductionConfig(Config):
    """Production environment configuration."""

    DEBUG: bool = False
    TESTING: bool = False


config_by_name: dict[str, type[Config]] = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}


def get_config() -> Config:
    """Get configuration based on FLASK_ENV environment variable.

    Returns:
        Config: The appropriate configuration object.
    """
    env: str = os.getenv('FLASK_ENV', 'development')
    config_class = config_by_name.get(env, DevelopmentConfig)
    return config_class()
