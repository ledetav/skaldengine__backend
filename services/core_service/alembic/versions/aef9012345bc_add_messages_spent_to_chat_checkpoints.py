"""Add messages_spent to chat_checkpoints

Revision ID: aef9012345bc
Revises: fde123456789
Create Date: 2026-04-03 11:47:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'aef9012345bc'
down_revision = 'fde123456789'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'chat_checkpoints',
        sa.Column('messages_spent', sa.Integer(), nullable=False, server_default='0')
    )


def downgrade() -> None:
    op.drop_column('chat_checkpoints', 'messages_spent')
