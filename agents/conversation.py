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
from llm.parse_health import record_fallback, record_miss, record_residue
from llm.parsing import (
    extract_label,
    is_error_response,
    is_sentinel_line,
    strip_decoration,
)
from engine.initial_conditions import (
    PLAYER_CHARACTER_ID,
    get_all_uk_advisors,
    get_character_info,
)


# Common title variants advisors are referred to by in LLM output,
# keyed by character id. Used to recognise "Role: message" pushback lines.
_ADVISOR_ROLE_ALIASES: Dict[str, List[str]] = {
    "prime_minister": ["prime minister", "pm", "government leader"],
    "chief_defence_staff": [
        "chief of the defence staff", "chief defence staff", "cds",
        "military commander",
    ],
    "national_security_advisor": [
        "national security advisor", "national security adviser", "nsa",
        "intelligence coordinator",
    ],
    "home_secretary": ["home secretary", "domestic security"],
    "foreign_secretary": ["foreign secretary", "diplomatic lead"],
    "attorney_general": ["attorney general", "legal advisor"],
}


# Words that mark a leading "Title, ..." prefix as an address to a specific
# official (as opposed to ordinary sentence openers like "Ok," or "Overall,").
# Used to catch questions aimed at advisors who are not in the room.
_TITLE_WORDS = {
    "chancellor", "secretary", "minister", "advisor", "adviser", "general",
    "chief", "commander", "admiral", "marshal", "director", "ambassador",
    "governor", "president", "chairman", "whip", "staff",
}

# Leading address: optional "the", then a short title, optional speech verb,
# and punctuation — e.g. "Chancellor, ..." or "Foreign Secretary says: ...".
_ADDRESS_RE = re.compile(
    r"^\s*(?:the\s+)?([A-Za-z][A-Za-z '\-]{1,40}?)"
    r"\s*(?:[*_`]+\s*)?"
    r"(?:\s+(says?|said|speaks?|speaking|respond(?:s|ed|ing)?|"
    r"repl(?:y|ies|ied|ying))\s*(?:[*_`]+\s*)?)?"
    r"([,;:–—-])"
)

_PUSHBACK_SEPARATORS = ",;:\u2013\u2014-"
_PUSHBACK_SPEECH_LABELS = {
    "push-back", "pushed-back", "pushes-back", "pushing-back",
    "replied", "replies", "reply", "replying",
    "respond", "responded", "responding", "responds",
    "said", "say", "saying", "says",
    "speak", "speaking", "speaks", "spoke",
    "warn", "warned", "warning", "warns",
}

# Lowercase connectives that appear inside natural titles ("Chancellor of the
# Exchequer", "Minister for the Armed Forces") and must not defeat the
# title-case test in _detect_unknown_addressee.
_TITLE_CONNECTIVES = {"of", "the", "for", "and", "to"}
_TITLE_PREFIX_RE = re.compile(
    r"^(?:the\s+)?"
    r"([A-Z][A-Za-z'\-]*"
    r"(?:\s+(?:of|the|for|and|to|[A-Z][A-Za-z'\-]*)){0,5})"
)

# The FLASH-tier pushback model sometimes leaks game time into the fiction
# ("we tried this in Turn 2"). The prompt now forbids it
# (llm.prompts.ADVISOR_VOICE_INSTRUCTIONS), and this display-side belt
# rewrites any survivor deterministically: "turn N" -> "day N", the
# in-fiction clock the voice instructions teach ("two days ago").
_TURN_REFERENCE_RE = re.compile(r"\bturn (\d+)\b", re.IGNORECASE)


def _scrub_turn_references(text: str) -> str:
    """Replace 'turn N' with 'day N' in advisor-voiced display text."""
    return _TURN_REFERENCE_RE.sub(r"day \1", text)


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
    """Build every role prefix recognised in per-advisor pushback."""
    roles: Set[str] = set()
    for aliases in _ADVISOR_ROLE_ALIASES.values():
        roles.update(aliases)

    player = get_character_info(initial_conditions, PLAYER_CHARACTER_ID) or {}
    player_role = player.get("role", "") if isinstance(player, dict) else ""
    if player_role:
        roles.add(player_role.strip().lower())

    uk_advisors = get_all_uk_advisors(initial_conditions)
    for char_id, char_info in uk_advisors.items():
        roles.add(char_id.replace("_", " ").lower())
        role = char_info.get("role", "")
        if role:
            roles.add(role.strip().lower())

    return roles


def _detect_unknown_pushback_role(
    line: str,
    known_roles: Set[str],
) -> Optional[str]:
    """Return an unseated, title-shaped role at the start of a reply."""
    match = _TITLE_PREFIX_RE.match(line)
    if match is None:
        return None
    candidate = match.group(1).strip()
    normalized = candidate.lower()
    if normalized in known_roles:
        return None
    significant = [
        word for word in normalized.split()
        if word not in _TITLE_CONNECTIVES
    ]
    if not set(significant) & _TITLE_WORDS:
        return None
    if len(significant) >= 2:
        return candidate

    tail = line[match.end():]
    if _split_pushback_prefix_tail(tail) is not None:
        return candidate
    speech_tail = tail.strip().lstrip(")]}'\"*_`").lstrip()
    speech_label = re.match(
        r"^([A-Za-z]+(?:-[A-Za-z]+)*)\b", speech_tail)
    if (speech_label is not None
            and speech_label.group(1).lower() in _PUSHBACK_SPEECH_LABELS):
        return candidate
    return None


def _split_pushback_prefix_tail(
    tail: str,
) -> Optional[Tuple[str, bool]]:
    """Split one unambiguous speaker prefix without consuming prose."""
    cleaned = tail.strip().lstrip(")]}'\"*_`").lstrip()
    if not cleaned or cleaned == ".":
        return "", True
    if cleaned[0] in _PUSHBACK_SEPARATORS:
        return cleaned[1:].lstrip("*_` \t"), True

    # A stage direction alone, e.g. ``[quietly]:``.
    if cleaned[0] in "([":
        closing = ")" if cleaned[0] == "(" else "]"
        end = cleaned.find(closing, 1)
        if 0 < end <= 81:
            rest = cleaned[end + 1:].lstrip("*_` \t")
            if rest and rest[0] in _PUSHBACK_SEPARATORS:
                return rest[1:].lstrip("*_` \t"), False
        return None

    # One speech-attribution token, optionally hyphenated and followed by a
    # short stage direction: ``warns:``, ``pushes-back:``, ``says (quietly):``.
    index = 0
    while index < len(cleaned) and cleaned[index].isalpha():
        index += 1
    while (index + 1 < len(cleaned)
           and cleaned[index] == "-"
           and cleaned[index + 1].isalpha()):
        index += 1
        while index < len(cleaned) and cleaned[index].isalpha():
            index += 1
    if index == 0:
        return None

    if cleaned[:index].lower() not in _PUSHBACK_SPEECH_LABELS:
        return None

    rest = cleaned[index:].lstrip()
    if rest.startswith(("(", "[")):
        closing = ")" if rest[0] == "(" else "]"
        end = rest.find(closing, 1)
        if not 0 < end <= 81:
            return None
        rest = rest[end + 1:].lstrip("*_` \t")
    if rest and rest[0] in _PUSHBACK_SEPARATORS:
        return rest[1:].lstrip("*_` \t"), False
    return None


def _extract_pushback_prefix(
    line: str,
    known_roles: Set[str],
) -> Optional[Tuple[str, Optional[str], bool]]:
    """Return a prefixed role, remainder, and direct-separator flag."""
    for known_role in sorted(known_roles, key=len, reverse=True):
        match = re.match(
            rf"^(?:the\s+)?{re.escape(known_role)}"
            r"(?=$|[\s*_`\"',.;:()\[\]{}\u2013\u2014-])",
            line,
            re.IGNORECASE,
        )
        if match is None:
            continue

        tail = line[match.end():]
        split = _split_pushback_prefix_tail(tail)
        if split is not None:
            remainder, is_direct = split
            return known_role, remainder, is_direct
        return known_role, None, False
    return None


def handle_player_question(
    world: WorldState,
    question: str,
    initial_conditions: Dict[str, Any],
    llm_generate_fn,
    rng: Random,
    transcript: List[str] = None,
    event_ledger=None
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
        event_ledger: Optional played-event ledger for the dossier (ER-003)

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
    
    # Generate responses. A failed, empty or error-slot reply is recorded
    # and answered with an in-fiction line - never an out-of-fiction
    # "System: Error ..." message.
    _DEFERRAL_LINE = ("Prime Minister, I want to verify that before I answer "
                      "- give me a moment.")
    responses = []
    for char_id in responding_advisors:
        role = uk_advisors[char_id].get("role", "Advisor")
        try:
            prompt = build_advisor_context(world, initial_conditions, char_id,
                                           question, transcript, event_ledger)
            response = llm_generate_fn(prompt, rng, context=LLMContext.ADVISOR_QA)
            cleaned = (response or "").strip()
            if cleaned.startswith("[ERROR:"):
                record_fallback("advisor_qa", f"{char_id} error slot")
                cleaned = ""
            elif not cleaned:
                record_fallback("advisor_qa", f"{char_id} empty reply")
            responses.append((role, cleaned or _DEFERRAL_LINE))
        except Exception as e:
            record_fallback("advisor_qa", f"{char_id} {type(e).__name__}")
            responses.append((role, _DEFERRAL_LINE))

    return responses


def handle_player_question_all(
    world: WorldState,
    question: str,
    initial_conditions: Dict[str, Any],
    llm_generate_fn,
    rng: Random,
    transcript: List[str] = None,
    llm_batch_fn=None,
    event_ledger=None
) -> List[Tuple[str, str]]:
    """Put one question to the whole room: every advisor answers in role.

    Unlike handle_player_question, which routes to whichever advisor's
    keywords match, this asks every character in initial_conditions the same
    question through the same per-advisor context builder, so each answer
    comes from that advisor's own dossier and voice.

    DELIBERATE COST: this is one LLM call per seated advisor — five with the
    full COBRA roster — where a routed question costs one. That is the point
    of the feature (the player asked the room, the room answers), but a
    front end should treat it as the expensive affordance it is rather than
    the default. The prompts are independent, so when ``llm_batch_fn`` is
    supplied they go out as one batched group (see llm/fanout.py). Prompt and
    result order is stable; exact batch-vs-sequential RNG consumption is a
    provider detail and is not treated as equivalent.

    Args:
        world: Current world state
        question: Player's question, asked of everyone
        initial_conditions: Parsed initial conditions
        llm_generate_fn: Single-call LLM function (prompt, rng -> str)
        rng: Random number generator for determinism
        transcript: Optional full game transcript for conversation history
        llm_batch_fn: Optional batch generator; when supplied the advisor
            prompts go out as one group rather than in sequence
        event_ledger: Optional played-event ledger for the dossier (ER-003)

    Returns:
        List of (advisor_role, response) tuples, one per advisor, in the
        roster's order.
    """
    uk_advisors = get_all_uk_advisors(initial_conditions)

    # get_all_uk_advisors excludes the player: the room answers, the chair asks.
    asked = list(uk_advisors)

    if not asked:
        return [("System", "Error: No advisors available. Initial conditions "
                           "may not have loaded correctly.")]

    # A failed, empty or error-slot reply is recorded and answered with an
    # in-fiction deferral - never an out-of-fiction "System: Error" line.
    _DEFERRAL_LINE = ("Prime Minister, I want to verify that before I answer "
                      "- give me a moment.")
    prompts = []
    prompt_ok = {}
    for char_id in asked:
        try:
            prompts.append(build_advisor_context(
                world, initial_conditions, char_id, question, transcript,
                event_ledger, fanout=True))
            prompt_ok[char_id] = True
        except Exception as e:
            record_fallback("advisor_qa", f"{char_id} {type(e).__name__}")
            prompts.append("")
            prompt_ok[char_id] = False

    responses = generate_group(
        [p for p in prompts if p],
        llm_generate_fn, rng, llm_batch_fn,
        context=LLMContext.ADVISOR_QA
    )
    answers = iter(responses)

    results = []
    for char_id, prompt in zip(asked, prompts):
        role = uk_advisors[char_id].get("role", "Advisor")
        if not prompt_ok[char_id]:
            results.append((role, _DEFERRAL_LINE))
            continue
        response = next(answers, "")
        cleaned = (response or "").strip()
        if cleaned.startswith("[ERROR:"):
            # A batch driver marks a per-prompt failure as "[ERROR: ...]" in
            # that slot rather than raising (see llm/fanout.py). That is a
            # failed call, not an advisor's line.
            record_fallback("advisor_qa", f"{char_id} error slot")
            cleaned = ""
        elif not cleaned:
            record_fallback("advisor_qa", f"{char_id} empty reply")
        results.append((role, cleaned or _DEFERRAL_LINE))

    return results


def interpret_player_action(
    world: WorldState,
    action: str,
    initial_conditions: Dict[str, Any],
    llm_generate_fn,
    rng: Random,
    transcript: List[str] = None,
    event_ledger=None
) -> str:
    """Interpret player's free-form action into structured summary.

    Args:
        world: Current world state
        action: Player's action description
        initial_conditions: Parsed initial conditions
        llm_generate_fn: Function to call LLM
        rng: Random number generator
        transcript: Optional full game transcript for conversation history
        event_ledger: Optional played-event ledger for the dossier (ER-003)

    Returns:
        Structured interpretation of the action
    """
    prompt = build_decision_interpretation_prompt(world, action, initial_conditions,
                                                  transcript, event_ledger)
    interpretation = llm_generate_fn(prompt, rng, context=LLMContext.DECISION_INTERPRETATION)
    # An empty interpretation flows into every downstream prompt and the
    # decision display; the substitution there must show in parse health.
    if not interpretation or not interpretation.strip():
        record_fallback("decision_interpretation", "empty reply")
    return interpretation


def generate_advisor_pushback(
    world: WorldState,
    action: str,
    interpretation: str,
    initial_conditions: Dict[str, Any],
    llm_generate_fn,
    rng: Random,
    transcript: List[str] = None,
    llm_batch_fn=None,
    event_ledger=None
) -> List[Tuple[str, str]]:
    """Ask each seated advisor independently for warnings or pushback.

    Args:
        world: Current world state
        action: Player's action description
        interpretation: LLM's interpretation of the action
        initial_conditions: Parsed initial conditions
        llm_generate_fn: Function to call LLM
        rng: Random number generator
        transcript: Optional full game transcript for conversation history
        llm_batch_fn: Optional batch generator for the independent prompts
        event_ledger: Optional played-event ledger for the dossier (ER-003)

    Returns:
        Roster-attributed concerns. Failed/malformed slots carry a visible
        error concern; valid standalone NO PUSHBACK slots are omitted.
    """
    advisors = get_all_uk_advisors(initial_conditions)
    prompts = [
        build_pushback_prompt(
            world, action, interpretation, initial_conditions, char_id,
            transcript, event_ledger)
        for char_id in advisors
    ]
    responses = generate_group(
        prompts, llm_generate_fn, rng, llm_batch_fn,
        context=LLMContext.ADVISOR_PUSHBACK)
    
    unavailable = "[ERROR: Advisor response unavailable]"
    known_roles = _known_pushback_roles(initial_conditions)
    player_roles = set(_ADVISOR_ROLE_ALIASES.get(PLAYER_CHARACTER_ID, []))
    player = get_character_info(initial_conditions, PLAYER_CHARACTER_ID) or {}
    if isinstance(player, dict) and player.get("role"):
        player_roles.add(player["role"].strip().lower())
    result = []
    for (char_id, char_info), response in zip(advisors.items(), responses):
        role = char_info.get("role", "Advisor")
        own_roles = set(_ADVISOR_ROLE_ALIASES.get(char_id, []))
        own_roles.add(char_id.replace("_", " ").lower())
        if role:
            own_roles.add(role.strip().lower())
        if not isinstance(response, str):
            record_fallback("advisor_pushback", f"{char_id} malformed reply")
            result.append((role, unavailable))
            continue
        cleaned = response.strip()

        if not cleaned or is_error_response(cleaned):
            record_fallback("advisor_pushback", f"{char_id} failed reply")
            result.append((role, unavailable))
            continue

        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        if len(lines) == 1 and is_sentinel_line(lines[0], "NO PUSHBACK"):
            continue

        # Attribution always comes from the roster. Tolerate and strip a
        # redundant self-prefix or player vocative; reject any other seat.
        parsed_lines = []
        malformed = False
        player_vocative_seen = False
        for line in lines:
            remainder = line
            while remainder:
                candidate_line, self_attributed = re.subn(
                    r"^(?:speaking\s+)?as\s+(?:the\s+)?",
                    "",
                    strip_decoration(remainder),
                    count=1,
                    flags=re.IGNORECASE,
                )
                prefixed = _extract_pushback_prefix(
                    candidate_line, known_roles)
                if prefixed is None:
                    if _detect_unknown_pushback_role(
                            candidate_line, known_roles):
                        malformed = True
                    else:
                        parsed_lines.append(remainder)
                    break

                prefix, stripped, is_direct = prefixed
                is_own = prefix in own_roles
                is_player_vocative = (
                    prefix in player_roles
                    and is_direct
                    and not self_attributed
                    and not parsed_lines
                    and not player_vocative_seen
                )
                if is_player_vocative:
                    player_vocative_seen = True
                elif not is_own or (player_vocative_seen and parsed_lines):
                    malformed = True
                    break
                if stripped is None:
                    parsed_lines.append(remainder)
                    remainder = ""
                else:
                    remainder = stripped

            if malformed:
                break

        if malformed or not parsed_lines or any(
                is_error_response(line)
                or is_sentinel_line(line, "NO PUSHBACK")
                for line in parsed_lines):
            record_fallback("advisor_pushback", f"{char_id} malformed reply")
            result.append((role, unavailable))
            continue

        result.append((role, _scrub_turn_references("\n".join(parsed_lines))))

    return result


def check_critical_omissions(
    world: WorldState,
    player_decision: str,
    interpretation: str,
    initial_conditions: Dict[str, Any],
    llm_generate_fn,
    rng: Random,
    transcript: List[str] = None,
    llm_batch_fn=None,
    event_ledger=None
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
        event_ledger: Optional played-event ledger for the dossier (ER-003)

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
            recent_events, transcript,
            # The structured reading of the decision, produced one call
            # earlier for exactly this purpose - the scan is about what the
            # decision omits, so the advisors get the reading, not just the
            # raw typed sentence (ER-002).
            interpretation=interpretation,
            event_ledger=event_ledger
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

            # An EMPTY reply is a failed call, not an advisor finding
            # nothing wrong - it must not be conflated with the genuine
            # NO_CONCERN sentinel below.
            if not response or not response.strip():
                record_miss("critical_omissions", "empty_reply", char_id)
                continue

            # The all-clear sentinel only counts as a standalone line, so an
            # answer that merely mentions NO_CONCERN mid-sentence still parses
            if any(
                is_sentinel_line(line, "NO_CONCERN")
                for line in response.splitlines()
            ):
                continue

            # Extract concern and recommendation (tolerating markdown-bold
            # labels); continuation lines append to whichever was seen last
            concern = ""
            recommendation = ""
            last_field = None
            residue = []

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
                else:
                    # Before any label: neither consumed nor recognised
                    residue.append(line)

            if residue:
                record_residue("critical_omissions", len(residue),
                               residue[0][:60])

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
