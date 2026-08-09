"""
Seed script: populates realistic edge-case inventory data for
  pawanyadav852768@gmail.com / System@26

Edge cases covered:
  1. Out of Stock          – quantity == 0
  2. Low Stock (boundary)  – quantity == minimum_quantity (exactly at limit)
  3. Low Stock (below)     – quantity < minimum_quantity
  4. In Stock              – quantity > minimum_quantity (normal)
  5. Very High Quantity    – tests large number rendering
  6. Zero minimum_quantity – anything > 0 is "In Stock"
  7. Zero price            – free / donated item
  8. Very high price       – expensive equipment
  9. Fractional price      – decimal precision
  10. No description        – nullable field left NULL
  11. No location           – nullable field left NULL
  12. No supplier           – nullable field left NULL
  13. Long product name     – UI truncation test
  14. Special characters in name/description
  15. Multiple categories   – Electronics, Furniture, Clothing, Food, Other, Tools
  16. Rich transaction history per item (audit trail)
"""

import sys
import os

# Resolve project root and load app
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models import User, Item, StockTransaction
from datetime import datetime, timedelta

app = create_app()

EMAIL    = "pawanyadav852768@gmail.com"
PASSWORD = "System@26"

SEED_ITEMS = [
    # 1. OUT OF STOCK: quantity == 0
    {
        "name": "Wireless Bluetooth Headphones",
        "description": "Premium over-ear noise-cancelling headphones. Compatible with all Bluetooth 5.0 devices.",
        "category": "Electronics",
        "sku": "ELEC-BT-001",
        "quantity": 0,
        "minimum_quantity": 5,
        "price": 2499.00,
        "supplier": "SoundWave India Pvt Ltd",
        "location": "Shelf A1",
        "days_ago": 30,
        "transactions": [
            {"change": +50, "type": "Initial Stock",      "days_ago": 30},
            {"change": -25, "type": "Stock Removed",      "days_ago": 20},
            {"change": -25, "type": "Stock Removed",      "days_ago": 5},
        ],
    },
    # 2. LOW STOCK boundary: quantity == minimum_quantity
    {
        "name": "USB-C Fast Charger 65W",
        "description": "65W GaN USB-C charger. Supports PD 3.0 and QC 4.0.",
        "category": "Electronics",
        "sku": "ELEC-USBC-002",
        "quantity": 5,
        "minimum_quantity": 5,
        "price": 849.99,
        "supplier": "PowerHub Electronics",
        "location": "Shelf A2",
        "days_ago": 25,
        "transactions": [
            {"change": +30, "type": "Initial Stock",      "days_ago": 25},
            {"change": -10, "type": "Stock Removed",      "days_ago": 15},
            {"change": -15, "type": "Stock Removed",      "days_ago": 8},
        ],
    },
    # 3. LOW STOCK: quantity < minimum_quantity, NULL description + NULL location
    {
        "name": "AA Alkaline Batteries (Pack of 4)",
        "description": None,
        "category": "Electronics",
        "sku": "ELEC-BAT-003",
        "quantity": 2,
        "minimum_quantity": 10,
        "price": 120.00,
        "supplier": "Duracell India",
        "location": None,
        "days_ago": 20,
        "transactions": [
            {"change": +100, "type": "Initial Stock",     "days_ago": 20},
            {"change": -50,  "type": "Stock Removed",     "days_ago": 12},
            {"change": -30,  "type": "Stock Removed",     "days_ago": 7},
            {"change": -18,  "type": "Manual Adjustment", "days_ago": 2},
        ],
    },
    # 4. IN STOCK: healthy quantity
    {
        "name": "Ergonomic Office Chair",
        "description": "Lumbar-support mesh chair with adjustable armrests and tilt lock. 5-year warranty.",
        "category": "Furniture",
        "sku": "FURN-CHAIR-001",
        "quantity": 42,
        "minimum_quantity": 10,
        "price": 12999.00,
        "supplier": "ComfortSeating Co.",
        "location": "Warehouse B - Row 3",
        "days_ago": 60,
        "transactions": [
            {"change": +50, "type": "Initial Stock",      "days_ago": 60},
            {"change": +20, "type": "Stock Added",        "days_ago": 30},
            {"change": -28, "type": "Stock Removed",      "days_ago": 10},
        ],
    },
    # 5. VERY HIGH QUANTITY
    {
        "name": "A4 Copy Paper Ream 500 Sheets",
        "description": "80 GSM bright white A4 paper. Suitable for laser and inkjet printers.",
        "category": "Other",
        "sku": "OFFC-PAPER-001",
        "quantity": 9999,
        "minimum_quantity": 100,
        "price": 350.00,
        "supplier": "PaperMart Wholesale",
        "location": "Store Room C - Pallet 7",
        "days_ago": 90,
        "transactions": [
            {"change": +10000, "type": "Initial Stock",   "days_ago": 90},
            {"change":    -1,  "type": "Stock Removed",   "days_ago": 45},
        ],
    },
    # 6. ZERO minimum_quantity (qty=1 still shows In Stock)
    {
        "name": "Promotional Flyers Custom Print",
        "description": "Single-sided A5 glossy flyers for marketing events.",
        "category": "Other",
        "sku": "MKTG-FLYER-001",
        "quantity": 1,
        "minimum_quantity": 0,
        "price": 2.50,
        "supplier": None,
        "location": "Marketing Desk",
        "days_ago": 10,
        "transactions": [
            {"change": +500, "type": "Initial Stock",     "days_ago": 10},
            {"change": -499, "type": "Stock Removed",     "days_ago": 3},
        ],
    },
    # 7. ZERO PRICE (free item)
    {
        "name": "Employee Feedback Forms",
        "description": "Printed A4 feedback forms for quarterly reviews.",
        "category": "Other",
        "sku": "HR-FORM-001",
        "quantity": 200,
        "minimum_quantity": 50,
        "price": 0.00,
        "supplier": "Internal Printing",
        "location": "HR Cabinet 2",
        "days_ago": 14,
        "transactions": [
            {"change": +200, "type": "Initial Stock",     "days_ago": 14},
        ],
    },
    # 8. VERY HIGH PRICE
    {
        "name": "Industrial CNC Router Machine",
        "description": "4-axis CNC router with 1500x1000mm work area. 3kW spindle, water-cooled.",
        "category": "Tools",
        "sku": "TOOL-CNC-001",
        "quantity": 2,
        "minimum_quantity": 1,
        "price": 875000.00,
        "supplier": "PrecisionTech Machinery",
        "location": "Factory Floor - Bay 1",
        "days_ago": 180,
        "transactions": [
            {"change": +3, "type": "Initial Stock",       "days_ago": 180},
            {"change": -1, "type": "Stock Removed",       "days_ago": 90},
        ],
    },
    # 9. FRACTIONAL PRICE
    {
        "name": "Ballpoint Pen Blue Box of 10",
        "description": "Smooth-writing 0.7mm ballpoint pens. Water-resistant ink.",
        "category": "Other",
        "sku": "OFFC-PEN-001",
        "quantity": 87,
        "minimum_quantity": 20,
        "price": 49.99,
        "supplier": "OfficeSupply Hub",
        "location": "Stationery Rack 1",
        "days_ago": 45,
        "transactions": [
            {"change": +100, "type": "Initial Stock",     "days_ago": 45},
            {"change":  -13, "type": "Stock Removed",     "days_ago": 20},
        ],
    },
    # 10. LONG PRODUCT NAME
    {
        "name": "Heavy-Duty Adjustable Industrial Steel Shelving Unit With Locking Wheels and Anti-Rust Coating",
        "description": "5-tier industrial shelving. Each shelf rated to 300kg. Easy assembly.",
        "category": "Furniture",
        "sku": "FURN-SHELF-001",
        "quantity": 15,
        "minimum_quantity": 5,
        "price": 6499.50,
        "supplier": "MetalWorks India",
        "location": "Warehouse A - Zone 4",
        "days_ago": 50,
        "transactions": [
            {"change": +20, "type": "Initial Stock",      "days_ago": 50},
            {"change":  -5, "type": "Stock Removed",      "days_ago": 25},
        ],
    },
    # 11. SPECIAL CHARACTERS in name and description
    {
        "name": "Safety Goggles Anti-Fog and UV Protected 200 pcs",
        "description": "CE certified. 99.9% UV protection. Adjustable strap. Ideal for labs & construction sites.",
        "category": "Tools",
        "sku": "SAFE-GOGL-001",
        "quantity": 120,
        "minimum_quantity": 25,
        "price": 189.00,
        "supplier": "SafeGuard Supplies",
        "location": None,
        "days_ago": 35,
        "transactions": [
            {"change": +200, "type": "Initial Stock",     "days_ago": 35},
            {"change":  -80, "type": "Stock Removed",     "days_ago": 15},
        ],
    },
    # 12. CLOTHING CATEGORY
    {
        "name": "Corporate Logo T-Shirt Size L",
        "description": "100% cotton round-neck t-shirt with embroidered company logo. Navy Blue.",
        "category": "Clothing",
        "sku": "CLTH-TSHRT-001",
        "quantity": 60,
        "minimum_quantity": 15,
        "price": 349.00,
        "supplier": "BrandWear Apparel",
        "location": "Apparel Storage - Rack 3",
        "days_ago": 28,
        "transactions": [
            {"change": +100, "type": "Initial Stock",     "days_ago": 28},
            {"change":  -40, "type": "Stock Removed",     "days_ago": 10},
        ],
    },
    # 13. FOOD CATEGORY - Low Stock
    {
        "name": "Instant Coffee Sachets Nescafe Classic Box 50",
        "description": "Premium instant coffee sachets for office pantry use. Best before: Dec 2026.",
        "category": "Food",
        "sku": "FOOD-COFFEE-001",
        "quantity": 3,
        "minimum_quantity": 10,
        "price": 425.00,
        "supplier": "Nestle India",
        "location": "Pantry Cabinet 1",
        "days_ago": 15,
        "transactions": [
            {"change": +20, "type": "Initial Stock",      "days_ago": 15},
            {"change": -17, "type": "Stock Removed",      "days_ago": 5},
        ],
    },
    # 14. OUT OF STOCK in Clothing category
    {
        "name": "Safety Vest High-Visibility Yellow Size M",
        "description": "EN ISO 20471 certified high-visibility vest for site workers.",
        "category": "Clothing",
        "sku": "CLTH-VEST-001",
        "quantity": 0,
        "minimum_quantity": 10,
        "price": 299.00,
        "supplier": "SafeGuard Supplies",
        "location": "Safety Equipment Room",
        "days_ago": 40,
        "transactions": [
            {"change": +30, "type": "Initial Stock",      "days_ago": 40},
            {"change": -30, "type": "Stock Removed",      "days_ago": 12},
        ],
    },
    # 15. ALL NULLABLE FIELDS NULL (description=None, supplier=None, location=None)
    {
        "name": "Spare Laptop Charger 45W",
        "description": None,
        "category": "Electronics",
        "sku": "ELEC-CHRG-004",
        "quantity": 8,
        "minimum_quantity": 3,
        "price": 1199.00,
        "supplier": None,
        "location": None,
        "days_ago": 7,
        "transactions": [
            {"change": +10, "type": "Initial Stock",      "days_ago": 7},
            {"change":  -2, "type": "Manual Adjustment",  "days_ago": 2},
        ],
    },
]


def run():
    with app.app_context():
        user = User.query.filter_by(email=EMAIL).first()
        if not user:
            print(f"[SEED] User {EMAIL!r} not found. Creating...")
            user = User(username="pawanyadav", email=EMAIL, currency="INR")
            user.set_password(PASSWORD)
            db.session.add(user)
            db.session.commit()
            print(f"[SEED] Created user id={user.id}")
        else:
            print(f"[SEED] Found user id={user.id}  ({user.email})")

        existing_skus = {
            item.sku for item in Item.query.filter_by(user_id=user.id).all()
        }

        added = skipped = 0
        for spec in SEED_ITEMS:
            if spec["sku"] in existing_skus:
                print(f"[SEED]  SKIP  {spec['sku']} – already exists")
                skipped += 1
                continue

            created_at = datetime.utcnow() - timedelta(days=spec["days_ago"])
            item = Item(
                user_id=user.id,
                name=spec["name"],
                description=spec.get("description"),
                category=spec["category"],
                sku=spec["sku"],
                quantity=spec["quantity"],
                minimum_quantity=spec["minimum_quantity"],
                price=spec["price"],
                supplier=spec.get("supplier"),
                location=spec.get("location"),
                created_at=created_at,
                updated_at=created_at,
            )
            db.session.add(item)
            db.session.flush()

            for tx in spec["transactions"]:
                tx_time = datetime.utcnow() - timedelta(days=tx["days_ago"])
                db.session.add(StockTransaction(
                    item_id=item.id,
                    user_id=user.id,
                    change=tx["change"],
                    transaction_type=tx["type"],
                    created_at=tx_time,
                ))

            db.session.commit()
            status = (
                "Out of Stock" if spec["quantity"] == 0
                else "Low Stock"  if spec["quantity"] <= spec["minimum_quantity"]
                else "In Stock"
            )
            print(f"[SEED]  ADD   {spec['sku']:25s}  {status:14s}  "
                  f"qty={spec['quantity']:>5}  price={spec['price']:>10,.2f}")
            added += 1

        total = Item.query.filter_by(user_id=user.id).count()
        print(f"\n[SEED] Done — {added} added, {skipped} skipped. "
              f"Total items for account: {total}")


if __name__ == "__main__":
    run()
