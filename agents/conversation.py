"""Conversational advisor system using LLM to generate in-character responses.

Replaces the old hardcoded AdvisorProposal system with free-form Q&A.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple
from random import Random

from models.world import WorldState
from llm.prompts import (
    build_advisor_context,
    build_decision_interpretation_prompt,
    build_pushback_prompt,
    build_critical_omissions_prompt
)
from llm.model_config import LLMContext
from llm.fanout import generate_group
from llm.parse_health import record_fallback, record_miss
from llm.parsing import extract_label, is_sentinel_line, strip_decoration
from engine.initial_conditions import get_all_uk_advisors


# Common title variants advisors are referred to by in LLM output,
# keyed by character id. Used to recognise "Role: message" pushback lines.
_ADVISOR_ROLE_ALIASES: Dict[str, List[str]] = {
    "prime_minister": ["prime minister", "pm"],
    "chief_defence_staff": ["chief of the defence staff", "chief defence staff", "cds"],
    "national_security_advisor": ["national security advisor", "national security adviser", "nsa"],
    "home_secretary": ["home secretary"],
    "foreign_secretary": ["foreign secretary"],
    "attorney_general": ["attorney general"],
}


# Words that mark a leading "Title, ..." prefix as an address to a specific
# official (as opposed to ordinary sentence openers like "Ok," or "Overall,").
# Used to catch questions aimed at advisors who are not in the room.
_TITLE_WORDS = {
    "chancellor", "secretary", "minister", "advisor", "adviser", "general",
    "chief", "commander", "admiral", "marshal", "director", "ambassador",
    "governor", "president", "chairman", "whip", "staff",
}

# Leading address: optional "the", then a short title, ending at a comma,
# colon or dash — e.g. "Chancellor, what do you think?"
_ADDRESS_RE = re.compile(r"^\s*(?:the\s+)?([A-Za-z][A-Za-z '\-]{1,40}?)\s*[,:–—-]")

# Lowercase connectives that appear inside natural titles ("Chancellor of the
# Exchequer", "Minister for the Armed Forces") and must not defeat the
# title-case test in _detect_unknown_addressee.
_TITLE_CONNECTIVES = {"of", "the", "for", "and", "to"}

# The cabinet titles the fiction seats around the COBRA table (matches /menu)
_COBRA_ROSTER = (
    "the National Security Advisor, the Chief of the Defence Staff, the "
    "Foreign Secretary, the Home Secretary and the Attorney General"
)


def _detect_unknown_addressee(question: str, known_roles: Set[str]) -> Optional[str]:
    """Return the addressed title if the player named an advisor who isn't present.

    A question like "Chancellor, what do you think?" addresses an official the
    roster doesn't contain; silently rerouting it to another advisor reads as
    a bug. Only title-shaped prefixes trigger (see _TITLE_WORDS), so ordinary
    openers ("Right, ...") never match.
    """
    match = _ADDRESS_RE.match(question)
    if not match:
        return None
    candidate = match.group(1).strip()
    words = candidate.split()
    # A real address is title-cased ("Defence Secretary, ..."); this keeps
    # sentence openers like "General question, ..." from matching. Lowercase
    # connectives are ignored so "Chancellor of the Exchequer, ..." matches.
    significant = [w for w in words if w.lower() not in _TITLE_CONNECTIVES]
    if not significant or not all(w[0].isupper() for w in significant):
        return None
    normalized = candidate.lower()
    if normalized in known_roles:
        return None
    if set(normalized.split()) & _TITLE_WORDS:
        return candidate
    return None


def _question_matches_keyword(question_lower: str, keyword: str) -> bool:
    """Match a routing keyword against the question using word boundaries.

    Prevents short keywords like "us" from matching inside words such as
    "Russia" or "status", while multi-word phrases still match as phrases.
    """
    return re.search(r"\b" + re.escape(keyword) + r"\b", question_lower) is not None


def _known_pushback_roles(initial_conditions: Dict[str, Any]) -> Set[str]:
    """Build the set of normalized role names that identify a pushback speaker."""
    roles: Set[str] = set()
    for aliases in _ADVISOR_ROLE_ALIASES.values():
        roles.update(aliases)

    uk_advisors = get_all_uk_advisors(initial_conditions)
    for char_id, char_info in uk_advisors.items():
        roles.add(char_id.replace("_", " ").lower())
        role = char_info.get("role", "")
        if role:
            roles.add(role.strip().lower())

    return roles


def _normalize_role_prefix(prefix: str) -> str:
    """Strip markdown/bullet/bracket decoration from a candidate 'Role:' prefix.

    Delegates to the shared strip_decoration, which also removes leading
    hyphens and bullet glyphs so a bulleted roster line ("- Legal Advisor:")
    resolves to the role it names.
    """
    return strip_decoration(prefix)


def handle_player_question(
    world: WorldState,
    question: str,
    initial_conditions: Dict[str, Any],
    llm_generate_fn,
    rng: Random,
    transcript: List[str] = None
) -> List[Tuple[str, str]]:
    """Handle player's question during discussion phase.
    
    Determines which advisor(s) should respond based on question content
    and their knowledge domains, then generates in-character responses.
    
    Args:
        world: Current world state
        question: Player's question
        initial_conditions: Parsed initial conditions
        llm_generate_fn: Function to call LLM (signature: prompt, rng -> str)
        rng: Random number generator for determinism
        transcript: Optional full game transcript for conversation history
    
    Returns:
        List of (advisor_role, response) tuples
    """
    uk_advisors = get_all_uk_advisors(initial_conditions)
    
    # If no advisors loaded, return error message
    if not uk_advisors:
        return [("System", "Error: No advisors available. Initial conditions may not have loaded correctly.")]
    
    # A named-but-absent advisor gets an in-fiction correction instead of a
    # silent reroute to whoever matched a keyword (and burns no LLM call).
    unknown_title = _detect_unknown_addressee(question, _known_pushback_roles(initial_conditions))
    if unknown_title:
        return [(
            "Cabinet Secretary",
            f"(leaning in) There is no {unknown_title} in this room, Prime "
            f"Minister. Around this table: {_COBRA_ROSTER}."
        )]

    # Simple keyword matching to determine which advisor(s) should respond
    # In a full implementation, this could use LLM to route questions
    question_lower = question.lower()
    
    responding_advisors = []
    
    # Check for specific advisor mentions
    advisor_keywords = {
        "chief_defence_staff": ["cds", "military", "defence", "forces", "deploy"],
        "national_security_advisor": ["nsa", "security", "intelligence", "threat", "assess"],
        "foreign_secretary": ["foreign", "diplomatic", "alliance", "nato", "us"],
        "home_secretary": ["home", "domestic", "public", "civilian", "infrastructure"],
        "attorney_general": ["legal", "law", "attorney", "international law"],
        "prime_minister": ["pm", "prime minister", "overall", "strategy"]
    }
    
    for char_id, keywords in advisor_keywords.items():
        if char_id in uk_advisors and any(
            _question_matches_keyword(question_lower, kw) for kw in keywords
        ):
            responding_advisors.append(char_id)
    
    # If no specific advisor mentioned, default to NSA (coordinates responses)
    if not responding_advisors and "national_security_advisor" in uk_advisors:
        responding_advisors = ["national_security_advisor"]
    
    # If still no advisors, return all available
    if not responding_advisors:
        responding_advisors = list(uk_advisors.keys())[:1]  # Just return first one
    
    # Generate responses
    responses = []
    for char_id in responding_advisors:
        try:
            prompt = build_advisor_context(world, initial_conditions, char_id, question, transcript)
            response = llm_generate_fn(prompt, rng, context=LLMContext.ADVISOR_QA)
            
            char_info = uk_advisors[char_id]
            role = char_info.get("role", "Advisor")
            responses.append((role, response))
        except Exception as e:
            responses.append(("System", f"Error generating response: {e}"))
    
    return responses


def interpret_player_action(
    world: WorldState,
    action: str,
    initial_conditions: Dict[str, Any],
    llm_generate_fn,
    rng: Random,
    transcript: List[str] = None
) -> str:
    """Interpret player's free-form action into structured summary.
    
    Args:
        world: Current world state
        action: Player's action description
        initial_conditions: Parsed initial conditions
        llm_generate_fn: Function to call LLM
        rng: Random number generator
        transcript: Optional full game transcript for conversation history
    
    Returns:
        Structured interpretation of the action
    """
    prompt = build_decision_interpretation_prompt(world, action, initial_conditions, transcript)
    interpretation = llm_generate_fn(prompt, rng, context=LLMContext.DECISION_INTERPRETATION)
    return interpretation


def generate_advisor_pushback(
    world: WorldState,
    action: str,
    interpretation: str,
    initial_conditions: Dict[str, Any],
    llm_generate_fn,
    rng: Random,
    transcript: List[str] = None
) -> List[Tuple[str, str]]:
    """Generate advisor warnings/pushback for player's action.
    
    Args:
        world: Current world state
        action: Player's action description
        interpretation: LLM's interpretation of the action
        initial_conditions: Parsed initial conditions
        llm_generate_fn: Function to call LLM
        rng: Random number generator
        transcript: Optional full game transcript for conversation history
    
    Returns:
        List of (advisor_role, pushback_message) tuples, or empty list if no pushback
    """
    prompt = build_pushback_prompt(world, action, interpretation, initial_conditions, transcript)
    pushback_text = llm_generate_fn(prompt, rng, context=LLMContext.ADVISOR_PUSHBACK)
    
    # Parse pushback response.
    # "NO PUSHBACK" only counts when it appears as a standalone line, so an
    # advisor mentioning the phrase mid-sentence doesn't drop real pushback.
    lines = pushback_text.strip().split("\n")
    if any(is_sentinel_line(line, "NO PUSHBACK") for line in lines):
        return []

    # A line starts a new pushback only when the prefix before ":" is a known
    # advisor role; other lines (markdown emphasis, wrapped text) are treated
    # as continuations of the previous advisor's message.
    known_roles = _known_pushback_roles(initial_conditions)
    pushback_list = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        role = None
        message = ""
        if ":" in stripped:
            prefix, remainder = stripped.split(":", 1)
            candidate = _normalize_role_prefix(prefix)
            if candidate.lower() in known_roles:
                role = candidate
                message = remainder.strip()

        if role is not None:
            pushback_list.append((role, message))
        elif pushback_list:
            prev_role, prev_message = pushback_list[-1]
            pushback_list[-1] = (prev_role, f"{prev_message} {stripped}".strip())
        else:
            # A line before any recognised advisor is still dropped (it is
            # usually preamble), but no longer silently: if it was a real
            # objection under an unrecognised prefix, the record shows it.
            record_miss("pushback", "orphan_line", stripped[:60])

    return pushback_list


def check_critical_omissions(
    world: WorldState,
    player_decision: str,
    interpretation: str,
    initial_conditions: Dict[str, Any],
    llm_generate_fn,
    rng: Random,
    transcript: List[str] = None,
    llm_batch_fn=None
) -> List[Tuple[str, str, str]]:
    """Check if player has failed to take critical actions.
    
    After decision interpretation, key advisors scan for catastrophic omissions:
    - Military action without NATO coordination
    - Offensive action without legal authority
    - Crisis without public communication
    - Escalation without ally consultation
    
    High threshold - only truly critical gaps are flagged.
    
    Args:
        world: Current world state
        player_decision: The decision the PM made
        interpretation: LLM's interpretation of the decision
        initial_conditions: Parsed initial conditions
        llm_generate_fn: Function to call LLM
        rng: Random number generator
        transcript: Optional full game transcript for conversation history
        llm_batch_fn: Optional batch generator. When supplied the five
            advisor prompts go out as one group rather than in sequence.

    Returns:
        List of (advisor_role, concern, recommendation) tuples
        Empty list if no critical omissions detected
    """
    uk_advisors = get_all_uk_advisors(initial_conditions)
    
    if not uk_advisors:
        return []
    
    # Build recent events context from world state
    recent_events = []
    if world.recent_injects:
        recent_events = world.recent_injects[-5:]  # Last 5 injects
    elif hasattr(world, 'flags') and world.flags:
        # Fallback: use flags as context
        recent_events = [f"Active situation: {flag}" for flag in list(world.flags.keys())[:3]]
    
    # Check with specific advisors based on their domain
    advisors_to_check = [
        "foreign_secretary",      # Alliance/diplomatic omissions
        "chief_defence_staff",    # Military readiness gaps
        "attorney_general",       # Legal authority gaps
        "home_secretary",         # Domestic security/messaging
        "national_security_advisor"  # Overall strategic coordination
    ]
    
    critical_concerns = []

    # The five advisors scan independently - none of them reads another's
    # answer - so these are asked together rather than one after another.
    # They are also the largest identical-prefix group in a turn, and the
    # interpretation and pushback calls that run before them share that same
    # prefix, so the provider's cache is already warm by the time they fire.
    checking = [c for c in advisors_to_check if c in uk_advisors]
    prompts = [
        build_critical_omissions_prompt(
            world, initial_conditions, char_id, player_decision,
            recent_events, transcript
        )
        for char_id in checking
    ]
    responses = generate_group(
        prompts, llm_generate_fn, rng, llm_batch_fn,
        context=LLMContext.CRITICAL_OMISSIONS
    )

    for char_id, response in zip(checking, responses):
        try:
            # A batch driver marks a per-prompt failure as "[ERROR: ...]" in
            # that slot rather than raising (see llm/fanout.py). That is a
            # failed call, not an advisor finding nothing wrong.
            if response and response.startswith("[ERROR:"):
                record_fallback("critical_omissions", char_id)
                print(f"[WARN] Critical omissions check failed for {char_id}: "
                      f"{response[:80]}")
                continue

            # The all-clear sentinel only counts as a standalone line, so an
            # answer that merely mentions NO_CONCERN mid-sentence still parses
            if not response or any(
                is_sentinel_line(line, "NO_CONCERN")
                for line in response.splitlines()
            ):
                continue

            # Extract concern and recommendation (tolerating markdown-bold
            # labels); continuation lines append to whichever was seen last
            concern = ""
            recommendation = ""
            last_field = None

            lines = response.strip().split("\n")
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                concern_text = extract_label(line, "CONCERN")
                recommendation_text = extract_label(line, "RECOMMENDATION")
                if concern_text is not None:
                    concern = concern_text
                    last_field = "concern"
                elif recommendation_text is not None:
                    recommendation = recommendation_text
                    last_field = "recommendation"
                elif last_field == "concern":
                    # Multi-line concern
                    concern = f"{concern} {line}".strip()
                elif last_field == "recommendation":
                    # Multi-line recommendation
                    recommendation = f"{recommendation} {line}".strip()

            if concern and not recommendation:
                # A concern with no recommendation is still a concern - it
                # must surface, not vanish over a missing second field
                record_miss("critical_omissions", "recommendation", char_id)
                recommendation = "(no specific recommendation given)"
            elif recommendation and not concern:
                record_miss("critical_omissions", "concern", char_id)
                continue

            if concern and recommendation:
                char_info = uk_advisors[char_id]
                role = char_info.get("role", "Advisor")
                critical_concerns.append((role, concern, recommendation))

        except Exception as e:
            # Keep checking the remaining advisors, but don't fail silently
            print(f"[WARN] Critical omissions check failed for {char_id}: {e}")
            continue

    return critical_concerns

