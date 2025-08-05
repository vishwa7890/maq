"""cleanup_chat_sessions

Revision ID: ac434985c1ec
Revises: e74d54a3c583
Create Date: 2025-07-20 15:54:02.577307

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ac434985c1ec'
down_revision: Union[str, Sequence[str], None] = 'e74d54a3c583'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
