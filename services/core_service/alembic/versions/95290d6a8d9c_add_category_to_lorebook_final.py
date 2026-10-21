"""add_category_to_lorebook_final

Revision ID: 95290d6a8d9c
Revises: cbc2d25b966f
Create Date: 2026-04-26 10:31:24.807643

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '95290d6a8d9c'
down_revision = 'cbc2d25b966f'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('lorebooks', sa.Column('category', sa.String(), nullable=True))
    op.execute("UPDATE lorebooks SET category = 'general'")
    op.alter_column('lorebooks', 'category', nullable=False)
    op.create_index(op.f('ix_lorebooks_category'), 'lorebooks', ['category'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_lorebooks_category'), table_name='lorebooks')
    op.drop_column('lorebooks', 'category')
