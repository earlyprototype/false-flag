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
        echo_player=False,
    )
    # Prompt label carries no trailing colon (CLI wrappers add their own)
    assert prompts and all(p == "Response" for p in prompts)
    # At a live keyboard the terminal already echoed the player's line, so
    # the call view must not repeat it
    assert transcript, "transcript should not be empty"
    assert any(line.startswith("Prime Minister:") for line in transcript)
    assert not any(line.startswith("Prime Minister:") for line in printed)


def test_diplomatic_call_shows_both_sides_when_input_is_piped():
    """Recorded/spectator playback must show the player's side of the call.

    With piped stdin nothing echoes what the player 'typed', so suppressing
    those lines left the transcript a one-sided monologue.
    """
    from engine.diplomacy import run_diplomatic_encounter

    printed = []
    transcript, _ = run_diplomatic_encounter(
        _world(cohesion=100), "Ireland", required=False, context=None,
        llm_generate=_fake_llm, rng=Random(42), root_path=root,
        get_player_input=lambda label: "Thank you.", print_fn=printed.append,
        echo_player=True,
    )
    assert any(line.startswith("Prime Minister:") for line in printed)
    # Still exactly once per exchange — no double-printing
    assert (sum(line.startswith("Prime Minister:") for line in printed)
            == sum(line.startswith("Prime Minister:") for line in transcript))


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


def test_titles_with_connectives_trigger_correction_without_llm_call():
    """Natural titles carry lowercase connectives ("Chancellor of the
    Exchequer"); they must still be caught instead of falling through to
    keyword routing."""
    from agents.conversation import (
        _detect_unknown_addressee,
        handle_player_question,
    )

    known = {"cds", "nsa", "foreign secretary"}
    assert _detect_unknown_addressee(
        "Chancellor of the Exchequer, can the Treasury cover this?", known,
    ) == "Chancellor of the Exchequer"
    assert _detect_unknown_addressee(
        "Minister for the Armed Forces, report.", known,
    ) == "Minister for the Armed Forces"
    # Lowercase words that are NOT connectives still read as sentence openers
    assert _detect_unknown_addressee(
        "General point of order, what now?", known) is None

    def exploding_llm(prompt, rng, **kwargs):
        raise AssertionError("no LLM call should be made for an absent advisor")

    responses = handle_player_question(
        _world(), "Chancellor of the Exchequer, can we afford this?",
        _initial_conditions(), exploding_llm, Random(42),
    )
    assert len(responses) == 1
    role, text = responses[0]
    assert role == "Cabinet Secretary"
    assert "no Chancellor of the Exchequer in this room" in text


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


# --- Rich markup injection (LLM-origin text) ---------------------------------

def test_markdown_to_rich_escapes_bracket_payloads():
    from rich.text import Text

    from cli.display_utils import markdown_to_rich

    out = markdown_to_rich("**Alert:** [flash traffic] intercepted")
    # The markdown emphasis still becomes live Rich markup...
    assert out.startswith("[bold]Alert:[/bold]")
    # ...and renders as intended, with the bracket payload shown literally
    rendered = Text.from_markup(out)
    assert rendered.plain == "Alert: [flash traffic] intercepted"
    assert any(span.style == "bold" for span in rendered.spans)

    # Plain text with brackets survives a markup round-trip unchanged
    plain = markdown_to_rich("[flash traffic] intercepted")
    assert Text.from_markup(plain).plain == "[flash traffic] intercepted"


def test_adjudication_display_escapes_llm_bracket_payloads(monkeypatch):
    import cli.display_utils as display_utils
    from cli.display_utils import display_adjudication_results
    from cli.rich_ui import console
    from cli.theme import theme_manager

    monkeypatch.setattr(display_utils, "RICH_ENABLED", True)
    colors = theme_manager.get_colors()

    actor_responses = [SimpleNamespace(
        actor_id="usa [signals]", trust_change=-2,
        public_response="We reject the [ultimatum] outright.")]
    world = _world()
    world.actor_system = None

    with console.capture() as cap:
        display_adjudication_results(
            colors, "immersive", "Action Quality: ADEQUATE\nReasoning: x.",
            {}, [("NSA [liaison]", "Copy that [bracket] payload.")],
            actor_responses, world)
    out = _plain(cap.get())
    # Bracketed LLM text must be printed literally, not parsed as markup
    assert "[ultimatum]" in out
    assert "usa [signals]" in out
    assert "NSA [liaison]" in out
    assert "[bracket]" in out


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

    us_idx = next(i for i, line in enumerate(lines)
                  if "US National Security Advisor" in line)
    divider_idx = next(i for i, line in enumerate(lines)
                       if "FOREIGN LIAISON" in line)
    assert divider_idx < us_idx, "US liaison must sit under a FOREIGN LIAISON divider"
    # Every UK cabinet row sits above the divider
    for line in lines[:divider_idx]:
        assert "US National Security Advisor" not in line


# --- Intro scene parsing ------------------------------------------------------

def test_intro_scene_subheading_never_leaks_into_body():
    """The date/time '## ' subheading after '## SCENE' belongs on the scene
    card, even when blank lines separate the two headings."""
    from cli.main import _parse_intro_scene

    for scene in (
        ["=" * 79,
         "## SCENE I: SEVEROMORSK NAVAL BASE, RUSSIA",
         "## 72 Hours Earlier — Thursday, 2nd October 2025, 03:15 Local Time",
         "",
         "The Barents Sea lies black and restless."],
        # Blank line between the headings must not defeat the skip
        ["=" * 79,
         "## SCENE I: SEVEROMORSK NAVAL BASE, RUSSIA",
         "",
         "## 72 Hours Earlier — Thursday, 2nd October 2025, 03:15 Local Time",
         "",
         "The Barents Sea lies black and restless."],
    ):
        body, header = _parse_intro_scene(scene)
        assert header is not None
        assert header[0] == "I"
        assert body == ["The Barents Sea lies black and restless."]
        assert not any("72 Hours Earlier" in line for line in body)


# --- Resume offer (defect 10) -----------------------------------------------

class _StopPlay(Exception):
    """Sentinel to halt `play` once the code under test has run."""


class _autosave_fixture:
    """Context manager: point WARGAME_SAVE_ROOT at a temp dir holding a
    Turn-3 autosave, so the repository's real saves/ is never touched."""

    def __enter__(self):
        import os
        import tempfile

        self._tmp = tempfile.TemporaryDirectory(prefix="wargame-saves-")
        self.save_root = Path(self._tmp.name)
        self._prev_env = os.environ.get("WARGAME_SAVE_ROOT")
        os.environ["WARGAME_SAVE_ROOT"] = str(self.save_root)

        from engine.persistence import save_game

        world = _world(turn=3)
        world.phase = "briefing"
        save_game(world, ["earlier transcript"], "war_game_2025", "autosave",
                  self.save_root, play_mode="classic", narrative_state=None,
                  variant="standard")
        return self

    def __exit__(self, *exc):
        import os

        if self._prev_env is None:
            os.environ.pop("WARGAME_SAVE_ROOT", None)
        else:
            os.environ["WARGAME_SAVE_ROOT"] = self._prev_env
        self._tmp.cleanup()
        return False


def test_play_offers_to_resume_autosave_when_interactive(monkeypatch):
    """With a TTY stdin and an autosave present, `play` must offer to resume
    before the setup menus; accepting routes into the --load path (verified up
    to the save's variant read, then execution is halted)."""
    import cli.main as main
    import engine.persistence as persistence

    with _autosave_fixture():
        monkeypatch.setattr(main.sys.stdin, "isatty", lambda: True,
                            raising=False)
        # Neutralise the interactive-only chrome ahead of the offer
        monkeypatch.setattr(main, "play_title_sequence", lambda *a, **k: None)
        monkeypatch.setattr(main, "wait_for_space", lambda *a, **k: None)
        monkeypatch.setattr(main.typer, "clear", lambda: None)

        prompts = []

        def fake_confirm(text, default=True, **kwargs):
            prompts.append(text)
            return True  # accept the resume offer

        monkeypatch.setattr(main.typer, "confirm", fake_confirm)

        loaded = {}

        def capture_and_stop(path):
            loaded["path"] = Path(path)
            raise _StopPlay()

        # Accepting the offer sets load_save; reading that save's variant is
        # the very next step, so halt there
        monkeypatch.setattr(persistence, "read_save_variant", capture_and_stop)

        with pytest.raises(_StopPlay):
            main.play(scenario="war_game_2025", seed=42, load_save=None,
                      stochastic_injects=True, intro_only=False, variant=None,
                      difficulty=None, play_mode=None, flash_only=False)

        assert prompts, "resume offer must be shown on a TTY"
        assert "Resume campaign (Turn 3" in prompts[0]
        assert loaded["path"].name == "war_game_2025_autosave.json"


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Piped-stdin input model differs on Windows (msvcrt consumes keys)",
)
def test_play_skips_resume_prompt_when_stdin_piped():
    """With piped stdin the resume confirm would silently eat the first queued
    command, so non-interactive runs must skip the offer and start a new
    campaign at the setup menus."""
    import os
    import subprocess

    with _autosave_fixture():
        env = dict(os.environ)
        env["WARGAME_LLM"] = "mock"
        result = subprocess.run(
            [sys.executable, "-m", "cli.main", "play"],
            # Four numeric setup menus, then quit at the first discussion
            # prompt (confirming "Leave the crisis room?")
            input="1\n1\n1\n1\n/quit\ny\n",
            capture_output=True, text=True, cwd=str(root), env=env,
            timeout=480,
        )
        out = _plain(result.stdout + result.stderr)
        assert result.returncode == 0, (
            f"piped run exited {result.returncode}:\n{out[-3000:]}")
        # No resume offer on a pipe...
        assert "Resume campaign" not in out
        assert "Resuming at Turn 3" not in out
        # ...and the first queued line reached the scenario menu (a new
        # campaign starts, so the setup menus are all shown)
        assert "SELECT SCENARIO" in out


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


# --- Diplomatic call metric leak in metric-hiding modes --------------------

def test_call_shows_number_in_classic_and_reading_in_emergent():
    """Immersive/emergent hide metrics; the call sign-off must too.

    "Alliance Cohesion: +10" after a call reintroduced the scoreboard those
    modes exist to remove — but the signal a call carries is worth keeping,
    so the delta becomes an in-fiction reading instead of vanishing.
    """
    from engine.diplomacy import run_diplomatic_encounter

    def run(show_metrics):
        printed = []
        run_diplomatic_encounter(
            _world(cohesion=100), "Ireland", required=False, context=None,
            llm_generate=_fake_llm, rng=Random(42), root_path=root,
            get_player_input=lambda label: "Thank you.",
            print_fn=printed.append, show_metrics=show_metrics,
        )
        return "\n".join(printed)

    classic = run(True)
    emergent = run(False)

    assert "Alliance Cohesion:" in classic
    assert "Alliance Cohesion:" not in emergent
    # Both still report that the call ended and how it went
    assert "CALL ENDED" in classic and "CALL ENDED" in emergent
    assert "Taoiseach" in emergent


# --- China is reachable on the diplomatic switchboard -----------------------

def test_china_is_callable_and_has_both_counterparts():
    """China drives a whole hidden narrative (CHINA_PROXY_WAR) but had no
    diplomatic profile, so the player could never speak to the power secretly
    running the crisis."""
    from engine.diplomacy import get_available_countries, load_diplomatic_profiles

    assert "China" in get_available_countries()

    profiles = load_diplomatic_profiles(root)
    china = profiles["countries"]["China"]
    assert china["full_name"] == "People's Republic of China"
    # The embassy always answers; the President is a call granted, not owed
    assert china["diplomat"]["access_threshold"] == 0
    assert china["leader"]["access_threshold"] > 0
    for level in ("leader", "diplomat"):
        assert china[level]["opening_lines"], f"{level} needs opening lines"
        assert china[level]["key_concerns"]


def test_calling_china_opens_a_real_encounter():
    from engine.diplomacy import run_diplomatic_encounter

    printed = []
    transcript, _ = run_diplomatic_encounter(
        _world(cohesion=100), "China", required=False, context=None,
        llm_generate=_fake_llm, rng=Random(42), root_path=root,
        get_player_input=lambda label: "Thank you.", print_fn=printed.append,
    )
    combined = "\n".join(printed)
    # Not the unknown-country failure path
    assert "no secure channel" not in combined
    assert "China" in combined
    assert any("Chinese Ambassador" in line or "President of China" in line
               for line in transcript)
