"""replace_is_admin_with_role

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-02 18:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add role column with a default
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('role', sa.String(), server_default='user', nullable=False))
    
    # Data migration is difficult via batch_op when column is just added, but we can execute raw SQL safely
    op.execute("UPDATE users SET role = 'admin' WHERE is_admin = true OR is_admin = 1")
    op.execute("UPDATE users SET role = 'user' WHERE is_admin = false OR is_admin = 0")

    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('is_admin')
        
    # Remove server_default so new inserts must specify or python default handles it
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('role', server_default=None)


def downgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('is_admin', sa.Boolean(), server_default=sa.text('0'), nullable=False))
    
    op.execute("UPDATE users SET is_admin = true WHERE role = 'admin' OR role = 'moderator'")
    op.execute("UPDATE users SET is_admin = false WHERE role = 'user'")

    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('role')
        batch_op.alter_column('is_admin', server_default=None)
