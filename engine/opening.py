"""The opening sequence, as structured beats both front ends can render.

The intro is a four-beat cold open — Severomorsk, Northwood, COBRA, then YOUR
ROLE — and it is *paced*: one beat per keypress, so the player reaches turn 1
having been told a story rather than handed a situation report. The turn 1
briefing then flows straight on from YOUR ROLE without a break, which is why
it alone is never split.

That structure used to live inside ``cli/main.py``. The browser build does not
bundle ``cli/``, so it inherited none of it and opened cold on the briefing —
five simultaneous crises, no lead-in, nothing to pace them. This module holds
the structure only: where the scenes divide, what each is called, and where a
briefing splits. Rendering stays with each front end, because they have
nothing in common there — the CLI draws animated scene cards and streams
through its typewriter, the browser draws its own and waits on the space bar.

Keep dramaturgy that both front ends need *here*, not in either of them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

from engine.intro import get_intro_lines

# Coordinates/timestamps for the intro scene cards, keyed by scene numeral.
# Titles are parsed from assets/placeholders/intro_stage.md so editing the
# asset stays authoritative; the geography is presentation-layer flavour.
INTRO_SCENE_META = {
    "I": ("69°04'N 033°25'E", "02 OCT 25 │ 03:15 LOCAL ── 72 HRS EARLIER"),
    "II": ("51°38'N 000°28'W", "05 OCT 25 │ 16:45 LONDON"),
    "III": ("51°30'N 000°07'W", "05 OCT 25 │ 17:00 LONDON"),
}

_SCENE_HEADER_RE = re.compile(r"SCENE\s+([IVXLC]+)\s*:\s*(.+)")

# The line the Turn 1 scene-setting hands over to the intelligence report on.
# Briefings are LLM-written from turn 2, so this matches on the handover
# rather than on an exact string — and on either spelling of the post. The UK
# title is "Adviser" and the roster uses it; the US spelling is what a model
# reaches for about half the time, and matching only one of them silently
# drops the pause that keeps several simultaneous crises from arriving as one
# wall of text.
_REPORT_SPEAKER_RE = re.compile(r"National Security Advis[eo]r", re.IGNORECASE)
_REPORT_VERBS = ("clears", "begins")

# The closing block of the intro. Not a numbered scene: it addresses the
# player directly rather than setting a location, so it carries no scene card.
ROLE_HEADING = "## YOUR ROLE"


@dataclass(frozen=True)
class Scene:
    """One paced beat of the opening.

    ``numeral`` is empty for the closing YOUR ROLE block, which is the signal
    that it gets no scene card.
    """

    body: List[str] = field(default_factory=list)
    numeral: str = ""
    title: str = ""
    location: str = ""
    timestamp: str = ""

    @property
    def has_card(self) -> bool:
        """Whether this beat opens with a scene card (location + timestamp)."""
        return bool(self.numeral)

    def to_dict(self) -> dict:
        """JSON-safe form, for front ends that cross a postMessage boundary."""
        return {
            "body": list(self.body),
            "numeral": self.numeral,
            "title": self.title,
            "location": self.location,
            "timestamp": self.timestamp,
            "hasCard": self.has_card,
        }


def parse_intro_scene(scene_lines: Sequence[str]) -> Tuple[List[str], Optional[tuple]]:
    """Split one intro section into ``(body_lines, header or None)``.

    Consumes the ``## SCENE N: TITLE`` line (and its date/time subheading)
    into a header tuple for the scene card; drops the ``====`` rules and the
    top-level ``#`` title (the title sequence replaced it).
    """
    header = None
    body: List[str] = []
    # After the "## SCENE" line, skip its date/time "## " subheading (shown
    # on the scene card instead). An explicit flag rather than a "body is
    # still empty" check: blank lines between the two headings land in body
    # and would otherwise let the timestamp through as scene text.
    awaiting_subheading = False
    for line in scene_lines:
        stripped = line.strip()
        if "===" in stripped:
            continue
        if stripped.startswith("## SCENE"):
            match = _SCENE_HEADER_RE.match(stripped[2:].strip())
            if match:
                numeral, title = match.group(1), match.group(2).strip()
                location, timestamp = INTRO_SCENE_META.get(numeral, ("", ""))
                header = (numeral, title, location, timestamp)
                awaiting_subheading = True
                continue
        if awaiting_subheading and stripped:
            awaiting_subheading = False
            if stripped.startswith("## "):
                continue  # date/time subheading - shown on the scene card
        if stripped.startswith("# "):
            continue  # plain-text masthead - replaced by the title sequence
        body.append(line)
    while body and not body[0].strip():
        body.pop(0)
    while body and not body[-1].strip():
        body.pop()
    return body, header


def split_intro_sections(lines: Sequence[str]) -> List[List[str]]:
    """Divide the intro script into sections on its ``====`` rules.

    Returned sections keep their rules and headings, so a front end that
    renders the raw text can use this without also taking
    ``parse_intro_scene``'s opinion about what to strip.
    """
    current: List[str] = []
    sections: List[List[str]] = []

    for line in lines:
        if "===" in line and current:
            sections.append(current)
            current = [line]
        else:
            current.append(line)

    # Only keep a trailing section if it holds something beyond a separator.
    if current and any(line.strip() and "===" not in line for line in current):
        sections.append(current)
    return sections


def get_opening_scenes(max_lines: int = 200) -> List[Scene]:
    """The intro, split into the beats a player is paced through.

    A section carrying nothing but a rule and the masthead is dropped — the
    title sequence covers it.
    """
    scenes: List[Scene] = []

    for section in split_intro_sections(get_intro_lines(max_lines)):
        body, header = parse_intro_scene(section)
        if not body and header is None:
            continue  # e.g. the bare title section
        if header is None:
            scenes.append(Scene(body=body))
        else:
            numeral, title, location, timestamp = header
            scenes.append(Scene(body=body, numeral=numeral, title=title,
                                location=location, timestamp=timestamp))
    return scenes


def split_briefing(lines: Sequence[str],
                   *, flows_from_intro: bool = False) -> Tuple[List[str], List[str]]:
    """Split a turn briefing into ``(scene_setting, report)``.

    The briefing opens by setting the room, then hands over to the National
    Security Advisor for the intelligence itself. Pausing between the two is
    what stops several simultaneous crises reading as one undifferentiated
    wall of text.

    ``flows_from_intro`` marks turn 1 of a new campaign, which is deliberately
    *not* split: it runs straight on from YOUR ROLE as one continuous opening.

    ``report`` is empty when there is no split point, in which case
    ``scene_setting`` is the whole briefing.
    """
    lines = list(lines)
    if flows_from_intro:
        return lines, []

    for i, line in enumerate(lines):
        if _REPORT_SPEAKER_RE.search(line) and any(v in line for v in _REPORT_VERBS):
            if i > 0:  # a briefing opening on the handover has nothing to split
                return lines[:i], lines[i:]
            break
    return lines, []
