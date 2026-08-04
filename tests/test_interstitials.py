"""Tests for the between-turn interstitial vignettes (cli/interstitials.py).

Covers the contracts the vignettes must keep:
- frame content is deterministic per (seed, escalation);
- every frame respects the 78-column width and the no-emoji glyph set;
- non-TTY stdout prints exactly one characteristic still, instantly;
- seeded selection never repeats the previous vignette;
- the escalation parameter changes the tea-round frames (rattle amplitude,
  and the >80 "trolley does not stop" punchline);
- total choreographed run time stays within the 3-6s envelope.
"""

import re
import sys
import time
from io import StringIO

import pytest
from rich.cells import cell_len
from rich.console import Console

from cli import cinematics as cin
from cli import interstitials as itl
from cli.theme import theme_manager

WIDTH = 78


@pytest.fixture(autouse=True)
def restore_theme():
    original = theme_manager.current_theme_name
    yield
    theme_manager.set_theme(original)


def render(renderable, width: int = 100) -> str:
    console = Console(file=StringIO(), width=width, force_terminal=False,
                      legacy_windows=False)
    console.print(renderable)
    return console.file.getvalue()


def render_frames(frames):
    return [render(frame) for frame, _duration in frames]


def _non_tty(monkeypatch):
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False, raising=False)


# ---------------------------------------------------------------------------
# Registry and API shape
# ---------------------------------------------------------------------------

def test_five_launch_vignettes():
    assert set(itl.VIGNETTE_NAMES) == {
        "tea_round", "periscope", "teleprinter", "red_phone", "radar_room"}


def test_unknown_name_raises():
    with pytest.raises(KeyError):
        itl.build_interstitial("interpretive_dance")


def test_total_duration_within_envelope():
    for name in itl.VIGNETTE_NAMES:
        for esc in (0, 45, 95):
            frames, _final = itl.build_interstitial(name, seed=3,
                                                    escalation=esc)
            total = sum(d for _f, d in frames)
            assert 3.0 <= total <= 6.0, f"{name} esc={esc}: {total:.2f}s"
            assert all(d > 0 for _f, d in frames)


def test_final_still_matches_last_frame():
    """The characteristic still IS the animation's resting state, so the
    skip path and the non-TTY path land on the same picture."""
    for name in itl.VIGNETTE_NAMES:
        frames, final = itl.build_interstitial(name, seed=9, escalation=30)
        assert render(frames[-1][0]) == render(final), name


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def test_frames_deterministic_per_seed():
    for name in itl.VIGNETTE_NAMES:
        a, fa = itl.build_interstitial(name, seed="alpha", escalation=60)
        b, fb = itl.build_interstitial(name, seed="alpha", escalation=60)
        assert render_frames(a) == render_frames(b), name
        assert [d for _f, d in a] == [d for _f, d in b], name
        assert render(fa) == render(fb), name


def test_seed_changes_content():
    """A different seed produces different frames (layout, redaction,
    contact geometry...) for the seed-sensitive vignettes."""
    for name in ("periscope", "teleprinter", "radar_room"):
        a, _ = itl.build_interstitial(name, seed="alpha")
        b, _ = itl.build_interstitial(name, seed="bravo")
        assert render_frames(a) != render_frames(b), name


# ---------------------------------------------------------------------------
# Escalation drives the tea round
# ---------------------------------------------------------------------------

def test_escalation_changes_tea_round_frames():
    calm, _ = itl.build_interstitial("tea_round", seed=5, escalation=0)
    tense, _ = itl.build_interstitial("tea_round", seed=5, escalation=70)
    assert render_frames(calm) != render_frames(tense)


def test_tea_round_rattle_amplitude_scales():
    assert itl._tea_rattle_amp(0) == 0
    assert itl._tea_rattle_amp(30) == 1
    assert itl._tea_rattle_amp(70) == 2
    assert itl._tea_rattle_amp(95) == 3
    amps = [itl._tea_rattle_amp(e) for e in range(0, 101, 5)]
    assert amps == sorted(amps), "amplitude must be monotone in escalation"


def test_tea_round_punchlines_by_escalation():
    """At sane escalation the PM gets a cup; above 80 the aide keeps
    walking and the trolley does not stop."""
    _frames, calm_final = itl.build_interstitial("tea_round", seed=5,
                                                 escalation=40)
    calm = render(calm_final)
    assert "YOURS, PRIME MINISTER." in calm
    assert "DID NOT STOP" not in calm

    frames, hot_final = itl.build_interstitial("tea_round", seed=5,
                                               escalation=90)
    hot = render(hot_final)
    assert "THE TROLLEY DID NOT STOP." in hot
    assert "PM" not in hot.replace("PRIME", "")  # no cup left behind
    # ...and mid-crossing the trolley is still very much on stage
    mid = render(frames[len(frames) // 2][0])
    assert "T E A" in mid


def test_tea_round_trolley_crosses():
    frames, _ = itl.build_interstitial("tea_round", seed=5, escalation=20)
    rendered = render_frames(frames)
    assert "T E A" not in rendered[0], "trolley must start off stage"
    assert any("T E A" in f for f in rendered)
    assert "T E A" not in rendered[-1], "trolley must exit"
    for label in ("CDS", "NSA", "FS", "HS", "AG"):
        assert any(label in f for f in rendered), f"cup {label} missing"


# ---------------------------------------------------------------------------
# Vignette-specific choreography beats
# ---------------------------------------------------------------------------

def test_periscope_looks_at_viewer_then_dives():
    frames, final = itl.build_interstitial("periscope", seed=11)
    rendered = render_frames(frames)
    assert any("(●)" in f for f in rendered), "lens must face the viewer"
    stare = max(i for i, f in enumerate(rendered) if "(●)" in f)
    after = rendered[stare + 1:]
    assert any("(" in f and "●" not in f for f in after), \
        "ripples must follow the dive"
    assert "SIGHTING REPORTED" in render(final)


def test_teleprinter_redaction_progresses_to_blackout():
    _frames, final = itl.build_interstitial("teleprinter", seed=2)
    last = render(final)
    assert "P M   E Y E S   O N L Y" in last
    assert "( )" in last, "the tea ring must stain the memo"
    body = [ln for ln in last.splitlines() if ln.strip().startswith("5.")]
    assert body and set(body[0].split("5.")[1].replace("( )", "").split()) \
        <= {"█" * n for n in range(1, 70)}, "final paragraph must be black"
    # Redaction gets heavier down the page
    counts = [ln.count("█") for ln in last.splitlines()
              if ln.strip()[:2] in ("1.", "2.", "3.", "4.", "5.")]
    assert counts == sorted(counts) and counts[-1] > counts[0]


def test_red_phone_stops_blinking_when_answered():
    frames, final = itl.build_interstitial("red_phone", seed=4)
    rendered = render_frames(frames)
    assert any("((" in f for f in rendered), "phone must ring"
    answered = min(i for i, f in enumerate(rendered) if "○" in f)
    for f in rendered[answered:]:
        assert "((" not in f, "no ring past the answer frame"
        assert "-.-" in f, "the cat stays"
    assert "LINE OPEN. CAT UNMOVED." in render(final)


def test_red_phone_cat_relocates_two_columns():
    frames, _ = itl.build_interstitial("red_phone", seed=4)
    rendered = render_frames(frames)
    cols = []
    for f in rendered:
        for line in f.splitlines():
            if "( -.- )" in line:
                cols.append(line.index("( -.- )"))
                break
    assert len(set(cols)) == 2, "cat must occupy exactly two positions"
    assert max(cols) - min(cols) == 2, "the concession is two columns"


def test_radar_room_gull_resolves_and_exits_left():
    frames, final = itl.build_interstitial("radar_room", seed=6)
    rendered = render_frames(frames)
    gull_frames = [(i, f) for i, f in enumerate(rendered)
                   if "~v~" in f or "_w_" in f]
    assert gull_frames, "the contact must resolve to a gull"
    cols = []
    for _i, f in gull_frames:
        for line in f.splitlines():
            for token in ("~v~", "_w_"):
                if token in line:
                    cols.append(line.index(token))
    assert cols == sorted(cols, reverse=True), "gull must head screen-left"
    last = render(final)
    assert "CONTACT RECLASSIFIED: GULL (FORMAL COMPLAINT LODGED)" in last
    assert "~v~" not in last and "_w_" not in last, "the gull has left"


# ---------------------------------------------------------------------------
# Width and glyph discipline
# ---------------------------------------------------------------------------

def test_all_frames_within_width():
    for name in itl.VIGNETTE_NAMES:
        for esc in (0, 85):
            frames, final = itl.build_interstitial(name, seed=8,
                                                   escalation=esc)
            for renderable in [f for f, _d in frames] + [final]:
                for line in render(renderable).splitlines():
                    assert cell_len(line.rstrip()) <= WIDTH, (
                        f"{name}: line exceeds {WIDTH}: {line!r}")


def test_character_discipline_no_emoji():
    for name in itl.VIGNETTE_NAMES:
        frames, final = itl.build_interstitial(name, seed=8, escalation=60)
        for renderable in [f for f, _d in frames] + [final]:
            for ch in render(renderable):
                assert ch == "\n" or ord(ch) <= 0x25FF, \
                    f"{name}: disallowed char {ch!r}"


def test_constant_height_per_vignette():
    """Each vignette's redraw region must not change height mid-play."""
    for name in itl.VIGNETTE_NAMES:
        heights = {len(render(f).splitlines())
                   for f, _d in itl.build_interstitial(name, seed=8)[0]}
        assert len(heights) == 1, f"{name}: heights vary: {heights}"


def test_renders_under_all_themes():
    from cli.theme import THEMES
    for theme in THEMES:
        theme_manager.set_theme(theme)
        for name in itl.VIGNETTE_NAMES:
            _frames, final = itl.build_interstitial(name, seed=1,
                                                    escalation=50)
            assert render(final).strip(), f"{name} blank under {theme}"


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------

def test_selection_deterministic_and_never_repeats():
    for seed in range(40):
        for avoid in itl.VIGNETTE_NAMES:
            pick = itl.choose_interstitial(seed, avoid=avoid)
            assert pick in itl.VIGNETTE_NAMES
            assert pick != avoid
        assert itl.choose_interstitial(seed) == itl.choose_interstitial(seed)


def test_selection_covers_all_vignettes():
    picks = {itl.choose_interstitial(seed) for seed in range(60)}
    assert picks == set(itl.VIGNETTE_NAMES)


def test_avoid_with_bogus_name_still_selects():
    assert itl.choose_interstitial(1, avoid="not_a_vignette") \
        in itl.VIGNETTE_NAMES


# ---------------------------------------------------------------------------
# Player integration: non-TTY still, skip path, return value
# ---------------------------------------------------------------------------

def test_non_tty_prints_single_still_instantly(monkeypatch):
    _non_tty(monkeypatch)
    for name in itl.VIGNETTE_NAMES:
        console = Console(file=StringIO(), width=100, force_terminal=False,
                          legacy_windows=False)
        started = time.monotonic()
        played = itl.play_interstitial(console=console, seed=13,
                                       escalation=50, name=name)
        assert time.monotonic() - started < 1.0, f"{name}: non-TTY slept"
        assert played == name
        out = console.file.getvalue()
        _frames, final = itl.build_interstitial(name, seed=13, escalation=50)
        expected = render(final)
        assert out == expected, f"{name}: non-TTY must print the still only"


def test_non_tty_still_is_characteristic(monkeypatch):
    _non_tty(monkeypatch)
    tokens = {
        "tea_round": "YOURS, PRIME MINISTER.",
        "periscope": "SIGHTING REPORTED",
        "teleprinter": "P M   E Y E S   O N L Y",
        "red_phone": "LINE OPEN. CAT UNMOVED.",
        "radar_room": "FORMAL COMPLAINT LODGED",
    }
    for name, token in tokens.items():
        console = Console(file=StringIO(), width=100, force_terminal=False,
                          legacy_windows=False)
        itl.play_interstitial(console=console, seed=13, escalation=50,
                              name=name)
        assert token in console.file.getvalue(), name


def test_keypress_skips_to_final(monkeypatch):
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True, raising=False)
    monkeypatch.setattr(cin, "key_pressed", lambda keys=None: True)
    console = Console(file=StringIO(), width=100, force_terminal=True,
                      legacy_windows=False)
    started = time.monotonic()
    itl.play_interstitial(console=console, seed=13, name="red_phone")
    assert time.monotonic() - started < 2.0, "skip must cut the vignette"
    plain = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", console.file.getvalue())
    assert "LINE OPEN. CAT UNMOVED." in plain


def test_play_uses_seeded_selection_and_avoid(monkeypatch):
    _non_tty(monkeypatch)
    for seed in range(8):
        expected = itl.choose_interstitial(seed, avoid="tea_round")
        console = Console(file=StringIO(), width=100, force_terminal=False,
                          legacy_windows=False)
        assert itl.play_interstitial(console=console, seed=seed,
                                     avoid="tea_round") == expected
