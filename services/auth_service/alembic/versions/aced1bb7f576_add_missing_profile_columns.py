"""add_missing_profile_columns

Revision ID: aced1bb7f576
Revises: a2b3c4d5e6f7
Create Date: 2026-04-20 19:36:45.048803

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'aced1bb7f576'
down_revision: Union[str, None] = 'a2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('cover_url', sa.String(), nullable=True))
    op.add_column('users', sa.Column('about', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('polza_api_key', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'polza_api_key')
    op.drop_column('users', 'about')
    op.drop_column('users', 'cover_url')
