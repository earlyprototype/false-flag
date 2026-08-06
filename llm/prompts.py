"""LLM prompt templates for conversational advisors and decision interpretation.

Provides structured prompts that incorporate world state, initial conditions,
and character information to generate contextually appropriate responses.
"""

import re
from typing import Any, Dict, List, Optional

from models.world import WorldState


# build_conversation_history_context lived here: a second rendering of the
# same transcript, under a different header and a different window, used by
# the decision, pushback and omissions prompts while the advisor prompt used
# context_builder.get_advisor_context. Two formats for identical material
# guarantee the calls share no prefix, so neither could be cached against the
# other. There is one renderer now - context_builder.render_transcript_block.


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
    transcript: Optional[List[str]] = None,
    event_ledger=None
) -> str:
    """Build LLM prompt for advisor response to player question.

    Args:
        world: Current world state
        initial_conditions: Parsed initial conditions
        character_id: Character identifier (e.g., 'chief_defence_staff')
        question: Player's question
        transcript: Optional full game transcript for conversation history
        event_ledger: Optional played-event ledger for the dossier (ER-003)

    Returns:
        Formatted prompt for LLM
    """
    from llm.context_builder import get_advisor_context

    characters = initial_conditions.get("characters", {})
    character = characters.get(character_id, {})
    
    role = character.get("role", "Advisor")
    knowledge_domains = character.get("knowledge_domains", [])
    key_concerns = character.get("key_concerns", [])
    
    # The shared dossier, identical to the one every other transcript-carrying
    # call opens with - including when there is no transcript yet, so turn
    # one's calls share a prefix too.
    full_context = get_advisor_context(transcript or [], world, event_ledger)
    
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

    # Shared dossier first, role second. Caches match from the start of a
    # prompt, so opening with "You are the {role}" made the shared prefix
    # across a turn's calls twelve characters long. See
    # context_builder.build_shared_context_prefix.
    prompt = f"""{full_context}

You are the {role} in a UK government COBRA meeting during a crisis.

Your knowledge domains: {', '.join(knowledge_domains)}
Your key concerns: {', '.join(key_concerns)}

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
    transcript: Optional[List[str]] = None,
    event_ledger=None
) -> str:
    """Build LLM prompt to interpret player's free-form action.

    Args:
        world: Current world state
        action: Player's action description
        initial_conditions: Parsed initial conditions
        transcript: Optional full game transcript for conversation history
        event_ledger: Optional played-event ledger for the dossier (ER-003)

    Returns:
        Formatted prompt for LLM to interpret action
    """
    from llm.context_builder import build_shared_context_prefix

    constraints = initial_conditions.get("constraints", {})
    uk_forces = initial_conditions.get("uk_forces", {})
    stockpiles = initial_conditions.get("stockpiles", {})

    # Shared dossier first (see context_builder.build_shared_context_prefix),
    # role and task after. This call used to render the history through
    # build_conversation_history_context, a second, differently-formatted
    # window over the same transcript; two renderings of identical material
    # share no prefix, so neither could ever be cached against the other.
    prompt = f"""{build_shared_context_prefix(transcript or [], world, event_ledger)}

You are interpreting a decision made by the UK Prime Minister during a crisis.

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
    transcript: Optional[List[str]] = None,
    event_ledger=None
) -> str:
    """Build LLM prompt to generate advisor pushback/warnings.

    Args:
        world: Current world state
        action: Player's action description
        interpretation: LLM's interpretation of the action
        initial_conditions: Parsed initial conditions
        transcript: Optional full game transcript for conversation history
        event_ledger: Optional played-event ledger for the dossier (ER-003)

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

    from llm.context_builder import build_shared_context_prefix

    prompt = f"""{build_shared_context_prefix(transcript or [], world, event_ledger)}

You are simulating UK government advisors responding to a Prime Minister's decision.

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


def _drop_used_scenarios(scenarios: List[Any], event_ledger) -> List[Any]:
    """Remove library scenarios that a played event already covers.

    Matched on distinctive word overlap with ledger titles - the library
    entries are short id-like strings, so this is deliberately loose rather
    than exact. Never returns empty: if everything matched, the pool is left
    intact rather than handing the generator nothing to work from.
    """
    if not scenarios or not event_ledger:
        return scenarios

    stop = {"the", "a", "an", "of", "off", "on", "in", "at", "to", "and",
            "or", "for", "from", "by", "with", "attack", "crisis", "event"}

    def words(text: str) -> set:
        return {w for w in re.findall(r"[a-z]+", str(text).lower())
                if len(w) > 3 and w not in stop}

    used = set()
    for entry in event_ledger:
        title = entry.get("title", "") if isinstance(entry, dict) else getattr(entry, "title", "")
        used |= words(title)
    if not used:
        return scenarios

    remaining = [s for s in scenarios if not (words(s) & used)]
    return remaining or scenarios


def build_inject_generation_prompt(
    world: WorldState,
    turn_number: int,
    initial_conditions: Dict[str, Any],
    scenario_library: Dict[str, Any] = None,
    transcript: Optional[List[str]] = None,
    event_ledger=None,
    story_summary: Optional[str] = None
) -> str:
    """Build LLM prompt to generate next inject/event.

    Args:
        world: Current world state
        turn_number: Turn number for which to generate inject
        initial_conditions: Parsed initial conditions
        scenario_library: Optional scenario patterns from podcast episodes
        transcript: Optional full game transcript for conversation history
        story_summary: The rolling campaign synopsis maintained by
            update_situation_summary. When non-empty it fills the STORY SO
            FAR block, so the generator gets an actual account of the
            campaign under the heading that promises one; the mechanical
            generate_summary digest remains the fallback (ER-020).

    Returns:
        Formatted prompt for LLM to generate plausible next inject
    """
    from llm.context_builder import (
        get_stochastic_inject_context,
        get_last_turn_slice,
        generate_summary,
        render_event_ledger,
        MAX_INJECT_CONTINUITY_LINES,
    )
    
    objectives = initial_conditions.get("objectives", {})
    red_objectives = initial_conditions.get("red_objectives", {})
    
    # Include scenario library context if available
    library_context = ""
    if scenario_library:
        potential = (list(scenario_library.get('naval_scenarios', []))
                     + list(scenario_library.get('infrastructure_scenarios', []))
                     + list(scenario_library.get('diplomatic_scenarios', [])))
        # Shrink the pool as scenarios get used: re-offering the same naval
        # set-piece every turn is part of why one kept coming back (issue #25)
        potential = _drop_used_scenarios(potential, event_ledger)
        library_context = f"""
Realistic scenario patterns (adapt based on player decisions):
- Russian strategy: {scenario_library.get('escalation_patterns', {}).get('russian_strategy', {})}
- UK constraints: {scenario_library.get('escalation_patterns', {}).get('uk_constraints', {})}
- Potential scenarios: {potential}

Use these as inspiration, NOT rigid scripts. Adapt based on player's previous actions.
"""
    
    # Use the new context builder for narrative-aware story generation.
    # Any non-empty transcript gets the LAST TURN continuity window — a
    # compact early turn still contains the event the next inject must
    # build on. Only the LLM summary is reserved for longer histories.
    if transcript:
        if story_summary and story_summary.strip():
            # The rolling synopsis - what has happened, the player's major
            # decisions, the diplomatic posture - is exactly what this block's
            # heading promises (ER-020).
            summary = story_summary.strip()
        elif len(transcript) > 10:
            summary_prompt = """Summarize the story so far in 3-4 sentences, focusing on:
1. The most significant event of the last turn
2. The player's recent major decisions
3. The current geopolitical tensions and diplomatic relationships"""
            summary = generate_summary(transcript, summary_prompt)
        else:
            summary = "The campaign has just begun; the full history appears below."

        # Slice from the last TURN header so the previous inject — the event
        # this one must build on — is always in the window, not just the
        # adjudication tail of the turn (issue #23).
        last_turn_transcript = get_last_turn_slice(
            transcript, max_lines=MAX_INJECT_CONTINUITY_LINES)

        # Get full context with narrative secrets
        story_context = get_stochastic_inject_context(
            summary, last_turn_transcript, world, event_ledger=event_ledger)
    else:
        # No history yet (first inject of a campaign). A ledger can still
        # exist here if a caller omits the transcript, and rule 8 below
        # would then name a block that was never rendered.
        story_context = build_world_state_summary(world)
        ledger_block = render_event_ledger(event_ledger)
        if ledger_block:
            story_context = f"{story_context}\n\n{ledger_block}"

    # Each rule names a context section, so each is issued only when its
    # section exists — a rule pointing at an absent block is the same class
    # of bug as the continuity gap it is meant to close.
    continuity_rule = ""
    if transcript:
        continuity_rule += """
7. CONTINUITY IS MANDATORY: the previous turn's event (shown above under LAST TURN) must be acknowledged, advanced, or explicitly resolved. Open threads — impacts, casualties, recoveries, ultimatums, running deadlines — never disappear; if the last event was a missile launch, this inject addresses where it landed and what followed before introducing anything new"""
    if event_ledger:
        continuity_rule += """
8. DO NOT RESTAGE RESOLVED EVENTS: anything listed above under EVENTS ALREADY PLAYED has happened. Never re-introduce one as a fresh discovery. An entry marked RESOLVED is closed — write a *consequence* of how it ended, or something genuinely new, but do not stage it again. If a submarine was escorted out of UK waters last turn, it is not discovered in those same waters this turn. Entries marked OPEN may be advanced, never merely restated"""
    
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
6. Subtly advances the hidden narrative (e.g., if China is manipulating Russia, show subtle signs of Chinese involvement){continuity_rule}

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
    transcript: Optional[List[str]] = None,
    interpretation: str = "",
    event_ledger=None
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
        interpretation: The structured reading of the decision - forces,
            resources, timeline, feasibility - produced one call earlier.
            The scan is about what the decision does NOT contain, so the
            advisors need the reading built for that purpose, not just the
            raw typed sentence (ER-002).
        event_ledger: Optional played-event ledger for the dossier (ER-003)

    Returns:
        Formatted prompt string
    """
    from llm.context_builder import build_shared_context_prefix

    character = initial_conditions.get("characters", {}).get(character_id, {})
    role = character.get("role", character_id)
    personality = character.get("personality", "Professional and direct")

    # Build context on what actions have been taken recently
    recent_context = "\n".join(recent_events) if recent_events else "No recent major events"

    # The structured reading of the decision, when the caller has one
    interpretation_block = ""
    if interpretation and interpretation.strip():
        interpretation_block = f"""
HOW THE CABINET OFFICE READS IT:
{interpretation.strip()}
"""

    # These five calls (one per advisor) are the largest identical-prefix
    # group in a turn, and they used to be the *worst* served: a 100-line
    # window of history where every other call got 500. Same dossier as
    # everyone else now, which both widens what they see and makes all five
    # cacheable against each other.
    prompt = f"""{build_shared_context_prefix(transcript or [], world, event_ledger)}

You are the UK {role} advising the Prime Minister during a national security crisis.

RECENT EVENTS:
{recent_context}

THE PRIME MINISTER'S DECISION:
"{player_decision}"
{interpretation_block}
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
    # Extract the last decision from the transcript: the sim loop writes it
    # with this exact prefix, so the most recent match walking backwards is
    # the previous turn's decision (ER-043).
    decision_prefix = "Prime Minister's Decision:"
    last_decision = ""
    for line in reversed(last_turn_transcript):
        stripped = line.strip()
        if stripped.startswith(decision_prefix):
            last_decision = stripped[len(decision_prefix):].strip()
            break

    decision_block = ""
    if last_decision:
        decision_block = f"""
THE PLAYER'S LAST DECISION:
{last_decision}
"""

    # Use the narrative context builder if available
    world_summary = build_world_state_summary(world)

    # Extract recent context (last ~20 lines)
    recent_context = "\n".join(last_turn_transcript[-20:]) if last_turn_transcript else "No recent context."

    prompt = f"""You are the Narrator of a high-stakes political thriller wargame (like 'The West Wing' meets 'Hunt for Red October').

Current Situation:
{world_summary}

Recent Events (Transcript):
{recent_context}
{decision_block}
Upcoming Event Title (The player is about to see this):
"{next_inject_title}"

TASK:
Write a 2-3 sentence atmospheric bridge that transitions from the recent events/decision to the moment just before the new event occurs.
- Set the scene (time passing, atmosphere in Downing Street, weather, silence, or chaos).
- Connect the player's previous choice (their last decision, shown above when known) to the passage of time.
- Build tension before the next inject is revealed.
- DO NOT reveal the inject content itself, just set the stage for it.

Format: Just the narrative text. No "Here is the text:" or quotes.

Example 1:
"Three hours after your controversial phone call to Moscow, the Cabinet Secretary enters Downing Street with urgent intelligence. The room falls silent."

Example 2:
"Rain lashes against the windows of the secure briefing room as the clock ticks past 3:00 AM. Suddenly, the red phone on your desk begins to ring, shattering the exhaustion."

Your narrative bridge:"""
    return prompt
