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
    assert block.index("assessment 1.0") < block.index("Escalation Risk:")


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
    # ...and before the narrative world-state summary that closes the dossier.
    assert with_ledger.index("EVENTS ALREADY PLAYED") < with_ledger.index("THREAT ASSESSMENT")
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
                              conditions, transcript),
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
    early = build_shared_context_prefix(_transcript(turns=3), world)
    later = build_shared_context_prefix(_transcript(turns=4), world)
    # Everything up to the end of the earlier transcript still matches.
    assert _shared_prefix(early, later) > len(early) * 0.8


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


def test_the_budget_is_large_enough_to_be_worth_caching():
    """~60K tokens of history, well inside a 128K window once the role text lands."""
    assert MAX_ADVISOR_TRANSCRIPT_CHARS >= 200_000


def test_the_budget_is_a_bound_whatever_shape_the_transcript_is():
    """Found by property check: the head could swallow an unbounded preamble.

    The opening was taken one whole turn at a time but the *first* turn was
    taken unconditionally, so a transcript whose first TURN header sits a
    long way in pulled all of that preamble into the head regardless of
    budget - 10,410 characters past the cap on the worst case generated
    below. Only the fixed header and elision marker may exceed it.
    """
    import random

    overhead_allowance = 400
    rng = random.Random(0)
    for _ in range(200):
        transcript = []
        for _ in range(rng.randint(1, 400)):
            if rng.random() < 0.1:
                transcript += ["=" * 60, f"TURN {len(transcript) // 10 + 1}", "=" * 60]
            transcript.append("x" * rng.randint(0, 500))
        budget = rng.choice([500, 2000, 10_000, 50_000])
        block = render_transcript_block(transcript, max_chars=budget)
        assert len(block) <= budget + overhead_allowance, (
            f"{len(block)} chars rendered against a {budget} budget")


def test_a_transcript_with_no_turn_headers_still_renders():
    """Synthetic transcripts in tests have no TURN N lines to cut on."""
    block = render_transcript_block(["line " + "x" * 200 for _ in range(500)],
                                    max_chars=5000)
    assert "elided" in block
    assert len(block) < 12_000


# --- the dossier says each thing once (ER-009) ------------------------------

def test_the_dossier_renders_the_metrics_once_not_three_times():
    """The raw values stay; the prose bands and the flags block that restated
    them (and the casualty counts two lines up) are gone. What survives of
    build_world_state_summary is the standing advisor-voice instruction."""
    world = _world()
    world.flags = {"risk_escalation": True}
    block = build_shared_context_prefix(_transcript(), world)

    # Raw values, once.
    assert block.count(f"Escalation Risk: {world.metrics.escalation_risk}/100") == 1
    # The duplicate renderings are out.
    assert "THREAT ASSESSMENT" not in block
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
