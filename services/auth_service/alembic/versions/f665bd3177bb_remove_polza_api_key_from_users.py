"""remove_polza_api_key_from_users

Revision ID: f665bd3177bb
Revises: e554ac2066aa
Create Date: 2026-10-26 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f665bd3177bb'
down_revision: Union[str, None] = 'e554ac2066aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop polza_api_key column from users table."""
    conn = op.get_bind()
    conn.execute(sa.text("ALTER TABLE users DROP COLUMN IF EXISTS polza_api_key;"))


def downgrade() -> None:
    """Restore polza_api_key column in users table."""
    conn = op.get_bind()
    conn.execute(sa.text("ALTER TABLE users ADD COLUMN IF NOT EXISTS polza_api_key VARCHAR;"))
