from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, DecimalField, SelectField, SubmitField
from wtforms.validators import DataRequired, InputRequired, Optional, Length, NumberRange, ValidationError
from app.models import Item


CATEGORY_CHOICES = [
    ('Electronics', 'Electronics'),
    ('Stationery', 'Stationery'),
    ('Furniture', 'Furniture'),
    ('Clothing', 'Clothing'),
    ('Other', 'Other')
]


class ItemForm(FlaskForm):
    """Inventory item creation and edit form."""
    name = StringField('Product Name', validators=[
        DataRequired(message="Product name is required."),
        Length(min=2, max=100, message="Product name must be between 2 and 100 characters.")
    ])
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=500, message="Description cannot exceed 500 characters.")
    ])
    category = SelectField('Category', choices=CATEGORY_CHOICES, validators=[
        DataRequired(message="Please select a category.")
    ])
    quantity = IntegerField('Quantity', validators=[
        NumberRange(min=0, message="Quantity cannot be negative. (0 is allowed for Out of Stock items).")
    ], default=0)
    minimum_quantity = IntegerField('Minimum Alert Quantity', validators=[
        NumberRange(min=0, message="Minimum quantity cannot be negative.")
    ], default=5)
    price = DecimalField('Unit Price', validators=[
        NumberRange(min=0.0, message="Price cannot be negative.")
    ], places=2, default=0.00)
    supplier = StringField('Supplier', validators=[
        Optional(),
        Length(max=100, message="Supplier name cannot exceed 100 characters.")
    ])
    sku = StringField('SKU / Product Code', validators=[
        DataRequired(message="SKU is required."),
        Length(min=2, max=64, message="SKU must be between 2 and 64 characters.")
    ])
    location = StringField('Storage Location', validators=[
        Optional(),
        Length(max=100, message="Location cannot exceed 100 characters.")
    ])
    submit = SubmitField('Save Inventory Item')

    def __init__(self, *args, user_id=None, item_id=None, **kwargs):
        super(ItemForm, self).__init__(*args, **kwargs)
        self.user_id = user_id
        self.item_id = item_id

    def validate_sku(self, field):
        """Validate that SKU is unique for the logged-in user."""
        if not self.user_id:
            return
        
        sku_clean = field.data.strip().upper()
        query = Item.query.filter_by(user_id=self.user_id, sku=sku_clean)
        
        if self.item_id:
            query = query.filter(Item.id != self.item_id)
            
        existing_item = query.first()
        if existing_item:
            raise ValidationError(f'You already have an item with SKU "{sku_clean}". SKUs must be unique within your inventory.')
