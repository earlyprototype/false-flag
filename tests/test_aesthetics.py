"""Tests for the Operation Tuman aesthetic engine (cli/aesthetics.py)."""

import re
from io import StringIO

import pytest
from rich.cells import cell_len
from rich.console import Console

from cli import aesthetics as ae
from cli.theme import THEMES, theme_manager

WIDTH = ae.DEFAULT_WIDTH  # 78


@pytest.fixture(autouse=True)
def restore_theme():
    original = theme_manager.current_theme_name
    yield
    theme_manager.set_theme(original)


def render(renderable, width: int = 100, force_terminal: bool = False) -> str:
    """Render to plain text (no ANSI) at a given console width."""
    console = Console(file=StringIO(), width=width,
                      force_terminal=force_terminal, legacy_windows=False)
    console.print(renderable)
    return console.file.getvalue()


def all_components(seed="test"):
    """One instance of every public component."""
    return {
        "fog_band": ae.fog_band(seed=seed),
        "classification_top": ae.classification_strip(seed=seed, edge="top"),
        "classification_bottom": ae.classification_strip(seed=seed, edge="bottom"),
        "classification_bare": ae.classification_strip(seed=seed, edge="bare"),
        "sonar": ae.sonar_divider(seed=seed),
        "masthead": ae.masthead(seed=seed),
        "scene_card": ae.scene_card(
            1, "Severomorsk Naval Base, Russia",
            location="69°04'N 033°25'E",
            timestamp="02 OCT 25 │ 03:15 LOCAL", seed=seed),
        "turn_banner": ae.turn_banner(3, seed=seed),
        "phase_banner": ae.phase_banner("DISCUSSION", 3, seed=seed),
        "boot_screen": ae.boot_screen(seed=seed),
        "debrief": ae.debrief_frame(
            "Uneasy Peace", subtitle="The fog lifts.",
            lines=["Escalation contained.", "NATO cohesion held."],
            seed=seed),
    }


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def test_same_seed_identical_output():
    first = {k: render(v) for k, v in all_components(seed="alpha").items()}
    second = {k: render(v) for k, v in all_components(seed="alpha").items()}
    assert first == second


def test_different_seeds_differ():
    a = render(ae.fog_band(seed=1))
    b = render(ae.fog_band(seed=2))
    assert a != b
    assert render(ae.sonar_divider(seed="x")) != render(ae.sonar_divider(seed="y"))


def test_seed_accepts_int_str_none():
    for seed in (0, 7, "operation-tuman", None):
        assert render(ae.fog_band(seed=seed))  # no crash, non-empty


def test_turn_trims_do_not_collide_between_turns():
    # Regression: CRC32 XOR seeding made turn N's bottom trim equal
    # turn N+1's top trim.
    t1 = render(ae.turn_banner(1)).splitlines()
    t2 = render(ae.turn_banner(2)).splitlines()
    assert t1[-1] != t2[0]


def test_reference_code_deterministic():
    assert ae.reference_code("scene-1") == ae.reference_code("scene-1")
    assert re.fullmatch(r"COBRA/TU/\d{2}", ae.reference_code("scene-1"))


# ---------------------------------------------------------------------------
# Width and alignment
# ---------------------------------------------------------------------------

def test_all_lines_within_width():
    for name, comp in all_components().items():
        for line in render(comp).splitlines():
            assert cell_len(line.rstrip()) <= WIDTH, (
                f"{name}: line exceeds {WIDTH}: {line!r}")


def test_framed_lines_exact_width():
    """Box/rule lines must be exactly DEFAULT_WIDTH so frames align."""
    checks = {
        "classification_top": ae.classification_strip(seed=1, edge="top"),
        "classification_bottom": ae.classification_strip(seed=1, edge="bottom"),
        "scene_card": ae.scene_card(2, "Northwood JOC", "51N", "16:45", seed=1),
        "turn_banner": ae.turn_banner(5),
        "phase_banner": ae.phase_banner("DECISION", 5),
        "debrief": ae.debrief_frame("Ending", subtitle="v", lines=["x"], seed=1),
    }
    for name, comp in checks.items():
        for line in render(comp).splitlines():
            stripped = line.rstrip()
            # Fog rows may end in spaces; structural lines must be full width
            if stripped and stripped[0] in "┌└│╔╚║━─":
                assert cell_len(line.rstrip("\n").rstrip()) == WIDTH or \
                    cell_len(line[:WIDTH]) == WIDTH, (
                        f"{name}: misaligned line {line!r} "
                        f"({cell_len(stripped)} != {WIDTH})")


def test_masthead_rows_equal_width():
    rows = ae._MASTHEAD_ROWS
    assert len(rows) == 5
    widths = {len(r) for r in rows}
    assert len(widths) == 1, f"masthead rows unequal: {[len(r) for r in rows]}"
    assert len(rows[0]) <= WIDTH


def test_custom_width_respected():
    for w in (60, 70, 78):
        out = render(ae.fog_band(width=w, seed=3))
        assert all(cell_len(l.rstrip()) <= w for l in out.splitlines())
        strip = render(ae.classification_strip(seed=3, width=w)).splitlines()[0]
        assert cell_len(strip.rstrip()) == w


# ---------------------------------------------------------------------------
# Character discipline (no emoji)
# ---------------------------------------------------------------------------

def test_no_emoji_or_wide_chars():
    # Everything must live below U+2600 (box drawing, blocks, geometric
    # shapes are all <= U+25FF); emoji live far above.
    for name, comp in all_components().items():
        for ch in render(comp):
            assert ord(ch) <= 0x25FF, (
                f"{name}: disallowed char {ch!r} (U+{ord(ch):04X})")
        # Everything is cell-width 1, so alignment is safe
        for line in render(comp).splitlines():
            assert cell_len(line) == len(line)


# ---------------------------------------------------------------------------
# Themes
# ---------------------------------------------------------------------------

def test_all_themes_render():
    for theme in THEMES:
        assert theme_manager.set_theme(theme)
        for name, comp in all_components(seed=theme).items():
            out = render(comp, force_terminal=True)
            assert out.strip(), f"{name} empty under theme {theme}"


def test_theme_read_at_render_time():
    """Colors must come from the active theme, not be cached at import."""
    theme_manager.set_theme("retro")
    retro = render(ae.turn_banner(1), force_terminal=True)
    theme_manager.set_theme("defcon")
    defcon = render(ae.turn_banner(1), force_terminal=True)
    assert retro != defcon  # ANSI differs between themes
    # Plain glyphs identical: only the colors changed
    ansi = re.compile(r"\x1b\[[0-9;]*m")
    assert ansi.sub("", retro) == ansi.sub("", defcon)


# ---------------------------------------------------------------------------
# Non-TTY / narrow console safety
# ---------------------------------------------------------------------------

def test_narrow_console_clips_not_crashes():
    for w in (79, 60, 40, 20):
        for name, comp in all_components().items():
            out = render(comp, width=w)
            for line in out.splitlines():
                assert cell_len(line) <= w, f"{name} overflows at width {w}"


def test_animate_boot_non_tty(monkeypatch):
    import sys as _sys
    monkeypatch.setattr(_sys.stdout, "isatty", lambda: False, raising=False)
    console = Console(file=StringIO(), width=100, force_terminal=False)
    ae.animate_boot(console=console, seed="boot")  # must not sleep or crash
    out = console.file.getvalue()
    assert "TUMAN" in out
    assert "██" in out  # masthead present in static render


# ---------------------------------------------------------------------------
# Boot sequence
# ---------------------------------------------------------------------------

def test_boot_frames_progressive():
    frames = ae.boot_sequence_frames(seed="boot")
    assert len(frames) >= 4
    rendered = [render(f) for f in frames]
    # Later frames reveal more lines
    assert rendered[0].count(">") < rendered[-2].count(">")
    # Final frame carries the masthead
    assert "██" in rendered[-1]
    # Static screen equals final frame
    assert render(ae.boot_screen(seed="boot")) == rendered[-1]


# ---------------------------------------------------------------------------
# Content details
# ---------------------------------------------------------------------------

def test_scene_card_contents():
    out = render(ae.scene_card(3, "Cabinet Office Briefing Room A",
                               location="51°30'N", timestamp="17:00"))
    assert "SCENE III" in out
    assert "CABINET OFFICE BRIEFING ROOM A" in out
    assert "51°30'N" in out and "17:00" in out
    assert "TOP SECRET" in out


def test_phase_banner_labels():
    for phase in ("BRIEFING", "DISCUSSION", "DECISION", "ADJUDICATION"):
        out = render(ae.phase_banner(phase, turn=2))
        assert phase in out and "TURN 2" in out


def test_debrief_frame_contents():
    out = render(ae.debrief_frame("Nuclear Dawn", subtitle="The fog wins.",
                                  lines=["Line one."], seed=9))
    assert "NUCLEAR DAWN" in out
    assert "The fog wins." in out
    assert "Line one." in out
    assert "╔" in out and "╝" in out


def test_fog_density_scales():
    thin = render(ae.fog_band(density=0.1, seed=5))
    thick = render(ae.fog_band(density=1.0, seed=5))
    def ink(s):
        return sum(1 for c in s if c not in " \n")
    assert ink(thin) < ink(thick)
    # Zero density is (near-)clear air
    assert ink(render(ae.fog_band(density=0.0, seed=5))) <= 6
