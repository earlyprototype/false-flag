"""
ContextBuilder: A centralized module for assembling tailored LLM context.

This module implements the role-based context strategy, providing specific,
efficient, and secure context for each type of LLM agent in the simulation.
"""

import re
from typing import List

from engine.utils import strip_effect_boxes
from llm.parse_health import record_miss
from models.narrative_state import format_event_consequences
from models.world import WorldState

# A full game transcript is a list of strings, where each string is a line of dialogue,
# an action, or a system message.
FullTranscript = List[str]

# Transcript budget, in characters rather than lines. Lines were always a
# proxy for the thing that actually binds - the model's context window - and
# a poor one: on the saved 18-turn campaign a transcript line averages 393
# characters but ranges from an empty string to a full paragraph.
#
# The window's job changed when the referee got memory: campaign history
# now travels in the rolling synopsis and the event ledger by design, so
# the raw transcript slice only needs to carry recent verbatim exchanges.
# The first live shakedown measured the old 320k allowance letting these
# prompts grow past 150,000 characters by turn 10 - linear cost growth on
# every advisory call for history the dossier already summarises. 60k
# (~15k tokens) holds several turns of recent exchanges; the head+tail
# slice keeps the campaign's opening either way.
#
# This constant is a NEVER-FIRE TRIPWIRE, not a guillotine. The window is
# scoped by dropping whole oldest turns until it fits; content is never cut
# mid-turn or mid-line to satisfy the number. When even the minimum window
# (the head plus the last _MIN_RECENT_WHOLE_TURNS whole turns) exceeds it,
# the turns are kept intact anyway and the breach is recorded through
# parse_health.record_miss("context_window", "tripwire", ...). Length
# discipline lives at generation time (the prompts bound what a turn can
# say) and structure time (turn boundaries), never as a character cut that
# shapes content.
MAX_ADVISOR_TRANSCRIPT_CHARS = 60_000

# The floor under the recent window: the advisory slice never carries fewer
# than this many whole recent turns, whatever they cost. Two, because the
# decision being adjudicated always needs the turn it answers *and* the turn
# before it (the exchange the inject built on).
_MIN_RECENT_WHOLE_TURNS = 2

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

# Character bound on the narrator bridge's transcript window. The narrator
# takes the last twenty transcript elements, and one element can be a full
# unwrapped paragraph — twenty of the long ones are unbounded by anything
# but the input (ER-008). ~2,000 tokens is plenty for a two-sentence bridge.
MAX_NARRATOR_CONTEXT_CHARS = 8_000

# Cap on a ledger title so one long headline cannot stretch the column
_LEDGER_TITLE_MAX = 60


def _ledger_field(entry, key: str, default=""):
    """Read a ledger field from a PlayedEvent or a plain dict."""
    if isinstance(entry, dict):
        return entry.get(key, default)
    return getattr(entry, key, default)


def render_event_ledger(event_ledger, always: bool = False) -> str:
    """Render the EVENTS ALREADY PLAYED block, or '' when there is nothing.

    States each past event's disposition outright. The rolling summary only
    *implies* that a thread was closed, and inferring it from prose is what
    failed in live play - the same submarine surfaced four turns running,
    once after the player had it escorted out of UK waters (issue #25).

    ``always=True`` renders the header over an empty ledger too, so a prompt
    rule that names this block never points at nothing (ER-001): the
    generation path issues its do-not-restage rule unconditionally, and the
    rule must always have a block to name.
    """
    if not event_ledger:
        if always:
            return "\n".join([
                "=" * 60,
                "EVENTS ALREADY PLAYED - do not re-introduce these",
                "=" * 60,
                "(nothing has been staged yet)",
            ])
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
        # Structured consequences (ER-077), one indented line when any are
        # present - absent on entries from older saves and on turns whose
        # adjudication has not yet run.
        consequences = format_event_consequences(
            str(_ledger_field(entry, "outcome", "")).strip(),
            _ledger_field(entry, "effects_direction", None) or {},
            _ledger_field(entry, "objectors", None) or [])
        if consequences:
            lines.append(f"  {consequences}")
    return "\n".join(lines)

# Pattern for the turn header line the sim loop writes between '=' rulers
_TURN_HEADER_RE = re.compile(r"^TURN \d+$")


def get_last_turn_slice(transcript: FullTranscript, max_lines: int = 120,
                        max_chars: int = MAX_ADVISOR_TRANSCRIPT_CHARS) -> FullTranscript:
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

    ``max_lines`` alone does not bound the result: lines range from empty to
    a full unwrapped paragraph, so 400 of the long ones ran to 792,572
    characters against a 320,000 budget - the same reason #32 moved the
    advisor window off a line count. ``max_chars`` is the bound that
    actually holds, applied after the line window and trimmed from the head
    so the turn's most recent material survives.
    """
    if max_lines < 1:
        raise ValueError("max_lines must be at least 1")
    start = None
    for i in range(len(transcript) - 1, -1, -1):
        if _TURN_HEADER_RE.match(transcript[i].strip()):
            start = max(0, i - 1)  # include the ruler above the header
            break
    if start is None:
        return bound_chars(transcript[-max_lines:], max_chars)
    turn_slice = transcript[start:]
    if len(turn_slice) <= max_lines:
        # Bounded here too. A turn that fits the line cap can still be huge:
        # 398 lines of a full unwrapped paragraph is ~796,000 characters, and
        # this return path skipped the budget entirely.
        return bound_chars(turn_slice, max_chars)
    # Too small to hold head + marker + tail: spend the whole budget on the
    # opening, since preserving the turn's inject is the point of this window.
    if max_lines < 3:
        return bound_chars(turn_slice[:max_lines], max_chars)
    budget = max_lines - 1  # the elision marker occupies one line
    head = (budget * 2) // 3
    tail = budget - head
    # A zero-length tail must stay empty; turn_slice[-0:] is the whole list.
    tail_lines = turn_slice[-tail:] if tail else []
    return bound_chars([*turn_slice[:head],
                         "[... mid-turn discussion elided for length ...]",
                         *tail_lines], max_chars)


def bound_chars(lines: FullTranscript, max_chars: int) -> FullTranscript:
    """Trim from the head until the block fits ``max_chars``.

    The line window is the wrong unit for a model context, and a turn of
    long unwrapped paragraphs blows straight through it. Trimming from the
    head rather than the tail keeps the decision and its adjudication, which
    is what the next inject has to build on.
    """
    if max_chars is None or max_chars < 1:
        return lines
    marker = "[... earlier lines elided for length ...]"
    total = sum(len(line) + 1 for line in lines)
    if total <= max_chars:
        return lines
    budget = max_chars - len(marker) - 1
    kept: FullTranscript = []
    running = 0
    for line in reversed(lines):
        cost = len(line) + 1
        if running + cost > budget:
            break
        kept.append(line)
        running += cost
    return [marker, *reversed(kept)]

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

    Three things are deliberate here.

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

    And the window is made of WHOLE TURNS only: the head plus the last N
    whole turns, oldest turns dropping first when the budget would otherwise
    be exceeded - their content already travels in the synopsis and the event
    ledger. ``max_chars`` is a never-fire tripwire, not a guillotine: once
    the window is down to the head plus _MIN_RECENT_WHOLE_TURNS whole recent
    turns, those turns are kept intact whatever they cost and the breach is
    recorded (record_miss "context_window.tripwire"). Content is never cut
    mid-turn under any circumstances.
    """
    total_chars = sum(len(line) + 1 for line in transcript)
    ruler = "=" * 60

    if total_chars <= max_chars:
        return "\n".join([ruler, _HISTORY_HEADER, ruler, *transcript])

    boundaries = _turn_boundaries(transcript)

    # No turn structure at all (synthetic transcripts, or a scenario that
    # never wrote TURN headers): there is no boundary to drop whole turns
    # at, and cutting anywhere else would slice content. Send it whole and
    # record that the tripwire was crossed.
    if not boundaries:
        record_miss("context_window", "tripwire",
                    f"{total_chars} chars over a {max_chars} budget with no "
                    "turn boundaries to drop")
        return "\n".join([ruler, _HISTORY_HEADER, ruler, *transcript])

    head_budget = int(max_chars * _TRANSCRIPT_HEAD_SHARE)

    # Grow the head one whole turn at a time, until the next whole turn would
    # spend more than the opening's share of the budget. Nothing is taken
    # unconditionally: a transcript whose first turn header is a long way in
    # would otherwise pull all of that preamble into the head regardless of
    # budget. If the opening does not fit, there is simply no head and this
    # degrades to the plain recent window.
    head_end = 0
    head_used = 0
    for boundary in boundaries:
        span = _span_chars(transcript, head_end, boundary)
        if head_used + span > head_budget:
            break
        head_used += span
        head_end = boundary

    # The recent window, in whole turns from the end. The last
    # _MIN_RECENT_WHOLE_TURNS turns are mandatory whatever they cost; older
    # turns are added whole while the budget holds, so the oldest drop first.
    if len(boundaries) >= _MIN_RECENT_WHOLE_TURNS:
        min_tail_start = boundaries[-_MIN_RECENT_WHOLE_TURNS]
    else:
        min_tail_start = boundaries[0]
    tail_budget = max(0, max_chars - head_used)
    tail_start = len(transcript)
    tail_used = 0
    for boundary in reversed(boundaries):
        span = _span_chars(transcript, boundary, tail_start)
        mandatory = boundary >= min_tail_start
        if not mandatory and (boundary <= head_end
                              or tail_used + span > tail_budget):
            break  # an optional older turn drops whole, never partially
        tail_used += span
        tail_start = boundary
        if boundary <= head_end:
            break  # the mandatory window has met the head; nothing to elide

    if tail_start <= head_end:
        # Head and tail meet: the whole transcript is in the window. It is
        # over budget (the fits-whole path returned above), which is exactly
        # what the tripwire exists to record - but the content still travels.
        record_miss("context_window", "tripwire",
                    f"{total_chars} chars over a {max_chars} budget with "
                    "nothing left to drop at a turn boundary")
        return "\n".join([ruler, _HISTORY_HEADER, ruler, *transcript])

    kept_turns = sum(1 for b in boundaries if b >= tail_start)
    assembled = head_used + tail_used
    if assembled > max_chars:
        # The minimum window itself exceeds the budget. Keep it intact
        # anyway - the tripwire records the breach, it never cuts.
        record_miss("context_window", "tripwire",
                    f"{assembled} chars over a {max_chars} budget after "
                    f"dropping to the last {kept_turns} whole turn(s)")

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
                                world_state: WorldState,
                                event_ledger=None) -> str:
    """The identical opening block every transcript-carrying prompt starts with.

    Prompt caches match from the *start* of a prompt, so what a prompt opens
    with decides what can be cached. Every call used to open with its own
    role line - "You are the {role} ..." - which made the shared prefix
    across a turn's calls twelve characters long, and put the large,
    identical, genuinely cacheable part (the transcript) after the point
    where the prompts had already diverged.

    The order below is by rate of change, slowest first, which is the only
    order a prefix cache can exploit:

    1. the campaign's fixed framing - constant for the whole campaign;
    2. the transcript - append-only, so turn N+1's block is turn N's block
       with more on the end, and a provider matches straight through it;
    3. the current metrics and phase - these change every turn, so they come
       last, after everything worth matching.

    The role-specific half of each prompt follows this block. Mystery mode's
    hidden narrative truth is deliberately excluded from this player-facing
    dossier (see the guard below).

    ``event_ledger``: optional sequence of played events (PlayedEvent objects
    or dicts). Rendered in the fast-moving tail — after the transcript, with
    the other per-turn state — so the dossier finally holds both the campaign
    history and the one structure that survives the history window's elision
    (ER-003) without moving anything above the transcript.
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

    # Mystery mode's secret truth is deliberately ABSENT from this dossier.
    # It briefs player-facing readers (advisors, interpretation, pushback,
    # omissions), and keeping the secret out of their context is the leak
    # defence: their output cannot reveal what they never saw. See
    # NarrativeConfig.to_llm_context for the segregation rule.

    parts.append(render_transcript_block(strip_effect_boxes(list(transcript))))
    parts.append("")

    # Everything from here down changes every turn, which is why it is here
    # and not at the top.
    #
    # The situation is given in words, not as raw values. This dossier closes
    # with the standing instruction never to reference 'metrics', 'scores' or
    # 'values' (below), and printing a scoreboard directly above it left the
    # model to guess which half of the prompt to obey - the readers of this
    # block are the four advisor-voiced calls, none of which has any use for
    # an integer it is forbidden to say out loud (issue #91). The prose
    # renderer is the same one the narrator and the diplomatic assessor take.
    from llm.prompts import _state_band_lines
    parts.extend([
        ruler,
        "CURRENT SITUATION",
        ruler,
        f"Turn: {world_state.turn}",
        f"Phase: {world_state.phase}",
        "",
    ])
    parts.extend(_state_band_lines(world_state))
    parts.append("")

    # The event ledger: one line per staged event with its disposition. It
    # belongs down here with the per-turn state - it grows every turn, so
    # placing it above the transcript would cut the cacheable prefix off at
    # the first new entry (ER-003).
    ledger_block = render_event_ledger(event_ledger)
    if ledger_block:
        parts.append(ledger_block)
        parts.append("")

    # The standing instruction not to talk about the numbers as numbers. The
    # decision, pushback and omissions prompts each carried this and the
    # advisor prompt did not; merging the two context shapes must not quietly
    # drop it from four call sites. The intelligence-flags block that used to
    # travel with it is still gone (ER-009): its only non-duplicate content —
    # the casualty thresholds — is already stated in the CASUALTIES TO DATE
    # line above. Imported here rather than at module scope because
    # llm.prompts imports this module.
    from llm.prompts import ADVISOR_VOICE_INSTRUCTIONS
    parts.append(ADVISOR_VOICE_INSTRUCTIONS)
    parts.append("")

    return "\n".join(parts)


def get_advisor_context(transcript: FullTranscript, world_state: WorldState,
                        event_ledger=None) -> str:
    """The shared dossier block, for the Advisory Council.

    Kept as a named entry point because callers and tests refer to it, but it
    is now exactly the block every other transcript-carrying prompt opens
    with - which is the point: identical text is what a prompt cache matches.
    """
    return build_shared_context_prefix(transcript, world_state, event_ledger)

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
    Return player-safe campaign history for creative story generation.

    Mystery truth is deliberately absent because generated inject prose is
    shown to the player verbatim.

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
    from llm.prompts import _state_band_lines
    context_parts.extend(_state_band_lines(world_state)[:3])
    context_parts.append("")
    
    # The secret truth is deliberately ABSENT: generated inject text goes to
    # the player verbatim, so the generator is a player-facing call and never
    # receives the narrative (see NarrativeConfig.to_llm_context). Story
    # steering comes from the summary and the event ledger below.

    # Add high-level summary
    context_parts.append("=" * 60)
    context_parts.append("STORY SO FAR (HIGH-LEVEL SUMMARY)")
    context_parts.append("=" * 60)
    context_parts.append(summary)
    context_parts.append("")
    
    # What has already been staged, and how each thread was left. Rendered
    # even over an empty ledger (always=True): the generation prompt's
    # do-not-restage rule names this block unconditionally (ER-001).
    context_parts.append(render_event_ledger(event_ledger, always=True))
    context_parts.append("")

    # Add last turn's transcript for continuity
    context_parts.append("=" * 60)
    context_parts.append(f"LAST TURN (TURN {world_state.turn - 1}) - FOR CONTINUITY")
    context_parts.append("=" * 60)
    context_parts.extend(strip_effect_boxes(list(last_turn_transcript)))

    return "\n".join(context_parts)

# Character bound on the foreign counterpart's transcript window. Smaller
# than the advisor budget: the counterpart needs the public shape of the
# crisis and its own calls, not the whole campaign.
MAX_DIPLOMATIC_CONTEXT_CHARS = 60_000

# A line spoken by someone: a short leading label ending in a colon
# ("Government Leader: ...", "Prime Minister: ...", "Effect: ..."). Anything
# matching this outside a diplomatic-call block is treated as internal UK
# material and excluded — fail closed (ER-018).
_SPEAKER_PREFIX_RE = re.compile(r"^[A-Z][^:]{0,47}:")

# Structural transcript furniture that carries no UK deliberation.
_STRUCTURAL_PREFIX_RE = re.compile(r"^(BREAKING|INTEL|BRIEFING)\b", re.IGNORECASE)

_CALL_HEADER_MARKER = "=== DIPLOMATIC CALL"
_CALL_FOOTER_MARKER = "=== CALL ENDED ==="


def _is_structural_line(stripped: str) -> bool:
    """A transcript element that is scenery rather than speech."""
    first = stripped.split("\n", 1)[0].strip()
    if first.startswith("==="):
        return True
    if _TURN_HEADER_RE.match(first):
        return True
    if first.startswith("[Narrator]"):
        return True
    return bool(_STRUCTURAL_PREFIX_RE.match(first))


def get_diplomatic_context(transcript: FullTranscript, world_state: WorldState, target_country_code: str) -> str:
    """
    Returns a securely filtered transcript for diplomatic conversations.

    Structural fail-closed whitelist (ER-018, ER-038):

    - A diplomatic-call block (from its ``=== DIPLOMATIC CALL`` header to
      ``=== CALL ENDED ===`` inclusive) is included whole when its header
      names the TARGET country, and excluded whole otherwise — one country
      never reads another's calls.
    - Outside call blocks, a line passes only when it carries NO speaker
      prefix or is structural (rulers, TURN headers, ``[Narrator]``,
      BREAKING/INTEL/BRIEFING). Every advisor line, player question and
      decision line is excluded by construction; scripted cast-list lines
      going with them is the accepted price of failing closed.
    - The UK's private metric numbers are not in the context at all.
    """
    target = str(target_country_code or "").strip().lower()
    filtered_lines: FullTranscript = []
    in_call_block = False
    call_is_with_target = False

    for entry in transcript:
        text = str(entry)
        stripped = text.strip()

        if not in_call_block and _CALL_HEADER_MARKER.lower() in stripped.lower():
            # e.g. "=== DIPLOMATIC CALL: President of the United States (US) ==="
            in_call_block = True
            call_is_with_target = bool(target) and f"({target})" in stripped.lower()
            if call_is_with_target:
                filtered_lines.append(text)
            continue

        if in_call_block:
            if call_is_with_target:
                filtered_lines.append(text)
            # The closing assessment is appended as one element that begins
            # with the footer, so the element carrying it closes the block.
            if _CALL_FOOTER_MARKER in text:
                in_call_block = False
                call_is_with_target = False
            continue

        if stripped[:1] in ("┌", "│", "└"):
            # Effect-box furniture: raw UK metric deltas (ER-038)
            continue

        if _is_structural_line(stripped) or not _SPEAKER_PREFIX_RE.match(stripped):
            filtered_lines.append(text)

    filtered_lines = bound_chars(filtered_lines, MAX_DIPLOMATIC_CONTEXT_CHARS)

    # Build the final context
    context_parts = []

    # World framing: the turn and one neutral sentence. The UK's private
    # metrics stay out of a foreign counterpart's head (ER-038).
    context_parts.append("=" * 60)
    context_parts.append("CURRENT SITUATION")
    context_parts.append("=" * 60)
    context_parts.append(f"Turn: {world_state.turn}")
    context_parts.append("A serious security crisis involving Russia and NATO is under way.")
    context_parts.append("")

    # Add narrative context if available: the counterpart IS a faction being
    # roleplayed, so it gets its stance and the roleplay instructions.
    if world_state.narrative:
        narrative_context = world_state.narrative.to_llm_context(
            target_country_code)
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
