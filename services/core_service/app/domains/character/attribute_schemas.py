from pydantic import BaseModel
from uuid import UUID


# ─── CharacterAttribute ────────────────────────────────────────────────────── #

class CharacterAttributeBase(BaseModel):
    category: str = "fact"  # "fact" | "speech_example" | "mindset" | "bio"
    content: str
    keywords: list[str] = []


class CharacterAttributeCreate(CharacterAttributeBase):
    character_id: UUID | None = None
    user_persona_id: UUID | None = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "character_id": "c138fbd8-8250-48e0-bb15-123456789abc",
                    "category": "fact",
                    "content": "The character has a severe allergy to moon dust.",
                    "keywords": ["moon dust", "allergy", "лунная пыль", "аллергия"]
                },
                {
                    "user_persona_id": "b228fbd8-8250-48e0-bb15-123456789abc",
                    "category": "fact",
                    "content": "The player's persona was born in a royal family.",
                    "keywords": ["royal", "family", "королевская", "семья"]
                }
            ]
        }
    }


class CharacterAttributeBulkCreate(BaseModel):
    character_id: UUID
    attributes: list[CharacterAttributeBase]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "character_id": "c138fbd8-8250-48e0-bb15-123456789abc",
                    "attributes": [
                        {"category": "fact", "content": "Fact 1"},
                        {"category": "fact", "content": "Fact 2"}
                    ]
                }
            ]
        }
    }


class CharacterAttributeUpdate(BaseModel):
    category: str | None = None
    content: str | None = None
    keywords: list[str] | None = None

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
