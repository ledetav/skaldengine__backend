"""Update embedding dim to 1536

Revision ID: fde123456789
Revises: e7bd18d271fe
Create Date: 2026-04-03 10:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = 'fde123456789'
down_revision = 'e7bd18d271fe'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Drop the HNSW index first (it depends on the column dimension)
    op.execute("DROP INDEX IF EXISTS ix_episodic_memories_embedding_hnsw;")
    
    # 2. Clear the table because old 768-dim vectors are invalid
    op.execute("DELETE FROM episodic_memories;")
    
    # 3. Alter the column type to Vector(1536)
    # Using raw SQL to ensure precision and avoid possible issues with op.alter_column and custom types
    op.execute("ALTER TABLE episodic_memories ALTER COLUMN embedding TYPE vector(1536);")
    
    # 4. Re-create the HNSW index
    op.execute(
        \"\"\"
        CREATE INDEX ix_episodic_memories_embedding_hnsw 
        ON episodic_memories USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
        \"\"\"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_episodic_memories_embedding_hnsw;")
    op.execute("DELETE FROM episodic_memories;")
    op.execute("ALTER TABLE episodic_memories ALTER COLUMN embedding TYPE vector(768);")
    op.execute(
        \"\"\"
        CREATE INDEX ix_episodic_memories_embedding_hnsw 
        ON episodic_memories USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
        \"\"\"
    )
