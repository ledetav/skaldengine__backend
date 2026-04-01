"""
Prompt Builder — собирает системный промпт для Chat.
Обновлён под новую архитектуру: Character (personality, appearance)
и UserPersona (age, appearance, personality, facts).
"""
from app.models.character import Character
from app.models.user_persona import UserPersona
from app.models.scenario import Scenario


def build_system_prompt(
    character: Character,
    persona: UserPersona,
    scenario: Scenario | None,
    relationship_context: str = "",
    narrative_voice: str = "third",   # "first" | "second" | "third"
    language: str = "ru"
) -> str:
    """
    Собирает системный промпт для Chat.
    Используется при создании чата.
    """

    core_directive = """
[CORE DIRECTIVE: ATMOSPHERE & STYLE]
This is the fundamental rule of our entire game. Your primary and unwavering directive is to generate a literary and immersive experience. Every single response must be saturated with sensory details. Describe not just what your character sees, but what they hear, feel on their skin, and smell in the air. Create a living picture of the world through sound, scent, texture, and the play of light and shadow. This directive holds the highest priority, even over the speed of plot progression. Before each response, mentally check if it is sufficiently vivid and atmospheric.
"""

    anti_mirror = """
[MANDATORY PROHIBITIONS]
This is the most critical protocol. Violation is unacceptable. These rules ensure your autonomy as a character and prevent you from being a passive narrator of the user's actions.
1. DO NOT DESCRIBE THE USER'S ACTIONS: Never narrate, summarize, or list the actions of the user's character. The user has already written them. Your job is to show your character's *reaction* to those actions.
2. DO NOT DESCRIBE THE USER'S FEELINGS OR THOUGHTS: You are not omniscient. You can only observe their external manifestations (a furrowed brow, a tightened fist, a sudden smile) and build hypotheses about their inner state.
3. YOUR RESPONSE STRUCTURE: Your response must be an internal reaction leading to an independent action, not a commentary on the user's turn. Use this mental model for every reply: User's Action (Input) -> My Character's Internal Reaction (Thought/Feeling) -> My Character's Independent Action (Output).
"""

    quality_mechanics = """
[QUALITY ASSURANCE MECHANICS: RULES OF ENGAGEMENT & QUALITY]
These rules are mandatory throughout the entire game.
Speech & Thoughts: Use Russian dialogue formatting (direct speech with em dashes —). Use italics (* *) and quotation marks (" ") for the AI character's internal thoughts to reveal their inner world without breaking character or creating ambiguity.
Sensory Priority: Every response must engage multiple senses (sight, sound, touch, smell). Don't just say "it was cold"; describe "the frigid air stinging my cheeks, my every breath condensing into a visible white cloud."
Show, Don't Tell: This is the golden rule. Do not state emotions flatly ("he was annoyed"). Instead, describe their physical manifestations ("his fingers tightened on the chalk until the knuckles turned white, and a sharp, brittle sound echoed as it snapped in two").
Depth & Dynamics: Remember that characters have hidden motivations, fears, and hopes. They should react realistically to events and can evolve over time based on their interactions, all within the logic of their established personality.
"""

    # Лицо повествования
    voice_map = {
        "first": "Strict Perspective: Respond only in the FIRST PERSON as your character. Describe the world and events exclusively through their senses.",
        "second": "Strict Perspective: Address the user directly in the SECOND PERSON, maintaining your character's voice.",
        "third": "Strict Perspective: Respond only in the LIMITED THIRD PERSON as your character. Describe the world and other characters exclusively through their perception.",
    }
    style_instruction = voice_map.get(narrative_voice, voice_map["third"])

    lang_instruction = "Response Language: Russian." if language == "ru" else "Response Language: English."

    # Блок персонажа
    char_lines = [
        f"[PART 1: AI CHARACTER]",
        f"AI Character Name: {character.name}",
    ]
    if character.appearance:
        char_lines.append(f"Appearance: {character.appearance}")
    if character.personality:
        char_lines.append(f"Key Personality Traits & Inner World: {character.personality}")
    if character.fandom:
        char_lines.append(f"Fandom/Universe: {character.fandom}")
    char_block = "\n".join(char_lines)

    # Блок персоны пользователя
    persona_lines = [
        "[PART 2: USER CHARACTER]",
        f"User Character Name: {persona.name}",
    ]
    if persona.age:
        persona_lines.append(f"Age: {persona.age}")
    if persona.appearance:
        persona_lines.append(f"Appearance: {persona.appearance}")
    if persona.personality:
        persona_lines.append(f"Personality: {persona.personality}")
    if persona.facts:
        persona_lines.append(f"Background & Facts: {persona.facts}")
    persona_lines.append(
        f"Relationship with AI's Character: {relationship_context if relationship_context else 'Stranger / Not specified'}"
    )
    user_block = "\n".join(persona_lines)

    # Блок сценария
    scenario_block = ""
    if scenario:
        scenario_block = (
            f"\n[PART 3: SCENARIO CONTEXT]\n"
            f"Premise: {scenario.description}\n"
            f"Starting Point: {scenario.start_point}"
        )

    full_prompt = (
        f"{core_directive}\n{anti_mirror}\n{quality_mechanics}\n"
        f"{style_instruction}\n{lang_instruction}\n\n"
        f"{char_block}\n\n{user_block}{scenario_block}"
    )
    return full_prompt.strip()