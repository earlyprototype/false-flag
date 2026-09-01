"""Prompt order, and why it decides whether caching is possible at all (issue #32).

Providers bill a repeated prompt *prefix* at a cache-read rate, matching from
character zero and stopping at the first difference. Every prompt in this game
used to open with "You are the {role} ...", so across a turn's ~15 calls the
shared opening was the twelve characters "You are the " and the large,
identical, genuinely cacheable part - the transcript - sat below the point
where the prompts had already diverged.

Measured against a full campaign played through a recording endpoint
(dev-scripts/fake_openrouter.py), the share of prompt characters a prefix
cache could match went from 2.2% to 75.9% once the order was fixed.

The tests below pin the three properties that result is built on:

1. the shared dossier comes first, and the volatile state comes last;
2. every transcript-carrying call opens with byte-identical text;
3. nothing above the transcript changes as the transcript grows - a line
   count in the history header was enough on its own to cut the matchable
   prefix down to a few hundred characters.
"""

import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from llm.context_builder import (
    MAX_ADVISOR_TRANSCRIPT_CHARS,
    build_shared_context_prefix,
    render_transcript_block,
)
from llm.prompts import (
    build_advisor_context,
    build_critical_omissions_prompt,
    build_decision_interpretation_prompt,
    build_pushback_prompt,
)
from models.world import Metrics, WorldState


def _world(turn=6, phase="decision", risk=70):
    return WorldState(
        turn=turn, scene=turn, phase=phase,
        metrics=Metrics(escalation_risk=risk, domestic_stability=40,
                        alliance_cohesion=55, casualties_mil=3, casualties_civ=1),
        flags={}, posture={}, narrative=None,
    )


def _conditions():
    return {
        "characters": {
            "foreign_secretary": {"role": "Foreign Secretary",
                                  "knowledge_domains": ["diplomacy"],
                                  "key_concerns": ["alliances"],
                                  "pushback_triggers": ["unilateral action"]},
            "chief_defence_staff": {"role": "Chief of the Defence Staff",
                                    "knowledge_domains": ["military_operations"],
                                    "key_concerns": ["readiness"],
                                    "pushback_triggers": ["overstretch"]},
        },
        "constraints": {"legal": ["Article 51 applies"]},
        "uk_forces": {"navy": "2 Type-45"},
        "stockpiles": {"missiles": 40},
    }


def _transcript(turns=4, lines_per_turn=6):
    lines = []
    for turn in range(1, turns + 1):
        lines.append("=" * 60)
        lines.append(f"TURN {turn}")
        lines.append("=" * 60)
        for i in range(lines_per_turn):
            lines.append(f"National Security Advisor: assessment {turn}.{i} "
                         + "detail " * 20)
    return lines


def _shared_prefix(a: str, b: str) -> int:
    limit = min(len(a), len(b))
    i = 0
    while i < limit and a[i] == b[i]:
        i += 1
    return i


# --- ordering ---------------------------------------------------------------

def test_transcript_comes_before_the_metrics_that_change_every_turn():
    """Slowest-changing content first is the only order a prefix cache can use."""
    block = build_shared_context_prefix(_transcript(), _world())
    assert block.index("GAME HISTORY") < block.index("CURRENT SITUATION")
    assert block.index("assessment 1.0") < block.index("THREAT ASSESSMENT:")


def test_the_event_ledger_sits_after_the_transcript_block():
    """The ledger grows every turn, so it lives in the fast-moving tail (ER-003).

    Placing it above the transcript would cut the cacheable prefix off at the
    first new entry; below it, the append-only prefix property is untouched.
    """
    ledger = [
        {"turn": 1, "title": "Submarine surfaces", "disposition": "resolved",
         "note": "Escorted out of UK waters"},
        {"turn": 2, "title": "Power station explosion", "disposition": "open",
         "note": ""},
    ]
    with_ledger = build_shared_context_prefix(_transcript(), _world(), ledger)
    without = build_shared_context_prefix(_transcript(), _world())

    assert "EVENTS ALREADY PLAYED" in with_ledger
    assert "Escorted out of UK waters" in with_ledger
    # After the transcript block and the CURRENT SITUATION header...
    assert with_ledger.index("GAME HISTORY") < with_ledger.index("EVENTS ALREADY PLAYED")
    assert with_ledger.index("assessment 1.0") < with_ledger.index("EVENTS ALREADY PLAYED")
    assert with_ledger.index("CURRENT SITUATION") < with_ledger.index("EVENTS ALREADY PLAYED")
    # ...and before the standing advisor-voice instructions that close the
    # dossier (the prose bands that used to close it are gone - ER-009).
    assert with_ledger.index("EVENTS ALREADY PLAYED") < with_ledger.index("Do NOT reference")
    # Everything above the transcript is untouched by the ledger.
    assert _shared_prefix(with_ledger, without) > with_ledger.index("CURRENT SITUATION")


def test_every_transcript_carrying_prompt_opens_with_the_same_dossier():
    """The four call types in a turn must be byte-identical up to their role text.

    They used to render the same history three different ways - one through
    get_advisor_context, two through a separate build_conversation_history_context
    at 500 lines, and the omissions check through the same helper at 100.
    Three renderings of identical material share no prefix.
    """
    world, conditions, transcript = _world(), _conditions(), _transcript()

    prompts = [
        build_advisor_context(world, conditions, "foreign_secretary",
                              "Where does NATO stand?", transcript),
        build_decision_interpretation_prompt(world, "Hold the deployment.",
                                             conditions, transcript),
        build_pushback_prompt(world, "Hold the deployment.", "INTERPRETATION: hold",
                              conditions, "foreign_secretary", transcript),
        build_critical_omissions_prompt(world, conditions, "chief_defence_staff",
                                        "Hold the deployment.", ["Submarine detected"],
                                        transcript),
    ]

    dossier = build_shared_context_prefix(transcript, world)
    for prompt in prompts:
        assert prompt.startswith(dossier), "a prompt no longer opens with the dossier"

    # And therefore with each other, for the whole length of the dossier.
    for other in prompts[1:]:
        assert _shared_prefix(prompts[0], other) >= len(dossier)


def test_the_dossier_is_most_of_what_a_long_prompt_contains():
    """The shared part has to be the large part, or sharing it buys nothing."""
    world, conditions, transcript = _world(), _conditions(), _transcript(turns=8)
    prompt = build_critical_omissions_prompt(
        world, conditions, "chief_defence_staff", "Hold.", [], transcript)
    dossier = build_shared_context_prefix(transcript, world)
    assert len(dossier) / len(prompt) > 0.8


# --- nothing above the transcript may move ----------------------------------

def test_the_history_header_does_not_change_as_the_campaign_grows():
    """A line count in the header cut the matchable prefix to a few hundred bytes.

    Every call in a turn sees a slightly different transcript length - the
    advisor question is asked before the decision is interpreted - so a count
    above the transcript makes the prompts differ within their first hundred
    characters, and no amount of identical text below that can be matched.
    """
    short = render_transcript_block(_transcript(turns=2))
    long = render_transcript_block(_transcript(turns=9))
    header_short = short.split("\n")[1]
    header_long = long.split("\n")[1]
    assert header_short == header_long
    assert not any(ch.isdigit() for ch in header_short)


def test_a_growing_transcript_only_appends_to_the_shared_prefix():
    """Append-only is what lets one turn's cache serve the next."""
    world = _world()
    earlier_lines = _transcript(turns=3)
    early = build_shared_context_prefix(earlier_lines, world)
    later = build_shared_context_prefix(_transcript(turns=4), world)
    # Everything up to the end of the earlier transcript still matches. Pinned
    # against the earlier transcript's own last line rather than a fraction of
    # the block, so the measure does not move when the fixed tail below the
    # transcript changes length.
    last_line = earlier_lines[-1]
    assert _shared_prefix(early, later) >= early.index(last_line) + len(last_line)


# --- honesty about what is actually sent ------------------------------------

def test_the_header_no_longer_claims_complete_over_a_window():
    """It said COMPLETE GAME HISTORY while sending the last 500 lines."""
    block = render_transcript_block(_transcript(turns=40), max_chars=4000)
    assert "COMPLETE" not in block.split("\n")[1].upper()
    assert "elided" in block


def test_an_over_budget_history_keeps_the_opening_and_marks_the_cut():
    """Head-anchored, not a sliding tail: the opening is where the crisis is set up.

    A tail window also moves on every single turn, which is the shape a
    prefix cache can do least with.
    """
    transcript = _transcript(turns=40)
    block = render_transcript_block(transcript, max_chars=8000)
    assert "TURN 1" in block.splitlines(), \
        "the campaign's opening was dropped"  # substring also matches TURN 10-19
    assert "TURN 40" in block, "the most recent turn was dropped"
    assert "elided for length" in block
    assert len(block) <= 8000 + len(block.split("\n")[1]) + 400


def test_a_history_within_budget_is_sent_whole():
    transcript = _transcript(turns=3)
    block = render_transcript_block(transcript)
    # The header is constant and mentions elision in the abstract; what must
    # be absent is the inline marker that names an actual cut.
    assert "lines of mid-campaign history elided" not in block
    for line in transcript:
        assert line in block


def test_the_budget_holds_recent_turns_without_buying_raw_history():
    """The window's job is recent verbatim exchanges - several turns' worth -
    not campaign history, which travels in the synopsis and event ledger.
    The first live shakedown measured the old 320k allowance letting the
    advisory prompts grow past 150k chars of paid input by turn 10 (ER-072).
    The constant is a never-fire tripwire now (ER-076), not a guillotine,
    but its magnitude still matters: big enough that whole-turn dropping is
    rare, small enough that the drop actually happens on a long campaign."""
    assert 40_000 <= MAX_ADVISOR_TRANSCRIPT_CHARS <= 100_000


def _split_block(block, transcript):
    """Decompose a rendered block into (head_lines, tail_lines, elided_n).

    elided_n is None when no elision marker is present. Fails the test if
    the block's content lines are anything other than a verbatim contiguous
    head of the transcript plus a verbatim contiguous tail - i.e. if any
    line was cut or rewritten rather than a whole span dropped.
    """
    import re as _re
    lines = block.split("\n")
    assert lines[0] == "=" * 60 and lines[2] == "=" * 60
    content = lines[3:]
    marker_idx = [i for i, l in enumerate(content)
                  if _re.match(r"^\[\.\.\. \d+ lines of mid-campaign history "
                               r"elided for length \.\.\.\]$", l)]
    if not marker_idx:
        assert content == transcript, "content altered without any marker"
        return content, [], None
    assert len(marker_idx) == 1
    i = marker_idx[0]
    head, tail = content[:i], content[i + 1:]
    elided = int(_re.findall(r"\d+", content[i])[0])
    assert head == transcript[:len(head)], "head is not a verbatim prefix"
    assert tail == transcript[len(transcript) - len(tail):], \
        "tail is not a verbatim suffix"
    assert elided == len(transcript) - len(head) - len(tail)
    return head, tail, elided


def test_elision_lands_on_turn_boundaries_and_the_tripwire_never_cuts():
    """The design invariant (ER-076), property-checked over random shapes.

    Whatever the transcript looks like, the rendered window is a verbatim
    contiguous head plus a verbatim contiguous tail - whole spans drop,
    lines never get cut or trimmed. The tail always starts on a turn
    boundary and carries at least the last 2 whole turns. When even that
    minimum exceeds the budget the content still travels whole and the
    tripwire records the breach - the budget is never enforced by cutting.
    """
    import random

    from llm import parse_health
    from llm.context_builder import _turn_boundaries

    overhead_allowance = 400
    rng = random.Random(0)
    for _ in range(200):
        transcript = []
        for _ in range(rng.randint(1, 400)):
            if rng.random() < 0.1:
                transcript += ["=" * 60, f"TURN {len(transcript) // 10 + 1}", "=" * 60]
            transcript.append("x" * rng.randint(0, 500))
        budget = rng.choice([500, 2000, 10_000, 50_000])

        parse_health.reset()
        block = render_transcript_block(transcript, max_chars=budget)
        head, tail, elided = _split_block(block, transcript)
        tripped = parse_health.snapshot()["misses"].get(
            "context_window.tripwire", 0)

        if len(block) > budget + overhead_allowance:
            # Over budget is legal in exactly one case: the tripwire fired
            # because nothing more could drop at a turn boundary.
            assert tripped, (f"{len(block)} chars against a {budget} budget "
                             "with no tripwire recorded")
        if elided is not None:
            boundaries = _turn_boundaries(transcript)
            tail_start = len(transcript) - len(tail)
            assert tail_start in boundaries, "tail does not start on a turn boundary"
            if len(boundaries) >= 2:
                assert tail_start <= boundaries[-2], \
                    "fewer than 2 whole recent turns survived"
    parse_health.reset()


def test_the_minimum_window_survives_the_tripwire_intact():
    """Two enormous recent turns blow the budget; both must arrive whole.

    This is the point of ER-076: detection of a cut does not help anyone -
    the cut must not happen. The tripwire records the breach instead.
    """
    from llm import parse_health

    fat_turn = lambda n: ["=" * 60, f"TURN {n}", "=" * 60] + ["Y" * 3000] * 5
    transcript = []
    for n in range(1, 7):
        transcript += fat_turn(n)

    parse_health.reset()
    block = render_transcript_block(transcript, max_chars=20_000)
    lines = block.split("\n")
    # The last two turns are each ~15k chars against a 20k budget, so the
    # assembled minimum exceeds it - and every line of both still arrives.
    for n in (5, 6):
        assert f"TURN {n}" in lines
    assert lines.count("Y" * 3000) >= 10, "a mandatory turn's content was cut"
    assert not any(0 < len(l) < 3000 and set(l) == {"Y"} for l in lines), \
        "a line was trimmed rather than kept whole"
    assert parse_health.snapshot()["misses"].get("context_window.tripwire"), \
        "an over-budget minimum window must record the tripwire"
    parse_health.reset()


def test_a_transcript_with_no_turn_headers_still_renders():
    """No TURN N lines means no boundary to drop whole turns at. The old
    code fell back to a character tail - a mid-content cut. Now the content
    travels whole and the tripwire records the breach instead."""
    from llm import parse_health

    transcript = ["line " + "x" * 200 for _ in range(500)]
    parse_health.reset()
    block = render_transcript_block(transcript, max_chars=5000)
    for line in transcript:
        assert line in block, "content was cut to satisfy the constant"
    assert parse_health.snapshot()["misses"].get("context_window.tripwire") == 1
    parse_health.reset()


# --- the dossier says each thing once (ER-009) ------------------------------

def test_the_dossier_renders_the_situation_once_and_in_words():
    """One rendering, and it is the prose one.

    ER-009 cut the dossier to a single rendering of the state; issue #91
    settled which one it is. This block closes with the standing rule never
    to reference 'values', so it prints none: the bands say the same thing
    in the register the advisors are told to speak in. The flags block stays
    out - its only non-duplicate content is the casualty counts, which the
    bands already carry.
    """
    world = _world()
    world.flags = {"risk_escalation": True}
    block = build_shared_context_prefix(_transcript(), world)

    # The prose situation, once.
    assert block.count("THREAT ASSESSMENT:") == 1
    assert block.count("CASUALTIES TO DATE:") == 1
    # No scoreboard under the rule that forbids talking about one.
    assert "/100" not in block
    assert "Escalation Risk:" not in block
    assert "KEY INTELLIGENCE FLAGS" not in block
    # The deliberate carry-over survives the slimming.
    assert "Do NOT reference 'metrics', 'game mechanics', 'scores', or 'values'." in block


def test_the_outcome_assessor_is_not_told_to_avoid_values(monkeypatch):
    """ER-027: a prompt that must answer ALLIANCE_COHESION_DELTA: [number]
    must not carry the advisor instruction never to reference values."""
    from random import Random
    from engine.diplomacy import assess_diplomatic_outcome

    captured = {}

    def fake_generate(prompt, rng, **kwargs):
        captured["prompt"] = prompt
        return ("ASSESSMENT: Constructive call.\n"
                "ALLIANCE_COHESION_DELTA: +3\n"
                "REASONING: Reassured the counterpart.")

    assess_diplomatic_outcome(_world(), "US",
                              [("Prime Minister", "We stand with you.")],
                              fake_generate, Random(0))

    assert "ALLIANCE_COHESION_DELTA" in captured["prompt"]
    assert "Do NOT reference" not in captured["prompt"]
    # The prose situation summary is still there.
    assert "THREAT ASSESSMENT" in captured["prompt"]


# --- the narrator window is bounded (ER-008) --------------------------------

def test_the_narrator_slice_is_character_bounded():
    """Twenty transcript elements can be twenty unwrapped paragraphs; the
    element count alone bounded nothing."""
    from llm.context_builder import MAX_NARRATOR_CONTEXT_CHARS
    from llm.prompts import build_narrator_intro_prompt

    fat_turn = ["X" * 4000 for _ in range(20)]
    prompt = build_narrator_intro_prompt(_world(), fat_turn, "Next Event")
    # The transcript window inside the prompt is bounded; the rest of the
    # prompt is fixed-size scaffolding.
    assert len(prompt) < MAX_NARRATOR_CONTEXT_CHARS + 4000
    assert "elided for length" in prompt
