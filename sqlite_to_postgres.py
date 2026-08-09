"""
sqlite_to_postgres.py
─────────────────────
Safe, idempotent one-shot migration of ALL existing SQLite data into
PostgreSQL without modifying or deleting the SQLite database.

How it works:
  1. Reads every row from instance/inventory.db via the sqlite3 stdlib.
  2. Opens the Flask app context so SQLAlchemy connects to the configured
     DATABASE_URL (must point at PostgreSQL — see instructions below).
  3. Inserts rows in dependency order (users → items → stock_transactions)
     using INSERT … ON CONFLICT DO NOTHING so the script is safe to re-run.
  4. Resets PostgreSQL SERIAL sequences so future inserts get correct IDs.

Prerequisites:
  • PostgreSQL tables already created  →  run `flask db upgrade` first.
  • DATABASE_URL env var must point to PostgreSQL, NOT SQLite, when you
    run this script.

Usage (Windows):
    set DATABASE_URL=postgresql://user:pass@host:5432/dbname
    .venv\Scripts\python.exe sqlite_to_postgres.py

Usage (Linux/macOS / Render shell):
    export DATABASE_URL=postgresql://user:pass@host:5432/dbname
    python sqlite_to_postgres.py

The SQLite database is NEVER modified or deleted by this script.
"""

import os
import sys
import sqlite3

# ── Bootstrap the Flask app ────────────────────────────────────────────────────
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from app import create_app, db
from sqlalchemy import text

app = create_app()

SQLITE_PATH = os.path.join(project_root, 'instance', 'inventory.db')


def abort(msg):
    print(f"[ERROR] {msg}")
    sys.exit(1)


def read_sqlite():
    """Read all rows from the SQLite database and return them as plain dicts."""
    if not os.path.exists(SQLITE_PATH):
        abort(f"SQLite database not found at: {SQLITE_PATH}")

    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row   # rows accessible by column name
    cur = conn.cursor()

    def fetch(table):
        cur.execute(f"SELECT * FROM {table}")
        rows = [dict(r) for r in cur.fetchall()]
        print(f"[READ ] {table:25s}: {len(rows):>5} rows")
        return rows

    data = {
        'users':              fetch('users'),
        'items':              fetch('items'),
        'stock_transactions': fetch('stock_transactions'),
    }
    conn.close()
    return data


def migrate(data):
    """Insert all rows into PostgreSQL, skipping already-existing primary keys."""
    with app.app_context():
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if 'sqlite' in db_uri:
            abort(
                "DATABASE_URL still points at SQLite!\n"
                "Set DATABASE_URL to your PostgreSQL connection string before running."
            )

        print(f"\n[INFO ] Connected to: {db_uri[:60]}...")
        conn = db.engine.connect()

        # ── 1. Users ──────────────────────────────────────────────────────────
        users_inserted = 0
        for row in data['users']:
            result = conn.execute(text("""
                INSERT INTO users (id, username, email, password_hash, currency)
                VALUES (:id, :username, :email, :password_hash, :currency)
                ON CONFLICT DO NOTHING
            """), {
                'id':            row['id'],
                'username':      row['username'],
                'email':         row['email'],
                'password_hash': row['password_hash'],
                'currency':      row.get('currency', 'INR'),
            })
            users_inserted += result.rowcount
        conn.commit()

        # ── 2. Items ──────────────────────────────────────────────────────────
        items_inserted = 0
        for row in data['items']:
            result = conn.execute(text("""
                INSERT INTO items (
                    id, user_id, name, description, category,
                    quantity, minimum_quantity, price,
                    supplier, sku, location, created_at, updated_at
                )
                VALUES (
                    :id, :user_id, :name, :description, :category,
                    :quantity, :minimum_quantity, :price,
                    :supplier, :sku, :location, :created_at, :updated_at
                )
                ON CONFLICT (id) DO NOTHING
            """), {
                'id':               row['id'],
                'user_id':          row['user_id'],
                'name':             row['name'],
                'description':      row.get('description'),
                'category':         row.get('category', 'Other'),
                'quantity':         row['quantity'],
                'minimum_quantity': row['minimum_quantity'],
                'price':            row['price'],
                'supplier':         row.get('supplier'),
                'sku':              row['sku'],
                'location':         row.get('location'),
                'created_at':       row.get('created_at'),
                'updated_at':       row.get('updated_at'),
            })
            items_inserted += result.rowcount
        conn.commit()

        # ── 3. Stock Transactions ─────────────────────────────────────────────
        tx_inserted = 0
        for row in data['stock_transactions']:
            result = conn.execute(text("""
                INSERT INTO stock_transactions (
                    id, item_id, user_id, change, transaction_type, created_at
                )
                VALUES (
                    :id, :item_id, :user_id, :change, :transaction_type, :created_at
                )
                ON CONFLICT (id) DO NOTHING
            """), {
                'id':               row['id'],
                'item_id':          row['item_id'],
                'user_id':          row['user_id'],
                'change':           row['change'],
                'transaction_type': row['transaction_type'],
                'created_at':       row.get('created_at'),
            })
            tx_inserted += result.rowcount
        conn.commit()

        # ── 4. Reset PostgreSQL SERIAL sequences ──────────────────────────────
        # After inserting rows with explicit IDs, the auto-increment sequence
        # still starts from 1. We reset each sequence to max(id) so that
        # future inserts get correct non-conflicting IDs.
        print("\n[SEQ  ] Resetting PostgreSQL sequences...")
        for table, col in [('users', 'id'), ('items', 'id'), ('stock_transactions', 'id')]:
            conn.execute(text(
                f"SELECT setval(pg_get_serial_sequence('{table}', '{col}'), "
                f"COALESCE(MAX({col}), 1)) FROM {table}"
            ))
            print(f"[SEQ  ] {table}.{col} sequence reset.")
        conn.commit()

        conn.close()

        print(f"""
[DONE ] Migration complete:
        users              inserted: {users_inserted:>4}  (skipped: {len(data['users']) - users_inserted})
        items              inserted: {items_inserted:>4}  (skipped: {len(data['items']) - items_inserted})
        stock_transactions inserted: {tx_inserted:>4}  (skipped: {len(data['stock_transactions']) - tx_inserted})

        Your SQLite database has NOT been modified.
        You can verify by logging in at your production URL.
""")


def main():
    print("=" * 60)
    print("  SQLite → PostgreSQL Migration")
    print("=" * 60)
    print(f"\n[READ ] Reading from SQLite: {SQLITE_PATH}\n")
    data = read_sqlite()
    migrate(data)


if __name__ == '__main__':
    main()
