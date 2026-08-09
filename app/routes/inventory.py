from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import Item, StockTransaction
from app.forms import ItemForm

inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.route('/items/add', methods=['GET', 'POST'])
@login_required
def add_item():
    """Add a new inventory product."""
    form = ItemForm(user_id=current_user.id)
    if form.validate_on_submit():
        item = Item(
            user_id=current_user.id,
            name=form.name.data.strip(),
            description=form.description.data.strip() if form.description.data else None,
            category=form.category.data,
            quantity=form.quantity.data,
            minimum_quantity=form.minimum_quantity.data,
            price=float(form.price.data),
            supplier=form.supplier.data.strip() if form.supplier.data else None,
            sku=form.sku.data.strip().upper(),
            location=form.location.data.strip() if form.location.data else None
        )
        db.session.add(item)
        db.session.commit()

        # Record initial stock transaction
        transaction = StockTransaction(
            item_id=item.id,
            user_id=current_user.id,
            change=item.quantity,
            transaction_type='Initial Stock'
        )
        db.session.add(transaction)
        db.session.commit()

        flash(f'Product "{item.name}" added to inventory successfully!', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('inventory/add_item.html', form=form)


@inventory_bp.route('/items/<int:item_id>')
@login_required
def item_detail(item_id):
    """View details of a specific inventory item."""
    item = db.session.get(Item, item_id)
    if item is None:
        abort(404)

    # Enforce strict user data ownership
    if item.user_id != current_user.id:
        abort(403)

    return render_template('inventory/item_detail.html', item=item)


@inventory_bp.route('/items/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    """Edit an existing inventory item."""
    item = db.session.get(Item, item_id)
    if item is None:
        abort(404)

    # Enforce strict user data ownership
    if item.user_id != current_user.id:
        abort(403)

    form = ItemForm(user_id=current_user.id, item_id=item.id, obj=item)

    if form.validate_on_submit():
        old_quantity = item.quantity

        # Update item attributes
        item.name = form.name.data.strip()
        item.description = form.description.data.strip() if form.description.data else None
        item.category = form.category.data
        item.quantity = form.quantity.data
        item.minimum_quantity = form.minimum_quantity.data
        item.price = float(form.price.data)
        item.supplier = form.supplier.data.strip() if form.supplier.data else None
        item.sku = form.sku.data.strip().upper()
        item.location = form.location.data.strip() if form.location.data else None

        new_quantity = item.quantity

        # Check if quantity changed during manual edit and log StockTransaction
        if old_quantity != new_quantity:
            diff = new_quantity - old_quantity
            trans_type = "Manual Adjustment"
            transaction = StockTransaction(
                item_id=item.id,
                user_id=current_user.id,
                change=diff,
                transaction_type=trans_type
            )
            db.session.add(transaction)

        db.session.commit()
        flash(f'Product "{item.name}" updated successfully!', 'success')
        return redirect(url_for('inventory.item_detail', item_id=item.id))

    return render_template('inventory/edit_item.html', form=form, item=item)


@inventory_bp.route('/items/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    """Delete an inventory item securely scoped to the current user."""
    item = Item.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    item_name = item.name

    # Explicitly delete related stock transaction audit records first
    StockTransaction.query.filter_by(item_id=item.id, user_id=current_user.id).delete(synchronize_session=False)

    # Perform full database record deletion
    db.session.delete(item)
    db.session.commit()

    flash(f'Product "{item_name}" has been deleted from your inventory.', 'success')
    return redirect(url_for('dashboard.index'))


@inventory_bp.route('/items/<int:item_id>/adjust-quantity', methods=['POST'])
@login_required
def adjust_quantity(item_id):
    """Increase (+1) or decrease (-1) product quantity via standard POST request."""
    item = db.session.get(Item, item_id)
    if item is None:
        abort(404)

    # Enforce strict user data ownership
    if item.user_id != current_user.id:
        abort(403)

    action = request.form.get('action')

    if action == 'increase':
        item.quantity += 1
        transaction = StockTransaction(
            item_id=item.id,
            user_id=current_user.id,
            change=1,
            transaction_type='Stock Added'
        )
        db.session.add(transaction)
        db.session.commit()
        flash(f'Increased quantity for "{item.name}" to {item.quantity}.', 'success')
    elif action == 'decrease':
        if item.quantity > 0:
            item.quantity -= 1
            transaction = StockTransaction(
                item_id=item.id,
                user_id=current_user.id,
                change=-1,
                transaction_type='Stock Removed'
            )
            db.session.add(transaction)
            db.session.commit()
            flash(f'Decreased quantity for "{item.name}" to {item.quantity}.', 'info')
        else:
            flash(f'Quantity for "{item.name}" is already 0 and cannot be negative.', 'warning')
    else:
        flash('Invalid action requested.', 'danger')

    # Return redirect to previous page or dashboard
    next_url = request.referrer or url_for('dashboard.index')
    return redirect(next_url)


@inventory_bp.route('/items/<int:item_id>/history')
@login_required
def stock_history(item_id):
    """View stock change audit history for a specific item."""
    item = db.session.get(Item, item_id)
    if item is None:
        abort(404)

    # Enforce strict user data ownership
    if item.user_id != current_user.id:
        abort(403)

    transactions = StockTransaction.query.filter_by(
        item_id=item.id,
        user_id=current_user.id
    ).order_by(StockTransaction.created_at.desc()).all()

    return render_template('inventory/stock_history.html', item=item, transactions=transactions)
