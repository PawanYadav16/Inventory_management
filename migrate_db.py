import os
import sqlite3
from flask_migrate import upgrade
from app import create_app, db


def migrate_sqlite_file(db_path):
    """Safely apply currency column migration to a specific SQLite database file."""
    if not os.path.exists(db_path):
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'currency' not in columns:
                print(f"[Migration] Adding missing 'currency' column to SQLite DB: {db_path}")
                cursor.execute("ALTER TABLE users ADD COLUMN currency VARCHAR(10) NOT NULL DEFAULT 'INR'")
                conn.commit()
                print(f"[Migration] Successfully added 'currency' column with default 'INR' to {db_path}")

            # Ensure alembic_version table exists and is stamped to 002_add_user_currency
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
            if cursor.fetchone():
                cursor.execute("UPDATE alembic_version set version_num='002_add_user_currency'")
            else:
                cursor.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL, CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))")
                cursor.execute("INSERT INTO alembic_version VALUES ('002_add_user_currency')")
            conn.commit()
        conn.close()
    except Exception as err:
        print(f"[Migration Warning] SQLite update error on {db_path}: {err}")


def run_database_migrations():
    """Apply Flask-Migrate migrations safely to preserve existing data."""
    app = create_app()
    with app.app_context():
        # Ensure instance directory exists
        os.makedirs(app.instance_path, exist_ok=True)

        # 1. Attempt standard Flask-Migrate upgrade via Alembic engine
        try:
            upgrade()
            print("[Migration] Flask-Migrate upgrade completed successfully.")
        except Exception as err:
            print(f"[Migration] Flask-Migrate notice: {err}")

        # 2. Check and migrate all SQLite databases in instance and root
        basedir = app.root_path
        possible_db_paths = [
            os.path.join(app.instance_path, 'inventory.db'),
            os.path.join(os.path.dirname(basedir), 'instance', 'inventory.db'),
            os.path.join(os.path.dirname(basedir), 'inventory.db')
        ]

        for path in set(possible_db_paths):
            if os.path.exists(path):
                migrate_sqlite_file(path)


if __name__ == '__main__':
    run_database_migrations()
