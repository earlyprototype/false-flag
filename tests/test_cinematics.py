"""Tests for the Operation Tuman cinematics (cli/cinematics.py).

Covers the contracts the animations must keep:
- non-TTY stdout prints the static final frame instantly (zero sleeps);
- frame content is deterministic per seed;
- every frame stays within the layout width;
- the condense/transition animations end on exactly their target frame;
- the restyled spinner keeps its API and stays silent on non-TTY.
"""

import re
import sys
import time
from io import StringIO

import pytest
from rich.cells import cell_len
from rich.console import Console

from cli import aesthetics as ae
from cli import cinematics as cin
from cli.spinner import Spinner, sonar_sweep_frames
from cli.theme import theme_manager

WIDTH = ae.DEFAULT_WIDTH  # 78


@pytest.fixture(autouse=True)
def restore_theme():
    original = theme_manager.current_theme_name
    yield
    theme_manager.set_theme(original)


def render(renderable, width: int = 100, force_terminal: bool = False) -> str:
    console = Console(file=StringIO(), width=width,
                      force_terminal=force_terminal, legacy_windows=False)
    console.print(renderable)
    return console.file.getvalue()


def render_frames(frames):
    return [render(frame) for frame, _duration in frames]


# ---------------------------------------------------------------------------
# Non-TTY instant path
# ---------------------------------------------------------------------------

def _non_tty(monkeypatch):
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False, raising=False)


def test_title_sequence_non_tty_instant(monkeypatch):
    _non_tty(monkeypatch)
    console = Console(file=StringIO(), width=100, force_terminal=False)
    started = time.monotonic()
    cin.play_title_sequence(console=console, seed=42)
    elapsed = time.monotonic() - started
    out = console.file.getvalue()
    assert elapsed < 1.5, "non-TTY path must not sleep"
    assert "██" in out                       # masthead present
    assert "OPERATION TUMAN" in out          # tagline typed out
    assert "OK" in out                       # boot ticks complete
    assert "TOP SECRET" in out               # classification strip stamped


def test_scene_stamp_non_tty_instant(monkeypatch):
    _non_tty(monkeypatch)
    console = Console(file=StringIO(), width=100, force_terminal=False)
    started = time.monotonic()
    cin.play_scene_stamp("I", "Severomorsk Naval Base, Russia",
                         "69°04'N 033°25'E", "02 OCT 25", console=console)
    assert time.monotonic() - started < 1.0
    out = console.file.getvalue()
    assert "SCENE I" in out
    assert "SEVEROMORSK NAVAL BASE, RUSSIA" in out
    assert "69°04'N 033°25'E" in out


def test_turn_transition_non_tty_instant(monkeypatch):
    _non_tty(monkeypatch)
    console = Console(file=StringIO(), width=100, force_terminal=False)
    started = time.monotonic()
    cin.play_turn_transition(3, console=console)
    assert time.monotonic() - started < 1.0
    assert "TURN 3" in console.file.getvalue()


def test_debrief_reveal_non_tty_instant(monkeypatch):
    _non_tty(monkeypatch)
    console = Console(file=StringIO(), width=100, force_terminal=False)
    started = time.monotonic()
    cin.play_debrief_reveal("The Line Held", subtitle="VICTORY ── 10 TURNS",
                            lines=["Escalation contained."], seed="end",
                            console=console)
    assert time.monotonic() - started < 1.5
    out = console.file.getvalue()
    assert "THE LINE HELD" in out
    assert "VICTORY" in out
    assert "Escalation contained." in out


# ---------------------------------------------------------------------------
# Skip path: a keypress jumps straight to the final frame
# ---------------------------------------------------------------------------

def test_keypress_skips_to_final(monkeypatch):
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True, raising=False)
    monkeypatch.setattr(cin, "key_pressed", lambda keys=None: True)
    console = Console(file=StringIO(), width=100, force_terminal=True,
                      legacy_windows=False)
    started = time.monotonic()
    cin.play_title_sequence(console=console, seed=7)
    assert time.monotonic() - started < 2.0, "skip must cut the animation"
    out = console.file.getvalue()
    assert "OPERATION TUMAN" in out  # final frame reached


def test_play_title_animation_starts_from_fog(monkeypatch):
    """Regression: building the final frame must not pre-reveal the
    masthead in the animation's own state (eager ``scene.final()`` bug)."""
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True, raising=False)
    monkeypatch.setattr(cin, "key_pressed", lambda keys=None: False)
    ticker = iter(range(1, 10 ** 6))
    monkeypatch.setattr(cin.time, "monotonic", lambda: float(next(ticker)))
    monkeypatch.setattr(cin.time, "sleep", lambda s: None)
    console = Console(file=StringIO(), width=100, force_terminal=True,
                      legacy_windows=False)
    cin.play_title_sequence(console=console, seed=42)
    raw = console.file.getvalue()
    frames = re.split(r"\x1b\[\d+F", raw)
    assert len(frames) > 60, "expected one write per animation frame"
    ansi = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
    assert "█" not in ansi.sub("", frames[0]), \
        "first frame must be pure fog - no masthead blocks yet"
    assert "█" in ansi.sub("", frames[-1])


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def test_title_frames_deterministic():
    a = render_frames(cin.title_frames(seed="alpha"))
    b = render_frames(cin.title_frames(seed="alpha"))
    assert a == b
    c = render_frames(cin.title_frames(seed="bravo"))
    assert a != c


def test_turn_transition_frames_deterministic():
    a = render_frames(cin.turn_transition_frames(4, seed=9))
    b = render_frames(cin.turn_transition_frames(4, seed=9))
    assert a == b


def test_title_final_matches_last_animated_state():
    frames = list(cin.title_frames(seed=11))
    last = render(frames[-1][0])
    final = render(cin.title_final(seed=11))
    assert last == final


# ---------------------------------------------------------------------------
# Choreography content
# ---------------------------------------------------------------------------

def test_title_condense_progression():
    """Early frames are fog; the masthead accretes; the end is complete."""
    frames = render_frames(cin.title_frames(seed=42))
    blocks = [f.count("█") for f in frames]
    assert blocks[0] == 0, "sequence must open on pure fog"
    assert blocks[len(blocks) // 3] > 0, "masthead must be condensing"
    target = render(cin.title_final(seed=42)).count("█")
    assert blocks[-1] == target, "sequence must end on the full masthead"
    # Monotone-ish accretion: no frame loses already-locked cells
    grow = [b for b in blocks if b]
    assert grow == sorted(grow)


def test_title_boot_and_tagline_late_stages():
    frames = render_frames(cin.title_frames(seed=42))
    mid = frames[len(frames) // 2]
    assert "CHANNEL HANDSHAKE" not in mid, "boot log must come after condense"
    assert "CHANNEL HANDSHAKE" in frames[-1]
    assert "OPERATION TUMAN ── A COBRA CRISIS SIMULATION" in frames[-1]


def test_condense_frames_end_on_target():
    target = ae.debrief_frame("Uneasy Peace", subtitle="The fog lifts.",
                              lines=["Line one."], seed=3)
    frames = list(cin.condense_frames(target, seed=3))
    # After the last frame every target glyph is revealed and fog has wiped
    last = render(frames[-1][0])
    for token in ("UNEASY PEACE", "The fog lifts.", "Line one."):
        assert token in last
    assert render(frames[0][0]) != last


def test_turn_transition_sweeps_left_to_right():
    frames = render_frames(cin.turn_transition_frames(2, seed=1))
    assert "TURN 2" not in frames[0], "banner must be hidden at the start"
    assert "TURN 2" in frames[-1]


def test_scene_stamp_chrome_before_text():
    frames = render_frames(cin.scene_stamp_frames(
        "II", "Joint Operations Centre, Northwood",
        "51°38'N 000°28'W", "05 OCT 25"))
    assert "TOP SECRET" in frames[0], "chrome stamps first"
    assert "NORTHWOOD" not in frames[0], "title types in later"
    assert "NORTHWOOD" in frames[-2]


# ---------------------------------------------------------------------------
# Width discipline
# ---------------------------------------------------------------------------

def test_all_frames_within_width():
    sources = {
        "title": cin.title_frames(seed=5),
        "turn": cin.turn_transition_frames(7, seed=5),
        "scene": cin.scene_stamp_frames(1, "Severomorsk", "69N", "03:15"),
        "debrief": cin.condense_frames(
            ae.debrief_frame("End", lines=["x"], seed=5), seed=5,
            pre=2, reveal=4, hold=2),
    }
    for name, frames in sources.items():
        for frame, _d in frames:
            for line in render(frame).splitlines():
                assert cell_len(line.rstrip()) <= WIDTH, (
                    f"{name}: line exceeds {WIDTH}: {line!r}")


def test_title_frames_constant_height():
    heights = {len(render(f).splitlines())
               for f, _d in cin.title_frames(seed=2)}
    assert len(heights) == 1, f"Live region height must not jump: {heights}"


def test_character_discipline_no_emoji():
    for frame, _d in cin.title_frames(seed=8):
        for ch in render(frame):
            assert ord(ch) <= 0x25FF, f"disallowed char {ch!r}"


# ---------------------------------------------------------------------------
# Setup banner
# ---------------------------------------------------------------------------

def test_setup_banner_contents():
    out = render(cin.setup_banner("Select Scenario"))
    assert "FALSE FLAG" in out
    assert "SELECT SCENARIO" in out
    assert "TOP SECRET" in out
    for line in out.splitlines():
        assert cell_len(line.rstrip()) <= WIDTH


def test_setup_banner_renders_under_all_themes():
    from cli.theme import THEMES
    for theme in THEMES:
        theme_manager.set_theme(theme)
        assert render(cin.setup_banner("Select Difficulty"),
                      force_terminal=True).strip()


# ---------------------------------------------------------------------------
# Spinner (API preserved, Tuman styling, silent on non-TTY)
# ---------------------------------------------------------------------------

def test_spinner_frames_character_discipline():
    for frame in sonar_sweep_frames():
        assert all(ord(ch) <= 0x25FF for ch in frame)
        assert "●" in frame  # the ping is always visible


def test_spinner_silent_on_non_tty(monkeypatch, capsys):
    _non_tty(monkeypatch)
    with Spinner("AWAITING SECURE TRAFFIC"):
        time.sleep(0.05)
    captured = capsys.readouterr()
    assert captured.out == ""


def test_spinner_api_shape():
    s = Spinner("Thinking", frames=["[·]", "[●]"])
    assert s.message == "Thinking"
    s.start()
    s.stop()
    with Spinner("x"):
        pass
