"""restore_login_column

Revision ID: a2b3c4d5e6f7
Revises: f7a8b9c0d1e2
Create Date: 2026-04-07 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, None] = 'f7a8b9c0d1e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add login column as nullable first to allow population
    op.add_column('users', sa.Column('login', sa.String(), nullable=True))
    
    # 2. Populate login from username (strip @ prefix)
    # In PostgreSQL, SUBSTRING(string FROM 2) or SUBSTR(string, 2)
    op.execute("UPDATE users SET login = SUBSTRING(username FROM 2) WHERE username LIKE '@%'")
    op.execute("UPDATE users SET login = username WHERE login IS NULL")
    
    # 3. Make nullable=False and add unique index
    op.alter_column('users', 'login', nullable=False)
    op.create_index(op.f('ix_users_login'), 'users', ['login'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_login'), table_name='users')
    op.drop_column('users', 'login')
