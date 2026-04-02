from pydantic import BaseModel
from uuid import UUID


# ─── CharacterAttribute ────────────────────────────────────────────────────── #

class CharacterAttributeBase(BaseModel):
    category: str = "fact"  # "fact" | "speech_example" | "mindset" | "bio"
    content: str


class CharacterAttributeCreate(CharacterAttributeBase):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "category": "fact",
                    "content": "The character has a severe allergy to moon dust."
                }
            ]
        }
    }


class CharacterAttributeUpdate(BaseModel):
    category: str | None = None
    content: str | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "category": "bio",
                    "content": "Born in 1980 in a small village."
                }
            ]
        }
    }


class CharacterAttribute(CharacterAttributeBase):
    id: UUID
    character_id: UUID

    class Config:
        from_attributes = True
