"""add_session_uuid_column

Revision ID: a8f3a8b54e81
Revises: 2c9123594bb1
Create Date: 2025-08-05 09:58:36.293872

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'a8f3a8b54e81'
down_revision: Union[str, Sequence[str], None] = '2c9123594bb1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add session_uuid as nullable first
    op.add_column('chat_sessions', sa.Column('session_uuid', sa.String(length=36), nullable=True))
    
    # Generate UUIDs for existing sessions
    conn = op.get_bind()
    sessions = conn.execute(text("SELECT id FROM chat_sessions")).fetchall()
    for session in sessions:
        conn.execute(
            text("UPDATE chat_sessions SET session_uuid = :uuid WHERE id = :id"),
            {'uuid': str(uuid.uuid4()), 'id': session[0]}
        )
    
    # Now alter the column to be NOT NULL and add unique constraint
    op.alter_column('chat_sessions', 'session_uuid', nullable=False)
    op.create_unique_constraint('uq_chat_sessions_session_uuid', 'chat_sessions', ['session_uuid'])
    
    # Create index for better query performance
    op.create_index('ix_chat_sessions_session_uuid', 'chat_sessions', ['session_uuid'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the index and constraint first
    op.drop_index('ix_chat_sessions_session_uuid', table_name='chat_sessions')
    op.drop_constraint('uq_chat_sessions_session_uuid', 'chat_sessions', type_='unique')
    
    # Then drop the column
    op.drop_column('chat_sessions', 'session_uuid')
