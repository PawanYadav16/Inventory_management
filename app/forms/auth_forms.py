from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp, ValidationError
from app.models import User


class RegistrationForm(FlaskForm):
    """User registration form with validations."""
    username = StringField('Username', validators=[
        DataRequired(message="Username is required."),
        Length(min=3, max=64, message="Username must be between 3 and 64 characters."),
        Regexp(r'^[A-Za-z0-9_]+$', message="Username must contain only letters, numbers, and underscores.")
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message="Email address is required."),
        Email(message="Please enter a valid email address."),
        Length(max=120, message="Email must not exceed 120 characters.")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required."),
        Length(min=6, message="Password must be at least 6 characters long.")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password."),
        EqualTo('password', message="Passwords must match exactly.")
    ])
    submit = SubmitField('Create Account')

    def validate_username(self, field):
        """Ensure username is unique."""
        if User.query.filter_by(username=field.data.strip()).first():
            raise ValidationError('This username is already taken. Please choose a different one.')

    def validate_email(self, field):
        """Ensure email is unique."""
        if User.query.filter_by(email=field.data.strip().lower()).first():
            raise ValidationError('An account with this email address already exists.')


class LoginForm(FlaskForm):
    """User login form."""
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required."),
        Email(message="Please enter a valid email address.")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required.")
    ])
    submit = SubmitField('Sign In')
