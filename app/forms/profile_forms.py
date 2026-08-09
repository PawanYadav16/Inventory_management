from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from flask_login import current_user

CURRENCY_CHOICES = [
    ('INR', 'INR - Indian Rupee (₹)'),
    ('USD', 'USD - US Dollar ($)'),
    ('EUR', 'EUR - Euro (€)'),
    ('GBP', 'GBP - British Pound (£)')
]


class CurrencyPreferenceForm(FlaskForm):
    """Currency preference update form for user profile."""
    currency = SelectField('Preferred Currency', choices=CURRENCY_CHOICES, validators=[
        DataRequired(message="Please select a currency preference.")
    ])
    submit_currency = SubmitField('Save Preference')


class ChangePasswordForm(FlaskForm):
    """Password update form for user profile."""
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message="Current password is required.")
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(message="New password is required."),
        Length(min=6, message="New password must be at least 6 characters long.")
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message="Please confirm your new password."),
        EqualTo('new_password', message="New passwords must match exactly.")
    ])
    submit_password = SubmitField('Update Password')

    def validate_current_password(self, field):
        """Verify that current password is correct."""
        if not current_user.check_password(field.data):
            raise ValidationError('Incorrect current password. Please try again.')
