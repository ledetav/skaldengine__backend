import pytest

# Load all models to avoid SQLAlchemy InvalidRequestError related to relationship resolution
from app.domains.character.models import Character
from app.domains.character.attribute_models import CharacterAttribute
from app.domains.persona.models import UserPersona
from app.domains.scenario.models import Scenario
from app.domains.chat.models import Chat, ChatCheckpoint
from app.domains.chat.message_models import Message
from app.domains.lorebook.models import Lorebook, LorebookEntry

@pytest.fixture(autouse=True)
def load_all_models():
    pass
