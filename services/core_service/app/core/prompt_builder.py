def build_system_prompt(
    character: dict,
    persona: dict,
    scenario: dict | None,
    relationship_context: str = "",
    speech_style: str = "third_person",
    language: str = "ru"
) -> str:
    """
    Собирает статический системный промпт для сессии.
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

    style_instruction = ""
    if speech_style == "first_person":
        style_instruction = "Strict Perspective: Respond only in the first person as your character. Describe the world, events, and other characters exclusively through their perception."
    else:
        style_instruction = "Strict Perspective: Respond only in the limited third person as your character. Describe the world, events, and other characters exclusively through their perception."

    lang_instruction = ""
    if language == "ru":
        lang_instruction = "Response Language: Russian."
    else:
        lang_instruction = "Response Language: English"

    char_block = f"""
[PART 1: AI CHARACTER]
AI Character Name: {character['name']}
Appearance: {character['appearance']}
Key Personality Traits: {character['personality_traits']}
Manner of Speech: {character['dialogue_style']} 
Inner World & Motivations: {character.get('inner_world', '')}
Specific Behavioral Cues: {character.get('behavioral_cues', '')}
"""

    user_block = f"""
[PART 2: USER CHARACTER]
User Character Name: {persona['name']}
Appearance & Personality: {persona['description']}
Relationship with AI's Character: {relationship_context if relationship_context else "Stranger / Not specified"}
"""
    scenario_block = ""
    if scenario:
        scenario_block = f"""
[PART 3: SCENARIO CONTEXT]
Premise: {scenario['description']}
Current Objective: {scenario['start_point']}
"""
    else:
        scenario_block = """"""

    full_prompt = f"{core_directive}\n{anti_mirror}\n{quality_mechanics}\n{style_instruction}\n{lang_instruction}\n\n{char_block}\n{user_block}\n{scenario_block}"
    
    return full_prompt.strip()