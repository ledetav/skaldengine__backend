"""add tags to lorebooks

Revision ID: 6a2e45678b90
Revises: 293bb3134039
Create Date: 2026-04-25 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6a2e45678b90'
down_revision = '293bb3134039'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('lorebooks', sa.Column('tags', sa.ARRAY(sa.String()), nullable=False, server_default='{}'))


def downgrade() -> None:
    op.drop_column('lorebooks', 'tags')
