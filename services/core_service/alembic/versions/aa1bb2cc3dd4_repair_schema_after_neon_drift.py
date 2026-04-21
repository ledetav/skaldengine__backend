"""Repair schema after Neon drift

Neon schema-push (Drizzle) accidentally dropped several objects that were
added by the f18dc3140740 migration.  This migration restores them in an
idempotent way (all statements use IF NOT EXISTS / DO…EXCEPTION).

Revision ID: aa1bb2cc3dd4
Revises: f18dc3140740
Create Date: 2026-04-21 18:49:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'aa1bb2cc3dd4'
down_revision = 'f18dc3140740'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # ── 1. chats.title ────────────────────────────────────────────────────────
    # Was dropped by Neon schema-push; restore it.
    conn.execute(sa.text("""
        ALTER TABLE chats
            ADD COLUMN IF NOT EXISTS title VARCHAR(255);
    """))

    # ── 2. lorebooktype enum ──────────────────────────────────────────────────
    conn.execute(sa.text("""
        DO $$
        BEGIN
            CREATE TYPE lorebooktype AS ENUM ('FANDOM', 'CHARACTER', 'PERSONA');
        EXCEPTION WHEN duplicate_object THEN
            NULL;  -- already exists, nothing to do
        END
        $$;
    """))

    # ── 3. lorebooks.type column ──────────────────────────────────────────────
    # Check via information_schema to avoid errors on re-run.
    conn.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'lorebooks' AND column_name = 'type'
            ) THEN
                ALTER TABLE lorebooks
                    ADD COLUMN type lorebooktype NOT NULL DEFAULT 'FANDOM';
            END IF;
        END
        $$;
    """))

    # ── 4. ix_lorebooks_type index ────────────────────────────────────────────
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_lorebooks_type ON lorebooks (type);
    """))

    # ── 5. HNSW index guard ───────────────────────────────────────────────────
    # If the HNSW index was also wiped, recreate it safely.
    conn.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'episodic_memories'
                  AND indexname = 'ix_episodic_memories_embedding_hnsw'
            ) THEN
                CREATE INDEX ix_episodic_memories_embedding_hnsw
                    ON episodic_memories
                    USING hnsw (embedding vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64);
            END IF;
        END
        $$;
    """))


def downgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text("DROP INDEX IF EXISTS ix_episodic_memories_embedding_hnsw;"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_lorebooks_type;"))
    conn.execute(sa.text("ALTER TABLE lorebooks DROP COLUMN IF EXISTS type;"))
    conn.execute(sa.text("DROP TYPE IF EXISTS lorebooktype;"))
    conn.execute(sa.text("ALTER TABLE chats DROP COLUMN IF EXISTS title;"))
