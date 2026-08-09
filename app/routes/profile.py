from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import User, Item
from app.forms.profile_forms import ChangePasswordForm, CurrencyPreferenceForm

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def index():
    """User profile details, currency preference, and password update page."""
    user = current_user._get_current_object()
    if not isinstance(user, User):
        user = db.session.get(User, current_user.id)

    password_form = ChangePasswordForm()
    currency_form = CurrencyPreferenceForm(currency=user.currency)

    form_type = request.form.get('form_type')

    if form_type == 'currency' and currency_form.validate_on_submit():
        user.currency = currency_form.currency.data
        db.session.commit()
        flash(f'Currency preference updated to {user.currency} ({user.currency_symbol}) successfully!', 'success')
        return redirect(url_for('profile.index'))

    if form_type == 'password' and password_form.validate_on_submit():
        user.set_password(password_form.new_password.data)
        db.session.commit()
        flash('Your password has been updated successfully!', 'success')
        return redirect(url_for('profile.index'))

    # User statistics overview
    total_items = Item.query.filter_by(user_id=user.id).count()

    return render_template(
        'profile/profile.html',
        password_form=password_form,
        currency_form=currency_form,
        user=user,
        total_items=total_items
    )
