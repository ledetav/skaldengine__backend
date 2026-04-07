"""restore_persona_description_and_gender

Revision ID: h3i4j5k6l7m8
Revises: 9c8d7e6f5a4b
Create Date: 2026-04-07 20:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'h3i4j5k6l7m8'
down_revision: Union[str, None] = '9c8d7e6f5a4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add description (Text) and gender (String) to user_personas
    op.add_column('user_personas', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('user_personas', sa.Column('gender', sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column('user_personas', 'gender')
    op.drop_column('user_personas', 'description')
