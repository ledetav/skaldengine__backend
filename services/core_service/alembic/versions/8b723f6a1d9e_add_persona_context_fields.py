"""Add persona context fields to chats, lorebooks, and character_attributes

Revision ID: 8b723f6a1d9e
Revises: ff726d3b9e02
Create Date: 2026-04-03 15:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8b723f6a1d9e'
down_revision = 'ff726d3b9e02'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Update chats table
    op.add_column('chats', sa.Column('persona_lorebook_id', sa.Uuid(), nullable=True))
    op.create_foreign_key('fk_chats_persona_lorebook_id', 'chats', 'lorebooks', ['persona_lorebook_id'], ['id'])

    # 2. Update lorebooks table
    op.add_column('lorebooks', sa.Column('user_persona_id', sa.Uuid(), nullable=True))
    # Make character_id nullable in lorebooks (if it wasn't already, but b2c3d4e5f6a7 had it as nullable)
    op.create_index(op.f('ix_lorebooks_user_persona_id'), 'lorebooks', ['user_persona_id'], unique=False)
    op.create_foreign_key('fk_lorebooks_user_persona_id', 'lorebooks', 'user_personas', ['user_persona_id'], ['id'], ondelete='CASCADE')

    # 3. Update character_attributes table
    op.add_column('character_attributes', sa.Column('user_persona_id', sa.Uuid(), nullable=True))
    # Make character_id nullable in character_attributes
    op.alter_column('character_attributes', 'character_id', 
               existing_type=sa.UUID(),
               nullable=True)
    
    op.create_index(op.f('ix_character_attributes_user_persona_id'), 'character_attributes', ['user_persona_id'], unique=False)
    op.create_foreign_key('fk_character_attributes_user_persona_id', 'character_attributes', 'user_personas', ['user_persona_id'], ['id'], ondelete='CASCADE')

    # Create composite index for persona attributes
    op.create_index('ix_character_attributes_persona_id_category', 'character_attributes', ['user_persona_id', 'category'], unique=False)

    # Add GIN index for keywords (for fast retrieval by stems)
    op.create_index(
        'ix_character_attributes_keywords',
        'character_attributes', ['keywords'],
        postgresql_using='gin'
    )


def downgrade() -> None:
    # 1. Revert character_attributes
    op.drop_index('ix_character_attributes_keywords', table_name='character_attributes')
    op.drop_index('ix_character_attributes_persona_id_category', table_name='character_attributes')
    op.drop_constraint('fk_character_attributes_user_persona_id', 'character_attributes', type_='foreignkey')
    op.drop_index(op.f('ix_character_attributes_user_persona_id'), table_name='character_attributes')
    op.alter_column('character_attributes', 'character_id',
               existing_type=sa.UUID(),
               nullable=False)
    op.drop_column('character_attributes', 'user_persona_id')

    # 2. Revert lorebooks
    op.drop_constraint('fk_lorebooks_user_persona_id', 'lorebooks', type_='foreignkey')
    op.drop_index(op.f('ix_lorebooks_user_persona_id'), table_name='lorebooks')
    op.drop_column('lorebooks', 'user_persona_id')

    # 3. Revert chats
    op.drop_constraint('fk_chats_persona_lorebook_id', 'chats', type_='foreignkey')
    op.drop_column('chats', 'persona_lorebook_id')
