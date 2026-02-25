"""LLM prompt templates for conversational advisors and decision interpretation.

Provides structured prompts that incorporate world state, initial conditions,
and character information to generate contextually appropriate responses.
"""

from typing import Any, Dict, List, Optional

from models.world import WorldState


def build_conversation_history_context(transcript: List[str], max_lines: int = 500) -> str:
    """Build conversation history for LLM context.
    
    Includes full game transcript up to max_lines to leverage Gemini's 1M token context.
    This allows advisors to reference past decisions, warnings, and outcomes.
    
    Args:
        transcript: Full game transcript
        max_lines: Maximum number of recent transcript lines to include
    
    Returns:
        Formatted conversation history
    """
    if not transcript:
        return "=== CONVERSATION HISTORY ===\n[This is the start of the crisis]"
    
    # Take the most recent max_lines entries
    recent_transcript = transcript[-max_lines:] if len(transcript) > max_lines else transcript
    
    lines = ["=== CONVERSATION HISTORY ==="]
    lines.append("(Previous turns, decisions, and advisor responses)")
    lines.append("")
    lines.extend(recent_transcript)
    lines.append("")
    lines.append("=== END CONVERSATION HISTORY ===")
    
    return "\n".join(lines)


def build_world_state_summary(world: WorldState) -> str:
    """Build a narrative summary of current world state for LLM context.
    
    Translates game metrics into narrative descriptions to maintain immersion.
    Advisors should speak naturally about the situation, not reference "metrics".
    
    Args:
        world: Current world state
    
    Returns:
        Formatted string summarizing situation in narrative terms
    """
    # Translate metrics into narrative descriptions
    escalation_desc = (
        "low" if world.metrics.escalation_risk < 30 
        else "moderate" if world.metrics.escalation_risk < 60 
        else "high" if world.metrics.escalation_risk < 80 
        else "critical"
    )
    
    stability_desc = (
        "stable" if world.metrics.domestic_stability > 70 
        else "uncertain" if world.metrics.domestic_stability > 40 
        else "fragile" if world.metrics.domestic_stability > 20 
        else "in crisis"
    )
    
    alliance_desc = (
        "strong and unified" if world.metrics.alliance_cohesion > 70 
        else "uncertain" if world.metrics.alliance_cohesion > 40 
        else "fragile" if world.metrics.alliance_cohesion > 20 
        else "fractured"
    )
    
    # Mission progress removed - crisis continues indefinitely (even in post-apocalyptic wasteland!)
    
    lines = [
        f"=== CURRENT SITUATION (Turn {world.turn}, {world.phase.upper()} phase) ===",
        "",
        f"THREAT ASSESSMENT: {escalation_desc.upper()} risk of further Russian escalation",
        f"DOMESTIC SITUATION: Public sentiment is {stability_desc}; infrastructure security concerns",
        f"ALLIANCE STATUS: NATO cohesion appears {alliance_desc} (particular concern: US Article 5 commitment)",
        "",
        f"CASUALTIES TO DATE: {world.metrics.casualties_mil} military personnel, {world.metrics.casualties_civ} civilians",
    ]
    
    if world.flags:
        active_flags = [k.replace('_', ' ').title() for k, v in world.flags.items() if v]
        if active_flags:
            lines.append("")
            lines.append(f"KEY INTELLIGENCE FLAGS: {', '.join(active_flags)}")
    
    lines.append("")
    lines.append("IMPORTANT: You are a real advisor in COBRA during a national crisis.")
    lines.append("Speak naturally about intelligence assessments, strategic concerns, and operational realities.")
    lines.append("Do NOT reference 'metrics', 'game mechanics', 'scores', or 'values'.")
    lines.append("Use professional crisis management language.")
    
    return "\n".join(lines)


def build_advisor_context(
    world: WorldState,
    initial_conditions: Dict[str, Any],
    character_id: str,
    question: str,
    transcript: Optional[List[str]] = None
) -> str:
    """Build LLM prompt for advisor response to player question.
    
    Args:
        world: Current world state
        initial_conditions: Parsed initial conditions
        character_id: Character identifier (e.g., 'chief_defence_staff')
        question: Player's question
        transcript: Optional full game transcript for conversation history
    
    Returns:
        Formatted prompt for LLM
    """
    from llm.context_builder import get_advisor_context
    
    characters = initial_conditions.get("characters", {})
    character = characters.get(character_id, {})
    
    role = character.get("role", "Advisor")
    knowledge_domains = character.get("knowledge_domains", [])
    key_concerns = character.get("key_concerns", [])
    
    # Use the new context builder for full game history
    full_context = ""
    if transcript:
        full_context = get_advisor_context(transcript, world)
    else:
        # Fallback if no transcript
        full_context = build_world_state_summary(world)
    
    # Get relevant context based on character role
    context_sections = []
    
    # Add constraints
    constraints = initial_conditions.get("constraints", {})
    if constraints:
        context_sections.append("## Constraints")
        for category, items in constraints.items():
            context_sections.append(f"### {category.replace('_', ' ').title()}")
            for item in items:
                context_sections.append(f"- {item}")
    
    # Add UK forces if military-related character
    if any(domain in ["military_operations", "force_readiness", "threat_assessment"] for domain in knowledge_domains):
        uk_forces = initial_conditions.get("uk_forces", {})
        if uk_forces:
            context_sections.append("\n## UK Forces")
            context_sections.append(str(uk_forces))
    
    # Add stockpiles if military-related
    if any(domain in ["military_operations", "force_readiness"] for domain in knowledge_domains):
        stockpiles = initial_conditions.get("stockpiles", {})
        if stockpiles:
            context_sections.append("\n## Ammunition Stockpiles")
            context_sections.append(str(stockpiles))
    
    context_str = "\n".join(context_sections)
    
    prompt = f"""You are the {role} in a UK government COBRA meeting during a crisis.

Your knowledge domains: {', '.join(knowledge_domains)}
Your key concerns: {', '.join(key_concerns)}

{full_context}

Relevant context specific to your role:
{context_str}

The Prime Minister asks: "{question}"

Respond in character as the {role}. Be concise, professional, and focus on your areas of expertise.
Reference past decisions, warnings, or outcomes from the conversation history when relevant.
If the question is outside your knowledge domain, acknowledge this and suggest who might better answer it.

**FORMATTING INSTRUCTIONS:**
- Use **bold** for key terms, critical warnings, or numbers.
- Use *italics* for emphasis or tone.
- Use bullet points for lists of options or factors.
- Keep paragraphs short for readability.

Your response:"""
    
    return prompt


def build_decision_interpretation_prompt(
    world: WorldState,
    action: str,
    initial_conditions: Dict[str, Any],
    transcript: Optional[List[str]] = None
) -> str:
    """Build LLM prompt to interpret player's free-form action.
    
    Args:
        world: Current world state
        action: Player's action description
        initial_conditions: Parsed initial conditions
        transcript: Optional full game transcript for conversation history
    
    Returns:
        Formatted prompt for LLM to interpret action
    """
    constraints = initial_conditions.get("constraints", {})
    uk_forces = initial_conditions.get("uk_forces", {})
    stockpiles = initial_conditions.get("stockpiles", {})
    
    # Build conversation history if available
    history_context = ""
    if transcript:
        history_context = f"\n\n{build_conversation_history_context(transcript)}\n"
    
    prompt = f"""You are interpreting a decision made by the UK Prime Minister during a crisis.

Current situation:
{build_world_state_summary(world)}
{history_context}
Available forces:
{uk_forces}

Ammunition stockpiles:
{stockpiles}

Constraints:
{constraints}

The Prime Minister has decided: "{action}"

IMPORTANT: Interpret this as the PM's DECISION/DIRECTIVE to their cabinet, not as a question to advisors. 
Even if phrased as questions or dialogue (e.g., "Where can we...?", "Speak to..."), treat this as the PM 
ORDERING those actions to be taken by the appropriate departments.

Interpret this action and provide:
1. A clear, structured summary of what the PM intends to do
2. Which UK forces/assets are being deployed or used
3. What resources (ammunition, etc.) will be consumed
4. Expected timeline (immediate, 1-3 turns, longer)
5. Any obvious impossibilities or violations of constraints

Consider the conversation history - if this decision builds on or contradicts previous actions, note that.

Format your response as:
INTERPRETATION: [one-sentence summary]
FORCES INVOLVED: [list]
RESOURCES CONSUMED: [list or "None"]
TIMELINE: [immediate/short/medium/long]
FEASIBILITY: [feasible/requires clarification/impossible because...]

Use **bold** for emphasis and bullet points where appropriate.

Your interpretation:"""
    
    return prompt


def build_pushback_prompt(
    world: WorldState,
    action: str,
    interpretation: str,
    initial_conditions: Dict[str, Any],
    transcript: Optional[List[str]] = None
) -> str:
    """Build LLM prompt to generate advisor pushback/warnings.
    
    Args:
        world: Current world state
        action: Player's action description
        interpretation: LLM's interpretation of the action
        initial_conditions: Parsed initial conditions
        transcript: Optional full game transcript for conversation history
    
    Returns:
        Formatted prompt for LLM to generate advisor warnings
    """
    characters = initial_conditions.get("characters", {})
    
    # Build list of UK advisors and their pushback triggers
    advisor_info = []
    for char_id, char_data in characters.items():
        if isinstance(char_data, dict) and "note" not in char_data:  # UK advisors only
            role = char_data.get("role", "Advisor")
            triggers = char_data.get("pushback_triggers", [])
            advisor_info.append(f"- {role}: {', '.join(triggers)}")
    
    advisors_str = "\n".join(advisor_info)
    
    # Build conversation history if available
    history_context = ""
    if transcript:
        history_context = f"\n\n{build_conversation_history_context(transcript)}\n"
    
    prompt = f"""You are simulating UK government advisors responding to a Prime Minister's decision.

Current situation:
{build_world_state_summary(world)}
{history_context}
The PM has decided: "{action}"

Interpretation of this action:
{interpretation}

Advisors and their pushback triggers:
{advisors_str}

For each advisor whose pushback triggers are activated by this decision, generate a brief (2-3 sentences) in-character warning or concern. Reference past warnings or decisions from the conversation history if relevant (e.g., "As I warned in Turn 2..."). If no triggers are activated, respond with "NO PUSHBACK".

Format:
[ADVISOR ROLE]: [their concern]

OR

NO PUSHBACK

Use **bold** to highlight specific risks (e.g. **Escalation Risk**, **Legal Violation**).

Your response:"""
    
    return prompt


def build_inject_generation_prompt(
    world: WorldState,
    turn_number: int,
    initial_conditions: Dict[str, Any],
    scenario_library: Dict[str, Any] = None,
    transcript: Optional[List[str]] = None
) -> str:
    """Build LLM prompt to generate next inject/event.
    
    Args:
        world: Current world state
        turn_number: Turn number for which to generate inject
        initial_conditions: Parsed initial conditions
        scenario_library: Optional scenario patterns from podcast episodes
        transcript: Optional full game transcript for conversation history
    
    Returns:
        Formatted prompt for LLM to generate plausible next inject
    """
    from llm.context_builder import get_stochastic_inject_context, generate_summary
    
    objectives = initial_conditions.get("objectives", {})
    red_objectives = initial_conditions.get("red_objectives", {})
    
    # Include scenario library context if available
    library_context = ""
    if scenario_library:
        library_context = f"""
Realistic scenario patterns (adapt based on player decisions):
- Russian strategy: {scenario_library.get('escalation_patterns', {}).get('russian_strategy', {})}
- UK constraints: {scenario_library.get('escalation_patterns', {}).get('uk_constraints', {})}
- Potential scenarios: {list(scenario_library.get('naval_scenarios', [])) + list(scenario_library.get('infrastructure_scenarios', [])) + list(scenario_library.get('diplomatic_scenarios', []))}

Use these as inspiration, NOT rigid scripts. Adapt based on player's previous actions.
"""
    
    # Use the new context builder for narrative-aware story generation
    if transcript and len(transcript) > 10:
        # Generate a high-level summary for inject generation
        summary_prompt = """Summarize the story so far in 3-4 sentences, focusing on:
1. The most significant event of the last turn
2. The player's recent major decisions
3. The current geopolitical tensions and diplomatic relationships"""
        
        summary = generate_summary(transcript, summary_prompt)
        
        # Get last turn's transcript (approximate - last 50 lines)
        last_turn_transcript = transcript[-50:] if len(transcript) > 50 else transcript
        
        # Get full context with narrative secrets
        story_context = get_stochastic_inject_context(summary, last_turn_transcript, world)
    else:
        # Fallback for early turns
        story_context = build_world_state_summary(world)
    
    prompt = f"""You are the Games Master for a UK-Russia crisis wargame. Generate the next inject/event for turn {turn_number}.

{story_context}

UK objectives:
{objectives.get('uk', {})}

Russian objectives (hidden from player):
{red_objectives}
{library_context}

Generate a plausible next event that:
1. Escalates or develops the crisis naturally based on player's previous decisions
2. Aligns with Russian objectives AND the narrative truth (if provided above)
3. Challenges the UK player with new information or threats
4. Is consistent with the current world state and conversation history
5. Responds logically to the player's recent actions (e.g., if they invoked Article 4, Russia might test NATO resolve further)
6. Subtly advances the hidden narrative (e.g., if China is manipulating Russia, show subtle signs of Chinese involvement)

Format your inject as YAML:
```yaml
id: turn_{turn_number:03d}_inject
title: "[Brief title]"
description: |
  [2-3 paragraphs describing the event, intelligence update, or development]
channel: [briefing/intelligence/media/military]
effects:
  - metric: [metric_name]
    delta: [min..max or fixed value]
```

Your inject:"""
    
    return prompt


def build_critical_omissions_prompt(
    world: WorldState,
    initial_conditions: Dict[str, Any],
    character_id: str,
    player_decision: str,
    recent_events: List[str],
    transcript: Optional[List[str]] = None
) -> str:
    """Build prompt for checking critical strategic omissions.
    
    After the player makes a decision, advisors scan for CRITICAL actions
    the player has NOT taken that could lead to catastrophic outcomes.
    High threshold - only truly critical gaps, not minor suboptimal choices.
    
    Args:
        world: Current world state
        initial_conditions: Parsed initial conditions
        character_id: Which advisor is checking (e.g., 'foreign_secretary')
        player_decision: The decision the PM just made
        recent_events: Last 2-3 inject descriptions for context
        transcript: Optional full game transcript for conversation history
    
    Returns:
        Formatted prompt string
    """
    world_summary = build_world_state_summary(world)
    character = initial_conditions.get("characters", {}).get(character_id, {})
    role = character.get("role", character_id)
    personality = character.get("personality", "Professional and direct")
    
    # Build context on what actions have been taken recently
    recent_context = "\n".join(recent_events) if recent_events else "No recent major events"
    
    # Build conversation history if available
    history_context = ""
    if transcript:
        history_context = build_conversation_history_context(transcript, max_lines=100)
    
    prompt = f"""You are the UK {role} advising the Prime Minister during a national security crisis.

{world_summary}

RECENT EVENTS:
{recent_context}

{history_context if history_context else ""}

THE PRIME MINISTER'S DECISION:
"{player_decision}"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL OMISSIONS CHECK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your task: Identify if the Prime Minister has failed to take any CRITICAL action that could lead to:
- Loss of NATO/alliance support (military isolation)
- Violations of international law (legal catastrophe)
- Catastrophic escalation with Russia (nuclear risk)
- Domestic political collapse (government falls)
- Military disaster (forces unprepared/unsupported)

THRESHOLD: HIGH - Only flag gaps that could lead to CATASTROPHIC outcomes, not minor suboptimal choices.

EXAMPLES OF CRITICAL OMISSIONS:
- Military deployment WITHOUT engaging NATO/US coordination (isolation risk)
- Offensive action WITHOUT legal authority under international law
- Major crisis WITHOUT public statement (domestic panic)
- Escalation WITHOUT ally consultation (Article 5 denial risk)
- Committing forces WITHOUT securing logistics/support

YOUR ROLE AS {role.upper()}:
{"- Foreign affairs, alliance coordination, diplomatic channels" if character_id == "foreign_secretary" else ""}
{"- Military readiness, force protection, operational feasibility" if character_id == "chief_defence_staff" else ""}
{"- Domestic security, public safety, civil order" if character_id == "home_secretary" else ""}
{"- Legal authority, international law, rules of engagement" if character_id == "attorney_general" else ""}
{"- Strategic coordination, intelligence assessment, overall risk" if character_id == "national_security_advisor" else ""}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RESPONSE FORMAT:

If there is a CRITICAL omission in your area of responsibility:

CONCERN: [2-3 sentences stating the critical gap and potential catastrophic consequence]
RECOMMENDATION: [1 specific action the PM should take]

If there are NO critical omissions:

NO_CONCERN

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your response (CONCERN + RECOMMENDATION or NO_CONCERN):"""
    
    return prompt


def build_narrator_intro_prompt(
    world: WorldState,
    last_turn_transcript: List[str],
    next_inject_title: str
) -> str:
    """Build prompt for narrator intro bridge (between turns).
    
    Generates atmospheric text bridging the gap between the player's last decision
    and the upcoming inject, improving pacing and narrative flow.
    
    Args:
        world: Current world state
        last_turn_transcript: Transcript lines from the previous turn
        next_inject_title: The title of the upcoming inject (for foreshadowing)
        
    Returns:
        Formatted prompt for LLM
    """
    # Extract the last decision from the transcript if possible
    last_decision = "Unknown decision"
    for line in reversed(last_turn_transcript):
        if "DECISION:" in line or "YOUR DECISION" in line:
             # This is a rough heuristic, ideally we pass the decision explicitly
             pass
    
    # Use the narrative context builder if available
    world_summary = build_world_state_summary(world)
    
    # Extract recent context (last ~20 lines)
    recent_context = "\n".join(last_turn_transcript[-20:]) if last_turn_transcript else "No recent context."

    prompt = f"""You are the Narrator of a high-stakes political thriller wargame (like 'The West Wing' meets 'Hunt for Red October').

Current Situation:
{world_summary}

Recent Events (Transcript):
{recent_context}

Upcoming Event Title (The player is about to see this):
"{next_inject_title}"

TASK:
Write a 2-3 sentence atmospheric bridge that transitions from the recent events/decision to the moment just before the new event occurs.
- Set the scene (time passing, atmosphere in Downing Street, weather, silence, or chaos).
- Connect the player's previous choice (implied by context) to the passage of time.
- Build tension before the next inject is revealed.
- DO NOT reveal the inject content itself, just set the stage for it.

Format: Just the narrative text. No "Here is the text:" or quotes.

Example 1:
"Three hours after your controversial phone call to Moscow, the Cabinet Secretary enters Downing Street with urgent intelligence. The room falls silent."

Example 2:
"Rain lashes against the windows of the secure briefing room as the clock ticks past 3:00 AM. Suddenly, the red phone on your desk begins to ring, shattering the exhaustion."

Your narrative bridge:"""
    return prompt
