"""Inject continuity: the previous turn's event must reach the next inject.

Regression tests for issue #23 — a fixed transcript[-50:] window fed the
inject generator only the adjudication tail of long turns, so the previous
inject (a ballistic-missile near-miss, in the live campaign that surfaced
this) vanished from the story.
"""

from llm.context_builder import get_last_turn_slice
from llm.prompts import build_inject_generation_prompt
from models.world import WorldState, Metrics


def _world():
    return WorldState(
        turn=4, scene=4,
        metrics=Metrics(escalation_risk=89, domestic_stability=29,
                        alliance_cohesion=47),
        flags={}, posture={}, narrative=None,
    )


def _turn(n, body_lines):
    return ["", "=" * 60, f"TURN {n}", "=" * 60, ""] + body_lines


def _campaign_transcript(last_turn_body):
    """Two earlier turns of filler, then the turn under test."""
    t = []
    t += _turn(1, [f"turn-1 filler {i}" for i in range(40)])
    t += _turn(2, [f"turn-2 filler {i}" for i in range(40)])
    t += _turn(3, last_turn_body)
    return t


# --- get_last_turn_slice -----------------------------------------------------

def test_slice_starts_at_last_turn_header():
    transcript = _campaign_transcript(
        ["=== FLASH ALERT ===", "missile launch detected from the Barents Sea"]
        + [f"adjudication line {i}" for i in range(10)])
    window = get_last_turn_slice(transcript)
    assert window[1] == "TURN 3"
    assert "missile launch detected from the Barents Sea" in window
    assert not any("turn-2 filler" in line for line in window)


def test_long_turn_keeps_inject_head_and_adjudication_tail():
    body = (["=== FLASH ALERT ===", "missile launch detected"]
            + [f"discussion line {i}" for i in range(300)]
            + ["FINAL ADJUDICATION LINE"])
    window = get_last_turn_slice(_campaign_transcript(body), max_lines=120)
    assert len(window) == 121  # max_lines plus the elision marker
    assert "missile launch detected" in window
    assert "FINAL ADJUDICATION LINE" in window
    assert any("elided" in line for line in window)


def test_short_turn_returned_whole():
    body = ["=== FLASH ALERT ===", "one-line event"]
    window = get_last_turn_slice(_campaign_transcript(body))
    assert window == _turn(3, body)[1:]  # from the ruler above the header


def test_fallback_without_turn_headers_is_tail_window():
    transcript = [f"line {i}" for i in range(200)]
    assert get_last_turn_slice(transcript, max_lines=50) == transcript[-50:]


# --- build_inject_generation_prompt ------------------------------------------

def test_previous_inject_survives_into_prompt(monkeypatch):
    # The event opens the turn, then >50 lines of discussion/adjudication
    # follow — exactly the shape that used to push it out of the window.
    body = (["=== FLASH ALERT ===",
             "Ballistic missile launch detected from the Barents Sea."]
            + [f"discussion/adjudication line {i}" for i in range(80)])
    transcript = _campaign_transcript(body)

    # Keep the test offline: the rolling summary normally calls the LLM.
    import llm.context_builder as cb
    monkeypatch.setattr(cb, "generate_summary",
                        lambda t, p: "summary unavailable in test")

    prompt = build_inject_generation_prompt(_world(), 4, {}, None, transcript)
    assert "Ballistic missile launch detected from the Barents Sea." in prompt
    assert "CONTINUITY IS MANDATORY" in prompt
    assert "LAST TURN (TURN 3) - FOR CONTINUITY" in prompt
