"""Add HNSW index for episodic_memories

Revision ID: e7bd18d271fe
Revises: c0123d4e5f6a
Create Date: 2026-04-02 18:51:46.587650

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e7bd18d271fe'
down_revision = 'c0123d4e5f6a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX ix_episodic_memories_embedding_hnsw "
        "ON episodic_memories USING hnsw (embedding vector_cosine_ops);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX ix_episodic_memories_embedding_hnsw;")
