from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models import Item

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/analytics')
@login_required
def index():
    """Analytics page showing metrics, charts, and breakdown of user inventory."""
    user_id = current_user.id

    items = Item.query.filter_by(user_id=user_id).all()

    total_products = len(items)
    total_quantity = sum(item.quantity for item in items)
    total_valuation = round(sum(item.quantity * item.price for item in items), 2)

    in_stock_count = sum(1 for item in items if item.quantity > item.minimum_quantity)
    low_stock_count = sum(1 for item in items if 0 < item.quantity <= item.minimum_quantity)
    out_of_stock_count = sum(1 for item in items if item.quantity == 0)

    # Category breakdown metrics
    category_summary = {}
    for item in items:
        cat = item.category or 'Other'
        if cat not in category_summary:
            category_summary[cat] = {'count': 0, 'total_qty': 0, 'total_value': 0.0}
        category_summary[cat]['count'] += 1
        category_summary[cat]['total_qty'] += item.quantity
        category_summary[cat]['total_value'] += round(item.quantity * item.price, 2)

    # Top items by quantity
    top_highest_stock = sorted(items, key=lambda x: x.quantity, reverse=True)[:5]
    top_lowest_stock = sorted(items, key=lambda x: x.quantity)[:5]

    return render_template(
        'analytics/analytics.html',
        total_products=total_products,
        total_quantity=total_quantity,
        total_valuation=total_valuation,
        in_stock_count=in_stock_count,
        low_stock_count=low_stock_count,
        out_of_stock_count=out_of_stock_count,
        category_count=len(category_summary),
        category_summary=category_summary,
        top_highest_stock=top_highest_stock,
        top_lowest_stock=top_lowest_stock
    )
