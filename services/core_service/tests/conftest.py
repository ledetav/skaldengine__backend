import pytest
from sqlalchemy.orm import configure_mappers

@pytest.fixture(autouse=True)
def setup_models():
    # Import ALL models before configuring mappers
    import app.domains.character.attribute_models
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

    configure_mappers()
