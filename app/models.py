from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login user loader callback."""
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    """User model for authentication and data ownership."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    currency = db.Column(db.String(10), nullable=False, default='INR')

    # Relationships
    items = db.relationship('Item', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    transactions = db.relationship('StockTransaction', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def currency_symbol(self):
        """Get the symbol corresponding to user's currency preference."""
        symbols = {'INR': '₹', 'USD': '$', 'EUR': '€', 'GBP': '£'}
        return symbols.get(self.currency, '₹')

    def set_password(self, password):
        """Securely hash and store user password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify user password against stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Item(db.Model):
    """Inventory item model."""
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False, index=True, default='Other')
    quantity = db.Column(db.Integer, nullable=False, default=0)
    minimum_quantity = db.Column(db.Integer, nullable=False, default=5)
    price = db.Column(db.Float, nullable=False, default=0.0)
    supplier = db.Column(db.String(100), nullable=True)
    sku = db.Column(db.String(64), nullable=False, index=True)
    location = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    transactions = db.relationship('StockTransaction', backref='item', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def stock_status(self):
        """Calculate dynamic stock status according to business rules."""
        if self.quantity == 0:
            return 'Out of Stock'
        elif self.quantity <= self.minimum_quantity:
            return 'Low Stock'
        else:
            return 'In Stock'

    @property
    def total_value(self):
        """Calculate total inventory value for this item."""
        return round(self.quantity * self.price, 2)

    def __repr__(self):
        return f'<Item {self.name} (SKU: {self.sku})>'


class StockTransaction(db.Model):
    """Stock audit trail model for logging quantity changes."""
    __tablename__ = 'stock_transactions'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    change = db.Column(db.Integer, nullable=False)  # Positive for addition, negative for reduction
    transaction_type = db.Column(db.String(50), nullable=False)  # e.g., 'Stock Added', 'Stock Removed', 'Initial Stock', 'Manual Adjustment'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<StockTransaction Item:{self.item_id} Change:{self.change:+d} Type:{self.transaction_type}>'
