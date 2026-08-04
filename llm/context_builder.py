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

# Transcript budget, in characters rather than lines. Lines were always a
# proxy for the thing that actually binds - the model's context window - and
# a poor one: on the saved 18-turn campaign a transcript line averages 393
# characters but ranges from an empty string to a full paragraph.
#
# 320,000 characters is roughly 80,000 tokens, which leaves real headroom
# inside a 128K window once the role-specific half of the prompt is added.
# It is also enough that the recent window alone exceeds what the old
# 500-line cap carried (233,978 characters on that campaign), so widening
# here takes nothing away to pay for keeping the campaign's opening.
MAX_ADVISOR_TRANSCRIPT_CHARS = 320_000

# The history header, and why it carries no counts. It has to be honest in
# both cases - complete and elided - without changing between them, because
# anything above the transcript that moves as the transcript grows cuts the
# cacheable prefix off at the header. A line count did exactly that: it made
# every prompt in a turn differ within its first hundred characters. The
# specifics of any elision are stated inline, at the point of the cut.
_HISTORY_HEADER = (
    "GAME HISTORY - everything that has happened, in order. Where any of it "
    "has been elided for length, the elision is marked inline."
)

# Share of the transcript budget spent on the campaign's opening when the
# whole history no longer fits.
#
# Chosen so the *recent* window is no smaller than the 500-line tail this
# replaced - on the saved 18-turn campaign that is about four and a half
# turns either way - and the opening comes on top of it rather than out of
# it. The opening is worth keeping because it is where the crisis is
# established, and the scripted turns are what everything since has been a
# reaction to.
#
# A stable head also stops the block from moving on every turn, which is what
# a prefix cache needs. Do not oversell that part: cache lifetimes are 3-30
# minutes, so it pays across the calls within one turn and usually not across
# a gap where a player is thinking.
_TRANSCRIPT_HEAD_SHARE = 0.2

# Continuity window for inject generation. The generator is the component
# most responsible for the story hanging together, yet it ran on 120 lines
# while advisors got 500 (issue #25). Widened - but still bounded: a real
# campaign transcript reaches ~1,850 lines / 727 KB by turn 18, past the
# context window of the models used in play, and a turn makes ~15 calls.
MAX_INJECT_CONTINUITY_LINES = 400

# Cap on a ledger title so one long headline cannot stretch the column
_LEDGER_TITLE_MAX = 60


def _ledger_field(entry, key: str, default=""):
    """Read a ledger field from a PlayedEvent or a plain dict."""
    if isinstance(entry, dict):
        return entry.get(key, default)
    return getattr(entry, key, default)


def render_event_ledger(event_ledger) -> str:
    """Render the EVENTS ALREADY PLAYED block, or '' when there is nothing.

    States each past event's disposition outright. The rolling summary only
    *implies* that a thread was closed, and inferring it from prose is what
    failed in live play - the same submarine surfaced four turns running,
    once after the player had it escorted out of UK waters (issue #25).
    """
    if not event_ledger:
        return ""

    def _title(entry) -> str:
        text = str(_ledger_field(entry, "title", "")).strip()
        if len(text) > _LEDGER_TITLE_MAX:
            text = text[:_LEDGER_TITLE_MAX - 3] + "..."
        return text

    titles = [_title(e) for e in event_ledger]
    width = max(len(t) for t in titles)

    lines = [
        "=" * 60,
        "EVENTS ALREADY PLAYED - do not re-introduce these",
        "=" * 60,
    ]
    for entry, title in zip(event_ledger, titles):
        turn = _ledger_field(entry, "turn", "?")
        disposition = str(_ledger_field(entry, "disposition", "open")).upper()
        note = str(_ledger_field(entry, "note", "")).strip()
        line = f"Turn {turn} | {title.ljust(width)} | {disposition}"
        if note:
            line += f" - {note}"
        lines.append(line)
    return "\n".join(lines)

# Pattern for the turn header line the sim loop writes between '=' rulers
_TURN_HEADER_RE = re.compile(r"^TURN \d+$")


def get_last_turn_slice(transcript: FullTranscript, max_lines: int = 120) -> FullTranscript:
    """Return the transcript lines belonging to the most recent turn.

    Slices from the last ``TURN N`` header (including its ruler) so the
    turn's opening inject — the event the next inject must build on — is
    always inside the continuity window. A fixed tail window of the
    transcript captures only the adjudication end of a long turn, which is
    how a ballistic missile can vanish from the story (issue #23).

    Turns longer than max_lines keep their head (the inject and early
    discussion) and tail (the decision and adjudication) around an elision
    marker, so both the event and its outcome survive. The marker is paid
    for out of the budget, so max_lines is a hard upper bound on the
    returned length. Falls back to the plain tail window when no turn
    header exists (e.g. synthetic transcripts in tests).
    """
    if max_lines < 1:
        raise ValueError("max_lines must be at least 1")
    start = None
    for i in range(len(transcript) - 1, -1, -1):
        if _TURN_HEADER_RE.match(transcript[i].strip()):
            start = max(0, i - 1)  # include the ruler above the header
            break
    if start is None:
        return transcript[-max_lines:]
    turn_slice = transcript[start:]
    if len(turn_slice) <= max_lines:
        return turn_slice
    # Too small to hold head + marker + tail: spend the whole budget on the
    # opening, since preserving the turn's inject is the point of this window.
    if max_lines < 3:
        return turn_slice[:max_lines]
    budget = max_lines - 1  # the elision marker occupies one line
    head = (budget * 2) // 3
    tail = budget - head
    # A zero-length tail must stay empty; turn_slice[-0:] is the whole list.
    tail_lines = turn_slice[-tail:] if tail else []
    return [*turn_slice[:head],
            "[... mid-turn discussion elided for length ...]",
            *tail_lines]

def _turn_boundaries(transcript: FullTranscript) -> List[int]:
    """Indices of the ``TURN N`` header lines, each backed up onto its ruler.

    Elision cuts land on these so a window never starts or stops halfway
    through a turn.
    """
    return [max(0, i - 1) for i, line in enumerate(transcript)
            if _TURN_HEADER_RE.match(line.strip())]


def _span_chars(transcript: FullTranscript, start: int, stop: int) -> int:
    """Characters (with newlines) occupied by transcript[start:stop]."""
    return sum(len(line) + 1 for line in transcript[start:stop])


def render_transcript_block(transcript: FullTranscript,
                            max_chars: int = MAX_ADVISOR_TRANSCRIPT_CHARS) -> str:
    """Render the game history, saying honestly how much of it is present.

    Two things are deliberate here.

    The header no longer claims COMPLETE over a window. It said so while
    dropping everything but the last 500 lines, which on an 18-turn campaign
    is the last quarter of the game - the same instinct that capped the event
    ledger at six entries and re-opened the bug the ledger existed to close.

    When the history does not fit, the campaign's *opening* is kept and the
    middle is elided at turn boundaries, rather than keeping a sliding tail.
    A tail window is the worst possible shape for a prompt cache: it moves on
    every turn, so the block never starts the same way twice and no provider
    can match a prefix. Anchoring the head means the start of this block is
    stable for many turns at a stretch.
    """
    total_chars = sum(len(line) + 1 for line in transcript)
    ruler = "=" * 60

    if total_chars <= max_chars:
        return "\n".join([ruler, _HISTORY_HEADER, ruler, *transcript])

    head_budget = int(max_chars * _TRANSCRIPT_HEAD_SHARE)
    boundaries = _turn_boundaries(transcript)

    # Grow the head one whole turn at a time, until the next whole turn would
    # spend more than the opening's share of the budget. Nothing is taken
    # unconditionally: a transcript whose first turn header is a long way in
    # would otherwise pull all of that preamble into the head regardless of
    # budget, and the block would run past the cap it exists to enforce. If
    # the opening does not fit, there is simply no head and this degrades to
    # the plain recent window.
    head_end = 0
    head_used = 0
    for boundary in boundaries:
        span = _span_chars(transcript, head_end, boundary)
        if head_used + span > head_budget:
            break
        head_used += span
        head_end = boundary

    # Spend what is left from the end, again stopping on a turn boundary.
    tail_budget = max(0, max_chars - head_used)
    tail_start = len(transcript)
    tail_used = 0
    for boundary in reversed(boundaries):
        if boundary <= head_end:
            break
        span = _span_chars(transcript, boundary, tail_start)
        if tail_used + span > tail_budget:
            break
        tail_used += span
        tail_start = boundary

    # No turn boundary fit inside the tail budget - a transcript with no turn
    # headers at all (the synthetic ones in tests), or one enormous turn.
    # Fall back to a plain character tail so the block still renders.
    if tail_start >= len(transcript):
        tail_start = head_end
        running = 0
        for i in range(len(transcript) - 1, head_end - 1, -1):
            running += len(transcript[i]) + 1
            if running > tail_budget:
                tail_start = i + 1
                break

    elided = tail_start - head_end
    return "\n".join([
        ruler,
        _HISTORY_HEADER,
        ruler,
        *transcript[:head_end],
        f"[... {elided} lines of mid-campaign history elided for length ...]",
        *transcript[tail_start:],
    ])


def build_shared_context_prefix(transcript: FullTranscript,
                                world_state: WorldState) -> str:
    """The identical opening block every transcript-carrying prompt starts with.

    Prompt caches match from the *start* of a prompt, so what a prompt opens
    with decides what can be cached. Every call used to open with its own
    role line - "You are the {role} ..." - which made the shared prefix
    across a turn's calls twelve characters long, and put the large,
    identical, genuinely cacheable part (the transcript) after the point
    where the prompts had already diverged.

    The order below is by rate of change, slowest first, which is the only
    order a prefix cache can exploit:

    1. the campaign's fixed framing, and the hidden narrative truth drawn at
       setup - constant for the whole campaign;
    2. the transcript - append-only, so turn N+1's block is turn N's block
       with more on the end, and a provider matches straight through it;
    3. the current metrics and phase - these change every turn, so they come
       last, after everything worth matching.

    The role-specific half of each prompt follows this block. Nothing here
    changes *what* a model is shown, only the order it is shown in.
    """
    ruler = "=" * 60
    parts = [
        ruler,
        "UK CRISIS WARGAME - SHARED BRIEFING DOSSIER",
        ruler,
        "The material below is the same for every member of the COBRA cell.",
        "Your own role and instructions follow it.",
        "",
    ]

    # Mystery mode's secret truth is drawn once at setup and never changes,
    # so it belongs with the static framing rather than below the transcript.
    # Global truth only - no per-country stance.
    if world_state.narrative:
        parts.append(world_state.narrative.to_llm_context())
        parts.append("")

    parts.append(render_transcript_block(transcript))
    parts.append("")

    # Everything from here down changes every turn, which is why it is here
    # and not at the top.
    parts.extend([
        ruler,
        "CURRENT SITUATION",
        ruler,
        f"Turn: {world_state.turn}",
        f"Phase: {world_state.phase}",
        f"Escalation Risk: {world_state.metrics.escalation_risk}/100",
        f"Domestic Stability: {world_state.metrics.domestic_stability}/100",
        f"Alliance Cohesion: {world_state.metrics.alliance_cohesion}/100",
        f"Military Casualties: {world_state.metrics.casualties_mil}",
        f"Civilian Casualties: {world_state.metrics.casualties_civ}",
        "",
    ])

    # The narrative rendering of the same numbers, plus the standing
    # instruction not to talk about them as numbers. The decision, pushback
    # and omissions prompts each carried this and the advisor prompt did not;
    # merging the two context shapes must not quietly drop it from four call
    # sites. Imported here rather than at module scope because llm.prompts
    # imports this module.
    from llm.prompts import build_world_state_summary
    parts.append(build_world_state_summary(world_state))
    parts.append("")

    return "\n".join(parts)


def get_advisor_context(transcript: FullTranscript, world_state: WorldState) -> str:
    """The shared dossier block, for the Advisory Council.

    Kept as a named entry point because callers and tests refer to it, but it
    is now exactly the block every other transcript-carrying prompt opens
    with - which is the point: identical text is what a prompt cache matches.
    """
    return build_shared_context_prefix(transcript, world_state)

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

def get_stochastic_inject_context(summary: str, last_turn_transcript: List[str],
                                  world_state: WorldState,
                                  event_ledger=None) -> str:
    """
    Returns a high-level summary, the last turn's transcript, and narrative secrets.
    Used for creative story generation.

    Args:
        event_ledger: Optional sequence of played events (PlayedEvent objects
            or dicts). When present, their dispositions are stated explicitly
            so resolved threads are not restaged (issue #25).
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
    
    # What has already been staged, and how each thread was left
    ledger_block = render_event_ledger(event_ledger)
    if ledger_block:
        context_parts.append(ledger_block)
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
