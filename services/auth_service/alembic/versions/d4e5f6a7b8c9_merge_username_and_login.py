"""merge_username_and_login

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-03 17:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop login index and column
    op.drop_index('ix_users_login', table_name='users')
    op.drop_column('users', 'login')


def downgrade() -> None:
    # Add login column back
    op.add_column('users', sa.Column('login', sa.String(), nullable=True))
    # Migration: copy username to login for existing rows
    op.execute("UPDATE users SET login = username")
    # Make nullable=False and create index
    op.alter_column('users', 'login', nullable=False)
    op.create_index('ix_users_login', 'users', ['login'], unique=True)
