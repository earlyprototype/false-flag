"""Operation Tuman aesthetic engine.

Generates the shared "fog + signals-room" visual language used across every
game surface: title masthead, intro scene cards, boot/loading screen, turn
and phase banners, section dividers, and the debrief frame.

Conventions
-----------
* Every public function returns a Rich renderable (``Text`` or ``Group``);
  print them with ``console.print(...)``.
* Every generator takes an explicit ``seed`` (int or str). The same seed
  always produces identical output; no unseeded randomness is ever used.
* Colors are read from ``cli.theme.theme_manager.get_colors()`` at render
  time, so output follows the active theme automatically.
* All output is ASCII/box-drawing only - no emoji.
* Content width defaults to 78 (theme WIDTH - 2). Lines are marked
  no-wrap/crop so narrow or non-TTY consoles clip instead of crashing.
"""

from __future__ import annotations

import math
import sys
import time
import zlib
from random import Random
from typing import Iterator, List, Optional, Union

from rich.console import Console, Group
from rich.text import Text

from cli.theme import theme_manager, WIDTH

Seed = Union[int, str, None]

DEFAULT_WIDTH = WIDTH - 2  # 78: fits inside an 80-column terminal

# Fog character ramp, sparse -> dense
_FOG_RAMP = (" ", "·", "░", "▒", "▓")


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------

def _seed_int(seed: Seed, salt: str = "") -> int:
    """Coerce an int/str/None seed (plus optional salt) to a stable int."""
    if seed is None:
        seed = 0
    if isinstance(seed, int):
        base = seed & 0xFFFFFFFF
    else:
        base = zlib.crc32(str(seed).encode("utf-8"))
    if salt:
        # Hash the combined string rather than XOR-ing two CRCs: CRC32 is
        # linear, so XOR combinations collide for related seed/salt pairs.
        base = zlib.crc32(f"{salt}|{base}".encode("utf-8"))
    return base


def _rng(seed: Seed, salt: str = "") -> Random:
    """Deterministic Random instance for a seed + salt."""
    return Random(_seed_int(seed, salt))


def reference_code(seed: Seed, prefix: str = "COBRA/TU") -> str:
    """Deterministic fictional document reference, e.g. ``COBRA/TU/07``."""
    n = _seed_int(seed, "refcode") % 97 + 1
    return f"{prefix}/{n:02d}"


def _roman(n: int) -> str:
    """Roman numeral for scene numbering (1..3999)."""
    pairs = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"),
             (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"),
             (5, "V"), (4, "IV"), (1, "I")]
    out, n = [], max(1, int(n))
    for value, glyph in pairs:
        while n >= value:
            out.append(glyph)
            n -= value
    return "".join(out)


def _clip(s: str, width: int) -> str:
    return s if len(s) <= width else s[: max(0, width - 1)] + "…"


def _no_wrap(text: Text) -> Text:
    text.no_wrap = True
    text.overflow = "crop"
    return text


# ---------------------------------------------------------------------------
# Fog fields
# ---------------------------------------------------------------------------

def _fog_rows(rng: Random, width: int, height: int, density: float) -> List[str]:
    """Character rows of drifting fog.

    Uses smoothed 1-D value noise: control points every few columns,
    cosine-interpolated across the row, drifting slightly row to row so the
    banks cohere vertically instead of reading as static.
    """
    density = max(0.0, min(1.0, density))
    step = 6
    n_ctrl = width // step + 2
    ctrl = [rng.random() for _ in range(n_ctrl)]
    rows: List[str] = []
    for _y in range(height):
        # Drift the bank slightly between rows
        ctrl = [min(1.0, max(0.0, v + rng.uniform(-0.16, 0.16))) for v in ctrl]
        chars: List[str] = []
        for x in range(width):
            i = x / step
            i0 = int(i)
            t = i - i0
            t = (1 - math.cos(t * math.pi)) / 2  # cosine ease
            v = ctrl[i0] * (1 - t) + ctrl[i0 + 1] * t
            level = v * density * 1.7
            if level < 0.16:
                chars.append(" ")
            elif level < 0.38:
                chars.append("·")
            elif level < 0.66:
                chars.append("░")
            elif level < 0.92:
                chars.append("▒")
            else:
                chars.append("▓")
        # Sparse horizontal drift accents in the thin parts of the bank
        for x in range(width):
            if chars[x] == " " and rng.random() < 0.02 * (0.3 + density):
                chars[x] = "╌" if rng.random() < 0.5 else "~"
        rows.append("".join(chars))
    return rows


def fog_band(width: int = DEFAULT_WIDTH, height: int = 3,
             density: float = 0.5, seed: Seed = 0) -> Text:
    """A band of drifting fog texture.

    Args:
        width: Band width in columns.
        height: Number of rows.
        density: 0.0 (clear air) to 1.0 (thick fog). Wire to escalation later.
        seed: Deterministic seed (int or str); same seed -> same weather.
    """
    colors = theme_manager.get_colors()
    style_for = {
        "·": colors["muted"], "╌": colors["muted"], "~": colors["muted"],
        "░": colors["muted"], "▒": colors["secondary"], "▓": colors["accent"],
    }
    rows = _fog_rows(_rng(seed, "fog"), width, max(1, height), density)
    text = Text()
    for r, row in enumerate(rows):
        if r:
            text.append("\n")
        # Group consecutive same-style chars into runs
        run, run_style = [], None
        for ch in row:
            st = style_for.get(ch)
            if st != run_style and run:
                text.append("".join(run), style=run_style)
                run = []
            run_style = st
            run.append(ch)
        if run:
            text.append("".join(run), style=run_style)
    return _no_wrap(text)


# ---------------------------------------------------------------------------
# Classification strips
# ---------------------------------------------------------------------------

def classification_strip(code: Optional[str] = None,
                         label: str = "TOP SECRET ── UK EYES ONLY",
                         width: int = DEFAULT_WIDTH,
                         seed: Seed = 0,
                         edge: str = "top") -> Text:
    """Single-line classification header/footer.

    ``edge`` is ``"top"`` (``┌─[ ... ]───[ CODE ]─┐``), ``"bottom"``
    (``└───[ CODE ]─┘``) or ``"bare"`` (no corners, for inline use).
    ``code`` defaults to a deterministic reference from the seed.
    """
    colors = theme_manager.get_colors()
    if code is None:
        code = reference_code(seed)

    corners = {"top": ("┌", "┐"), "bottom": ("└", "┘"), "bare": ("─", "─")}
    left_c, right_c = corners.get(edge, corners["top"])

    text = Text()
    if edge == "bottom":
        # └────────...────[ CODE ]─┘
        fill = width - len(code) - 7
        if fill < 1:
            fill = 1
        text.append(left_c + "─" * fill, style=colors["muted"])
        text.append("[ ", style=colors["muted"])
        text.append(code, style=colors["warning"])
        text.append(" ]─" + right_c, style=colors["muted"])
        return _no_wrap(text)

    # ┌─[ LABEL ]────...────[ CODE ]─┐
    label = _clip(label, width - len(code) - 13)
    fill = width - len(label) - len(code) - 12
    if fill < 1:
        fill = 1
    text.append(left_c + "─", style=colors["muted"])
    text.append("[ ", style=colors["muted"])
    text.append(label, style=f"{colors['danger']} bold")
    text.append(" ]", style=colors["muted"])
    text.append("─" * fill, style=colors["muted"])
    text.append("[ ", style=colors["muted"])
    text.append(code, style=colors["warning"])
    text.append(" ]─" + right_c, style=colors["muted"])
    return _no_wrap(text)


# ---------------------------------------------------------------------------
# Sonar contact dividers
# ---------------------------------------------------------------------------

def sonar_divider(seed: Seed = 0, width: int = DEFAULT_WIDTH) -> Text:
    """Sparse sonar-trace divider: faint returns and one strong contact.

    e.g. ``·  ··   •    · ───●────  ·   • ··``
    """
    colors = theme_manager.get_colors()
    rng = _rng(seed, "sonar")
    cells = [" "] * max(10, width)

    # Faint returns
    for _ in range(max(4, width // 9)):
        cells[rng.randrange(width)] = "·"
    # A few stronger blips
    for _ in range(3):
        cells[rng.randrange(width)] = "•"
    # Primary contact with trace lines either side
    p = rng.randrange(int(width * 0.25), int(width * 0.72))
    run = rng.randrange(3, 7)
    for i in range(p - run, p + run + 1):
        if 0 <= i < width:
            cells[i] = "─"
    cells[p] = "●"

    style_for = {"·": colors["muted"], "•": colors["secondary"],
                 "─": colors["muted"], "●": f"{colors['primary']} bold"}
    text = Text()
    for ch in cells[:width]:
        text.append(ch, style=style_for.get(ch))
    return _no_wrap(text)


# ---------------------------------------------------------------------------
# Masthead
# ---------------------------------------------------------------------------

# Hand-crafted 5-row block font for the letters of FALSE FLAG.
# Every row of every glyph is exactly 6 columns wide.
_FONT = {
    "F": ["██████",
          "██    ",
          "█████ ",
          "██    ",
          "██    "],
    "A": ["▄████▄",
          "██  ██",
          "██████",
          "██  ██",
          "██  ██"],
    "L": ["██    ",
          "██    ",
          "██    ",
          "██    ",
          "██████"],
    "S": ["▄█████",
          "██    ",
          "▀████▄",
          "    ██",
          "█████▀"],
    "E": ["██████",
          "██    ",
          "█████ ",
          "██    ",
          "██████"],
    "G": ["▄████▄",
          "██    ",
          "██ ███",
          "██  ██",
          "▀████▀"],
}


def _block_title(words: str) -> List[str]:
    """Assemble block-letter rows for a title string (letters in _FONT)."""
    rows = ["", "", "", "", ""]
    for w, word in enumerate(words.split()):
        for i, letter in enumerate(word):
            glyph = _FONT[letter]
            for r in range(5):
                sep = "" if (w == 0 and i == 0) else ("      " if i == 0 else "  ")
                rows[r] += sep + glyph[r]
    return rows


_MASTHEAD_ROWS = _block_title("FALSE FLAG")
_TAGLINE = "OPERATION TUMAN ── A COBRA CRISIS SIMULATION"


def masthead(width: int = DEFAULT_WIDTH, seed: Seed = 0,
             tagline: bool = True) -> Group:
    """The FALSE FLAG title masthead: fog above, block title, fog below."""
    colors = theme_manager.get_colors()
    parts: List[Text] = [fog_band(width, 2, 0.40, _seed_int(seed, "mast-top"))]

    title_width = len(_MASTHEAD_ROWS[0])
    pad = " " * max(0, (width - title_width) // 2)
    for row in _MASTHEAD_ROWS:
        t = Text(pad)
        t.append(row, style=f"{colors['primary']} bold")
        parts.append(_no_wrap(t))

    if tagline:
        parts.append(Text())
        tag_pad = " " * max(0, (width - len(_TAGLINE)) // 2)
        t = Text(tag_pad)
        t.append(_TAGLINE, style=colors["muted"])
        parts.append(_no_wrap(t))

    parts.append(fog_band(width, 2, 0.40, _seed_int(seed, "mast-bot")))
    return Group(*parts)


# ---------------------------------------------------------------------------
# Scene cards
# ---------------------------------------------------------------------------

def scene_card(number: Union[int, str], title: str,
               location: str = "", timestamp: str = "",
               seed: Seed = None, width: int = DEFAULT_WIDTH) -> Group:
    """Framed intro scene header.

    Combines a classification strip, ``SCENE I — TITLE`` line, a
    coordinates/timestamp strip, and a thin fog band underneath.

    Args:
        number: Scene number (int -> roman numeral) or a pre-formed string.
        title: e.g. ``"SEVEROMORSK NAVAL BASE, RUSSIA"``.
        location: e.g. ``"69°04'N 033°25'E"``.
        timestamp: e.g. ``"02 OCT 25 │ 03:15 LOCAL"``.
        seed: Defaults to a seed derived from the scene number + title.
    """
    colors = theme_manager.get_colors()
    if seed is None:
        seed = f"scene-{number}-{title}"
    numeral = _roman(number) if isinstance(number, int) else str(number)
    inner = width - 4

    def wall_line(content: Text) -> Text:
        t = Text("│ ", style=colors["muted"])
        t.append_text(content)
        pad = inner - content.cell_len
        if pad > 0:
            t.append(" " * pad)
        t.append(" │", style=colors["muted"])
        return _no_wrap(t)

    title_line = Text(" ")
    title_line.append(f"SCENE {numeral}", style=f"{colors['emphasis']} bold")
    title_line.append(" ── ", style=colors["muted"])
    title_line.append(_clip(title.upper(), inner - len(numeral) - 11),
                      style=f"{colors['highlight']} bold")

    meta_bits = [b for b in (location, timestamp) if b]
    meta_line = Text(" " + _clip(" │ ".join(meta_bits), inner - 1),
                     style=colors["muted"])

    parts: List[Union[Text, Group]] = [
        classification_strip(seed=seed, width=width, edge="top"),
        wall_line(Text()),
        wall_line(title_line),
    ]
    if meta_bits:
        parts.append(wall_line(meta_line))
    parts.append(wall_line(Text()))
    bottom = Text("└" + "─" * (width - 2) + "┘", style=colors["muted"])
    parts.append(_no_wrap(bottom))
    parts.append(fog_band(width, 2, 0.35, _seed_int(seed, "scene-fog")))
    return Group(*parts)


# ---------------------------------------------------------------------------
# Turn and phase banners
# ---------------------------------------------------------------------------

def turn_banner(turn: int, seed: Seed = None,
                width: int = DEFAULT_WIDTH) -> Group:
    """Heavy turn banner with seeded fog trim above and below.

    Each turn's trim differs subtly because the seed defaults to the turn.
    """
    colors = theme_manager.get_colors()
    if seed is None:
        seed = f"turn-{turn}"
    code = reference_code(seed)

    label = f"[ TURN {turn} ]"
    right = f"[ {code} ]"
    fill = width - len(label) - len(right) - 6  # 4 left + 2 right rule caps
    if fill < 1:
        fill = 1
    rule = Text("━━━━", style=colors["accent"])
    rule.append("[ ", style=colors["accent"])
    rule.append(f"TURN {turn}", style=f"{colors['highlight']} bold")
    rule.append(" ]", style=colors["accent"])
    rule.append("━" * fill, style=colors["accent"])
    rule.append("[ ", style=colors["accent"])
    rule.append(code, style=colors["muted"])
    rule.append(" ]", style=colors["accent"])
    rule.append("━━", style=colors["accent"])

    return Group(
        fog_band(width, 1, 0.30, _seed_int(seed, "trim-a")),
        _no_wrap(rule),
        fog_band(width, 1, 0.30, _seed_int(seed, "trim-b")),
    )


def phase_banner(phase: str, turn: Optional[int] = None,
                 seed: Seed = None, width: int = DEFAULT_WIDTH) -> Text:
    """Light phase header in the sonar language.

    e.g. ``──●──[ DISCUSSION · TURN 3 ]──────────────── ·· ─ ·``
    Phase color follows the theme (BRIEFING accent, DISCUSSION primary,
    DECISION emphasis, ADJUDICATION success).
    """
    colors = theme_manager.get_colors()
    phase = phase.upper()
    if seed is None:
        seed = f"phase-{phase}-{turn}"
    rng = _rng(seed, "phase")

    phase_colors = {
        "BRIEFING": colors["accent"],
        "DISCUSSION": colors["primary"],
        "DECISION": colors["emphasis"],
        "ADJUDICATION": colors["success"],
    }
    color = phase_colors.get(phase, colors["accent"])

    label = phase if turn is None else f"{phase} · TURN {turn}"
    text = Text("──", style=colors["muted"])
    text.append("●", style=f"{color} bold")
    text.append("──", style=colors["muted"])
    text.append("[ ", style=colors["muted"])
    text.append(label, style=f"{color} bold")
    text.append(" ]", style=colors["muted"])

    # Solid rule that fades out into faint sonar returns on the right
    tail_len = 12
    fill = width - text.cell_len - tail_len
    if fill > 0:
        text.append("─" * fill, style=colors["muted"])
    for i in range(tail_len):
        frac = (i + 1) / tail_len
        r = rng.random()
        ch = "─" if r > frac else ("·" if r > frac * 0.4 else " ")
        text.append(ch, style=colors["muted"])
    return _no_wrap(text)


# ---------------------------------------------------------------------------
# Boot / loading screen
# ---------------------------------------------------------------------------

_BOOT_LINES = [
    ("TUMAN/COBRA SECURE TERMINAL ── NODE WHITEHALL/A", None),
    ("CHANNEL HANDSHAKE", "OK"),
    ("LINK ESTABLISHED ── NORTHWOOD JOC", "OK"),
    ("CLEARANCE VERIFIED: TOP SECRET ── UK EYES ONLY", None),
    ("DECRYPTING BRIEFING PACKAGE", "OK"),
    ("OPERATION TUMAN ── FILE OPEN", None),
]


def _boot_line(label: str, status: Optional[str], first: bool,
               width: int) -> Text:
    """One boot line: ``> LABEL ············· OK`` with dot leaders."""
    colors = theme_manager.get_colors()
    text = Text()
    if first:
        text.append(label, style=f"{colors['accent']} bold")
        return _no_wrap(text)
    text.append("> ", style=colors["muted"])
    text.append(label, style=colors["normal"] if "normal" in colors
                else colors["highlight"])
    if status:
        leaders = width - len(label) - len(status) - 20
        if leaders > 2:
            text.append(" " + "·" * leaders + " ", style=colors["muted"])
        else:
            text.append(" ")
        text.append(status, style=f"{colors['success']} bold")
    return _no_wrap(text)


def boot_sequence_frames(seed: Seed = 0,
                         width: int = DEFAULT_WIDTH) -> List[Group]:
    """Frames of the secure-terminal boot for animated use (e.g. rich Live).

    Frame N reveals the first N boot lines over a fog band that thins as the
    sequence progresses; the final frame is the cleared-fog masthead.
    """
    frames: List[Group] = []
    n = len(_BOOT_LINES)
    for k in range(1, n + 1):
        colors = theme_manager.get_colors()
        parts: List[Text] = [classification_strip(seed=seed, width=width,
                                                  edge="bare")]
        for i in range(k):
            label, status = _BOOT_LINES[i]
            parts.append(_boot_line(label, status, i == 0, width))
        density = 0.75 * (1 - k / (n + 1))
        parts.append(Text())
        parts.append(fog_band(width, 3, density, _seed_int(seed, f"boot-{k}")))
        frames.append(Group(*parts))
    # Fog fully cleared: the masthead resolves out of it
    final: List[Union[Text, Group]] = [
        classification_strip(seed=seed, width=width, edge="bare")]
    for i, (label, status) in enumerate(_BOOT_LINES):
        final.append(_boot_line(label, status, i == 0, width))
    final.append(Text())
    final.append(masthead(width, seed))
    frames.append(Group(*final))
    return frames


def boot_screen(seed: Seed = 0, width: int = DEFAULT_WIDTH) -> Group:
    """Single static render of the completed boot (for non-TTY output)."""
    return boot_sequence_frames(seed, width)[-1]


def animate_boot(console: Optional[Console] = None, seed: Seed = 0,
                 delay: float = 0.25, width: int = DEFAULT_WIDTH) -> None:
    """Print the boot sequence line by line with a delay between lines.

    Prints the static ``boot_screen`` instantly when stdout is not a TTY
    (pipes, CI) so redirected output stays clean.
    """
    if console is None:
        console = Console()
    if not sys.stdout.isatty():
        console.print(boot_screen(seed, width))
        return
    console.print(classification_strip(seed=seed, width=width, edge="bare"))
    for i, (label, status) in enumerate(_BOOT_LINES):
        console.print(_boot_line(label, status, i == 0, width))
        time.sleep(delay)
    console.print()
    # Fog thins across three quick bands, then the masthead resolves
    for step, density in enumerate((0.7, 0.45, 0.2)):
        console.print(fog_band(width, 1, density,
                               _seed_int(seed, f"clear-{step}")))
        time.sleep(delay)
    console.print(masthead(width, seed))


# ---------------------------------------------------------------------------
# Debrief / ending frame
# ---------------------------------------------------------------------------

def debrief_frame(title: str, subtitle: Optional[str] = None,
                  lines: Optional[List[str]] = None, seed: Seed = 0,
                  width: int = DEFAULT_WIDTH,
                  header: str = "AFTER ACTION ── OPERATION TUMAN") -> Group:
    """Heavier double-ruled frame for campaign endings and the debrief.

    Args:
        title: Ending headline (centered, emphasised).
        subtitle: Optional verdict line under the title.
        lines: Optional body lines (clipped to the frame's inner width).
        seed: Drives the reference code and the interior fog trim.
    """
    colors = theme_manager.get_colors()
    code = reference_code(seed)
    inner = width - 4

    def wall(content: Text) -> Text:
        t = Text("║ ", style=colors["secondary"])
        t.append_text(content)
        pad = inner - content.cell_len
        if pad > 0:
            t.append(" " * pad)
        t.append(" ║", style=colors["secondary"])
        return _no_wrap(t)

    def centered(s: str, style: str) -> Text:
        s = _clip(s, inner)
        pad = " " * max(0, (inner - len(s)) // 2)
        return Text(pad).append(s, style=style)

    # ╔═[ HEADER ]═══════...═══[ CODE ]═╗
    head = Text("╔═", style=colors["secondary"])
    head.append("[ ", style=colors["secondary"])
    head.append(_clip(header, width - len(code) - 13),
                style=f"{colors['danger']} bold")
    head.append(" ]", style=colors["secondary"])
    fill = width - head.cell_len - len(code) - 6  # "[ " + " ]═╗"
    head.append("═" * max(1, fill), style=colors["secondary"])
    head.append("[ ", style=colors["secondary"])
    head.append(code, style=colors["warning"])
    head.append(" ]═╗", style=colors["secondary"])

    # Interior fog trim row, kept inside the walls
    fog_row = _fog_rows(_rng(seed, "debrief-fog"), inner, 1, 0.35)[0]

    parts: List[Text] = [
        _no_wrap(head),
        wall(Text(fog_row, style=colors["muted"])),
        wall(Text()),
        wall(centered(title.upper(), f"{colors['emphasis']} bold")),
    ]
    if subtitle:
        parts.append(wall(centered(subtitle, colors["highlight"])))
    parts.append(wall(Text()))
    for line in lines or []:
        parts.append(wall(Text(_clip(line, inner),
                               style=colors.get("normal", "default"))))
    if lines:
        parts.append(wall(Text()))
    parts.append(wall(Text(fog_row, style=colors["muted"])))
    foot = Text("╚" + "═" * (width - 2) + "╝", style=colors["secondary"])
    parts.append(_no_wrap(foot))
    return Group(*parts)
