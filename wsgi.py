"""
wsgi.py — Production WSGI entry point for Gunicorn on Render.

Start command:
    gunicorn wsgi:app

This module is intentionally separate from run.py (which is the local
development entry point) so that production startup logic is isolated.

Note: _run_db_upgrade() is called at module import time. With multiple
Gunicorn workers, each worker will call it once, but flask_migrate.upgrade()
is idempotent — it checks alembic_version and skips already-applied migrations,
so parallel calls from workers are completely safe.
"""
import os
from app import create_app

app = create_app()


def _run_db_upgrade():
    """Apply any pending Alembic migrations on startup.

    Safe to call multiple times — Alembic skips already-applied migrations.
    """
    with app.app_context():
        try:
            from flask_migrate import upgrade
            upgrade()
            print("[WSGI] flask db upgrade — OK")
        except Exception as exc:
            # Log but do not crash — tables may already exist on re-deploy
            print(f"[WSGI] flask db upgrade notice: {exc}")


# Run migrations when this module is first imported by Gunicorn
_run_db_upgrade()
