"""add_conversations_and_messages

Revision ID: 319f8335a997
Revises: ec9f5f8b6d16
Create Date: 2026-11-12 13:12:27.488728

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '319f8335a997'
down_revision: Union[str, Sequence[str], None] = 'ec9f5f8b6d16'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema idempotently."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = set(inspector.get_table_names())

    if 'conversations' not in tables:
        op.create_table(
            'conversations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('resident_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('title', sa.String(length=200), nullable=True),
            sa.Column('status', sa.String(length=30), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('extra_metadata', sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(['resident_id'], ['residents.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('conversations', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_conversations_id'), ['id'], unique=False)
            batch_op.create_index(batch_op.f('ix_conversations_resident_id'), ['resident_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_conversations_status'), ['status'], unique=False)
            batch_op.create_index(batch_op.f('ix_conversations_user_id'), ['user_id'], unique=False)

    if 'messages' not in tables:
        op.create_table(
            'messages',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('conversation_id', sa.Integer(), nullable=False),
            sa.Column('role', sa.Enum('system', 'user', 'assistant', name='messagerole', native_enum=False, length=20), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('token_count', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('extra_metadata', sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('messages', schema=None) as batch_op:
            batch_op.create_index('ix_messages_conv_created', ['conversation_id', 'created_at'], unique=False)
            batch_op.create_index(batch_op.f('ix_messages_conversation_id'), ['conversation_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_messages_created_at'), ['created_at'], unique=False)
            batch_op.create_index(batch_op.f('ix_messages_id'), ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = set(inspector.get_table_names())

    if 'messages' in tables:
        with op.batch_alter_table('messages', schema=None) as batch_op:
            batch_op.drop_index(batch_op.f('ix_messages_id'))
            batch_op.drop_index(batch_op.f('ix_messages_created_at'))
            batch_op.drop_index(batch_op.f('ix_messages_conversation_id'))
            batch_op.drop_index('ix_messages_conv_created')
        op.drop_table('messages')

    if 'conversations' in tables:
        with op.batch_alter_table('conversations', schema=None) as batch_op:
            batch_op.drop_index(batch_op.f('ix_conversations_user_id'))
            batch_op.drop_index(batch_op.f('ix_conversations_status'))
            batch_op.drop_index(batch_op.f('ix_conversations_resident_id'))
            batch_op.drop_index(batch_op.f('ix_conversations_id'))
        op.drop_table('conversations')
