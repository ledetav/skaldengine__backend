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
    # HNSW index requires pgvector to be installed as a PostgreSQL extension.
    # On some hosts (e.g. plain Replit PostgreSQL) the shared library is absent.
    # We wrap in try/except so the overall migration chain is not blocked;
    # the index can be created later once pgvector is available.
    try:
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_episodic_memories_embedding_hnsw "
            "ON episodic_memories USING hnsw (embedding vector_cosine_ops);"
        )
    except Exception as e:
        import warnings
        warnings.warn(
            f"Could not create HNSW index (pgvector may not be installed): {e}. "
            "Skipping. Re-run this migration after enabling pgvector.",
            stacklevel=2,
        )
        # Roll back the failed DDL statement so the transaction stays clean.
        op.get_bind().execute(sa.text("ROLLBACK TO SAVEPOINT hnsw_index"))



def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_episodic_memories_embedding_hnsw;")
