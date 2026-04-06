"""add_character_stats_and_props

Revision ID: 9c8d7e6f5a4b
Revises: 8b723f6a1d9e
Create Date: 2026-04-07 00:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9c8d7e6f5a4b'
down_revision = '8b723f6a1d9e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Добавляем колонки
    op.add_column('characters', sa.Column('total_chats_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('characters', sa.Column('monthly_chats_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('characters', sa.Column('gender', sa.String(length=50), nullable=True))
    op.add_column('characters', sa.Column('nsfw_allowed', sa.Boolean(), nullable=False, server_default='true'))

    # 2. Заполняем исторические данные: общее кол-во чатов
    op.execute("""
        UPDATE characters c
        SET total_chats_count = (
            SELECT count(*) 
            FROM chats ch 
            WHERE ch.character_id = c.id
        )
    """)

    # 3. Заполняем исторические данные: чаты за ПРЕДЫДУЩИЙ месяц
    op.execute("""
        UPDATE characters c
        SET monthly_chats_count = (
            SELECT count(*) 
            FROM chats ch 
            WHERE ch.character_id = c.id
              AND ch.created_at >= date_trunc('month', current_date - interval '1 month')
              AND ch.created_at < date_trunc('month', current_date)
        )
    """)


def downgrade() -> None:
    op.drop_column('characters', 'nsfw_allowed')
    op.drop_column('characters', 'gender')
    op.drop_column('characters', 'monthly_chats_count')
    op.drop_column('characters', 'total_chats_count')
