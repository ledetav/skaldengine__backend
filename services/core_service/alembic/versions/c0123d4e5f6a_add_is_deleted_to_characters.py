"""add_is_deleted_to_characters

Revision ID: c0123d4e5f6a
Revises: b2c3d4e5f6a7
Create Date: 2026-04-02 18:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c0123d4e5f6a'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('characters', sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False))


def downgrade() -> None:
    op.drop_column('characters', 'is_deleted')
