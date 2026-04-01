"""full_schema_redesign_v2

Полная переработка схемы core_service по ТЗ.

Изменения:
- Добавлено расширение pgvector (CREATE EXTENSION IF NOT EXISTS vector)
- Таблица sessions → chats (переработана)
- Таблица lore_items → character_attributes + lorebooks + lorebook_entries
- Добавлены: episodic_memories (с HNSW-индексом на Vector(768))
- Добавлены: chat_checkpoints
- Изменены: characters, user_personas, messages, scenarios

Revision ID: b2c3d4e5f6a7
Revises: c3c08566509f
Create Date: 2026-04-01 18:05:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'c3c08566509f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # 0. Включаем расширение pgvector                                     #
    # ------------------------------------------------------------------ #
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # ------------------------------------------------------------------ #
    # 1. Удаляем старые таблицы (в порядке зависимостей FK)              #
    # ------------------------------------------------------------------ #
    op.drop_table("messages")
    op.drop_table("sessions")
    op.drop_table("lore_items")

    # ------------------------------------------------------------------ #
    # 2. Изменяем таблицу characters                                      #
    # ------------------------------------------------------------------ #
    # Удаляем старые поля
    op.drop_column("characters", "personality_traits")
    op.drop_column("characters", "speech_style")
    op.drop_column("characters", "inner_world")
    op.drop_column("characters", "behavioral_cues")

    # Добавляем новые поля
    op.add_column("characters", sa.Column("creator_id", sa.Uuid(), nullable=True))
    op.add_column("characters", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("characters", sa.Column("fandom", sa.String(), nullable=True))
    op.add_column("characters", sa.Column("card_image_url", sa.String(), nullable=True))
    op.add_column("characters", sa.Column("personality", sa.Text(), nullable=True))
    op.add_column("characters", sa.Column("is_public", sa.Boolean(), nullable=False, server_default="false"))

    # Делаем appearance nullable (раньше был NOT NULL)
    op.alter_column("characters", "appearance", nullable=True)

    # Индекс по fandom
    op.create_index("ix_characters_fandom", "characters", ["fandom"])

    # ------------------------------------------------------------------ #
    # 3. Изменяем таблицу user_personas                                   #
    # ------------------------------------------------------------------ #
    # Удаляем description
    op.drop_column("user_personas", "description")

    # Добавляем новые поля
    op.add_column("user_personas", sa.Column("age", sa.Integer(), nullable=True))
    op.add_column("user_personas", sa.Column("appearance", sa.Text(), nullable=True))
    op.add_column("user_personas", sa.Column("personality", sa.Text(), nullable=True))
    op.add_column("user_personas", sa.Column("facts", sa.Text(), nullable=True))

    # ------------------------------------------------------------------ #
    # 4. Изменяем таблицу scenarios                                       #
    # ------------------------------------------------------------------ #
    # Переименовываем owner_character_id → character_id
    op.alter_column("scenarios", "owner_character_id", new_column_name="character_id")

    # Переименовываем FK constraint (если нужно, PostgreSQL позволяет)
    op.drop_constraint("scenarios_owner_character_id_fkey", "scenarios", type_="foreignkey")
    op.create_foreign_key(
        "scenarios_character_id_fkey",
        "scenarios", "characters",
        ["character_id"], ["id"],
        ondelete="SET NULL"
    )

    # Удаляем suggested_relationships
    op.drop_column("scenarios", "suggested_relationships")

    # ------------------------------------------------------------------ #
    # 5. Создаём character_attributes                                     #
    # ------------------------------------------------------------------ #
    op.create_table(
        "character_attributes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("category", sa.String(), nullable=False, server_default="fact"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_character_attributes_character_id_category",
                    "character_attributes", ["character_id", "category"])

    # ------------------------------------------------------------------ #
    # 6. Создаём lorebooks                                                #
    # ------------------------------------------------------------------ #
    op.create_table(
        "lorebooks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), nullable=True),
        sa.Column("fandom", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lorebooks_character_id", "lorebooks", ["character_id"])
    op.create_index("ix_lorebooks_fandom", "lorebooks", ["fandom"])

    # ------------------------------------------------------------------ #
    # 7. Создаём lorebook_entries                                         #
    # ------------------------------------------------------------------ #
    op.create_table(
        "lorebook_entries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lorebook_id", sa.Uuid(), nullable=False),
        sa.Column("keywords", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["lorebook_id"], ["lorebooks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    # GIN-индекс для поиска по keywords
    op.create_index(
        "ix_lorebook_entries_keywords",
        "lorebook_entries", ["keywords"],
        postgresql_using="gin"
    )

    # ------------------------------------------------------------------ #
    # 8. Создаём chats (без active_leaf_id — добавим после messages)     #
    # ------------------------------------------------------------------ #
    op.create_table(
        "chats",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("user_persona_id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("mode", sa.String(), nullable=False, server_default="sandbox"),
        sa.Column("scenario_id", sa.Uuid(), nullable=True),
        sa.Column("is_acquainted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("relationship_dynamic", sa.Text(), nullable=True),
        sa.Column("language", sa.String(), nullable=False, server_default="ru"),
        sa.Column("narrative_voice", sa.String(), nullable=False, server_default="third"),
        sa.Column("active_leaf_id", sa.Uuid(), nullable=True),  # FK добавим ниже с use_alter
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"]),
        sa.ForeignKeyConstraint(["user_persona_id"], ["user_personas.id"]),
        sa.ForeignKeyConstraint(["scenario_id"], ["scenarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------------ #
    # 9. Создаём messages (с chat_id вместо session_id)                  #
    # ------------------------------------------------------------------ #
    op.create_table(
        "messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("chat_id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("hidden_thought", sa.Text(), nullable=True),
        sa.Column("is_edited", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["chat_id"], ["chats.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["messages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    # B-Tree индекс для быстрой выборки истории
    op.create_index("ix_messages_chat_id_created_at", "messages", ["chat_id", "created_at"])

    # ------------------------------------------------------------------ #
    # 10. Добавляем FK active_leaf_id в chats (после создания messages)  #
    # ------------------------------------------------------------------ #
    op.create_foreign_key(
        "fk_chats_active_leaf_id",
        "chats", "messages",
        ["active_leaf_id"], ["id"],
        use_alter=True,
    )

    # ------------------------------------------------------------------ #
    # 11. Создаём episodic_memories (pgvector)                           #
    # ------------------------------------------------------------------ #
    op.create_table(
        "episodic_memories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("chat_id", sa.Uuid(), nullable=False),
        sa.Column("message_id", sa.Uuid(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(768), nullable=False),
        sa.ForeignKeyConstraint(["chat_id"], ["chats.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    # HNSW-индекс (cosine distance) для pgvector — быстрый ANN
    op.execute(
        """
        CREATE INDEX ix_episodic_memories_embedding_hnsw
        ON episodic_memories USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
        """
    )

    # ------------------------------------------------------------------ #
    # 12. Создаём chat_checkpoints                                        #
    # ------------------------------------------------------------------ #
    op.create_table(
        "chat_checkpoints",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("chat_id", sa.Uuid(), nullable=False),
        sa.Column("order_num", sa.Integer(), nullable=False),
        sa.Column("goal_description", sa.Text(), nullable=False),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["chat_id"], ["chats.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("chat_checkpoints")
    op.execute("DROP INDEX IF EXISTS ix_episodic_memories_embedding_hnsw;")
    op.drop_table("episodic_memories")
    op.drop_constraint("fk_chats_active_leaf_id", "chats", type_="foreignkey")
    op.drop_table("messages")
    op.drop_table("chats")
    op.drop_table("lorebook_entries")
    op.drop_table("lorebooks")
    op.drop_table("character_attributes")

    # Восстанавливаем scenarios
    op.add_column("scenarios", sa.Column("suggested_relationships", sa.JSON(), nullable=False, server_default="[]"))
    op.drop_constraint("scenarios_character_id_fkey", "scenarios", type_="foreignkey")
    op.alter_column("scenarios", "character_id", new_column_name="owner_character_id")
    op.create_foreign_key(
        "scenarios_owner_character_id_fkey",
        "scenarios", "characters",
        ["owner_character_id"], ["id"]
    )

    # Восстанавливаем user_personas
    op.drop_column("user_personas", "facts")
    op.drop_column("user_personas", "personality")
    op.drop_column("user_personas", "appearance")
    op.drop_column("user_personas", "age")
    op.add_column("user_personas", sa.Column("description", sa.Text(), nullable=False, server_default=""))

    # Восстанавливаем characters
    op.drop_index("ix_characters_fandom", "characters")
    op.drop_column("characters", "is_public")
    op.drop_column("characters", "personality")
    op.drop_column("characters", "card_image_url")
    op.drop_column("characters", "fandom")
    op.drop_column("characters", "description")
    op.drop_column("characters", "creator_id")
    op.alter_column("characters", "appearance", nullable=False)
    op.add_column("characters", sa.Column("behavioral_cues", sa.Text(), nullable=True))
    op.add_column("characters", sa.Column("inner_world", sa.Text(), nullable=True))
    op.add_column("characters", sa.Column("speech_style", sa.Text(), nullable=False, server_default=""))
    op.add_column("characters", sa.Column("personality_traits", sa.Text(), nullable=False, server_default=""))

    # Восстанавливаем lore_items
    op.create_table(
        "lore_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("keywords", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Восстанавливаем sessions
    op.create_table(
        "sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("persona_id", sa.Uuid(), nullable=False),
        sa.Column("scenario_id", sa.Uuid(), nullable=True),
        sa.Column("mode", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("speech_style", sa.String(), nullable=False),
        sa.Column("character_name_snapshot", sa.String(), nullable=False),
        sa.Column("persona_name_snapshot", sa.String(), nullable=False),
        sa.Column("relationship_context", sa.Text(), nullable=True),
        sa.Column("cached_system_prompt", sa.Text(), nullable=False),
        sa.Column("current_step", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"]),
        sa.ForeignKeyConstraint(["persona_id"], ["user_personas.id"]),
        sa.ForeignKeyConstraint(["scenario_id"], ["scenarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Восстанавливаем messages (старый формат)
    op.create_table(
        "messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["messages.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
