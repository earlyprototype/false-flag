"""Unit tests for the interactive decision loop (cli.main.run_decision_phase).

These pin the two decision-flow bugs fixed on this branch, in-process (the
subprocess-driven turn-loop integration tests are skipped on Windows, so
this seam is driven directly with scripted prompt/confirm stand-ins):

- Issue #16: after the player applies advisor recommendations and residual
  concerns trigger the second confirm ("Proceed anyway?", default No),
  declining must NOT silently discard the enhanced decision. The next
  Decision> prompt re-offers it: pressing Enter re-submits the enhanced
  text unchanged.
- Issue #22: on the apply-recommendations branch, exactly one
  "Prime Minister's Decision:" block lands in the transcript for one
  committed decision - the enhanced block replaces the superseded
  original's instead of stacking beside it.
"""

import sys
from pathlib import Path
from random import Random
from types import SimpleNamespace

import pytest
import typer

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

import cli.main as cli_main  # noqa: E402

DECISION = "Hold current military posture and convene COBRA."
REPLACEMENT = "Stand down patrols and open a back channel."
CONCERNS = [("NSA", "No cyber posture set.", "Raise CNI cyber readiness to HIGH.")]

# Sentinel: the player pressed Enter, accepting whatever default is offered.
ENTER = object()


class ScriptedIO:
    """Scripted stand-ins for typer.prompt / typer.confirm.

    Answers are consumed in order; the ENTER sentinel returns the offered
    default, exactly like pressing Enter at the real prompt. Prompt texts
    and offered defaults are recorded for assertions.
    """

    def __init__(self, prompts, confirms):
        self.prompts = list(prompts)
        self.confirms = list(confirms)
        self.prompt_log = []   # (text, offered_default) per typer.prompt
        self.confirm_log = []  # (text, offered_default) per typer.confirm

    def prompt(self, text, default=None, **kwargs):
        self.prompt_log.append((text, default))
        assert self.prompts, f"unexpected extra prompt: {text!r}"
        answer = self.prompts.pop(0)
        return default if answer is ENTER else answer

    def confirm(self, text, default=False, **kwargs):
        self.confirm_log.append((text, default))
        assert self.confirms, f"unexpected extra confirm: {text!r}"
        answer = self.confirms.pop(0)
        return default if answer is ENTER else answer


def make_run_turn_decision(script):
    """Fake engine decision call. `script` holds (concerns, pushback) per
    successive call; the transcript block mirrors the real
    format_decision_transcript shape closely enough to count blocks."""
    calls = []

    def fake(world, scenario, action, rng, root_path, transcript,
             narrative_state=None):
        assert len(calls) < len(script), (
            f"run_turn_decision called {len(calls) + 1} times, "
            f"scripted for {len(script)}")
        concerns, pushback = script[len(calls)]
        calls.append(action)
        interpretation = f"Interpretation of: {action}"
        lines = [f"Prime Minister's Decision: {action}", "",
                 interpretation, ""]
        return interpretation, pushback, concerns, lines

    fake.calls = calls
    return fake


def drive(monkeypatch, io, script, selection=("A", [0]),
          transcript=None):
    """Run cli_main.run_decision_phase with everything scripted."""
    monkeypatch.setattr(typer, "prompt", io.prompt)
    monkeypatch.setattr(typer, "confirm", io.confirm)
    monkeypatch.setattr(typer, "clear", lambda: None)
    monkeypatch.setattr(cli_main, "wait_for_space", lambda *a, **k: None)
    monkeypatch.setattr(cli_main, "display_decision_summary",
                        lambda *a, **k: None)
    monkeypatch.setattr(cli_main, "display_critical_concerns_with_selection",
                        lambda concerns: selection)
    fake = make_run_turn_decision(script)
    monkeypatch.setattr(cli_main, "run_turn_decision", fake)

    if transcript is None:
        transcript = []
    result = cli_main.run_decision_phase(
        SimpleNamespace(turn=3), "war_game_2025", Random(42), root,
        transcript, narrative_state=None)
    return result, transcript, fake


def decision_blocks(transcript):
    return [l for l in transcript
            if l.startswith("Prime Minister's Decision:")]


def enhanced_text():
    """The enhanced decision exactly as production builds it."""
    return cli_main.append_recommendations_to_decision(DECISION, CONCERNS, [0])


# --- issue #16: declining the residual-concerns confirm ---------------------

def test_declining_residual_concerns_reoffers_enhanced_decision(monkeypatch):
    """Player applies recommendations, confirms the enhanced decision, and
    residual concerns raise "Proceed anyway?" - pressing Enter (default No)
    must re-offer the enhanced decision at the next Decision> prompt, not
    drop back to a blank prompt with the text unrecoverable."""
    enhanced = enhanced_text()
    io = ScriptedIO(
        prompts=[DECISION,  # Decision>
                 "",        # see-details gate
                 ENTER,     # Decision> again: Enter keeps the re-offered text
                 ""],       # see-details gate
        confirms=[ENTER,    # "Proceed with enhanced decision?" (default True)
                  ENTER],   # "Proceed anyway?" (default False -> decline)
    )
    result, transcript, fake = drive(
        monkeypatch, io,
        script=[(CONCERNS, []),   # original: concerns raised
                (CONCERNS, []),   # enhanced: concerns REMAIN -> second gate
                ([], [])],        # re-submitted enhanced: clean
    )

    # The declined confirm was the second gate, at its documented default.
    assert io.confirm_log == [("Proceed with enhanced decision?", True),
                              ("Proceed anyway?", False)]

    # The Decision> prompt after the decline offered the enhanced decision
    # as its default - the text is still in hand, Enter re-submits it.
    decision_prompts = [(t, d) for t, d in io.prompt_log if t == "Decision>"]
    assert decision_prompts == [("Decision>", ""), ("Decision>", enhanced)]

    # Pressing Enter committed the enhanced decision, nothing was lost.
    assert result is not None
    action, interpretation, pushback = result
    assert action == enhanced
    assert interpretation == f"Interpretation of: {enhanced}"
    assert fake.calls == [DECISION, enhanced, enhanced]


def test_decline_then_resubmit_lands_exactly_one_decision_block(monkeypatch):
    """The decline/re-offer cycle must not stack transcript blocks either:
    one committed decision, one "Prime Minister's Decision:" block."""
    enhanced = enhanced_text()
    prior = "Foreign Secretary: earlier discussion line."
    io = ScriptedIO(prompts=[DECISION, "", ENTER, ""],
                    confirms=[ENTER, ENTER])
    result, transcript, _ = drive(
        monkeypatch, io,
        script=[(CONCERNS, []), (CONCERNS, []), ([], [])],
        transcript=[prior],
    )

    assert result is not None and result[0] == enhanced
    assert transcript[0] == prior, "earlier history must survive the replace"
    assert decision_blocks(transcript) == [
        f"Prime Minister's Decision: {enhanced}"]


def test_decline_then_replacement_decision_lands_exactly_one_block(monkeypatch):
    """Typing a fresh decision over the re-offered text replaces the
    declined enhanced block instead of stacking a second one."""
    io = ScriptedIO(prompts=[DECISION, "", REPLACEMENT, ""],
                    confirms=[ENTER, ENTER])
    result, transcript, fake = drive(
        monkeypatch, io,
        script=[(CONCERNS, []), (CONCERNS, []), ([], [])],
    )

    assert result is not None and result[0] == REPLACEMENT
    assert decision_blocks(transcript) == [
        f"Prime Minister's Decision: {REPLACEMENT}"]


# --- issue #22: one committed decision, one transcript block ----------------

def test_enhanced_decision_replaces_original_transcript_block(monkeypatch):
    """Apply-recommendations commit: the enhanced decision's block must be
    the only decision block - the superseded original's is replaced."""
    enhanced = enhanced_text()
    prior = "NSA: the room's earlier assessment."
    io = ScriptedIO(prompts=[DECISION, ""],
                    confirms=[ENTER])  # "Proceed with enhanced decision?"
    result, transcript, fake = drive(
        monkeypatch, io,
        script=[(CONCERNS, []),  # original: concerns raised
                ([], [])],       # enhanced re-interpretation: clean
        transcript=[prior],
    )

    assert result is not None
    assert result[0] == enhanced
    assert fake.calls == [DECISION, enhanced]
    assert transcript[0] == prior, "earlier history must survive the replace"
    assert decision_blocks(transcript) == [
        f"Prime Minister's Decision: {enhanced}"]
    # The original's exact block line is gone, not merely outnumbered.
    assert f"Prime Minister's Decision: {DECISION}" not in transcript


# --- extraction regression guards -------------------------------------------

def test_plain_decision_records_a_single_block(monkeypatch):
    """No concerns, no pushback: the decision commits first pass with its
    one transcript block - the pre-fix happy path is unchanged."""
    io = ScriptedIO(prompts=[DECISION, ""], confirms=[])
    result, transcript, fake = drive(
        monkeypatch, io, script=[([], [])])

    assert result == (DECISION, f"Interpretation of: {DECISION}", [])
    assert fake.calls == [DECISION]
    assert decision_blocks(transcript) == [
        f"Prime Minister's Decision: {DECISION}"]


def test_cancel_returns_to_discussion_without_touching_transcript(monkeypatch):
    """'cancel' at the Decision> prompt returns None and leaves the
    transcript exactly as it was."""
    prior = ["Home Secretary: earlier line."]
    io = ScriptedIO(prompts=["cancel"], confirms=[])
    result, transcript, fake = drive(
        monkeypatch, io, script=[], transcript=list(prior))

    assert result is None
    assert transcript == prior
    assert fake.calls == []
