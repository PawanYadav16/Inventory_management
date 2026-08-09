from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import func, or_
from app import db
from app.models import Item

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def home():
    """Public landing home page."""
    return render_template('home.html')


@dashboard_bp.route('/dashboard')
@login_required
def index():
    """Authenticated user inventory dashboard."""
    user_id = current_user.id

    # Summary Statistics
    total_products = Item.query.filter_by(user_id=user_id).count()
    total_quantity = db.session.query(func.sum(Item.quantity)).filter(Item.user_id == user_id).scalar() or 0
    low_stock_count = Item.query.filter(Item.user_id == user_id, Item.quantity > 0, Item.quantity <= Item.minimum_quantity).count()
    out_of_stock_count = Item.query.filter(Item.user_id == user_id, Item.quantity == 0).count()
    
    # Dynamic distinct categories owned by current user
    user_categories_raw = db.session.query(Item.category).filter(Item.user_id == user_id).distinct().all()
    user_categories = sorted(list(set([c[0] for c in user_categories_raw if c[0]] + ['Electronics', 'Stationery', 'Furniture', 'Clothing', 'Other'])))
    category_count = len(set([c[0] for c in user_categories_raw if c[0]]))

    # Search, Filter, and Sort URL Parameters
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', 'All').strip()
    status_filter = request.args.get('status', 'All').strip()
    sort_by = request.args.get('sort', 'name_asc').strip()

    # Base query restricted strictly to logged-in user
    query = Item.query.filter(Item.user_id == user_id)

    # Apply Search Filter (by Item Name or SKU)
    if search_query:
        query = query.filter(
            or_(
                Item.name.ilike(f'%{search_query}%'),
                Item.sku.ilike(f'%{search_query}%')
            )
        )

    # Apply Category Filter
    if category_filter and category_filter != 'All':
        query = query.filter(Item.category == category_filter)

    # Apply Stock Status Filter
    if status_filter and status_filter != 'All':
        if status_filter == 'Out of Stock':
            query = query.filter(Item.quantity == 0)
        elif status_filter == 'Low Stock':
            query = query.filter(Item.quantity > 0, Item.quantity <= Item.minimum_quantity)
        elif status_filter == 'In Stock':
            query = query.filter(Item.quantity > Item.minimum_quantity)

    # Apply Sorting
    if sort_by == 'name_desc':
        query = query.order_by(Item.name.desc())
    elif sort_by == 'qty_asc':
        query = query.order_by(Item.quantity.asc())
    elif sort_by == 'qty_desc':
        query = query.order_by(Item.quantity.desc())
    elif sort_by == 'price_asc':
        query = query.order_by(Item.price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Item.price.desc())
    else:  # Default to Name A-Z
        query = query.order_by(Item.name.asc())

    items = query.all()

    return render_template(
        'dashboard/index.html',
        items=items,
        total_products=total_products,
        total_quantity=total_quantity,
        low_stock_count=low_stock_count,
        out_of_stock_count=out_of_stock_count,
        category_count=category_count,
        user_categories=user_categories,
        search_query=search_query,
        category_filter=category_filter,
        status_filter=status_filter,
        sort_by=sort_by
    )
