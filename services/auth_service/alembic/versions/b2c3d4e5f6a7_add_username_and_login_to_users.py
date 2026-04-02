"""add_username_and_login_to_users

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-02 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns with server_default for existing rows
    op.add_column('users', sa.Column('username', sa.String(), server_default='default_user', nullable=False))
    op.add_column('users', sa.Column('login', sa.String(), server_default='default_login', nullable=False))
    # Remove server default so it requires input on subsequent inserts
    op.alter_column('users', 'username', server_default=None)
    op.alter_column('users', 'login', server_default=None)
    
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_login'), 'users', ['login'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_login'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_column('users', 'login')
    op.drop_column('users', 'username')
