"""add_role_to_users

Revision ID: f1a2b3c4d5e6
Revises: eb4c3129a20c
Create Date: 2025-08-24 06:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'eb4c3129a20c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add role column with default and index."""
    # Add column with server_default to backfill existing rows
    op.add_column('users', sa.Column('role', sa.String(length=20), nullable=False, server_default='normal'))
    # Create an index on role for quick filtering
    op.create_index('ix_users_role', 'users', ['role'], unique=False)
    # Optionally drop the server_default after backfill so future inserts use app default
    op.alter_column('users', 'role', server_default=None)


def downgrade() -> None:
    """Downgrade schema: remove role column and its index."""
    op.drop_index('ix_users_role', table_name='users')
    op.drop_column('users', 'role')
