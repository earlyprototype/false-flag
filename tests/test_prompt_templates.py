"""Tests for the prompt hot-edit loader (llm/prompt_templates) and the
byte-parity of the extracted templates.

The parity gate: tests/data/prompt_parity_golden.json was captured by
running tests/prompt_parity_fixtures.build_all_prompts() against the
PRE-refactor inline f-string builders. With unedited templates, the
refactored builders must reproduce those prompts byte for byte.
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


@pytest.fixture(autouse=True)
def restore_templates():
    """Tests may edit template files; leave the defaults behind."""
    yield
    for family in pt.FAMILIES:
        pt.reset_template(family)


# --- byte parity ----------------------------------------------------------

def test_assembled_prompts_match_pre_refactor_golden():
    """With unedited templates the three refactored builders reproduce the
    pre-refactor prompts exactly - the extraction changed nothing."""
    from tests.prompt_parity_fixtures import build_all_prompts

    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    live = build_all_prompts()
    assert set(live) == set(golden)
    for family, expected in golden.items():
        assert live[family] == expected, (
            f"{family}: assembled prompt diverged from the pre-refactor bytes"
        )


def test_template_files_match_embedded_defaults():
    """The shipped data/prompts/*.txt files ARE the defaults; if one drifts
    from the embedded canonical text, reset/fallback would silently change
    live prompts."""
    for family in pt.FAMILIES:
        path = pt.template_path(family)
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
    out = pt.render(family, action="A", interpretation="B", advisors_str="C")
    assert out == pt.DEFAULTS[family].format(
        action="A", interpretation="B", advisors_str="C")
