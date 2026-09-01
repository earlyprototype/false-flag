"""Tests for the prompt hot-edit loader (llm/prompt_templates) and the
byte-parity of the extracted templates.

The parity gate: tests/data/prompt_parity_golden.json holds the intended
bytes of the three hot-editable families, first captured against the
PRE-refactor inline f-string builders and deliberately re-captured for
issue #91's presentation fixes and issue #87's per-advisor pushback prompt.
With unedited templates, the builders must reproduce those prompts byte for
byte.
"""

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from llm import prompt_templates as pt

GOLDEN_PATH = Path(__file__).parent / "data" / "prompt_parity_golden.json"

# The directory of COMMITTED template files. The parity gate below reads it
# directly instead of going through pt.template_path, which tests/conftest.py
# redirects to a throwaway directory for every test.
REPO_PROMPT_DIR = Path(__file__).resolve().parent.parent / "data" / "prompts"


@pytest.fixture(autouse=True)
def seeded_templates():
    """Seed the isolated template directory with the canonical defaults.

    The loader tests exercise files on disk (direct edits, unlink, CRLF
    rewrites), so the per-test directory (tests/conftest.py) starts out
    looking like an unedited checkout. Writes land there, never on the
    committed data/prompts/ files - which is what let a drifted committed
    file pass the parity gate for as long as teardowns wrote it back.
    """
    for family in pt.FAMILIES:
        pt.reset_template(family)


# --- byte parity ----------------------------------------------------------

def test_assembled_prompts_match_golden():
    """With unedited templates the three hot-editable families assemble to
    exactly the golden bytes.

    The golden was captured against the pre-refactor inline builders and
    deliberately re-captured for issues #91 and #87 (see
    tests/prompt_parity_fixtures). Anything else that moves these bytes -
    a stray edit to DEFAULTS, a changed shared prefix - fails here.
    """
    from tests.prompt_parity_fixtures import GOLDEN_FAMILIES, build_all_prompts

    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    live = build_all_prompts()
    assert set(golden) == set(GOLDEN_FAMILIES)
    assert set(golden) <= set(live)
    for family, expected in golden.items():
        assert live[family] == expected, (
            f"{family}: assembled prompt diverged from the golden bytes"
        )


def test_template_files_match_embedded_defaults():
    """The COMMITTED data/prompts/*.txt files ARE the defaults; if one
    drifts from the embedded canonical text, reset/fallback would silently
    change live prompts.

    Reads the repo directory directly - never the loader's path, which the
    suite isolates to a tmp dir - so no other test's template writes can
    heal a drifted commit before this gate sees it. (Exactly that masking
    let a placeholder advisor_pushback.txt ship: every earlier teardown
    rewrote the real file from DEFAULTS.)"""
    for family in pt.FAMILIES:
        path = REPO_PROMPT_DIR / f"{family}.txt"
        assert path.exists(), f"missing template file: {path}"
        on_disk = pt._normalise(path.read_text(encoding="utf-8"))
        assert on_disk == pt.DEFAULTS[family], f"{family}.txt drifted from DEFAULTS"


def test_significant_trailing_spaces_survive():
    """Two decision_interpretation lines end with a significant trailing
    space in the pre-refactor bytes; normalisation must keep them."""
    text = pt.get_template("decision_interpretation")
    assert "not as a question to advisors. \n" in text
    assert "treat this as the PM \n" in text


# --- loader behaviour -----------------------------------------------------

def test_edit_is_picked_up_without_restart():
    """mtime-based reload: writing new text is served on the next call."""
    family = "advisor_pushback"
    original = pt.get_template(family)
    edited = original + "\n\nAlways answer in exactly one sentence."

    pt.set_template(family, edited)
    assert pt.get_template(family) == edited
    assert pt.is_edited(family) is True

    pt.reset_template(family)
    assert pt.get_template(family) == pt.DEFAULTS[family]
    assert pt.is_edited(family) is False


def test_direct_file_edit_is_picked_up():
    """An edit that bypasses set_template (a text editor on the file) is
    still served: the cache keys on mtime+size."""
    family = "advisor_qa"
    pt.get_template(family)  # prime the cache
    path = pt.template_path(family)
    edited = pt.DEFAULTS[family] + "\nSpeak plainly."
    path.write_text(edited, encoding="utf-8", newline="\n")
    # Some filesystems have coarse mtime resolution; size changed too, and
    # the cache keys on both.
    assert pt.get_template(family) == edited


def test_missing_file_serves_default():
    family = "advisor_qa"
    path = pt.template_path(family)
    path.unlink()
    try:
        assert pt.get_template(family) == pt.DEFAULTS[family]
        assert pt.is_edited(family) is False
    finally:
        pt.reset_template(family)


def test_crlf_and_trailing_newline_are_normalised():
    family = "advisor_pushback"
    crlf_text = pt.DEFAULTS[family].replace("\n", "\r\n") + "\r\n"
    pt.template_path(family).write_bytes(crlf_text.encode("utf-8"))
    assert pt.get_template(family) == pt.DEFAULTS[family]


# --- validation and fallback ----------------------------------------------

def test_unknown_placeholder_is_rejected():
    with pytest.raises(ValueError, match="Unknown placeholder"):
        pt.set_template("advisor_qa", "Hello {no_such_field}")


def test_positional_placeholder_is_rejected():
    with pytest.raises(ValueError, match="Positional"):
        pt.set_template("advisor_qa", "Hello {}")


def test_malformed_braces_are_rejected():
    with pytest.raises(ValueError):
        pt.set_template("advisor_qa", "Broken {role")


def test_unknown_family_raises_keyerror():
    with pytest.raises(KeyError):
        pt.get_template("no_such_family")
    with pytest.raises(KeyError):
        pt.set_template("no_such_family", "text")


def test_render_falls_back_to_default_on_broken_file():
    """A bad template written straight to disk (bypassing validation) must
    not crash prompt assembly - render serves the default instead."""
    family = "advisor_pushback"
    pt.template_path(family).write_text("Broken {nonsense_field}",
                                        encoding="utf-8", newline="\n")
    values = {
        "action": "A",
        "interpretation": "B",
        "role": "C",
        "key_concerns": "D",
        "pushback_triggers": "E",
    }
    out = pt.render(family, **values)
    assert out == pt.DEFAULTS[family].format(
        **values)
