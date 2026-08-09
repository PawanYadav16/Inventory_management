import os
from dotenv import load_dotenv

# Load environment variables from .env file
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    """Base application configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'default-fallback-secret-key-2026'

    # Handle database URL configuration
    db_url = os.environ.get('DATABASE_URL')

    # Normalize SQLite paths to use absolute instance/inventory.db
    if not db_url or db_url in ('sqlite:///inventory.db', 'sqlite:///instance/inventory.db'):
        db_path = os.path.join(basedir, 'instance', 'inventory.db').replace('\\', '/')
        db_url = f'sqlite:///{db_path}'
    elif db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-WTF CSRF Protection
    WTF_CSRF_ENABLED = True
