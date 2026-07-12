"""
ContextBuilder: A centralized module for assembling tailored LLM context.

This module implements the role-based context strategy, providing specific,
efficient, and secure context for each type of LLM agent in the simulation.
"""

import re
from typing import List

from models.world import WorldState

# A full game transcript is a list of strings, where each string is a line of dialogue,
# an action, or a system message.
FullTranscript = List[str]

# Maximum transcript lines embedded in advisor context (keeps prompts bounded)
MAX_ADVISOR_TRANSCRIPT_LINES = 500

def get_advisor_context(transcript: FullTranscript, world_state: WorldState) -> str:
    """
    Returns the game transcript (capped at the most recent
    MAX_ADVISOR_TRANSCRIPT_LINES lines) with a world state summary.
    Used for the Advisory Council to ensure recall and persona consistency.
    """
    context_parts = []
    
    # Add world state summary at the top
    context_parts.append("=" * 60)
    context_parts.append("CURRENT SITUATION")
    context_parts.append("=" * 60)
    context_parts.append(f"Turn: {world_state.turn}")
    context_parts.append(f"Phase: {world_state.phase}")
    context_parts.append(f"Escalation Risk: {world_state.metrics.escalation_risk}/100")
    context_parts.append(f"Domestic Stability: {world_state.metrics.domestic_stability}/100")
    context_parts.append(f"Alliance Cohesion: {world_state.metrics.alliance_cohesion}/100")
    context_parts.append(f"Military Casualties: {world_state.metrics.casualties_mil}")
    context_parts.append(f"Civilian Casualties: {world_state.metrics.casualties_civ}")
    context_parts.append("")
    
    # Add transcript (capped to keep the prompt bounded on long games)
    context_parts.append("=" * 60)
    context_parts.append("COMPLETE GAME HISTORY")
    context_parts.append("=" * 60)
    if len(transcript) > MAX_ADVISOR_TRANSCRIPT_LINES:
        context_parts.append("[... earlier history truncated ...]")
        context_parts.extend(transcript[-MAX_ADVISOR_TRANSCRIPT_LINES:])
    else:
        context_parts.extend(transcript)

    return "\n".join(context_parts)

def get_decision_interpreter_context(current_turn_transcript: List[str], world_state: WorldState) -> str:
    """
    Returns only the transcript for the current turn's discussion.
    Used for interpreting the player's final decision.
    """
    context_parts = []
    
    # Add current situation
    context_parts.append("=" * 60)
    context_parts.append(f"TURN {world_state.turn} - DECISION INTERPRETATION")
    context_parts.append("=" * 60)
    context_parts.append(f"Escalation Risk: {world_state.metrics.escalation_risk}/100")
    context_parts.append(f"Domestic Stability: {world_state.metrics.domestic_stability}/100")
    context_parts.append(f"Alliance Cohesion: {world_state.metrics.alliance_cohesion}/100")
    context_parts.append("")
    
    # Add this turn's discussion
    context_parts.append("=" * 60)
    context_parts.append("THIS TURN'S DISCUSSION")
    context_parts.append("=" * 60)
    context_parts.extend(current_turn_transcript)
    
    return "\n".join(context_parts)

def get_stochastic_inject_context(summary: str, last_turn_transcript: List[str], world_state: WorldState) -> str:
    """
    Returns a high-level summary, the last turn's transcript, and narrative secrets.
    Used for creative story generation.
    """
    context_parts = []
    
    # Add current situation
    context_parts.append("=" * 60)
    context_parts.append(f"DYNAMIC INJECT GENERATION - TURN {world_state.turn}")
    context_parts.append("=" * 60)
    context_parts.append(f"Escalation Risk: {world_state.metrics.escalation_risk}/100")
    context_parts.append(f"Domestic Stability: {world_state.metrics.domestic_stability}/100")
    context_parts.append(f"Alliance Cohesion: {world_state.metrics.alliance_cohesion}/100")
    context_parts.append("")
    
    # Add narrative context (the secret truth that guides story generation)
    if world_state.narrative:
        narrative_context = world_state.narrative.to_llm_context()  # No specific country - global truth
        context_parts.append(narrative_context)
        context_parts.append("")
    
    # Add high-level summary
    context_parts.append("=" * 60)
    context_parts.append("STORY SO FAR (HIGH-LEVEL SUMMARY)")
    context_parts.append("=" * 60)
    context_parts.append(summary)
    context_parts.append("")
    
    # Add last turn's transcript for continuity
    context_parts.append("=" * 60)
    context_parts.append(f"LAST TURN (TURN {world_state.turn - 1}) - FOR CONTINUITY")
    context_parts.append("=" * 60)
    context_parts.extend(last_turn_transcript)
    
    return "\n".join(context_parts)

def get_diplomatic_context(transcript: FullTranscript, world_state: WorldState, target_country_code: str) -> str:
    """
    Returns a securely filtered transcript for diplomatic conversations.

    - Includes all direct communications with the target country.
    - Includes all public events (news, official statements).
    - EXCLUDES all internal UK COBRA deliberations.
    """
    filtered_lines = []
    in_public_event = False
    in_diplomatic_exchange = False
    in_cobra_deliberation = False
    
    for line in transcript:
        line_lower = line.lower()
        
        # Detect public events (briefings, news, injects)
        if any(marker in line_lower for marker in ["===", "turn ", "briefing", "breaking news", "intel report"]):
            in_public_event = True
            in_cobra_deliberation = False
            filtered_lines.append(line)
            continue
        
        # Detect diplomatic exchanges with the target country
        if target_country_code.lower() in line_lower or "diplomatic" in line_lower:
            in_diplomatic_exchange = True
            in_cobra_deliberation = False
        
        # Detect COBRA internal discussions
        if any(marker in line_lower for marker in [
            "prime minister:", 
            "national security advisor:", 
            "chief of the defence staff:",
            "home secretary:",
            "foreign secretary:",
            "attorney general:",
            "discussion phase"
        ]):
            in_cobra_deliberation = True
            in_public_event = False
            in_diplomatic_exchange = False
        
        # Include line if it's public or part of a diplomatic exchange
        if (in_public_event or in_diplomatic_exchange) and not in_cobra_deliberation:
            filtered_lines.append(line)
    
    # Build the final context
    context_parts = []
    
    # Add world state summary
    context_parts.append("=" * 60)
    context_parts.append("CURRENT SITUATION")
    context_parts.append("=" * 60)
    context_parts.append(f"Turn: {world_state.turn}")
    context_parts.append(f"UK Escalation Risk: {world_state.metrics.escalation_risk}/100")
    context_parts.append(f"UK Domestic Stability: {world_state.metrics.domestic_stability}/100")
    context_parts.append(f"NATO Alliance Cohesion: {world_state.metrics.alliance_cohesion}/100")
    context_parts.append("")
    
    # Add narrative context if available
    if world_state.narrative:
        narrative_context = world_state.narrative.to_llm_context(target_country_code)
        context_parts.append(narrative_context)
        context_parts.append("")
    
    # Add filtered transcript
    context_parts.append("=" * 60)
    context_parts.append("KNOWN EVENTS AND COMMUNICATIONS")
    context_parts.append("=" * 60)
    context_parts.extend(filtered_lines)
    
    return "\n".join(context_parts)

def get_adjudicator_context(decision: str, summary: str, world_state: WorldState) -> str:
    """
    Returns the player's action, a narrative summary, and the world state.
    Used for context-aware adjudication of metric changes.
    """
    context_parts = []
    
    # Add current situation
    context_parts.append("=" * 60)
    context_parts.append(f"ADJUDICATION - TURN {world_state.turn}")
    context_parts.append("=" * 60)
    context_parts.append("")
    context_parts.append("CURRENT METRICS:")
    context_parts.append(f"  Escalation Risk: {world_state.metrics.escalation_risk}/100")
    context_parts.append(f"  Domestic Stability: {world_state.metrics.domestic_stability}/100")
    context_parts.append(f"  Alliance Cohesion: {world_state.metrics.alliance_cohesion}/100")
    context_parts.append("")
    
    # Add narrative context
    context_parts.append("NARRATIVE CONTEXT:")
    context_parts.append(summary)
    context_parts.append("")
    
    # Add the player's decision
    context_parts.append("=" * 60)
    context_parts.append("PLAYER'S DECISION")
    context_parts.append("=" * 60)
    context_parts.append(decision)
    context_parts.append("")
    
    # Add adjudication instructions
    context_parts.append("=" * 60)
    context_parts.append("INSTRUCTIONS")
    context_parts.append("=" * 60)
    context_parts.append("Based on the player's decision and the narrative context,")
    context_parts.append("determine the impact on each metric:")
    context_parts.append("  - Escalation Risk (0-100): Likelihood of conflict escalating")
    context_parts.append("  - Domestic Stability (0-100): Public confidence and security")
    context_parts.append("  - Alliance Cohesion (0-100): Strength of NATO solidarity")
    context_parts.append("")
    context_parts.append("Consider:")
    context_parts.append("  - The player's track record (from narrative context)")
    context_parts.append("  - The current public mood")
    context_parts.append("  - Recent events and their cumulative effect")
    context_parts.append("")
    
    return "\n".join(context_parts)

def generate_summary(transcript: FullTranscript, summary_prompt: str) -> str:
    """
    Builds a short deterministic digest of the game so far (no LLM call).

    The digest is derived mechanically from the transcript, so no placeholder
    text can leak into downstream prompts. The summary_prompt argument is
    accepted for API compatibility but does not alter the digest.
    """
    del summary_prompt  # Deterministic digest; kept for API compatibility

    turn_numbers = []
    event_lines = []
    for raw_line in transcript:
        line = raw_line.strip()
        if not line:
            continue
        turn_match = re.match(r"^TURN\s+(\d+)\b", line)
        if turn_match:
            turn_numbers.append(int(turn_match.group(1)))
            continue
        # Collect lines that look like events/injects for the digest
        if line.startswith(("[Narrator]", "[Stochastically generated inject]", "***")) or \
                re.match(r"^(BREAKING|INTEL|BRIEFING)\b", line, re.IGNORECASE):
            event_lines.append(line.strip("* ").strip())

    summary_lines = ["STORY DIGEST:"]
    if turn_numbers:
        summary_lines.append(
            f"- Turns played: {len(set(turn_numbers))} (latest: TURN {max(turn_numbers)})"
        )
    summary_lines.append(f"- Transcript length: {len(transcript)} lines")
    if event_lines:
        summary_lines.append("- Recent events:")
        for event in event_lines[-3:]:
            summary_lines.append(f"  - {event[:100]}")
    else:
        summary_lines.append("- No notable events recorded yet.")

    return "\n".join(summary_lines)
