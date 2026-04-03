"""add location to scenarios

Revision ID: ff726d3b9e02
Revises: aef9012345bc
Create Date: 2026-04-03 14:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ff726d3b9e02'
down_revision = 'aef9012345bc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('scenarios', sa.Column('location', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('scenarios', 'location')
