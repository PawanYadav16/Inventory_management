"""Add currency column to User model

Revision ID: 002_add_user_currency
Revises: 001_initial_schema
Create Date: 2026-08-09 23:39:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_user_currency'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('currency', sa.String(length=10), nullable=False, server_default='INR'))


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('currency')
