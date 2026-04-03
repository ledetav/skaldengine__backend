"""Add keywords to character_attributes

Revision ID: d7e8f9a0b1c2
Revises: aef9012345bc
Create Date: 2026-04-03 13:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd7e8f9a0b1c2'
down_revision = 'aef9012345bc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('character_attributes', sa.Column('keywords', postgresql.ARRAY(sa.Text()), server_default='{}', nullable=False))


def downgrade() -> None:
    op.drop_column('character_attributes', 'keywords')
