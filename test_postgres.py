"""
test_postgres.py
────────────────
Comprehensive PostgreSQL connection and functionality test.

Usage:
    1. Set DATABASE_URL to your PostgreSQL connection string:

       Windows CMD:
           set DATABASE_URL=postgresql://user:pass@host:5432/dbname

       PowerShell:
           $env:DATABASE_URL = "postgresql://user:pass@host:5432/dbname"

    2. Run:
           .venv\Scripts\python test_postgres.py

Tests performed:
    1.  Can connect to PostgreSQL
    2.  All 3 tables exist (users, items, stock_transactions)
    3.  Can INSERT a test user
    4.  Can SELECT the test user back
    5.  Can INSERT a test item linked to the user
    6.  Can SELECT the test item back
    7.  Can INSERT a stock transaction
    8.  Can UPDATE the item quantity
    9.  Can DELETE the stock transaction
    10. Can DELETE the item
    11. Can DELETE the test user
    12. PostgreSQL sequences are working (auto-increment IDs)
    13. All data is cleaned up — no test pollution
"""

import os
import sys
import time

project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from app import create_app, db
from sqlalchemy import text, inspect

PASS = "✅ PASS"
FAIL = "❌ FAIL"
SKIP = "⚠️  SKIP"

results = []

def check(label, passed, detail=""):
    status = PASS if passed else FAIL
    msg = f"  {status}  {label}"
    if detail:
        msg += f"\n         → {detail}"
    print(msg)
    results.append((label, passed))

def run():
    app = create_app()

    with app.app_context():
        db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        print("\n" + "=" * 60)
        print("  PostgreSQL Connection & Functionality Test")
        print("=" * 60)
        print(f"\n  DATABASE_URL = {db_uri[:72]}{'...' if len(db_uri) > 72 else ''}\n")

        # ── Test 1: DATABASE_URL is PostgreSQL ─────────────────────────────
        is_postgres = "postgresql" in db_uri or "postgres" in db_uri
        check("DATABASE_URL points to PostgreSQL", is_postgres,
              "Detected: SQLite — set DATABASE_URL to PostgreSQL" if not is_postgres else db_uri[:60])
        if not is_postgres:
            print("\n  ⛔  DATABASE_URL is not PostgreSQL. Set it and re-run.\n")
            sys.exit(1)

        # ── Test 2: Can connect ────────────────────────────────────────────
        try:
            conn = db.engine.connect()
            conn.execute(text("SELECT 1"))
            check("Connect to PostgreSQL server", True)
        except Exception as e:
            check("Connect to PostgreSQL server", False, str(e))
            print("\n  ⛔  Cannot connect. Check your DATABASE_URL credentials.\n")
            sys.exit(1)

        # ── Test 3: Required tables exist ──────────────────────────────────
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        for tbl in ["users", "items", "stock_transactions"]:
            check(f"Table '{tbl}' exists", tbl in existing_tables,
                  "Table missing — run: flask db upgrade" if tbl not in existing_tables else "")

        if not all(t in existing_tables for t in ["users", "items", "stock_transactions"]):
            print("\n  ⛔  Missing tables. Run: flask db upgrade\n")
            conn.close()
            sys.exit(1)

        # ── Test 4: INSERT a test user ──────────────────────────────────────
        TEST_EMAIL = f"_test_pg_{int(time.time())}@test.invalid"
        try:
            conn.execute(text("""
                INSERT INTO users (username, email, password_hash, currency)
                VALUES (:u, :e, :p, :c)
            """), {"u": "_test_pg_user", "e": TEST_EMAIL, "p": "x", "c": "INR"})
            conn.commit()
            check("INSERT test user", True)
        except Exception as e:
            check("INSERT test user", False, str(e))

        # ── Test 5: SELECT the test user back ──────────────────────────────
        try:
            row = conn.execute(text("SELECT id, username, email FROM users WHERE email = :e"),
                               {"e": TEST_EMAIL}).fetchone()
            check("SELECT test user back", row is not None,
                  f"id={row.id}, username={row.username}" if row else "No row returned")
            user_id = row.id if row else None
        except Exception as e:
            check("SELECT test user back", False, str(e))
            user_id = None

        # ── Test 6: INSERT a test item ──────────────────────────────────────
        item_id = None
        if user_id:
            try:
                r = conn.execute(text("""
                    INSERT INTO items (user_id, name, category, quantity, minimum_quantity,
                                      price, sku, created_at, updated_at)
                    VALUES (:uid, '_Test Item', 'Other', 99, 5, 1.23, '_TEST-SKU',
                            NOW(), NOW())
                    RETURNING id
                """), {"uid": user_id})
                conn.commit()
                item_id = r.fetchone()[0]
                check("INSERT test item", True, f"id={item_id}")
            except Exception as e:
                check("INSERT test item", False, str(e))
        else:
            check("INSERT test item", False, "Skipped — no user_id")

        # ── Test 7: SELECT test item back ───────────────────────────────────
        if item_id:
            try:
                row = conn.execute(text("SELECT id, name, quantity FROM items WHERE id = :id"),
                                   {"id": item_id}).fetchone()
                check("SELECT test item back", row is not None,
                      f"name={row.name}, qty={row.quantity}" if row else "No row")
            except Exception as e:
                check("SELECT test item back", False, str(e))

        # ── Test 8: INSERT stock transaction ────────────────────────────────
        tx_id = None
        if item_id and user_id:
            try:
                r = conn.execute(text("""
                    INSERT INTO stock_transactions (item_id, user_id, change, transaction_type, created_at)
                    VALUES (:iid, :uid, 10, 'Test Transaction', NOW())
                    RETURNING id
                """), {"iid": item_id, "uid": user_id})
                conn.commit()
                tx_id = r.fetchone()[0]
                check("INSERT stock_transaction", True, f"id={tx_id}")
            except Exception as e:
                check("INSERT stock_transaction", False, str(e))

        # ── Test 9: UPDATE item quantity ────────────────────────────────────
        if item_id:
            try:
                conn.execute(text("UPDATE items SET quantity = 42 WHERE id = :id"), {"id": item_id})
                conn.commit()
                updated = conn.execute(text("SELECT quantity FROM items WHERE id = :id"),
                                       {"id": item_id}).fetchone()
                check("UPDATE item quantity", updated and updated.quantity == 42,
                      f"quantity={updated.quantity if updated else '?'}")
            except Exception as e:
                check("UPDATE item quantity", False, str(e))

        # ── Test 10: Cascade DELETE (tx → item → user) ──────────────────────
        try:
            if tx_id:
                conn.execute(text("DELETE FROM stock_transactions WHERE id = :id"), {"id": tx_id})
            if item_id:
                conn.execute(text("DELETE FROM items WHERE id = :id"), {"id": item_id})
            if user_id:
                conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
            conn.commit()
            # Verify user gone
            gone = conn.execute(text("SELECT id FROM users WHERE id = :id"),
                                {"id": user_id}).fetchone()
            check("DELETE test data (cleanup)", gone is None, "Test rows removed cleanly")
        except Exception as e:
            check("DELETE test data (cleanup)", False, str(e))

        # ── Test 11: PostgreSQL SERIAL sequence working ─────────────────────
        try:
            r = conn.execute(text("""
                SELECT last_value FROM pg_sequences
                WHERE sequencename LIKE '%users%'
                LIMIT 1
            """)).fetchone()
            check("PostgreSQL SERIAL sequence accessible", r is not None,
                  f"last_value={r[0]}" if r else "No sequence found")
        except Exception as e:
            check("PostgreSQL SERIAL sequence accessible", False, str(e))

        conn.close()

        # ── Summary ─────────────────────────────────────────────────────────
        total  = len(results)
        passed = sum(1 for _, ok in results if ok)
        failed = total - passed

        print("\n" + "=" * 60)
        print(f"  Results:  {passed}/{total} passed   {'❌ ' + str(failed) + ' failed' if failed else '🎉 All passed!'}")
        print("=" * 60 + "\n")

        if failed:
            sys.exit(1)

if __name__ == "__main__":
    run()
