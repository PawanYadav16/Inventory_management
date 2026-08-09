import os
from dotenv import load_dotenv

# Load environment variables from .env for local development
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    """Application configuration — reads from environment variables.

    Local development: set DATABASE_URL in .env to sqlite:///... (or leave
    unset to fall back to the local SQLite file automatically).

    Production (Render): set DATABASE_URL to the PostgreSQL connection string
    provided by Render. The postgres:// → postgresql:// rewrite is applied
    automatically because SQLAlchemy 1.4+ dropped the old dialect alias.
    """

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'change-me-in-production-env'

    # ── Database ──────────────────────────────────────────────────────────────
    _db_url = os.environ.get('DATABASE_URL')

    if not _db_url:
        # No DATABASE_URL set → fall back to local SQLite for development
        _sqlite_path = os.path.join(basedir, 'instance', 'inventory.db').replace('\\', '/')
        _db_url = f'sqlite:///{_sqlite_path}'
    elif _db_url.startswith('postgres://'):
        # Render (and Heroku) still issue the old postgres:// scheme;
        # SQLAlchemy 1.4+ requires postgresql://
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # PostgreSQL connection pool tuning (ignored by SQLite, safe to leave on)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,   # reconnect automatically if connection drops
        'pool_recycle': 300,     # recycle connections every 5 min (Render idle timeout)
    }

    # ── Flask-WTF CSRF Protection ─────────────────────────────────────────────
    WTF_CSRF_ENABLED = True
