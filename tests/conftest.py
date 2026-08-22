"""Suite-wide fixtures.

Prompt-template isolation: llm/prompt_templates persists edits to its
template directory, and several tests (loader tests, the dashboard's
PUT/DELETE /prompts tests, autouse reset teardowns) write templates.
Without isolation those writes land on the REAL committed
data/prompts/*.txt files - so any earlier test's teardown could silently
heal a drifted committed file before the parity gate
(tests/test_prompt_templates.py::test_template_files_match_embedded_defaults)
ever read it. Every test therefore runs against a throwaway template
directory via the loader's WARGAME_PROMPT_DIR override; the parity gate
deliberately bypasses the loader path and reads the committed files
directly.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


@pytest.fixture(autouse=True)
def isolated_prompt_dir(tmp_path, monkeypatch):
    """Point the prompt-template loader at a per-test throwaway directory.

    The directory starts empty (the loader serves its embedded defaults for
    missing files, same text as an unedited checkout); tests that need the
    files on disk seed them here via reset_template.
    """
    prompt_dir = tmp_path / "prompts"
    monkeypatch.setenv("WARGAME_PROMPT_DIR", str(prompt_dir))
    yield prompt_dir
