"""add_avatar_birth_date_to_users

Revision ID: a1b2c3d4e5f6
Revises: 3c3c8c46ef37
Create Date: 2026-04-01 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '3c3c8c46ef37'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Переименовываем hashed_password → password_hash
    op.alter_column('users', 'hashed_password', new_column_name='password_hash')

    # Добавляем новые поля
    op.add_column('users', sa.Column('avatar_url', sa.String(), nullable=True))
    op.add_column('users', sa.Column('birth_date', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'birth_date')
    op.drop_column('users', 'avatar_url')
    op.alter_column('users', 'password_hash', new_column_name='hashed_password')
