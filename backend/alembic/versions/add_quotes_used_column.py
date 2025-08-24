"""Add quotes_used column to users table

Revision ID: add_quotes_used
Revises: f1a2b3c4d5e6
Create Date: 2024-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_quotes_used'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None

def upgrade():
    # Add quotes_used column to users table
    op.add_column('users', sa.Column('quotes_used', sa.Integer(), nullable=False, server_default='0'))

def downgrade():
    # Remove quotes_used column from users table
    op.drop_column('users', 'quotes_used')