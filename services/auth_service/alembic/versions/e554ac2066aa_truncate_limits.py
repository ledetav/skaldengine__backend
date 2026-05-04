"""truncate_limits

Revision ID: e554ac2066aa
Revises: aced1bb7f576
Create Date: 2026-05-05 00:51:05.521908

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e554ac2066aa'
down_revision: Union[str, None] = 'aced1bb7f576'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # users
    op.execute("UPDATE users SET full_name = LEFT(full_name, 200) WHERE full_name IS NOT NULL AND LENGTH(full_name) > 200;")
    op.execute("UPDATE users SET about = LEFT(about, 500) WHERE about IS NOT NULL AND LENGTH(about) > 500;")


def downgrade() -> None:
    """Downgrade schema."""
    pass