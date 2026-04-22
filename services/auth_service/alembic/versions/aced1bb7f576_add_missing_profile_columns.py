"""add_missing_profile_columns

Revision ID: aced1bb7f576
Revises: a2b3c4d5e6f7
Create Date: 2026-04-20 19:36:45.048803

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'aced1bb7f576'
down_revision: Union[str, None] = '20aa05eaf397'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # These columns were already added by 20aa05eaf397 (duplicate migration).
    # Using raw SQL with IF NOT EXISTS to be safe on both fresh and existing DBs.
    import sqlalchemy as sa
    conn = op.get_bind()
    conn.execute(sa.text("ALTER TABLE users ADD COLUMN IF NOT EXISTS cover_url VARCHAR;"))
    conn.execute(sa.text("ALTER TABLE users ADD COLUMN IF NOT EXISTS about TEXT;"))
    conn.execute(sa.text("ALTER TABLE users ADD COLUMN IF NOT EXISTS polza_api_key VARCHAR;"))


def downgrade() -> None:
    # Only drop if this migration is rolled back past 20aa05eaf397 too.
    import sqlalchemy as sa
    conn = op.get_bind()
    conn.execute(sa.text("ALTER TABLE users DROP COLUMN IF EXISTS polza_api_key;"))
    conn.execute(sa.text("ALTER TABLE users DROP COLUMN IF EXISTS about;"))
    conn.execute(sa.text("ALTER TABLE users DROP COLUMN IF EXISTS cover_url;"))

