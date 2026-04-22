"""Repair full schema after Neon drift

Idempotent migration that ensures every column, index and type defined in
the SQLAlchemy models actually exists in the database.  All statements use
IF NOT EXISTS / DO…EXCEPTION so it is safe to run multiple times and will
not fail when objects already exist.

Caused by: Neon schema-push (Drizzle) ran a destructive diff that dropped
columns and types added by earlier Alembic migrations.

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


# ---------------------------------------------------------------------------
# Helper: execute a block of raw SQL
# ---------------------------------------------------------------------------
def _sql(conn, stmt: str) -> None:
    conn.execute(sa.text(stmt))


def upgrade() -> None:
    conn = op.get_bind()

    # ══════════════════════════════════════════════════════════════════════════
    # 0. Extensions
    # ══════════════════════════════════════════════════════════════════════════
    _sql(conn, "CREATE EXTENSION IF NOT EXISTS vector;")

    # ══════════════════════════════════════════════════════════════════════════
    # 1. ENUM types
    # ══════════════════════════════════════════════════════════════════════════

    # lorebooktype  ('fandom' | 'character' | 'persona')
    # Note: SQLAlchemy Python enum stores lowercase values.
    _sql(conn, """
        DO $$
        BEGIN
            CREATE TYPE lorebooktype AS ENUM ('fandom', 'character', 'persona');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ══════════════════════════════════════════════════════════════════════════
    # 2. characters
    # ══════════════════════════════════════════════════════════════════════════
    _sql(conn, """
        ALTER TABLE characters
            ADD COLUMN IF NOT EXISTS creator_id      UUID,
            ADD COLUMN IF NOT EXISTS description     TEXT,
            ADD COLUMN IF NOT EXISTS fandom          VARCHAR,
            ADD COLUMN IF NOT EXISTS avatar_url      VARCHAR,
            ADD COLUMN IF NOT EXISTS card_image_url  VARCHAR,
            ADD COLUMN IF NOT EXISTS appearance      TEXT,
            ADD COLUMN IF NOT EXISTS personality     TEXT,
            ADD COLUMN IF NOT EXISTS total_chats_count   INTEGER NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS monthly_chats_count INTEGER NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS gender          VARCHAR(50),
            ADD COLUMN IF NOT EXISTS nsfw_allowed    BOOLEAN  NOT NULL DEFAULT TRUE,
            ADD COLUMN IF NOT EXISTS is_public       BOOLEAN  NOT NULL DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS is_deleted      BOOLEAN  NOT NULL DEFAULT FALSE;
    """)
    _sql(conn, "CREATE INDEX IF NOT EXISTS ix_characters_fandom ON characters (fandom);")

    # ══════════════════════════════════════════════════════════════════════════
    # 3. user_personas
    # ══════════════════════════════════════════════════════════════════════════
    _sql(conn, """
        ALTER TABLE user_personas
            ADD COLUMN IF NOT EXISTS description TEXT,
            ADD COLUMN IF NOT EXISTS avatar_url  VARCHAR,
            ADD COLUMN IF NOT EXISTS age         INTEGER,
            ADD COLUMN IF NOT EXISTS appearance  TEXT,
            ADD COLUMN IF NOT EXISTS personality TEXT,
            ADD COLUMN IF NOT EXISTS gender      VARCHAR(50),
            ADD COLUMN IF NOT EXISTS facts       TEXT;
    """)

    # ══════════════════════════════════════════════════════════════════════════
    # 4. scenarios
    # ══════════════════════════════════════════════════════════════════════════
    _sql(conn, """
        ALTER TABLE scenarios
            ADD COLUMN IF NOT EXISTS location VARCHAR;
    """)

    # ══════════════════════════════════════════════════════════════════════════
    # 5. lorebooks
    # ══════════════════════════════════════════════════════════════════════════
    _sql(conn, """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'lorebooks' AND column_name = 'type'
            ) THEN
                ALTER TABLE lorebooks
                    ADD COLUMN type lorebooktype NOT NULL DEFAULT 'fandom';
            END IF;
        END $$;
    """)
    _sql(conn, """
        ALTER TABLE lorebooks
            ADD COLUMN IF NOT EXISTS user_persona_id UUID
                REFERENCES user_personas(id) ON DELETE CASCADE;
    """)
    _sql(conn, "CREATE INDEX IF NOT EXISTS ix_lorebooks_type          ON lorebooks (type);")
    _sql(conn, "CREATE INDEX IF NOT EXISTS ix_lorebooks_character_id  ON lorebooks (character_id);")
    _sql(conn, "CREATE INDEX IF NOT EXISTS ix_lorebooks_fandom        ON lorebooks (fandom);")
    _sql(conn, "CREATE INDEX IF NOT EXISTS ix_lorebooks_user_persona_id ON lorebooks (user_persona_id);")

    # ══════════════════════════════════════════════════════════════════════════
    # 6. lorebook_entries
    # ══════════════════════════════════════════════════════════════════════════
    _sql(conn, """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'lorebook_entries'
                  AND indexname = 'ix_lorebook_entries_keywords'
            ) THEN
                CREATE INDEX ix_lorebook_entries_keywords
                    ON lorebook_entries USING gin (keywords);
            END IF;
        END $$;
    """)

    # ══════════════════════════════════════════════════════════════════════════
    # 7. chats
    # ══════════════════════════════════════════════════════════════════════════
    _sql(conn, """
        ALTER TABLE chats
            ADD COLUMN IF NOT EXISTS title              VARCHAR(255),
            ADD COLUMN IF NOT EXISTS persona_lorebook_id UUID
                REFERENCES lorebooks(id);
    """)

    # ══════════════════════════════════════════════════════════════════════════
    # 8. character_attributes
    # ══════════════════════════════════════════════════════════════════════════
    _sql(conn, """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'character_attributes'
            ) THEN
                CREATE TABLE character_attributes (
                    id              UUID PRIMARY KEY,
                    character_id    UUID REFERENCES characters(id)   ON DELETE CASCADE,
                    user_persona_id UUID REFERENCES user_personas(id) ON DELETE CASCADE,
                    category        VARCHAR NOT NULL DEFAULT 'fact',
                    content         TEXT    NOT NULL,
                    keywords        TEXT[]  NOT NULL DEFAULT '{}'
                );
            END IF;
        END $$;
    """)
    _sql(conn, """
        CREATE INDEX IF NOT EXISTS ix_character_attributes_character_id_category
            ON character_attributes (character_id, category);
    """)
    _sql(conn, """
        CREATE INDEX IF NOT EXISTS ix_character_attributes_persona_id_category
            ON character_attributes (user_persona_id, category);
    """)
    _sql(conn, """
        CREATE INDEX IF NOT EXISTS ix_character_attributes_user_persona_id
            ON character_attributes (user_persona_id);
    """)
    _sql(conn, """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'character_attributes'
                  AND indexname = 'ix_character_attributes_keywords'
            ) THEN
                CREATE INDEX ix_character_attributes_keywords
                    ON character_attributes USING gin (keywords);
            END IF;
        END $$;
    """)

    # ══════════════════════════════════════════════════════════════════════════
    # 9. messages
    # ══════════════════════════════════════════════════════════════════════════
    _sql(conn, """
        ALTER TABLE messages
            ADD COLUMN IF NOT EXISTS hidden_thought TEXT,
            ADD COLUMN IF NOT EXISTS is_edited      BOOLEAN NOT NULL DEFAULT FALSE;
    """)
    _sql(conn, """
        CREATE INDEX IF NOT EXISTS ix_messages_chat_id_created_at
            ON messages (chat_id, created_at);
    """)

    # ══════════════════════════════════════════════════════════════════════════
    # 10. chat_checkpoints
    # ══════════════════════════════════════════════════════════════════════════
    _sql(conn, """
        ALTER TABLE chat_checkpoints
            ADD COLUMN IF NOT EXISTS messages_spent INTEGER NOT NULL DEFAULT 0;
    """)

    # ══════════════════════════════════════════════════════════════════════════
    # 11. episodic_memories — HNSW index with operator class
    # ══════════════════════════════════════════════════════════════════════════
    _sql(conn, """
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
        END $$;
    """)


def downgrade() -> None:
    # Downgrade just removes the things this migration added.
    # Objects that existed before (from earlier migrations) are left intact.
    conn = op.get_bind()

    _sql(conn, "DROP INDEX IF EXISTS ix_episodic_memories_embedding_hnsw;")
    _sql(conn, "ALTER TABLE chat_checkpoints DROP COLUMN IF EXISTS messages_spent;")
    _sql(conn, "ALTER TABLE messages DROP COLUMN IF EXISTS hidden_thought;")
    _sql(conn, "ALTER TABLE messages DROP COLUMN IF EXISTS is_edited;")
    _sql(conn, "DROP INDEX IF EXISTS ix_messages_chat_id_created_at;")
    _sql(conn, "ALTER TABLE chats DROP COLUMN IF EXISTS title;")
    _sql(conn, "ALTER TABLE chats DROP COLUMN IF EXISTS persona_lorebook_id;")
    _sql(conn, "DROP INDEX IF EXISTS ix_character_attributes_keywords;")
    _sql(conn, "DROP INDEX IF EXISTS ix_character_attributes_user_persona_id;")
    _sql(conn, "DROP INDEX IF EXISTS ix_character_attributes_persona_id_category;")
    _sql(conn, "DROP INDEX IF EXISTS ix_character_attributes_character_id_category;")
    _sql(conn, "DROP TABLE IF EXISTS character_attributes;")
    _sql(conn, "DROP INDEX IF EXISTS ix_lorebooks_user_persona_id;")
    _sql(conn, "DROP INDEX IF EXISTS ix_lorebooks_fandom;")
    _sql(conn, "DROP INDEX IF EXISTS ix_lorebooks_character_id;")
    _sql(conn, "DROP INDEX IF EXISTS ix_lorebooks_type;")
    _sql(conn, "ALTER TABLE lorebooks DROP COLUMN IF EXISTS user_persona_id;")
    _sql(conn, "ALTER TABLE lorebooks DROP COLUMN IF EXISTS type;")
    _sql(conn, "DROP TYPE IF EXISTS lorebooktype;")
    _sql(conn, "ALTER TABLE scenarios DROP COLUMN IF EXISTS location;")
    _sql(conn, "ALTER TABLE user_personas DROP COLUMN IF EXISTS facts;")
    _sql(conn, "ALTER TABLE user_personas DROP COLUMN IF EXISTS gender;")
    _sql(conn, "ALTER TABLE user_personas DROP COLUMN IF EXISTS personality;")
    _sql(conn, "ALTER TABLE user_personas DROP COLUMN IF EXISTS appearance;")
    _sql(conn, "ALTER TABLE user_personas DROP COLUMN IF EXISTS age;")
    _sql(conn, "ALTER TABLE user_personas DROP COLUMN IF EXISTS avatar_url;")
    _sql(conn, "ALTER TABLE user_personas DROP COLUMN IF EXISTS description;")
    _sql(conn, "DROP INDEX IF EXISTS ix_characters_fandom;")
