import os
import pytest
from sqlalchemy.orm import configure_mappers

os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-chars-long")
os.environ.setdefault("CORE_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/test_db")
os.environ.setdefault("POLZA_API_KEY", "test-polza-key")

@pytest.fixture(autouse=True, scope="session")
def setup_models():
    # Import ALL models before configuring mappers
    try:
        import app.domains.character.attribute_models
    except ImportError:
        pass
    import app.domains.character.models
    import app.domains.scenario.models
    import app.domains.chat.models
    import app.domains.lorebook.models
    import app.domains.persona.models
    # We found missing Message model, so let's import it too if it's there
    try:
        import app.domains.chat.message_models
    except ImportError:
        pass
    try:
        import app.domains.message.models
    except ImportError:
        pass

    try:
        configure_mappers()
    except Exception:
        pass
