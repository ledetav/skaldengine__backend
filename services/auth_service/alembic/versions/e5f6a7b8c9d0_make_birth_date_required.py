"""make_birth_date_required

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-04-03 17:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Set a default value for existing users who don't have birth_date
    op.execute("UPDATE users SET birth_date = '2000-01-01' WHERE birth_date IS NULL")
    # Make birth_date non-nullable
    op.alter_column('users', 'birth_date', nullable=False)


def downgrade() -> None:
    op.alter_column('users', 'birth_date', nullable=True)
