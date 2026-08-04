#!/usr/bin/env python3
"""Generate the canned ANSI that ``docs/play/`` needs, from the game itself.

The playable page (``docs/play/index.html``) renders raw ANSI in the browser.
Two things it shows are not produced by the engine at run time and so have to
be baked in:

* ``docs/play/assets.js`` - the boot screen. Classification strip, thinning
  fog bands and the FALSE FLAG masthead, rendered by ``cli.aesthetics`` at 78
  columns and frozen as ANSI strings. The page replays them against the
  worker's ``booting`` progress messages, so the wait for Pyodide looks like
  the game's own secure-terminal boot rather than a spinner.

* ``docs/play/stub-data.js`` - a recorded campaign for ``stub-worker.js``,
  the offline stand-in for the real engine worker. Captured from a live
  ``wargame_cli.py play`` run against the mock LLM driver at ``COLUMNS=78``,
  then sliced into the beats the contract sends as ``output`` messages.

Neither file is edited by hand. Regenerate with::

    .venv/bin/python dev-scripts/build_play_assets.py

The capture is re-recorded on every run (mock driver, fixed seed, no network),
so the output is deterministic and needs no transcript archive.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import io  # noqa: E402

from rich.console import Console  # noqa: E402

from cli.aesthetics import (  # noqa: E402
    classification_strip, debrief_frame, fog_band, masthead,
)

OUT = REPO / "docs" / "play"
WIDTH = 78
SGR = re.compile(r"\x1b\[[0-9;]*m")
CURSOR = re.compile(r"\x1b\[[0-9;]*[ABCDEFGJKST]")


def render(renderable) -> str:
    """Render a Rich renderable to raw ANSI at the game's own width."""
    buf = io.StringIO()
    console = Console(file=buf, width=WIDTH, force_terminal=True,
                      color_system="truecolor", highlight=False,
                      soft_wrap=False, legacy_windows=False)
    console.print(renderable)
    return buf.getvalue().rstrip("\n")


# ---------------------------------------------------------------------------
# Boot screen
# ---------------------------------------------------------------------------

def build_assets() -> str:
    """Fog that thins as the boot progresses, plus the masthead it clears to."""
    fogs = [render(fog_band(WIDTH, 3, d, seed=f"play-boot-{i}"))
            for i, d in enumerate((0.78, 0.66, 0.54, 0.42, 0.30, 0.18))]
    payload = {
        "strip": render(classification_strip(
            code="COBRA/TU/00", label="TOP SECRET ── UK EYES ONLY",
            width=WIDTH, seed="play", edge="bare")),
        "fog": fogs,
        "masthead": render(masthead(WIDTH, seed="play-site")),
        "debrief": render(debrief_frame(
            "THE FOG HOLDS",
            subtitle="VERDICT: MIXED ── the crisis did not break, and it did not end",
            lines=[
                "You kept the alliance in one room and the deterrent in its tubes.",
                "Moscow learned what Britain will do at sea and what it will not.",
                "No one has yet found out who was really wearing whose face.",
                "",
                "This was the offline demonstration. Nothing above was reasoned",
                "about your words - it is a recording. Add an OpenRouter key and",
                "the advisors read what you actually wrote.",
            ],
            seed="play-debrief", width=WIDTH)),
    }
    return payload


# ---------------------------------------------------------------------------
# Recorded campaign for the stub worker
# ---------------------------------------------------------------------------

DECISION = ("Order HMS Prince of Wales north of Orkney, keep her outside "
            "twelve miles, and put two Typhoons on airborne alert. Brief the "
            "Norwegians before anyone briefs the press.")
QUESTION = "What is the Chief of the Defence Staff's read on the submarine posture?"


def capture() -> List[str]:
    """Play one scripted campaign against the mock driver and keep the ANSI."""
    feed = ([""] * 4 + [QUESTION, "/decide", DECISION] + [""] * 24)
    env = dict(os.environ, COLUMNS=str(WIDTH), WARGAME_LLM="mock",
               PYTHONIOENCODING="utf-8")
    proc = subprocess.run(
        [sys.executable, "wargame_cli.py", "play", "--seed", "7",
         "--no-stochastic-injects"],
        cwd=REPO, input="\n".join(feed) + "\n", env=env,
        capture_output=True, text=True, timeout=900, check=False)
    # The CLI exits non-zero when piped stdin runs out at a prompt; that is the
    # end of the recording, not a failure. An empty stdout is a failure.
    if not proc.stdout.strip():
        raise SystemExit("the game printed nothing - capture failed:\n"
                         + proc.stderr[-2000:])
    raw = CURSOR.sub("", proc.stdout).replace("\x1b[2J", "").replace("\x1b[H", "")
    return raw.split("\n")


def plain(line: str) -> str:
    return SGR.sub("", line)


def find(lines: Sequence[str], needle: str, start: int = 0) -> int:
    for i in range(start, len(lines)):
        if needle in plain(lines[i]):
            return i
    raise SystemExit(f"capture marker not found: {needle!r}")


def slab(lines: Sequence[str], start: str, stop: str, *,
         from_index: int = 0, drop_stop: bool = True) -> str:
    """The ANSI between two markers, trimmed of leading/trailing blank rows."""
    i = find(lines, start, from_index)
    j = find(lines, stop, i + 1)
    chunk = list(lines[i:j if drop_stop else j + 1])
    while chunk and not plain(chunk[0]).strip():
        chunk.pop(0)
    while chunk and not plain(chunk[-1]).strip():
        chunk.pop()
    return "\n".join(chunk)


def build_stub() -> Dict[str, object]:
    lines = capture()

    t1 = find(lines, "[ TURN 1 ]")
    disc1 = find(lines, "DISCUSSION · TURN 1", t1)
    t2 = find(lines, "[ TURN 2 ]", disc1)

    briefing1 = slab(lines, "[ TURN 1 ]", "Press SPACE (or Enter) to begin")
    # The advisor's reply to the typed question, between the two sonar rules.
    answer = slab(lines, "Chief of the Defence Staff", ">: ",
                  from_index=disc1)
    # The player's own words go in a panel the page builds live, so only the
    # engine's reading-back of them - the OPERATIONAL ORDER - is canned.
    order = slab(lines, "OPERATIONAL ORDER", "Press Enter to continue",
                 from_index=disc1)
    adjudication = slab(lines, "ADJUDICATION · TURN 1", "TURN 1 COMPLETE",
                        from_index=disc1)
    turnend = slab(lines, "TURN 1 COMPLETE", "Press SPACE (or Enter) to "
                   "continue to next turn", from_index=disc1)
    briefing2 = slab(lines, "[ TURN 2 ]", "Press SPACE (or Enter) to begin",
                     from_index=t2)

    for name, blob in (("briefing1", briefing1), ("answer", answer),
                       ("order", order), ("adjudication", adjudication),
                       ("turnend", turnend), ("briefing2", briefing2)):
        if not blob.strip():
            raise SystemExit(f"empty capture slice: {name}")

    return {
        "decision": DECISION,
        "question": QUESTION,
        "briefings": [briefing1, briefing2],
        "answer": answer,
        "orderPanel": order,
        "adjudication": adjudication,
        "turnEnd": turnend,
    }


# ---------------------------------------------------------------------------

BANNER = ("// GENERATED by dev-scripts/build_play_assets.py - do not edit.\n"
          "// Raw ANSI captured from the game at 78 columns.\n")


def write(name: str, varname: str, payload) -> None:
    body = json.dumps(payload, ensure_ascii=False, indent=1)
    text = f"{BANNER}self.{varname} = {body};\n"
    path = OUT / name
    path.write_text(text, encoding="utf-8")
    print(f"wrote docs/play/{name} ({len(text.encode()) / 1024:.1f} KB)")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    write("assets.js", "FF_ASSETS", build_assets())
    write("stub-data.js", "FF_STUB_DATA", build_stub())


if __name__ == "__main__":
    main()
