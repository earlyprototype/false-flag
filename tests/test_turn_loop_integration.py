"""Headless integration tests for the interactive turn loop.

These drive the *real* CLI (``python -m cli.main play``) through scripted
stdin, exactly the way a player (or CI pipe) would. They exist because the
turn-idempotence bugs they cover previously survived CI, which only smoke-
tested ``--help``:

- cancelling out of the decision phase must not re-apply the turn briefing's
  scripted inject effects;
- loading a save (autosave or a mid-turn named save) must replay briefing
  context WITHOUT re-applying its effects, so repeated loads of the same
  save are deterministic.

Mechanics this relies on (see cli/keyboard.py): on non-TTY stdin the
"Press SPACE" pacing gates pass through without consuming stdin, so piped
lines map 1:1 onto real prompts (the four numeric setup menus, the ``>``
discussion prompt, the ``Decision>`` prompt, and any in-briefing
diplomatic-response prompt).

Metrics are asserted from the JSON save files (``world.metrics``) rather
than scraped from ANSI output. Runs use the deterministic mock LLM driver
(WARGAME_LLM=mock) and the default seed (42), so results are reproducible.

The game always writes saves to <repo>/saves/ (the path is derived from the
package location and cannot be redirected), so the module fixture moves any
pre-existing saves directory aside and restores it afterwards.

Each full game run takes roughly 20-60 seconds in mock mode; the module
runs the game four times total, shared across all tests via a
module-scoped fixture.
"""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="Piped-stdin input model differs on Windows (msvcrt consumes keys)",
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SAVES_DIR = REPO_ROOT / "saves"
AUTOSAVE = SAVES_DIR / "war_game_2025_autosave.json"
TURN1_SAVE = SAVES_DIR / "war_game_2025_turn_001.json"
TURN2_SAVE = SAVES_DIR / "war_game_2025_turn_002.json"

# Generous per-run ceiling: mock-mode runs measure ~40-180s locally (the
# text streaming sleeps run even on non-TTY stdout), so leave headroom for
# slower CI machines.
SUBPROCESS_TIMEOUT = 480

# Four numeric setup menus: scenario variant, play mode, difficulty, game type
MENU_INPUTS = "1\n1\n1\n1\n"

# A benign free-text line. Depending on scripted content it is consumed
# either by an in-briefing diplomatic-response prompt or as a discussion
# question — both are deterministic in mock mode and harmless.
FILLER_LINE = "We are monitoring the situation closely.\n"

# Trailing /quit lines guarantee a clean exit no matter how many extra
# prompts the scripted content raises; unconsumed lines are simply dropped
# when the process exits.
QUIT_TAIL = "/quit\n/quit\n/quit\n"


def _run_game(stdin_text, extra_args=()):
    """Run `python -m cli.main play` headlessly with scripted stdin."""
    env = dict(os.environ)
    env["WARGAME_LLM"] = "mock"  # force deterministic mock driver
    started = time.monotonic()
    result = subprocess.run(
        [sys.executable, "-m", "cli.main", "play", *extra_args],
        input=stdin_text,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        env=env,
        timeout=SUBPROCESS_TIMEOUT,
    )
    result.duration = time.monotonic() - started
    return result


def _read_save(path):
    assert path.exists(), (
        f"Expected save file {path} was not written. "
        f"Saves present: {sorted(p.name for p in SAVES_DIR.glob('*.json')) if SAVES_DIR.exists() else 'none'}"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _clear_saves():
    shutil.rmtree(SAVES_DIR, ignore_errors=True)


def _combined_output(result):
    return (result.stdout or "") + (result.stderr or "")


@pytest.fixture(scope="module")
def game_runs():
    """Run the four scripted game sessions once and share the results.

    Sequencing matters because every run reads/writes the same <repo>/saves
    directory, so all subprocess work happens inside this single
    module-scoped fixture rather than in per-test fixtures.
    """
    # Preserve any real saves the developer has, then start clean.
    backup = None
    if SAVES_DIR.exists():
        backup = SAVES_DIR.with_name(f"saves.pytest-backup-{os.getpid()}")
        SAVES_DIR.rename(backup)

    try:
        outputs = []

        # --- Run A: new game, enter decision phase, cancel back out,
        # save, quit. Cancel must not re-apply the turn-1 briefing inject.
        _clear_saves()
        run_a = _run_game(
            MENU_INPUTS + "/decide\ncancel\n/save\n" + QUIT_TAIL
        )
        outputs.append(("cancel-run", run_a))
        assert run_a.returncode == 0, (
            f"cancel-run exited {run_a.returncode}\n"
            f"--- tail of output ---\n{_combined_output(run_a)[-3000:]}"
        )
        cancel_save = _read_save(TURN1_SAVE)

        # --- Run B: new game, play a full turn (decision adjudicates),
        # let the end-of-turn autosave land, then quit in turn 2.
        _clear_saves()
        run_b = _run_game(
            MENU_INPUTS
            + "/decide\n"
            + "Open a direct diplomatic channel and hold current military posture.\n"
            + FILLER_LINE  # consumed by turn-2 briefing prompt or discussion
            + QUIT_TAIL
        )
        outputs.append(("full-turn-run", run_b))
        assert run_b.returncode == 0, (
            f"full-turn-run exited {run_b.returncode}\n"
            f"--- tail of output ---\n{_combined_output(run_b)[-3000:]}"
        )
        autosave = _read_save(AUTOSAVE)

        # --- Run C: load the autosave (turn 2, phase "briefing"); the
        # turn-2 briefing streams and applies its inject exactly once,
        # then we save mid-turn and quit.
        run_c = _run_game(
            FILLER_LINE + "/save\n" + QUIT_TAIL,
            extra_args=("--load", "saves/war_game_2025_autosave.json"),
        )
        outputs.append(("load-autosave-run", run_c))
        assert run_c.returncode == 0, (
            f"load-autosave-run exited {run_c.returncode}\n"
            f"--- tail of output ---\n{_combined_output(run_c)[-3000:]}"
        )
        turn2_first = _read_save(TURN2_SAVE)

        # --- Run D: load the mid-turn (discussion-phase) named save that
        # run C just wrote, then immediately save again. Run D overwrites
        # the same file, so run C's payload was captured above first.
        # Loading a mid-turn save replays the briefing for context and
        # must NOT re-apply its effects.
        run_d = _run_game(
            FILLER_LINE + "/save\n" + QUIT_TAIL,
            extra_args=("--load", "saves/war_game_2025_turn_002.json"),
        )
        outputs.append(("reload-turn2-run", run_d))
        assert run_d.returncode == 0, (
            f"reload-turn2-run exited {run_d.returncode}\n"
            f"--- tail of output ---\n{_combined_output(run_d)[-3000:]}"
        )
        turn2_second = _read_save(TURN2_SAVE)

        # Per-run timings, visible with `pytest -s` for slow-CI diagnostics.
        for name, result in outputs:
            print(f"[turn-loop-integration] {name}: {result.duration:.1f}s",
                  file=sys.stderr)

        yield SimpleNamespace(
            outputs=outputs,
            cancel_save=cancel_save,
            autosave=autosave,
            turn2_first=turn2_first,
            turn2_second=turn2_second,
        )
    finally:
        _clear_saves()
        if backup is not None:
            backup.rename(SAVES_DIR)


def test_cancel_does_not_reapply_briefing(game_runs):
    """Entering the decision phase and cancelling back to discussion must
    leave metrics at their post-briefing values — the turn-1 scripted
    inject (+3 escalation, -2 stability at 0.5x standard difficulty on the
    60/50/40 baseline) must be applied exactly once, not compounded."""
    world = game_runs.cancel_save["world"]
    metrics = world["metrics"]

    assert world["turn"] == 1
    assert metrics["escalation_risk"] == 63
    assert metrics["domestic_stability"] == 48
    assert metrics["alliance_cohesion"] == 40


def test_full_turn_and_autosave_resume(game_runs):
    """A full turn autosaves the start of turn 2, and loading that save
    (or the mid-turn save derived from it) is deterministic: briefing
    effects apply exactly once per turn, never again on reload."""
    # End-of-turn autosave: positioned at the start of turn 2's briefing.
    autosave_world = game_runs.autosave["world"]
    autosave_metrics = autosave_world["metrics"]

    assert autosave_world["turn"] == 2
    assert autosave_world["phase"] == "briefing"
    assert game_runs.autosave.get("variant", "standard") == "standard"

    # Metrics reflect briefing (63/48/40) plus exactly one adjudication pass.
    # The mock pipeline is fully deterministic: the diplomatic decision draws
    # supportive USA/POL actor responses plus an "adequate" quality
    # assessment, netting esc -3 / stab +1 / coh +13 on top of the briefing.
    # Exact equality catches both a skipped and a compounded briefing inject
    # (run A independently proves the inject applies exactly once).
    assert autosave_metrics["escalation_risk"] == 60, (
        f"escalation {autosave_metrics['escalation_risk']} != 60 — briefing "
        "inject skipped/compounded, or mock adjudication deltas changed"
    )
    assert autosave_metrics["domestic_stability"] == 49
    assert autosave_metrics["alliance_cohesion"] == 53

    # Loading the autosave ran the turn-2 briefing once and saved mid-turn.
    first_world = game_runs.turn2_first["world"]
    assert first_world["turn"] == 2

    # Idempotence: reloading the resulting mid-turn save and saving again
    # must reproduce the same state — the replayed briefing must not
    # re-apply its inject deltas.
    second_world = game_runs.turn2_second["world"]
    assert second_world["turn"] == first_world["turn"]
    assert second_world["metrics"] == first_world["metrics"], (
        "Metrics drifted across a load/save round-trip of the same "
        f"mid-turn save: {first_world['metrics']} -> {second_world['metrics']}"
    )


def test_no_traceback_in_output(game_runs):
    """None of the scripted runs may emit a Python traceback."""
    for name, result in game_runs.outputs:
        combined = _combined_output(result)
        assert "Traceback" not in combined, (
            f"{name} emitted a traceback:\n{combined[-4000:]}"
        )
