"""
Configuration for SQLite local database setup
Place environment variables in .env file or set them before running the app
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

AVAILABLE_THEMES = [
    {'key': 'theme-default', 'name': 'Blue (Default)', 'preview': '#2563eb'},
    {'key': 'theme-emerald', 'name': 'Emerald Green',  'preview': '#059669'},
    {'key': 'theme-crimson', 'name': 'Crimson Red',    'preview': '#dc2626'},
    {'key': 'theme-violet',  'name': 'Violet Purple',  'preview': '#7c3aed'},
    {'key': 'theme-amber',   'name': 'Amber Gold',     'preview': '#d97706'},
    {'key': 'theme-sky',     'name': 'Sky Blue',        'preview': '#0284c7'},
    {'key': 'theme-rose',    'name': 'Rose Pink',       'preview': '#e11d48'},
    {'key': 'theme-teal',    'name': 'Teal',            'preview': '#0d9488'},
    {'key': 'theme-indigo',  'name': 'Indigo',          'preview': '#4338ca'},
    {'key': 'theme-orange',  'name': 'Orange',          'preview': '#ea580c'},
]


class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get("SESSION_SECRET") or "red-dot-pharmacy-dev-secret"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }


class DevelopmentConfig(Config):
    """Development configuration - Uses SQLite locally"""
    SQLALCHEMY_DATABASE_URI = "sqlite:///red_dot_pharmacy.db"
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration - Uses PostgreSQL"""
    # On Replit, DATABASE_URL is set in Secrets
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///red_dot_pharmacy.db"  # Fallback to SQLite
    )
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    DEBUG = True
    TESTING = True


# Select configuration based on environment
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
