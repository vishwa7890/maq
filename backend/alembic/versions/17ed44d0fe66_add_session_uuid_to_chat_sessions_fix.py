"""add_session_uuid_to_chat_sessions_fix

Revision ID: 17ed44d0fe66
Revises: a8f3a8b54e81
Create Date: 2025-08-05 10:04:13.076603

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '17ed44d0fe66'
down_revision: Union[str, Sequence[str], None] = 'a8f3a8b54e81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if the column already exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('chat_sessions')]
    
    if 'session_uuid' not in columns:
        # Add the session_uuid column
        op.add_column('chat_sessions', sa.Column('session_uuid', sa.String(length=36), nullable=True))
        
        # Generate UUIDs for existing sessions
        sessions = conn.execute(sa.text("SELECT id FROM chat_sessions")).fetchall()
        for session in sessions:
            conn.execute(
                sa.text("UPDATE chat_sessions SET session_uuid = :uuid WHERE id = :id"),
                {'uuid': str(sa.text("gen_random_uuid()")), 'id': session[0]}
            )
        
        # Make the column NOT NULL after populating it
        op.alter_column('chat_sessions', 'session_uuid', nullable=False)
        
        # Create a unique index on session_uuid
        op.create_index('ix_chat_sessions_session_uuid', 'chat_sessions', ['session_uuid'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the index and column
    op.drop_index('ix_chat_sessions_session_uuid', table_name='chat_sessions')
    op.drop_column('chat_sessions', 'session_uuid')
