"""truncate_limits

Revision ID: bd8557bb34da
Revises: dac95b615cd5
Create Date: 2026-05-05 00:50:22.564702

"""
from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy
import pgvector


# revision identifiers, used by Alembic.
revision = 'bd8557bb34da'
down_revision = 'dac95b615cd5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # characters
    op.execute("UPDATE characters SET name = LEFT(name, 200) WHERE name IS NOT NULL AND LENGTH(name) > 200;")
    op.execute("UPDATE characters SET description = LEFT(description, 500) WHERE description IS NOT NULL AND LENGTH(description) > 500;")
    op.execute("UPDATE characters SET fandom = LEFT(fandom, 200) WHERE fandom IS NOT NULL AND LENGTH(fandom) > 200;")
    op.execute("UPDATE characters SET appearance = LEFT(appearance, 2000) WHERE appearance IS NOT NULL AND LENGTH(appearance) > 2000;")
    op.execute("UPDATE characters SET personality = LEFT(personality, 2000) WHERE personality IS NOT NULL AND LENGTH(personality) > 2000;")
    op.execute("UPDATE characters SET gender = LEFT(gender, 100) WHERE gender IS NOT NULL AND LENGTH(gender) > 100;")
    op.execute("UPDATE characters SET age = LEFT(age, 100) WHERE age IS NOT NULL AND LENGTH(age) > 100;")

    # user_personas
    op.execute("UPDATE user_personas SET name = LEFT(name, 200) WHERE name IS NOT NULL AND LENGTH(name) > 200;")
    op.execute("UPDATE user_personas SET description = LEFT(description, 500) WHERE description IS NOT NULL AND LENGTH(description) > 500;")
    op.execute("UPDATE user_personas SET appearance = LEFT(appearance, 2000) WHERE appearance IS NOT NULL AND LENGTH(appearance) > 2000;")
    op.execute("UPDATE user_personas SET personality = LEFT(personality, 2000) WHERE personality IS NOT NULL AND LENGTH(personality) > 2000;")
    op.execute("UPDATE user_personas SET gender = LEFT(gender, 100) WHERE gender IS NOT NULL AND LENGTH(gender) > 100;")
    op.execute("UPDATE user_personas SET age = LEFT(age, 100) WHERE age IS NOT NULL AND LENGTH(age) > 100;")
    op.execute("UPDATE user_personas SET facts = LEFT(facts, 2000) WHERE facts IS NOT NULL AND LENGTH(facts) > 2000;")

    # lorebooks
    op.execute("UPDATE lorebooks SET name = LEFT(name, 200) WHERE name IS NOT NULL AND LENGTH(name) > 200;")
    op.execute("UPDATE lorebooks SET description = LEFT(description, 500) WHERE description IS NOT NULL AND LENGTH(description) > 500;")
    op.execute("UPDATE lorebooks SET fandom = LEFT(fandom, 200) WHERE fandom IS NOT NULL AND LENGTH(fandom) > 200;")

    # lorebook_entries
    op.execute("UPDATE lorebook_entries SET content = LEFT(content, 2000) WHERE content IS NOT NULL AND LENGTH(content) > 2000;")
    # truncate array size to 10
    op.execute("UPDATE lorebook_entries SET keywords = keywords[1:10] WHERE array_length(keywords, 1) > 10;")

    # scenarios
    op.execute("UPDATE scenarios SET title = LEFT(title, 200) WHERE title IS NOT NULL AND LENGTH(title) > 200;")
    op.execute("UPDATE scenarios SET location = LEFT(location, 200) WHERE location IS NOT NULL AND LENGTH(location) > 200;")
    op.execute("UPDATE scenarios SET description = LEFT(description, 500) WHERE description IS NOT NULL AND LENGTH(description) > 500;")
    op.execute("UPDATE scenarios SET start_point = LEFT(start_point, 500) WHERE start_point IS NOT NULL AND LENGTH(start_point) > 500;")
    op.execute("UPDATE scenarios SET end_point = LEFT(end_point, 500) WHERE end_point IS NOT NULL AND LENGTH(end_point) > 500;")
    op.execute("UPDATE scenarios SET internal_description = LEFT(internal_description, 1000) WHERE internal_description IS NOT NULL AND LENGTH(internal_description) > 1000;")

    # messages
    op.execute("UPDATE messages SET content = LEFT(content, 4000) WHERE content IS NOT NULL AND LENGTH(content) > 4000;")

def downgrade() -> None:
    pass
