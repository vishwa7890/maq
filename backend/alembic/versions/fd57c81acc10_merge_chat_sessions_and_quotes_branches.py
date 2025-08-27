"""merge_chat_sessions_and_quotes_branches

Revision ID: fd57c81acc10
Revises: 17ed44d0fe66, add_quotes_used
Create Date: 2025-08-27 20:01:03.126165

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fd57c81acc10'
down_revision: Union[str, Sequence[str], None] = ('17ed44d0fe66', 'add_quotes_used')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
