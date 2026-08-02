"""Regression tests for the mock-playtest UX fix round.

Covers, headlessly:
- /call failure paths speak in fiction and are actually printed
- diplomatic prompt label has no doubled colon and the PM line isn't echoed
- addressing an advisor who isn't in the room gets an in-fiction correction
  (and burns no LLM call)
- internal persona names map to cabinet titles at display time
- immersive/emergent adjudication shows no quality grades or numeric deltas
- inject effect boxes are transcript-only (single display, one glyph style)
- stochastic inject failure degrades to a diegetic quiet turn (no debug spew,
  no meta-header)
- debrief decision recap entries are truncated on a word boundary
- the US National Security Advisor is sectioned apart from the UK cabinet
- the dashboard SITREP labels fit the sidebar untruncated
"""

import re
import sys
from pathlib import Path
from random import Random
from types import SimpleNamespace

import pytest

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from models.world import WorldState, Metrics


RNG = Random(42)

_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")


def _plain(text: str) -> str:
    return _ANSI_RE.sub("", text)


def _world(cohesion=40, turn=1):
    return WorldState(
        turn=turn,
        scene=turn,
        metrics=Metrics(
            escalation_risk=60,
            domestic_stability=50,
            alliance_cohesion=cohesion,
        ),
        flags={},
        posture={},
    )


def _fake_llm(prompt, rng, **kwargs):
    if "assessing the outcome" in prompt.lower():
        return ("OUTCOME: NEUTRAL\n"
                "ALLIANCE_COHESION_DELTA: 0\n"
                "SUMMARY: The conversation concluded politely.")
    return "We hear you, Prime Minister."


# --- /call failure paths (defect 1) ---------------------------------------

def test_call_unknown_country_prints_in_fiction_failure():
    from engine.diplomacy import run_diplomatic_encounter

    printed = []
    transcript, delta = run_diplomatic_encounter(
        _world(), "Atlantis", required=False, context=None,
        llm_generate=_fake_llm, rng=Random(42), root_path=root,
        print_fn=printed.append,
    )
    assert delta == 0
    assert printed, "failure must be shown to the player, not just returned"
    combined = " ".join(printed)
    assert "no secure channel" in combined
    assert "Atlantis" in combined
    # No dev-speak
    assert "Connection failed" not in combined


def test_call_known_country_without_access_prints_in_fiction_refusal():
    from engine.diplomacy import run_diplomatic_encounter

    printed = []
    transcript, delta = run_diplomatic_encounter(
        _world(cohesion=1), "US", required=False, context=None,
        llm_generate=_fake_llm, rng=Random(42), root_path=root,
        print_fn=printed.append,
    )
    assert delta == 0
    combined = " ".join(printed)
    assert "not accepting the call" in combined


# --- Diplomatic prompt label / echo (defect 2) -----------------------------

def test_diplomatic_prompt_label_and_no_pm_echo():
    from engine.diplomacy import run_diplomatic_encounter

    prompts = []
    printed = []

    def fake_input(label):
        prompts.append(label)
        return "Thank you."  # standalone closer ends the call

    transcript, delta = run_diplomatic_encounter(
        _world(cohesion=100), "Ireland", required=False, context=None,
        llm_generate=_fake_llm, rng=Random(42), root_path=root,
        get_player_input=fake_input, print_fn=printed.append,
    )
    # Prompt label carries no trailing colon (CLI wrappers add their own)
    assert prompts and all(p == "Response" for p in prompts)
    # The player's own line is transcript-only, never echoed back
    assert transcript, "transcript should not be empty"
    assert any(line.startswith("Prime Minister:") for line in transcript)
    assert not any(line.startswith("Prime Minister:") for line in printed)


# --- Unknown advisor correction (defect 3) ---------------------------------

def _initial_conditions():
    return {
        "characters": {
            "chief_defence_staff": {"role": "Military Commander"},
            "national_security_advisor": {"role": "Intelligence Coordinator"},
            "home_secretary": {"role": "Domestic Security"},
            "foreign_secretary": {"role": "Diplomatic Lead"},
            "attorney_general": {"role": "Legal Advisor"},
        }
    }


def test_unknown_advisor_gets_correction_without_llm_call():
    from agents.conversation import handle_player_question

    def exploding_llm(prompt, rng, **kwargs):
        raise AssertionError("no LLM call should be made for an absent advisor")

    responses = handle_player_question(
        _world(), "Chancellor, what do you think?", _initial_conditions(),
        exploding_llm, Random(42),
    )
    assert len(responses) == 1
    role, text = responses[0]
    assert role == "Cabinet Secretary"
    assert "no Chancellor in this room" in text


def test_known_advisor_still_routes_normally():
    from agents.conversation import handle_player_question

    calls = []

    def llm(prompt, rng, **kwargs):
        calls.append(prompt)
        return "Assessment follows, Prime Minister."

    responses = handle_player_question(
        _world(), "CDS, what are our options?", _initial_conditions(),
        llm, Random(42),
    )
    assert calls, "a real advisor question must reach the LLM"
    assert responses[0][0] == "Military Commander"  # internal name; mapped at display


def test_sentence_openers_do_not_trigger_correction():
    from agents.conversation import _detect_unknown_addressee

    known = {"cds", "nsa", "foreign secretary"}
    assert _detect_unknown_addressee("Right, what next?", known) is None
    assert _detect_unknown_addressee("General question: what now?", known) is None
    assert _detect_unknown_addressee("Overall, how bad is it?", known) is None
    assert _detect_unknown_addressee("Defence Secretary, report.", known) == "Defence Secretary"


# --- Display-time role mapping (defect 6) ----------------------------------

def test_display_role_maps_internal_personas_to_cabinet_titles():
    from cli.display_utils import display_role

    assert display_role("Military Commander") == "Chief of the Defence Staff"
    assert display_role("Intelligence Coordinator") == "National Security Advisor"
    assert display_role("Diplomatic Lead") == "Foreign Secretary"
    assert display_role("Domestic Security") == "Home Secretary"
    assert display_role("Legal Advisor") == "Attorney General"
    # Unknown labels pass through
    assert display_role("Cabinet Secretary") == "Cabinet Secretary"


# --- Immersive adjudication leaks (defect 4) --------------------------------

def test_narrative_assessment_removes_grades_and_labels():
    from cli.display_utils import narrative_assessment

    raw = ("Action Quality: ADEQUATE\n"
           "Reasoning: A measured response.\n"
           "\n"
           "International Response:\n"
           "  ✓ United States: Stands with the UK.")
    out = narrative_assessment(raw)
    assert "ADEQUATE" not in out
    assert "Action Quality" not in out
    assert "measured" in out
    assert "Reasoning:" not in out
    assert "United States" in out


def test_adjudication_display_hides_numbers_outside_classic(monkeypatch):
    import cli.display_utils as display_utils
    from cli.display_utils import display_adjudication_results
    from cli.rich_ui import console
    from cli.theme import theme_manager

    # engine.game_manager (imported by other test modules) force-disables the
    # Rich UI process-wide; pin the Rich branch so this test is order-proof.
    monkeypatch.setattr(display_utils, "RICH_ENABLED", True)

    colors = theme_manager.get_colors()
    actor_responses = [SimpleNamespace(
        actor_id="USA", trust_change=6,
        public_response="The United States stands with the United Kingdom.")]
    world = _world()
    world.actor_system = None

    reasoning = "Action Quality: ADEQUATE\nReasoning: Fine."
    effects = {"escalation_risk": -3, "alliance_cohesion": 5}

    with console.capture() as cap:
        display_adjudication_results(
            colors, "immersive", reasoning, effects,
            [("National Security Advisor", "Understood.")],
            actor_responses, world)
    immersive_out = _plain(cap.get())
    assert "ADEQUATE" not in immersive_out
    assert "(+6)" not in immersive_out
    assert "escalation_risk" not in immersive_out

    with console.capture() as cap:
        display_adjudication_results(
            colors, "classic", reasoning, effects,
            [("National Security Advisor", "Understood.")],
            actor_responses, world)
    classic_out = _plain(cap.get())
    assert "(+6)" in classic_out  # classic keeps the numbers


# --- Effect boxes (defect 7) ------------------------------------------------

def test_apply_inject_effects_is_transcript_only_with_one_glyph(capsys):
    from engine.sim_loop import apply_inject_effects

    world = _world()
    inject = {"effects": [
        {"metric": "escalation_risk", "delta": 6},
        {"metric": "domestic_stability", "delta": -4},
    ]}
    lines = apply_inject_effects(world, inject, silent=False)

    # Nothing printed: display is the caller's job (exactly once, after the
    # narrative)
    captured = capsys.readouterr()
    assert captured.out == ""

    content = [l for l in lines if "Effect:" in l]
    assert len(content) == 2
    assert all("→" in l for l in content)
    assert not any("->" in l for l in content)

    # Non-classic display still strips them
    from cli.display_utils import strip_effect_boxes
    assert not any("Effect:" in l for l in strip_effect_boxes(lines))


# --- Stochastic inject fallback + meta header (defects 8, 9) ----------------

def test_generation_failure_yields_diegetic_quiet_turn(monkeypatch):
    import engine.sim_loop as sim_loop

    monkeypatch.setattr(sim_loop, "generate_inject",
                        lambda *a, **k: None)
    world = _world(turn=99)
    inject, transcript = sim_loop.run_turn_briefing(
        world, "war_game_2025", stochastic_injects=True, rng=Random(42),
        root_path=root, suppress_display=True, silent_effects=True,
    )
    assert inject is not None
    assert inject["id"] == "turn_099_quiet"
    combined = "\n".join(transcript)
    assert "no significant developments" in combined
    for leak in ("[WARNING]", "[ERROR]", "[DEBUG]", "No inject for this turn",
                 "[Stochastically generated inject]"):
        assert leak not in combined


def test_generated_inject_has_no_meta_header(monkeypatch):
    import engine.sim_loop as sim_loop

    monkeypatch.setattr(sim_loop, "generate_inject", lambda *a, **k: {
        "id": "x", "title": "Test Event", "description": "Something happens.",
        "channel": "briefing", "effects": [],
    })
    world = _world(turn=99)
    inject, transcript = sim_loop.run_turn_briefing(
        world, "war_game_2025", stochastic_injects=True, rng=Random(42),
        root_path=root, suppress_display=True, silent_effects=True,
    )
    assert inject is not None
    assert "[Stochastically generated inject]" not in "\n".join(transcript)


# --- Debrief recap truncation (defect 11) -----------------------------------

def test_debrief_truncates_long_decisions_on_word_boundary():
    from engine.endings import Ending, build_debrief_lines

    long_decision = " ".join(["reinforce the northern flank"] * 30)  # ~850 chars
    transcript = [f"Prime Minister's Decision: {long_decision}"]
    ending = Ending("uneasy_peace", "AN UNEASY PEACE", "partial", "It held.")
    world = _world(turn=10)

    lines = build_debrief_lines(world, ending, {}, transcript)
    recap = [l for l in lines if l.strip().startswith("1.")]
    assert recap, "decision recap entry missing"
    entry = recap[0].strip()[3:]
    assert entry.endswith("...")
    assert len(entry) <= 165
    # Word boundary: no chopped word before the ellipsis
    assert entry[:-3].rstrip()[-1].isalpha()
    body = entry[:-3].strip()
    assert body in long_decision  # cut on a word boundary, words intact


# --- US liaison sectioning (defect 13) --------------------------------------

def test_us_liaison_sectioned_apart_from_uk_cabinet():
    from cli.display_utils import advisor_attitude_lines
    from models.narrative_state import create_initial_narrative_state

    state = create_initial_narrative_state(metrics=Metrics(
        escalation_risk=60, domestic_stability=50, alliance_cohesion=40))
    lines = advisor_attitude_lines(state)

    us_idx = next(i for i, l in enumerate(lines)
                  if "US National Security Advisor" in l)
    divider_idx = next(i for i, l in enumerate(lines) if "WASHINGTON" in l)
    assert divider_idx < us_idx, "US liaison must sit under a WASHINGTON divider"
    # Every UK cabinet row sits above the divider
    for i, line in enumerate(lines[:divider_idx]):
        assert "US National Security Advisor" not in line


# --- Resume offer (defect 10) -----------------------------------------------

@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Piped-stdin input model differs on Windows (msvcrt consumes keys)",
)
def test_play_offers_to_resume_existing_autosave():
    """`play` with an autosave present must offer to resume before the setup
    menus; accepting loads the save (the --load path)."""
    import os
    import shutil
    import subprocess

    saves_dir = root / "saves"
    backup = None
    if saves_dir.exists():
        backup = saves_dir.with_name(f"saves.pytest-backup-ux-{os.getpid()}")
        saves_dir.rename(backup)
    try:
        from engine.persistence import save_game

        world = _world(turn=3)
        world.phase = "briefing"
        save_game(world, ["earlier transcript"], "war_game_2025", "autosave",
                  root, play_mode="classic", narrative_state=None,
                  variant="standard")

        env = dict(os.environ)
        env["WARGAME_LLM"] = "mock"
        result = subprocess.run(
            [sys.executable, "-m", "cli.main", "play"],
            input="y\n/quit\ny\n/quit\ny\n",
            capture_output=True, text=True, cwd=str(root), env=env,
            timeout=480,
        )
        out = _plain(result.stdout + result.stderr)
        assert result.returncode == 0, f"resume run exited {result.returncode}:\n{out[-3000:]}"
        assert "Resume campaign (Turn 3" in out
        assert "Resuming at Turn 3" in out
        # Setup menus must have been skipped
        assert "SELECT GAMEPLAY MODE" not in out
    finally:
        shutil.rmtree(saves_dir, ignore_errors=True)
        if backup is not None:
            backup.rename(saves_dir)


# --- Dashboard SITREP labels (defect 12c) -----------------------------------

def test_sitrep_labels_fit_sidebar_untruncated():
    from rich.console import Console
    from cli.dashboard import WargameDashboard

    render_console = Console(width=30, force_terminal=False)
    dash = WargameDashboard(_world(), render_console)
    with render_console.capture() as cap:
        render_console.print(dash.render_sidebar())
    out = cap.get()
    for label in ("Risk", "Stability", "Cohesion", "Casualties"):
        assert label in out, f"{label} truncated in SITREP sidebar: {out}"
    assert "…" not in out
