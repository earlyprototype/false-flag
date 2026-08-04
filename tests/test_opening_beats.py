"""The opening sequence, and the bundle that has to carry it.

Two regressions live here. The browser build shipped without the cold open
because ``cli/`` holds the terminal front end and the browser does not bundle
it; and it could not have played the cold open anyway, because the asset the
intro reads was not in ``docs/game.zip`` and the reader returned ``[]`` rather
than saying so.
"""

from __future__ import annotations

import importlib.util
import os
import zipfile
from pathlib import Path

import pytest

from engine.intro import get_intro_lines
from engine.opening import (
    Scene,
    get_opening_scenes,
    split_briefing,
    split_intro_sections,
)

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "docs" / "game.zip"


# --------------------------------------------------------------- the beats

def test_the_cold_open_is_four_paced_beats():
    """Severomorsk, Northwood, COBRA, then YOUR ROLE."""
    scenes = get_opening_scenes()
    assert len(scenes) == 4
    assert [s.numeral for s in scenes] == ["I", "II", "III", ""]
    assert all(s.body for s in scenes), "a beat with no text is not a beat"


def test_numbered_scenes_carry_a_card_and_the_role_block_does_not():
    scenes = get_opening_scenes()
    for scene in scenes[:3]:
        assert scene.has_card
        assert scene.location and scene.timestamp, "a card needs place and time"
    assert not scenes[-1].has_card, "YOUR ROLE addresses the player, not a place"


def test_scene_bodies_drop_their_own_headings():
    """The heading is rendered from the card, so it must not repeat in the body."""
    for scene in get_opening_scenes():
        assert not any(ln.strip().startswith("## SCENE") for ln in scene.body)
        assert not any("===" in ln for ln in scene.body)


def test_the_role_block_survives_as_the_last_beat():
    role = get_opening_scenes()[-1]
    text = "\n".join(role.body)
    assert "## YOUR ROLE" in text
    assert "You are the Prime Minister" in text


def test_beats_are_json_safe_for_the_worker_boundary():
    import json

    payload = json.dumps([s.to_dict() for s in get_opening_scenes()])
    assert json.loads(payload)[0]["numeral"] == "I"


def test_a_section_that_is_only_a_rule_is_dropped(monkeypatch):
    """The masthead section carries no text; it must not become a blank beat."""
    import engine.opening as opening

    script = ["# FALSE FLAG", "=" * 20, "", "=" * 20, "real text"]
    monkeypatch.setattr(opening, "get_intro_lines", lambda *a, **k: script)

    scenes = opening.get_opening_scenes()
    assert len(scenes) == 1, f"expected one beat, got {[s.body for s in scenes]}"
    assert "real text" in "\n".join(scenes[0].body)


def test_split_intro_sections_divides_on_the_rules():
    sections = split_intro_sections(["a", "=" * 20, "b", "=" * 20, "c"])
    assert len(sections) == 3
    assert sections[0] == ["a"]


# ----------------------------------------------------------- the briefing

def test_a_briefing_splits_where_the_nsa_takes_over():
    lines = [
        "The room is windowless and tense.",
        "Officials line the walls.",
        "The National Security Advisor clears their throat and begins:",
        '"Prime Minister, in the past 48 hours..."',
    ]
    setting, report = split_briefing(lines)
    assert setting == lines[:2]
    assert report[0].startswith("The National Security Advisor")


def test_turn_one_of_a_new_campaign_is_not_split():
    """It runs straight on from YOUR ROLE as one continuous opening."""
    lines = [
        "The room is windowless and tense.",
        "The National Security Advisor clears their throat and begins:",
    ]
    setting, report = split_briefing(lines, flows_from_intro=True)
    assert setting == lines
    assert report == []


def test_a_briefing_with_no_handover_is_left_whole():
    lines = ["Nothing new has come in overnight.", "The room waits."]
    setting, report = split_briefing(lines)
    assert setting == lines
    assert report == []


def test_a_briefing_opening_on_the_handover_is_left_whole():
    """Splitting at index 0 would emit an empty first beat."""
    lines = ["The National Security Advisor begins:", "Bad news."]
    setting, report = split_briefing(lines)
    assert setting == lines
    assert report == []


# ------------------------------------------------- the asset, and the bundle

def test_a_missing_intro_asset_raises_rather_than_reading_as_empty(monkeypatch,
                                                                  tmp_path):
    """Returning [] made a packaging mistake look like an editorial choice."""
    import engine.intro as intro

    monkeypatch.setattr(intro, "INTRO_ASSET", Path("nowhere") / "missing.md")
    with pytest.raises(FileNotFoundError) as excinfo:
        intro.get_intro_lines()
    assert "missing.md" in str(excinfo.value)


def test_the_intro_asset_is_in_the_browser_bundle():
    """engine/intro.py reads this at runtime, so the browser needs it too."""
    assert BUNDLE.exists(), "run dev-scripts/build_play_bundle.py"
    names = zipfile.ZipFile(BUNDLE).namelist()
    assert "assets/placeholders/intro_stage.md" in names
    assert "engine/opening.py" in names


def test_the_bundle_matches_the_repo():
    """A stale bundle means the browser runs older code than the repo shows.

    The build stamps fixed timestamps precisely so this comparison is
    meaningful; a mismatch here means someone changed bundled code without
    running dev-scripts/build_play_bundle.py.
    """
    spec = importlib.util.spec_from_file_location(
        "build_play_bundle", ROOT / "dev-scripts" / "build_play_bundle.py")
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)

    expected = {}
    for top in build.INCLUDE_DIRS:
        base = ROOT / top
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in build.SKIP_DIRS]
            for name in filenames:
                if name.endswith(build.SKIP_SUFFIXES):
                    continue
                full = Path(dirpath) / name
                expected[str(full.relative_to(ROOT))] = full.read_bytes()
    for src, arc in build.EXTRA_FILES.items():
        expected[arc] = Path(src).read_bytes()

    with zipfile.ZipFile(BUNDLE) as z:
        packed = {n: z.read(n) for n in z.namelist()}

    missing = sorted(set(expected) - set(packed))
    extra = sorted(set(packed) - set(expected))
    stale = sorted(n for n in set(expected) & set(packed)
                   if expected[n] != packed[n])
    assert not (missing or extra or stale), (
        f"docs/game.zip is out of date — rebuild it with "
        f"dev-scripts/build_play_bundle.py.\n"
        f"  missing from bundle: {missing}\n"
        f"  no longer in repo:   {extra}\n"
        f"  stale contents:      {stale}"
    )
