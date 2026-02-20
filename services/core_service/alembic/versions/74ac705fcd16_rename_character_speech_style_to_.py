"""rename_character_speech_style_to_dialogue_style

Revision ID: 74ac705fcd16
Revises: c3c08566509f
Create Date: 2026-02-20 08:36:08.695427

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '74ac705fcd16'
down_revision = 'c3c08566509f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename column from speech_style to dialogue_style in characters table
    op.alter_column('characters', 'speech_style', new_column_name='dialogue_style')


def downgrade() -> None:
    # Revert: rename column back from dialogue_style to speech_style
    op.alter_column('characters', 'dialogue_style', new_column_name='speech_style')
