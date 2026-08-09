import os
from app import create_app, db
from app.models import User, Item, StockTransaction
from migrate_db import run_database_migrations

app = create_app()


def initialize_database(seed_sample_data=True):
    """Initialize database tables, apply migrations, and optionally populate demo sample data."""
    # Ensure database migrations are applied first
    run_database_migrations()

    with app.app_context():
        print("Ensuring database tables exist...")
        db.create_all()

        if seed_sample_data:
            # Check if any user exists
            if User.query.count() == 0:
                print("Seeding sample user and inventory data...")
                
                # Create demo user
                demo_user = User(username="demouser", email="demo@example.com", currency="INR")
                demo_user.set_password("password123")
                db.session.add(demo_user)
                db.session.commit()

                # Add sample products for demouser
                items = [
                    Item(
                        user_id=demo_user.id,
                        name="Dell XPS 15 Laptop",
                        description="High-performance 15-inch laptop with 32GB RAM and 1TB SSD.",
                        category="Electronics",
                        quantity=12,
                        minimum_quantity=5,
                        price=1499.99,
                        supplier="Dell Technologies",
                        sku="ELE-XPS15",
                        location="Warehouse A, Shelf 1"
                    ),
                    Item(
                        user_id=demo_user.id,
                        name="Ergonomic Mesh Office Chair",
                        description="Adjustable lumbar support ergonomic swivel chair.",
                        category="Furniture",
                        quantity=3,
                        minimum_quantity=5,
                        price=249.50,
                        supplier="Office Comfort Inc.",
                        sku="FUR-CHR01",
                        location="Warehouse B, Rack 3"
                    ),
                    Item(
                        user_id=demo_user.id,
                        name="A4 Multipurpose Copy Paper",
                        description="80gsm white printing paper ream (500 sheets).",
                        category="Stationery",
                        quantity=0,
                        minimum_quantity=10,
                        price=6.99,
                        supplier="PaperCraft Supplies",
                        sku="STA-PPR01",
                        location="Storage Room 2"
                    ),
                    Item(
                        user_id=demo_user.id,
                        name="Wireless Noise-Canceling Headphones",
                        description="Over-ear Bluetooth headphones with 30-hour battery life.",
                        category="Electronics",
                        quantity=25,
                        minimum_quantity=8,
                        price=129.99,
                        supplier="AudioSound Co.",
                        sku="ELE-AUD05",
                        location="Warehouse A, Shelf 4"
                    )
                ]

                for item in items:
                    db.session.add(item)
                    db.session.commit()

                    # Add initial stock transaction record
                    trans = StockTransaction(
                        item_id=item.id,
                        user_id=demo_user.id,
                        change=item.quantity,
                        transaction_type="Initial Stock"
                    )
                    db.session.add(trans)
                
                db.session.commit()
                print(f"Sample data created! Demo login -> Email: demo@example.com | Password: password123")
            else:
                print("Database already contains data.")

        print("Database initialization complete.")


if __name__ == '__main__':
    initialize_database(seed_sample_data=True)
