import os
from app import create_app, db
from app.models import User, Item, StockTransaction
from migrate_db import run_database_migrations

app = create_app()


@app.shell_context_processor
def make_shell_context():
    """Register models for flask shell context."""
    return {
        'db': db,
        'User': User,
        'Item': Item,
        'StockTransaction': StockTransaction
    }


if __name__ == '__main__':
    # Ensure database migrations are applied to existing database
    run_database_migrations()

    print("==================================================")
    print(" Inventory Management System starting locally...")
    print(" Access URL: http://127.0.0.1:5000/")
    print("==================================================")

    app.run(debug=True, host='127.0.0.1', port=5000)
