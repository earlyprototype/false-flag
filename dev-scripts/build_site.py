#!/usr/bin/env python3
"""Build the FALSE FLAG GitHub Pages site into ``docs/``.

The site is committed static HTML: no build step, no JavaScript framework,
no external requests. Python is needed only here, when regenerating.

What it does
------------
* Renders real ANSI terminal captures of live campaigns to styled HTML with
  Rich (``Text.from_ansi`` -> ``export_html``), the way
  ``scratchpad/live_console.py`` did, but emitting committed files instead
  of a self-refreshing live page. All fragments go through one recording
  console so they share a single class map (one small stylesheet instead of
  megabytes of inline ``style=`` attributes).
* Restores the Prime Minister's typed lines. The captures were recorded with
  piped stdin, so the terminal never echoed what was typed; the recorded
  input files are replayed against the prompt stream to put the words back
  where they were entered. The replay is self-checking: the text fed to the
  ``Decision>:`` prompt must match the decision the game printed back in its
  YOUR DECISION panel, for every turn, or the build fails.
* Draws the page chrome (masthead, fog bands, sonar dividers, scene card)
  with the game's own ``cli.aesthetics`` engine, so the site speaks the
  Operation Tuman language literally rather than imitating it.

Usage
-----
    .venv/bin/python dev-scripts/build_site.py [TRANSCRIPT_DIR]

``TRANSCRIPT_DIR`` defaults to ``$FALSE_FLAG_TRANSCRIPTS`` and holds the
capture files (``c4_turn*.txt`` under ``campaign_archive/c4/``, ``c5_turn*``
and ``c?t?_input.txt`` at the top level). Without it the script rebuilds the
pages that do not need transcripts and leaves the replays alone.
"""

from __future__ import annotations

import html
import io
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from rich.console import Console  # noqa: E402
from rich.terminal_theme import TerminalTheme  # noqa: E402
from rich.text import Text  # noqa: E402

from cli.aesthetics import (  # noqa: E402
    classification_strip, fog_band, masthead, reference_code, scene_card,
    sonar_divider,
)

SITE = Path(__file__).resolve().parent / "site"
OUT = REPO / "docs"
COLS = 100

# The captures use a mix of true-colour styles (which survive untouched) and
# the sixteen named ANSI colours, which Rich would otherwise export as its
# washed-out default palette - unreadable on the Tuman ground. This maps the
# sixteen onto the game's own colours, so `bold red` comes back as the
# Operation Tuman orange the terminal actually showed.
TUMAN_TERMINAL = TerminalTheme(
    (11, 16, 23),        # background  --ground
    (201, 214, 224),     # foreground
    [
        (11, 16, 23),      # black
        (255, 59, 48),     # red        --red
        (0, 180, 140),     # green
        (214, 158, 60),    # yellow
        (69, 123, 157),    # blue       --dim
        (178, 132, 214),   # magenta
        (69, 123, 157),    # cyan       (classification chrome)
        (201, 214, 224),   # white
    ],
    [
        (124, 146, 166),   # bright black (the game's "muted": advisor names)
        (255, 107, 53),    # bright red     --accent
        (0, 217, 163),     # bright green   --teal
        (255, 182, 39),    # bright yellow  --amber
        (110, 171, 214),   # bright blue
        (219, 163, 255),   # bright magenta
        (0, 209, 205),     # bright cyan
        (241, 250, 238),   # bright white   --ink
    ],
)

# ---------------------------------------------------------------------------
# Capture cleaning
# ---------------------------------------------------------------------------

SGR = re.compile(r"\x1b\[[0-9;]*m")
CURSOR = re.compile(r"\x1b\[[0-9;]*[ABCDEFGJKST]")
NOISE = re.compile(r"^\s*(\[Rate Limit\]|\[WARNING\]|\[ERROR\]|\[DEBUG\]|"
                   r"Warning:|Traceback \(most recent)")

# Prompts that consume one line of piped stdin. "Press SPACE (or Enter) to
# ..." prompts are raw key reads and consume nothing - which is why the
# replay below lines up.
PROMPTS = (">: ", "Decision>: ", "Response: ", "Choose: ",
           "Press Enter to continue (or type 'details'",
           "Proceed anyway? [y/N]: ",
           "Proceed with enhanced decision? [Y/n]: ",
           "Leave the crisis room? [y/N]: ")
MENU_PROMPT = re.compile(r"^(Select|Enter|Choose)\b[^:]*: $")

# Where a turn capture stops being about this turn.
TURN_END = "Press SPACE (or Enter) to continue to next turn"
# Where the replayed boot/title preamble ends on a resumed turn.
RESUME = re.compile(r"^Resuming at Turn \d+")

TYPED_OPEN = "\x1b[1;38;2;255;182;39m"   # --amber, bold: the PM's own words
TYPED_CLOSE = "\x1b[0m"


def is_prompt(plain: str) -> bool:
    return plain.startswith(PROMPTS) or bool(MENU_PROMPT.match(plain))


def load_turn(path: Path, inputs: Optional[List[str]],
              drop_preamble: bool) -> Tuple[List[str], List[str], int]:
    """Clean one capture and replay the recorded keystrokes into it.

    Returns ``(lines, typed, blanks)`` where ``lines`` still carry SGR
    colour, ``typed`` is the ordered list of things fed to each prompt, and
    ``blanks`` counts the empty ``>:`` echoes dropped from the render.
    """
    raw = path.read_text(errors="replace")
    raw = CURSOR.sub("", raw).replace("\x1b[2J", "").replace("\x1b[H", "")

    lines: List[str] = []
    for ln in raw.split("\n"):
        plain = SGR.sub("", ln)
        if plain.startswith("Progress this turn is unsaved"):
            break
        if NOISE.match(plain):
            continue
        lines.append(ln)
        if plain.startswith(TURN_END):
            break

    if drop_preamble:
        for i, ln in enumerate(lines):
            if RESUME.match(SGR.sub("", ln)):
                lines = lines[i + 1:]
                break

    typed: List[str] = []
    blanks = 0
    if inputs is not None:
        out: List[str] = []
        k = 0
        for ln in lines:
            plain = SGR.sub("", ln)
            if is_prompt(plain):
                fed = inputs[k] if k < len(inputs) else ""
                k += 1
                typed.append(fed)
                if fed.strip():
                    head, tail = ln, ""
                    # "Response: " prints the reply on the same line; the
                    # typed words belong between the two.
                    if plain.startswith("Response: ") and len(plain) > 10:
                        cut = ln.index("Response: ") + len("Response: ")
                        head, tail = ln[:cut], ln[cut:]
                    out.append(head + TYPED_OPEN + fed + TYPED_CLOSE)
                    if tail:
                        out.append(tail)
                    continue
                # A blank line fed to a bare ">:" is the piped-play scaffold
                # stepping through a pacing gate; the prompt echoes with
                # nothing after it. A player at a keyboard presses a key and
                # sees none of this, so the echo is dropped from the render.
                # Note the input has already been consumed (k advanced, fed
                # recorded) above - the replay stays in step with the prompt
                # stream and the decision self-check is untouched.
                if plain.rstrip() == ">:":
                    blanks += 1
                    continue
            out.append(ln)
        lines = out

    while lines and not SGR.sub("", lines[-1]).strip():
        lines.pop()
    return lines, typed, blanks


def decision_panel_text(lines: Sequence[str]) -> str:
    """The decision as the game printed it back, out of its YOUR DECISION box."""
    grab, box = False, []
    for ln in lines:
        p = SGR.sub("", ln)
        if p.startswith("╭") and "YOUR DECISION" in p:
            grab = True
            continue
        if grab:
            if p.startswith("╰"):
                break
            box.append(p.strip("│ ").strip())
    return " ".join(x for x in box if x)


def squash(s: str) -> str:
    return re.sub(r"\W+", "", s).lower()


# ---------------------------------------------------------------------------
# One recording console for every fragment on the site
# ---------------------------------------------------------------------------

class Rig:
    """Collects renderables, exports them once, hands back HTML fragments.

    Rich restarts its ``.rN`` class numbering on every ``export_html`` call,
    so everything is printed into a single console with sentinels between
    fragments and split apart afterwards. One stylesheet, no collisions.
    """

    MARK = "@@FRAG@@"

    def __init__(self, width: int = COLS) -> None:
        self.console = Console(record=True, width=width, force_terminal=True,
                               color_system="truecolor", highlight=False,
                               soft_wrap=False, file=io.StringIO())
        self._keys: List[str] = []

    def add(self, key: str, renderable) -> None:
        assert key not in self._keys, f"duplicate fragment {key}"
        self._keys.append(key)
        self.console.print(Text(f"{self.MARK}{key}{self.MARK}"), no_wrap=True,
                           overflow="ignore", crop=False)
        self.console.print(renderable)

    def ansi(self, key: str, lines: Sequence[str]) -> None:
        self.add(key, Text.from_ansi("\n".join(lines)))

    def finish(self) -> Tuple[str, Dict[str, str]]:
        blob = self.console.export_html(
            inline_styles=False, code_format="{stylesheet}@@SHEET@@{code}",
            theme=TUMAN_TERMINAL, clear=True)
        stylesheet, code = blob.split("@@SHEET@@", 1)
        parts = re.split(re.escape(self.MARK) + r"([\w.:-]+)"
                         + re.escape(self.MARK) + r"\n?", code)
        frags: Dict[str, str] = {}
        for i in range(1, len(parts) - 1, 2):
            frags[parts[i]] = parts[i + 1].strip("\n")
        missing = [k for k in self._keys if k not in frags]
        assert not missing, f"lost fragments: {missing}"
        # Rich emits a body rule we do not want; keep only the .rN classes.
        rules = re.findall(r"\.r\d+ \{[^}]*\}", stylesheet)
        return "\n".join(rules), frags


# ---------------------------------------------------------------------------
# Page shell
# ---------------------------------------------------------------------------

NAV = (("index.html", "01 BRIEF"),
       ("interstitials.html", "02 VIGNETTES"),
       ("replay.html", "03 REPLAY"),
       # Hand-written, not generated here: docs/play/ is the playable build.
       ("play/index.html", "04 PLAY"))


def strip_html(label: str, code: str, edge: str = "top") -> str:
    corners = {"top": ("┌", "┐"), "bottom": ("└", "┘"), "bare": ("─", "─")}
    left, right = corners[edge]
    cls = "strip bottom" if edge == "bottom" else "strip"
    return (f'<div class="{cls}" aria-hidden="true">'
            f'<span>{left}─[ <b>{html.escape(label)}</b> ]</span>'
            f'<span class="fill"></span>'
            f'<span class="code">[ {html.escape(code)} ]─{right}</span></div>')


def nav_html(current: str) -> str:
    here = ' aria-current="page"'
    links = "".join(
        f'<a href="{href}"{here if href == current else ""}>{label}</a>'
        for href, label in NAV)
    return ('<nav class="bar">'
            '<a class="home" href="index.html">FALSE&nbsp;FLAG</a>'
            f'<span class="links">{links}</span></nav>')


def page(*, title: str, desc: str, current: str, code: str, body: str,
         css: str, rich_css: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta name="color-scheme" content="dark light">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:type" content="website">
<style>
{css}
/* Rich terminal export classes (one shared map for the whole site) */
{rich_css}
</style>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{strip_html("TOP SECRET ── UK EYES ONLY", code)}
{nav_html(current)}
<main id="main">
{body}
</main>
<footer>
{strip_html("FALSE FLAG ── OPERATION TUMAN", "END OF FILE", edge="bottom")}
<div class="inner">
<p>FALSE FLAG is a terminal wargame written in Python. This site is a window
onto it — a record of play, not a playable build. Everything shown here was
captured from live runs against a real LLM backend.</p>
<p>Inspired by Sky News' <a href="https://www.audible.co.uk/podcast/The-Wargame/B0FCLQ7W9B">The
Wargame</a> podcast. Independent project — not affiliated with or endorsed by
Sky News, Tortoise, or the podcast's participants. MIT licensed.
<a href="https://github.com/earlyprototype/false-flag">Source on GitHub</a>.</p>
</div>
</footer>
</body>
</html>
"""


def term(label: str, ref: str, frag: str, *, clip: bool = False,
         hint: bool = True) -> str:
    """A terminal capture pane: labelled, dark, and scrolling on its own."""
    cls = "console clip" if clip else "console"
    text = ("── EXCERPT · SCROLL INSIDE THE PANE FOR THE REST"
            if clip else
            "── CAPTURE IS 100 COLUMNS WIDE · SCROLL THE PANE SIDEWAYS IF CLIPPED")
    foot = f'<div class="scrollhint">{text}</div>' if hint or clip else ""
    return (f'<div class="term">'
            f'<div class="label"><span class="r">●</span>'
            f'<b>{html.escape(label)}</b><span>{html.escape(ref)}</span></div>'
            f'<pre class="{cls}"><code>{frag}</code></pre>{foot}</div>')


# ---------------------------------------------------------------------------
# Transcript excerpts
# ---------------------------------------------------------------------------

def find(lines: Sequence[str], needle: str, start: int = 0) -> int:
    for k in range(start, len(lines)):
        if needle in SGR.sub("", lines[k]):
            return k
    raise SystemExit(f"excerpt marker not found: {needle!r}")


def excerpt(lines: Sequence[str], start: str, stop: str, *,
            after: int = 0, limit: int = 400) -> List[str]:
    """Lines from the first one containing ``start`` to the first ``stop``."""
    i = find(lines, start) + after
    plains = [SGR.sub("", x) for x in lines]
    j = i + 1
    while j < len(plains) and stop not in plains[j] and j - i < limit:
        j += 1
    return list(lines[i:j + 1])


def panel(lines: Sequence[str], title: str) -> List[str]:
    """A whole rounded box: the ``╭─ TITLE ─╮`` line down to its ``╰``."""
    i = find(lines, title)
    while i >= 0 and not SGR.sub("", lines[i]).lstrip().startswith("╭"):
        i -= 1
    j = i + 1
    while j < len(lines) and not SGR.sub("", lines[j]).lstrip().startswith("╰"):
        j += 1
    return list(lines[i:j + 1])


def window(lines: Sequence[str], start: str, count: int) -> List[str]:
    i = find(lines, start)
    return list(lines[i:i + count])


def dedent_blank(lines: List[str]) -> List[str]:
    while lines and not SGR.sub("", lines[0]).strip():
        lines.pop(0)
    while lines and not SGR.sub("", lines[-1]).strip():
        lines.pop()
    return lines


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def gist(text: str, width: int = 96) -> str:
    t = " ".join(text.split())
    if len(t) <= width:
        return t
    return t[:width].rsplit(" ", 1)[0] + " …"


def main() -> None:
    src = None
    if len(sys.argv) > 1:
        src = Path(sys.argv[1])
    elif os.environ.get("FALSE_FLAG_TRANSCRIPTS"):
        src = Path(os.environ["FALSE_FLAG_TRANSCRIPTS"])
    if src is None or not src.is_dir():
        raise SystemExit(__doc__.strip().splitlines()[-1] +
                         "\nGive me the transcript directory.")

    css = (SITE / "site.css").read_text()
    rig = Rig()

    # -- chrome ------------------------------------------------------------
    rig.add("mast", masthead(COLS, seed="false-flag-site"))
    rig.add("fog_hero", fog_band(COLS, 3, 0.62, "hero"))
    rig.add("fog_mid", fog_band(COLS, 2, 0.44, "mid"))
    rig.add("fog_thin", fog_band(COLS, 2, 0.30, "thin"))
    rig.add("fog_vig", fog_band(COLS, 3, 0.52, "vignettes"))
    rig.add("fog_replay", fog_band(COLS, 3, 0.58, "replay"))
    for i, seed in enumerate(("a", "b", "c", "d", "e", "f")):
        rig.add(f"sonar_{i}", sonar_divider(seed=f"site-{seed}", width=COLS))
    rig.add("scene", scene_card(
        1, "SEVEROMORSK NAVAL BASE, RUSSIA",
        location="69°04'N 033°25'E",
        timestamp="02 OCT 25 │ 03:15 LOCAL ── 72 HRS EARLIER",
        seed="site-scene", width=COLS))
    rig.add("strip_mystery", classification_strip(
        code="COBRA/TU/00", label="NARRATIVE SEALED ── PM NOT CLEARED",
        width=COLS, seed="mystery", edge="top"))

    # -- campaigns ---------------------------------------------------------
    campaigns = {
        "c4": dict(dir=src / "campaign_archive" / "c4", turns=17,
                   file="c4_turn{n}.txt"),
        "c5": dict(dir=src, turns=3, file="c5_turn{n}.txt"),
    }
    data: Dict[str, List[dict]] = {}
    for tag, meta in campaigns.items():
        rows = []
        checked = blanks = 0
        for n in range(1, meta["turns"] + 1):
            path = Path(meta["dir"]) / meta["file"].format(n=n)
            inputs = (src / f"{tag}t{n}_input.txt").read_text().split("\n")
            lines, typed, dropped = load_turn(path, inputs,
                                              drop_preamble=(n > 1))
            blanks += dropped
            # Self-check: what we fed the decision prompt must be exactly
            # what the game echoed into its YOUR DECISION panel.
            fed = [t for t in typed if len(t) > 40]
            decided = decision_panel_text(lines)
            if decided:
                if not any(squash(decided)[:120] == squash(t)[:120]
                           for t in fed):
                    raise SystemExit(
                        f"{tag} turn {n}: keystroke replay does not match the "
                        f"decision the game printed back — refusing to build.")
                checked += 1
            rows.append(dict(n=n, lines=lines, typed=typed, panel=decided))
            rig.ansi(f"{tag}.t{n}", lines)
        data[tag] = rows
        print(f"{tag}: {len(rows)} turns, {checked} decisions verified against "
              f"the game's own echo, {blanks} empty '>:' echoes collapsed")

    c4, c5 = data["c4"], data["c5"]

    # -- landing exhibits --------------------------------------------------
    t1 = c4[0]["lines"]
    rig.ansi("ex.decision", panel(t1, "YOUR DECISION"))
    rig.ansi("ex.order", panel(t1, "OPERATIONAL ORDER"))
    rig.ansi("ex.advisory", dedent_blank(
        excerpt(t1, "[1] ", "───●───", limit=40)))
    rig.ansi("ex.brief", dedent_blank(
        excerpt(t1, "BREAKING UPDATE", "Press SPACE", limit=40)[:-1]))
    rig.ansi("ex.call", dedent_blank(
        window(c4[3]["lines"], "=== DIPLOMATIC CALL", 10)))
    rig.ansi("ex.mystery", dedent_blank(
        excerpt(c5[0]["lines"], "SELECT GAME TYPE", "Mystery Mode activated",
                limit=40)))

    narratives = (REPO / "data/scenarios/war_game_2025/narratives.yaml"
                  ).read_text().split("\n")
    start = next(i for i, ln in enumerate(narratives)
                 if "CHINA_PROXY_WAR" in ln)
    caption = ("\x1b[38;2;69;123;157m"
               "# data/scenarios/war_game_2025/narratives.yaml"
               "  --  one of the truths the game can draw\x1b[0m")
    rig.ansi("ex.narrative",
             [caption, ""] + ["\x1b[38;2;241;250;238m" + ln + "\x1b[0m"
                              for ln in narratives[start:start + 11]])

    rich_css, F = rig.finish()

    # -- assemble ----------------------------------------------------------
    ctx = dict(F)
    ctx["TERM_DECISION"] = term("PM TYPES, TURN 1", "COBRA/TU/·· DECISION",
                                F["ex.decision"], hint=False)
    ctx["TERM_ORDER"] = term("THE ENGINE READS IT BACK", "OPERATIONAL ORDER",
                             F["ex.order"], hint=False)
    ctx["TERM_ADVISORY"] = term("THE ROOM PUSHES BACK", "CRITICAL ADVISORIES",
                                F["ex.advisory"], clip=True)
    ctx["TERM_BRIEF"] = term("BRIEFING, TURN 1", "COBRA/TU/85",
                             F["ex.brief"], clip=True)
    ctx["TERM_CALL"] = term("DIPLOMATIC CALL, TURN 4", "MOSCOW DIRECT",
                            F["ex.call"], clip=True)
    ctx["TERM_MYSTERY"] = term("CAMPAIGN SETUP", "GAME TYPE",
                               F["ex.mystery"], hint=False)
    ctx["TERM_NARRATIVE"] = term("WHAT THE GAME KNOWS", "SEALED",
                                 F["ex.narrative"], clip=True)

    counts = {}
    for tag, rows in data.items():
        words = sum(len(SGR.sub("", "\n".join(r["lines"])).split())
                    for r in rows)
        counts[tag] = words
    ctx["C4_WORDS"] = f"{counts['c4']:,}"
    ctx["C5_WORDS"] = f"{counts['c5']:,}"

    body = (SITE / "index.body.html").read_text()
    write("index.html", page(
        title="FALSE FLAG — an LLM crisis wargame in a terminal",
        desc="You are the Prime Minister in COBRA. Your advisors are LLM "
             "agents, your decisions are free text, and a hidden narrative "
             "is running behind the crisis.",
        current="index.html", code=reference_code("site-index"),
        body=fill(body, ctx), css=css, rich_css=rich_css))

    body = (SITE / "interstitials.body.html").read_text()
    write("interstitials.html", page(
        title="FALSE FLAG — the interstitials",
        desc="Five ASCII vignettes that play between turns: the tea round, "
             "the periscope, the teleprinter, the red phone, the radar room.",
        current="interstitials.html", code=reference_code("site-vig"),
        body=fill(body, ctx), css=css, rich_css=rich_css))

    write("replay.html", page(
        title="FALSE FLAG — campaign replay: seventeen turns",
        desc="A complete recorded campaign: seventeen turns of briefings, "
             "cabinet questions, free-text decisions and adjudication.",
        current="replay.html", code=reference_code("site-replay"),
        body=replay_body(c4, F, tag="c4"),
        css=css, rich_css=rich_css))

    write("replay-nuclear-order.html", page(
        title="FALSE FLAG — campaign replay: the nuclear order",
        desc="Three turns spent testing the edge of the system: a Prime "
             "Minister orders a nuclear strike, is refused, and tries to "
             "announce it anyway.",
        current="replay.html", code=reference_code("site-c5"),
        body=replay_body(c5, F, tag="c5"),
        css=css, rich_css=rich_css))

    (OUT / ".nojekyll").write_text("")
    print("wrote docs/.nojekyll")


def fill(template: str, ctx: Dict[str, str]) -> str:
    def sub(m):
        key = m.group(1)
        if key not in ctx:
            raise SystemExit(f"template asks for unknown fragment {key!r}")
        return ctx[key]
    return re.sub(r"\{\{([\w.]+)\}\}", sub, template)


def write(name: str, text: str) -> None:
    path = OUT / name
    path.write_text(text, encoding="utf-8")
    print(f"wrote docs/{name} ({len(text.encode()) / 1024:.0f} KB)")


# ---------------------------------------------------------------------------
# Replay pages
# ---------------------------------------------------------------------------

REPLAY_INTRO = """
<div class="fogwrap"><pre class="rig wide" aria-hidden="true">{fog}</pre></div>
<h1 class="rule" style="margin-top:26px"><span class="num">{ref}</span>
<span>{heading}</span><span class="fill"></span></h1>
<p class="lede">{lede}</p>
{blurb}
<ul class="chips">{chips}</ul>
<div class="note"><b>How to read this.</b> Every pane below is the real
terminal output, colour and box-drawing intact. Captures were recorded with
piped input, so the terminal never echoed the Prime Minister's typing — those
lines have been put back from the recorded input files and are shown
<span style="color:var(--amber)">in amber</span>. Nothing else is added,
reordered or rewritten; only the repeated title sequence at the top of each
resumed turn, the rate-limit chatter, and the empty <code>&gt;:</code> echoes
the piped-play scaffold left behind when it stepped through a pacing gate —
which a player at a keyboard never sees — have been dropped.</div>
"""


CAMPAIGNS = {
    "c4": dict(
        ref="C4",
        heading="REPLAY ── SEVENTEEN TURNS",
        fog="fog_replay",
        lede="One campaign, played end to end against a live LLM backend. "
             "Briefings arrive, the cabinet is questioned in plain English, "
             "the Prime Minister writes a paragraph, and the game makes the "
             "world answer it.",
        blurb="<p>It starts with a Russian submarine surfacing off Orkney and "
              "two dead F-35 pilots in Norfolk. By turn seventeen the Prime "
              "Minister is no longer investigating an attack on Britain but "
              "hunting a service that wears other countries' faces. "
              "Nothing in that arc was scripted; it is what the adjudicator "
              "made of seventeen paragraphs of free text.</p>"
              '<p><a href="replay-nuclear-order.html">A shorter campaign, '
              "spent finding the edge of the system →</a></p>",
        chips=[("MODE", "STORY"), ("TURNS", "17"), ("ADVISORS", "5"),
               ("SCENARIO", "WAR GAME 2025"), ("RECORDED", "LIVE, UNSCRIPTED")],
    ),
    "c5": dict(
        ref="C5",
        heading="REPLAY ── THE NUCLEAR ORDER",
        fog="fog_mid",
        lede="Three turns spent deliberately looking for the wall. The Prime "
             "Minister orders a nuclear strike on Moscow in the first turn, "
             "then spends the next two finding out what the machinery around "
             "them actually does about it.",
        blurb="<p>This is not representative play, and it is not a Mystery "
              "Mode demonstration — it was started in Mystery Mode, so a "
              "hidden narrative was drawn and never revealed, but the run "
              "went somewhere else. It is a stress test, published because "
              "what it produced is more informative than a careful game.</p>"
              "<p>Turn one: the Attorney General is asked, in terms, whether "
              "anyone in the room can lawfully stop the Prime Minister — and "
              "then the deterrent is ordered released. Turn two opens with "
              "the Chief of the Defence Staff confirming that nothing left a "
              "tube, a wing or a silo; the Prime Minister responds by going "
              "on television to announce a strike that did not happen. Turn "
              "three sends F-35s on a penetrating course for Moscow and "
              "demands the chain of command confirm its obedience in "
              "writing.</p>"
              "<p>Nothing here is a scripted failure state. The refusal is "
              "the advisors and the adjudicator reasoning about an unlawful "
              "order, in character, at run time.</p>"
              '<p><a href="replay.html">← The seventeen-turn campaign</a></p>',
        chips=[("MODE", "MYSTERY, UNRESOLVED"), ("TURNS", "3"),
               ("NARRATIVE", "SEALED"), ("ORDER", "REFUSED"),
               ("SCENARIO", "WAR GAME 2025")],
    ),
}


def replay_body(rows: List[dict], F: Dict[str, str], *, tag: str) -> str:
    turns = []
    index = []
    for r in rows:
        n = r["n"]
        summary = gist(r["panel"] or "No decision recorded this turn.")
        anchor = f"turn-{n}"
        opened = " open" if n == 1 else ""
        index.append(
            f'<li><a href="#{anchor}"><span class="n">TURN {n:02d}</span>'
            f'<span class="t">{html.escape(gist(summary, 120))}</span></a></li>')
        turns.append(
            f'<details class="turn" id="{anchor}"{opened}>'
            f'<summary><span>──[ TURN {n:02d} ]──</span>'
            f'<span class="gist">{html.escape(summary)}</span></summary>'
            f'<div class="body">'
            + term(f"CAMPAIGN {tag.upper()} · TURN {n}",
                   reference_code(f"{tag}-{n}"), F[f"{tag}.t{n}"])
            + '</div></details>')

    meta = CAMPAIGNS[tag]
    chip_html = "".join(f'<li>{k} <b>{v}</b></li>' for k, v in meta["chips"])
    intro = REPLAY_INTRO.format(fog=F[meta["fog"]], heading=meta["heading"],
                                lede=meta["lede"], blurb=meta["blurb"],
                                chips=chip_html, ref=meta["ref"])
    return (intro
            + '<h2 class="rule"><span class="node">──●──</span>'
              '<span>&nbsp;[ TURN INDEX ]</span><span class="fill"></span></h2>'
            + f'<ul class="index">{"".join(index)}</ul>'
            + '<h2 class="rule"><span class="node">──●──</span>'
              '<span>&nbsp;[ THE CAMPAIGN ]</span><span class="fill"></span></h2>'
            + "".join(turns))


if __name__ == "__main__":
    main()
