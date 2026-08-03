"""Operation Tuman between-turn interstitials.

Short (3-6s, skippable) LucasArts-style ASCII vignettes played between
turns: little pieces of Whitehall business-as-usual staged in the fog +
signals-room language of ``cli.aesthetics``. Each one has a character, a
timing, and a punchline - and the pause before the punchline is the joke.

The five launch vignettes:

* ``tea_round``   - the aide's tea trolley crosses beneath the
  classification strip; five cups labelled CDS/NSA/FS/HS/AG; the CDS cup
  rattles harder as ``escalation`` rises. Above 80 the aide simply keeps
  walking.
* ``periscope``   - a periscope rises out of a fog bank, sweeps left and
  right, points its lens straight at the viewer for a beat, crash-dives.
  Ripples close the scene.
* ``teleprinter`` - a JIC memo chatters out line by line with progressively
  heavier █ redaction until the final paragraph is solid black, leaving
  "PM EYES ONLY" and a tea-ring ( ) stain.
* ``red_phone``   - the [ MOSCOW DIRECT ] phone blinks; the Downing Street
  cat sits on it; a shooing hand achieves a two-column relocation; the
  phone stops blinking the exact frame it is answered.
* ``radar_room``  - a radar sweep with contact blips; one blip, on close
  approach, resolves to a seagull and exits screen-left. A formal
  complaint is lodged.

Conventions (shared with ``cli.cinematics``):

* Frame content is deterministic per ``seed`` (plus ``escalation`` where a
  vignette uses it); only timing touches the wall clock.
* Any keypress skips to the final frame (via the cinematics player).
* Non-TTY stdout prints a single characteristic still - zero sleeps.
* Theme colors are read from ``cli.theme.theme_manager`` at build time;
  all glyphs are ASCII/box-drawing/geometric (<= U+25FF, cell width 1);
  all rows are no-wrap/crop at ``DEFAULT_WIDTH``.
"""

from __future__ import annotations

import math
from typing import Callable, Dict, List, Optional, Tuple, Union

from rich.console import Console, Group
from rich.text import Text

from cli import aesthetics as ae
from cli import cinematics as cin
from cli.aesthetics import DEFAULT_WIDTH, Seed, _rng
from cli.theme import theme_manager

Frame = cin.Frame
Renderable = Union[Text, Group]
Builder = Callable[[Seed, int, int], Tuple[List[Frame], Renderable]]


# ---------------------------------------------------------------------------
# Canvas: a fixed-size (char, style) grid the vignettes paint sprites onto
# ---------------------------------------------------------------------------

class _Canvas:
    """Fixed width x height cell grid; every ``put`` clips at the edges, so
    sprites can enter and exit the frame without any bounds bookkeeping."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid: List[List[cin.Cell]] = [
            [(" ", None) for _ in range(width)] for _ in range(height)]

    def put(self, row: int, col: int, s: str, style: Optional[str] = None,
            transparent: bool = True) -> None:
        """Paint string ``s`` at (row, col). Spaces are transparent unless
        ``transparent=False`` (so sprites don't punch holes in scenery)."""
        if not 0 <= row < self.height:
            return
        line = self.grid[row]
        for i, ch in enumerate(s):
            c = col + i
            if 0 <= c < self.width and not (transparent and ch == " "):
                line[c] = (ch, style)

    def center(self, row: int, s: str, style: Optional[str] = None) -> None:
        self.put(row, (self.width - len(s)) // 2, s, style)

    def hline(self, row: int, ch: str = "─",
              style: Optional[str] = None) -> None:
        self.put(row, 0, ch * self.width, style, transparent=False)

    def group(self, *top: Renderable) -> Group:
        rows = [cin._row_text(r) for r in self.grid]
        return Group(*top, *rows)


def _ink(colors: Dict[str, str]) -> str:
    """Primary-text style; not every theme defines the ``normal`` key."""
    return colors.get("normal", colors.get("highlight", "default"))


# ---------------------------------------------------------------------------
# 1. The Tea Round
# ---------------------------------------------------------------------------

_TEA_LABELS = ("CDS", "NSA", "FS", "HS", "AG")
_TEA_CUP_COLS = (4, 11, 17, 23, 29)     # cup columns relative to trolley
_TEA_TW = 34                            # trolley width


def _tea_rattle_amp(escalation: int) -> int:
    """CDS cup rattle amplitude in columns, scaled from escalation 0-100."""
    if escalation < 15:
        return 0
    if escalation < 50:
        return 1
    if escalation <= 80:
        return 2
    return 3


def _tea_stage(seed: Seed, width: int, escalation: int, phase: int,
               trolley_x: Optional[int], serving: bool, pm_cup: bool,
               caption: str = "", caption_style: Optional[str] = None,
               ) -> Group:
    """One tea-round frame: strip on top, trolley scene, caption row.

    Rows: 0 rattle-ticks/steam, 1 labels, 2 cups, 3 trolley top, 4 body,
    5 wheels, 6 floor, 7 caption. ``trolley_x`` None = trolley off stage.
    """
    colors = theme_manager.get_colors()
    cv = _Canvas(width, 8)
    cv.hline(6, "─", colors["muted"])
    amp = _tea_rattle_amp(escalation)
    rng = _rng(seed, f"tea-rattle-{phase}")

    if trolley_x is not None:
        x = trolley_x
        # Chassis
        cv.put(3, x, "┌" + "─" * (_TEA_TW - 2) + "┐", colors["secondary"])
        body = list(" " * (_TEA_TW - 2))
        body[2:5] = "▐█▌"                       # the urn
        body[10:21] = "T E A  ─  1"
        body[21:24] = "600"
        cv.put(4, x, "│", colors["secondary"])
        cv.put(4, x + 1, "".join(body), colors["muted"])
        cv.put(4, x + _TEA_TW - 1, "│", colors["secondary"])
        wheels = list("└" + "─" * (_TEA_TW - 2) + "┘")
        wheel_ch = "○" if phase % 2 == 0 else "◎"
        wheels[4] = wheel_ch
        wheels[_TEA_TW - 5] = wheel_ch
        cv.put(5, x, "".join(wheels), colors["secondary"])
        # Cups and labels; the CDS cup (and label) jitter with escalation
        dx = rng.randint(-amp, amp) if amp else 0
        for i, lab in enumerate(_TEA_LABELS):
            off = dx if i == 0 else 0
            cup_c = x + _TEA_CUP_COLS[i] + off
            style = colors["warning"] if (i == 0 and amp) else _ink(colors)
            cv.put(2, cup_c, "⊔", style)
            cv.put(1, x + _TEA_CUP_COLS[i] - len(lab) // 2 + off, lab,
                   colors["muted"])
        # Rattle ticks over the CDS cup
        if amp:
            tick_c = x + _TEA_CUP_COLS[0] + dx
            if phase % 2 == 0:
                cv.put(0, tick_c - 1, "'", colors["warning"])
            else:
                cv.put(0, tick_c + 1, "'", colors["warning"])
            if amp >= 2:
                cv.put(0, tick_c + (1 if phase % 2 == 0 else -1), "`",
                       colors["warning"])
        # Steam over the served cups while paused
        if serving:
            for i in range(1, 5):
                if (phase + i) % 2 == 0:
                    cv.put(0, x + _TEA_CUP_COLS[i], "~", colors["muted"])
        # The aide, pushing from behind (screen left)
        ax = x - 4
        cv.put(2, ax, "o", _ink(colors))
        cv.put(3, ax, "├──", _ink(colors))
        cv.put(4, ax, "│", _ink(colors))
        legs = "∧" if (phase % 2 == 0 and not serving) else "│"
        cv.put(5, ax, legs, _ink(colors))

    if pm_cup:
        # The cup set down on the floor for the player, clear of the
        # trolley's track (it parks at (width - _TEA_TW) // 2 when serving)
        c = (width - _TEA_TW) // 2 - 8
        cv.put(4, c - 1, "PM", colors["highlight"])
        cv.put(5, c, "⊔", colors["highlight"])
        if phase % 2 == 0:
            cv.put(3, c, "~", colors["muted"])

    if caption:
        cv.center(7, caption, caption_style or colors["muted"])

    strip = ae.classification_strip(seed=seed, width=width, edge="bare")
    return cv.group(strip)


def _tea_round(seed: Seed, escalation: int,
               width: int) -> Tuple[List[Frame], Renderable]:
    frames: List[Frame] = []
    start = -_TEA_TW - 8
    end = width + 6
    center = (width - _TEA_TW) // 2
    phase = 0

    def stage(**kw) -> Group:
        return _tea_stage(seed, width, escalation, phase, **kw)

    if escalation > 80:
        # No stop. The aide has read the same telegrams you have.
        steps = 26
        for i in range(steps):
            x = round(start + (end - start) * (i + 1) / steps)
            frames.append((stage(trolley_x=x, serving=False, pm_cup=False),
                           0.08))
            phase += 1
        # The pause before the punchline is the joke.
        empty = stage(trolley_x=None, serving=False, pm_cup=False)
        frames.append((empty, 0.55))
        frames.append((empty, 0.55))
        colors = theme_manager.get_colors()
        final = _tea_stage(seed, width, escalation, phase, trolley_x=None,
                           serving=False, pm_cup=False,
                           caption="THE TROLLEY DID NOT STOP.",
                           caption_style=f"{colors['highlight']} bold")
        frames.append((final, 1.30))
        return frames, final

    # Roll in
    for i in range(12):
        x = round(start + (center - start) * (i + 1) / 12)
        frames.append((stage(trolley_x=x, serving=False, pm_cup=False), 0.07))
        phase += 1
    # The tea round itself: steam, rattle, and the PM's cup set down
    for k in range(9):
        frames.append((stage(trolley_x=center, serving=True, pm_cup=(k >= 4),
                             caption="THE TEA ROUND ── 16:00 SHARP"), 0.11))
        phase += 1
    frames.append((stage(trolley_x=center, serving=True, pm_cup=True,
                         caption="THE TEA ROUND ── 16:00 SHARP"), 0.30))
    # Roll out, leaving one cup behind
    for i in range(12):
        x = round(center + (end - center) * (i + 1) / 12)
        frames.append((stage(trolley_x=x, serving=False, pm_cup=True), 0.07))
        phase += 1
    # Beat, then the tag
    frames.append((stage(trolley_x=None, serving=False, pm_cup=True), 0.50))
    colors = theme_manager.get_colors()
    final = _tea_stage(seed, width, escalation, phase, trolley_x=None,
                       serving=False, pm_cup=True,
                       caption="YOURS, PRIME MINISTER.",
                       caption_style=f"{colors['highlight']} bold")
    frames.append((final, 1.20))
    return frames, final


# ---------------------------------------------------------------------------
# 2. Periscope
# ---------------------------------------------------------------------------

def _peri_stage(seed: Seed, width: int, escalation: int, phase: int,
                head_row: Optional[int], head: str,
                ripples: Tuple[int, ...] = (), splash: bool = False,
                caption: str = "", lens_style: Optional[str] = None,
                ) -> Group:
    """One periscope frame.

    Rows: 0-2 sky (mast/head), 3-4 fog bank, 5 waterline, 6-7 open sea,
    8 blank, 9 caption. ``head_row`` None = submerged.
    """
    colors = theme_manager.get_colors()
    cv = _Canvas(width, 10)
    rng = _rng(seed, "peri-layout")
    px = width // 2 + rng.randint(-14, 14)

    # Fog bank hugging the water (thicker as the world worsens)
    field = cin._FogField(seed, "peri-fog", width, 2)
    style_map = cin._fog_style_map()
    density = 0.40 + min(100, max(0, escalation)) * 0.002
    for r in (3, 4):
        for c in range(width):
            ch = field.char(r - 3, c, phase * 2, density)
            if ch != " ":
                cv.put(r, c, ch, style_map.get(ch))

    # Waterline, drifting slowly
    wrng = _rng(seed, "peri-water")
    water = [wrng.choice("≈~≈─~≈") for _ in range(width + 48)]
    off = (phase // 2) % 48
    cv.put(5, 0, "".join(water[off:off + width]), colors["secondary"],
           transparent=False)
    # Sparse open-sea returns
    srng = _rng(seed, "peri-sea")
    for r in (6, 7):
        for _ in range(width // 12):
            cv.put(r, srng.randrange(width), "·", colors["muted"])

    # Ripple rings on the waterline after the dive
    for i, radius in enumerate(ripples):
        style = colors["secondary"] if i == len(ripples) - 1 \
            else colors["muted"]
        cv.put(5, px - radius, "(", style)
        cv.put(5, px + radius, ")", style)

    if splash:
        cv.put(4, px - 2, "∴", colors["secondary"])
        cv.put(4, px + 2, "∴", colors["secondary"])
        cv.put(3, px, "·", colors["muted"])

    # Mast and head
    if head_row is not None:
        for r in range(head_row + 1, 5):
            cv.put(r, px, "║", _ink(colors))
        lens = lens_style or f"{colors['danger']} bold"
        if head == "up":
            cv.put(head_row, px, "●", lens)
        elif head == "left":
            cv.put(head_row, px - 2, "●", lens)
            cv.put(head_row, px - 1, "─┐", _ink(colors))
        elif head == "right":
            cv.put(head_row, px, "┌─", _ink(colors))
            cv.put(head_row, px + 2, "●", lens)
        elif head == "viewer":
            cv.put(head_row, px - 1, "(", _ink(colors))
            cv.put(head_row, px, "●", lens)
            cv.put(head_row, px + 1, ")", _ink(colors))
        elif head == "glint":
            cv.put(head_row, px - 1, "(", _ink(colors))
            cv.put(head_row, px, "◉", f"{colors['warning']} bold")
            cv.put(head_row, px + 1, ")", _ink(colors))

    if caption:
        cv.center(9, caption, colors["muted"])
    return cv.group()


def _periscope(seed: Seed, escalation: int,
               width: int) -> Tuple[List[Frame], Renderable]:
    frames: List[Frame] = []
    phase = 0

    def stage(**kw) -> Group:
        return _peri_stage(seed, width, escalation, phase, **kw)

    def add(duration: float, **kw) -> None:
        nonlocal phase
        frames.append((stage(**kw), duration))
        phase += 1

    # Rise out of the fog bank
    for head_row in (4, 3, 2):
        add(0.15, head_row=head_row, head="up")
    # Sweep: left... right...
    add(0.28, head_row=2, head="left")
    add(0.30, head_row=2, head="left")
    add(0.28, head_row=2, head="right")
    add(0.30, head_row=2, head="right")
    # ...and straight at you. Hold it. Hold it.
    add(0.50, head_row=2, head="viewer")
    add(0.14, head_row=2, head="glint")
    add(0.55, head_row=2, head="viewer")
    # Crash-dive (fast) and splash
    add(0.06, head_row=4, head="up")
    add(0.14, head_row=None, head="", splash=True)
    # Ripples widen and fade
    for rings in ((2,), (2, 4), (4, 7), (7, 10), (10, 14)):
        add(0.13, head_row=None, head="", ripples=rings)
    # Calm sea, then the log entry
    add(0.40, head_row=None, head="")
    final = _peri_stage(seed, width, escalation, phase, head_row=None,
                        head="",
                        caption="── SIGHTING REPORTED ── BY BOTH PARTIES ──")
    frames.append((final, 1.10))
    return frames, final


# ---------------------------------------------------------------------------
# 3. The Teleprinter
# ---------------------------------------------------------------------------

_MEMO_HEADER = ("FROM: JIC LONDON ── FLASH ── MOST IMMEDIATE",
                "TO:   PM ── COPY: NOBODY")
_MEMO_LINES = (
    "1. NORTHERN FLEET UNITS DEPARTED KOLA ANCHORAGES AT 0311 LOCAL.",
    "2. INTENT ASSESSED AS EXERCISE COVER FOR FORWARD DEPLOYMENT.",
    "3. HMG OPTIONS REVIEWED: SHADOW, SIGNAL, OR SIT VERY STILL.",
    "4. CABINET APPETITE FOR OPTIONS ONE AND TWO REMAINS LIMITED.",
    "5. FURTHER PARTICULARS FOLLOW BY SECURE BAG.",
)
_MEMO_REDACTION = (0.15, 0.40, 0.65, 0.90, 1.0)


def _memo_redacted(seed: Seed) -> List[str]:
    """The memo lines with seeded, progressively heavier redaction.

    Each line blacks out (at least) its target fraction of body characters,
    choosing which words go under the bar in seeded order - so the censor
    always gets bolder line by line, but never the same way twice.
    """
    rng = _rng(seed, "tele-redact")
    out = []
    for line, frac in zip(_MEMO_LINES, _MEMO_REDACTION):
        words = line.split(" ")
        body = words[1:]                     # the numbering survives
        order = list(range(len(body)))
        rng.shuffle(order)
        target = frac * sum(len(w) for w in body)
        covered = 0.0
        redact = set()
        for idx in order:
            if covered >= target:
                break
            redact.add(idx)
            covered += len(body[idx])
        kept = [words[0]] + ["█" * len(w) if i in redact else w
                             for i, w in enumerate(body)]
        out.append(" ".join(kept))
    # The final paragraph goes fully black, edge to edge
    out[-1] = out[-1].split(" ")[0] + " " + "█" * 58
    return out


def _tele_stage(seed: Seed, width: int, shown: List[str], cursor: Tuple[int,
                int], stamped: bool, ring: bool) -> Group:
    """One teleprinter frame.

    Rows: 0-1 header, 2 blank, 3-7 memo lines, 8 blank, 9 stamp row.
    ``shown`` holds the visible prefix of each memo row; ``cursor`` is the
    (row, col) of the print head (row -1 = parked).
    """
    colors = theme_manager.get_colors()
    cv = _Canvas(width, 10)
    margin = 4
    cv.put(0, margin, _MEMO_HEADER[0], colors["muted"])
    cv.put(1, margin, _MEMO_HEADER[1], colors["muted"])
    for i, prefix in enumerate(shown):
        cv.put(3 + i, margin, prefix, _ink(colors))
    crow, ccol = cursor
    if crow >= 0:
        cv.put(3 + crow, margin + ccol, "▌", colors["accent"])
    if stamped:
        cv.center(9, "P M   E Y E S   O N L Y",
                  f"{colors['danger']} bold")
    if ring:
        # Someone rested a cup on the blackout paragraph
        cv.put(7, width - 16, "( )", colors["warning"], transparent=False)
    strip = ae.classification_strip(seed=seed, width=width, edge="bare")
    return cv.group(strip)


def _teleprinter(seed: Seed, escalation: int,
                 width: int) -> Tuple[List[Frame], Renderable]:
    frames: List[Frame] = []
    lines = _memo_redacted(seed)
    rng = _rng(seed, "tele-chatter")
    shown = ["" for _ in lines]

    def stage(cursor=(-1, 0), stamped=False, ring=False) -> Group:
        return _tele_stage(seed, width, list(shown), cursor, stamped, ring)

    # Header chatters in almost at once
    frames.append((_tele_stage(seed, width, [""] * len(lines), (-1, 0),
                               False, False), 0.22))
    # Each line types in bursts; the carriage return is its own beat
    for i, line in enumerate(lines):
        col = 0
        while col < len(line):
            col = min(len(line), col + rng.randint(5, 10))
            shown[i] = line[:col]
            # Chatter rhythm: burst, burst, breath
            frames.append((stage(cursor=(i, col)),
                           0.045 if rng.random() < 0.75 else 0.08))
        # Carriage return: head snaps back, platen advances
        frames.append((stage(cursor=(i + 1, 0) if i + 1 < len(lines)
                             else (-1, 0)), 0.15))
    # The machine stops. Read what's left of it.
    frames.append((stage(), 0.60))
    # Stamp...
    frames.append((stage(stamped=True), 0.55))
    # ...and someone's tea has already been here
    final = stage(stamped=True, ring=True)
    frames.append((final, 1.25))
    return frames, final


# ---------------------------------------------------------------------------
# 4. The Red Phone
# ---------------------------------------------------------------------------

def _phone_stage(seed: Seed, width: int, phase: int, ringing: bool,
                 handset: bool, cat_x: Optional[int], hand_x: Optional[int],
                 shoo: bool = False, puff_x: Optional[int] = None,
                 caption: str = "", answered: bool = False) -> Group:
    """One red-phone frame.

    Rows: 0 label, 1-2 handset (and cat, and hand), 3-5 body, 6 table,
    7 blank, 8 caption. ``cat_x``/``hand_x`` are absolute columns.
    """
    colors = theme_manager.get_colors()
    cv = _Canvas(width, 9)
    pw = 30
    px = (width - pw) // 2

    blink_on = ringing and phase % 2 == 0
    lamp_style = f"{colors['danger']} bold" if blink_on else colors["muted"]
    label_style = f"{colors['danger']} bold" if blink_on else colors["muted"]

    cv.center(0, "[ MOSCOW DIRECT ]", label_style)
    # Body
    cv.put(3, px, "┌" + "─" * (pw - 2) + "┐", colors["secondary"])
    cv.put(4, px, "│", colors["secondary"])
    cv.put(4, px + pw - 1, "│", colors["secondary"])
    cv.put(4, px + 3, "●" if not answered else "○", lamp_style)
    cv.put(4, px + 6, "К Р Е М Л Ь", colors["muted"])
    cv.put(5, px, "└" + "─" * (pw - 2) + "┘", colors["secondary"])
    cv.hline(6, "─", colors["muted"])
    # Handset resting across the left of the cradle, cups down
    if handset:
        hx = px + 2
        cv.put(1, hx + 1, "┌" + "─" * 10 + "┐", _ink(colors))
        cv.put(2, hx, "┌┘", _ink(colors))
        cv.put(2, hx + 12, "└┐", _ink(colors))
    # Ring marks while it rings
    if blink_on:
        cv.put(3, px - 4, "((", colors["danger"])
        cv.put(4, px - 3, "(", colors["danger"])
        cv.put(3, px + pw + 2, "))", colors["danger"])
        cv.put(4, px + pw + 2, ")", colors["danger"])
    # The cat, loafed on top of the phone body, unbothered
    if cat_x is not None:
        cv.put(1, cat_x + 1, "/\\_/\\", colors["highlight"])
        tail = "~" if phase % 4 < 2 else ","
        cv.put(2, cat_x, "( -.- )" + tail, colors["highlight"])
    # The shooing hand, entering screen-right
    if hand_x is not None:
        cv.put(2, hand_x, "≡", _ink(colors))
        cv.put(2, hand_x + 1, "━" * max(0, width - hand_x - 1),
               _ink(colors))
        if shoo:
            cv.put(1, hand_x + (0 if phase % 2 == 0 else 2), "~",
                   colors["muted"])
    if puff_x is not None:
        cv.put(2, puff_x, "∙", colors["muted"])
    if caption:
        cv.center(8, caption, f"{colors['highlight']} bold"
                  if answered else colors["muted"])
    return cv.group()


def _red_phone(seed: Seed, escalation: int,
               width: int) -> Tuple[List[Frame], Renderable]:
    frames: List[Frame] = []
    phase = 0
    pw = 30
    px = (width - pw) // 2
    cat_home = px + 17           # loafed on the right half of the phone
    rng = _rng(seed, "phone")
    # Seeded flourish: which way the tail starts
    phase = rng.randrange(2)

    def add(duration: float, **kw) -> None:
        nonlocal phase
        frames.append((_phone_stage(seed, width, phase, **kw), duration))
        phase += 1

    # It rings. And rings.
    for _ in range(4):
        add(0.16, ringing=True, handset=True, cat_x=None, hand_x=None)
    # The cat is already there. The cat was always going to be there.
    for _ in range(4):
        add(0.16, ringing=True, handset=True, cat_x=cat_home, hand_x=None)
    # A hand enters
    for hx in (width - 8, cat_home + 13, cat_home + 10):
        add(0.08, ringing=True, handset=True, cat_x=cat_home, hand_x=hx)
    # Shoo. Shoo.
    for _ in range(4):
        add(0.11, ringing=True, handset=True, cat_x=cat_home,
            hand_x=cat_home + 10, shoo=True)
    # The beat: nothing happens. The hand waits. The cat considers.
    add(0.30, ringing=True, handset=True, cat_x=cat_home,
        hand_x=cat_home + 10)
    add(0.30, ringing=True, handset=True, cat_x=cat_home,
        hand_x=cat_home + 10)
    # The concession: two columns
    add(0.14, ringing=True, handset=True, cat_x=cat_home + 2,
        hand_x=cat_home + 10, puff_x=cat_home + 1)
    add(0.30, ringing=True, handset=True, cat_x=cat_home + 2,
        hand_x=cat_home + 12)
    # Hand withdraws, honour satisfied
    add(0.09, ringing=True, handset=True, cat_x=cat_home + 2,
        hand_x=width - 10)
    add(0.09, ringing=True, handset=True, cat_x=cat_home + 2, hand_x=None)
    # Still ringing. Of course it's still ringing.
    for _ in range(3):
        add(0.20, ringing=True, handset=True, cat_x=cat_home + 2,
            hand_x=None)
    # Answered: handset lifted, and the blinking stops THIS exact frame
    add(0.55, ringing=False, handset=False, cat_x=cat_home + 2, hand_x=None,
        answered=True)
    final = _phone_stage(seed, width, phase, ringing=False, handset=False,
                         cat_x=cat_home + 2, hand_x=None, answered=True,
                         caption="LINE OPEN. CAT UNMOVED.")
    frames.append((final, 1.25))
    return frames, final


# ---------------------------------------------------------------------------
# 5. Radar Room
# ---------------------------------------------------------------------------

def _radar_geometry(width: int) -> Tuple[int, int, float, float]:
    cx = width // 2
    cy = 5                      # scope rows are 1..9, centre row 5
    return cx, cy, 17.0, 4.2    # rx, ry


def _radar_stage(seed: Seed, width: int, sweep: float,
                 blips: List[Tuple[float, float, bool]],
                 gull: Optional[Tuple[int, int, int]],
                 log1: str = "", log2: str = "") -> Group:
    """One radar frame.

    Rows: 0 header, 1-9 scope, 10-11 log lines. ``blips`` are
    (theta, r, flash) contacts; ``gull`` is (row, col, flap-phase).
    """
    colors = theme_manager.get_colors()
    cv = _Canvas(width, 12)
    cx, cy, rx, ry = _radar_geometry(width)

    cv.center(0, "[ NORTHWOOD JOC ── AIR PICTURE ]", colors["muted"])
    # Scope ring
    for r in range(1, 10):
        for c in range(cx - int(rx) - 2, cx + int(rx) + 3):
            d = ((c - cx) / rx) ** 2 + ((r - cy) / ry) ** 2
            if abs(d - 1.0) < 0.13:
                cv.put(r, c, "·", colors["muted"])
    # Sweep arm with two-step afterglow
    for k, (ch, style) in enumerate(
            (("▒", colors["secondary"]), ("░", colors["muted"]),
             ("·", colors["muted"]))):
        a = sweep - k * 0.38
        rr = 0.14
        while rr < 0.97:
            c = cx + int(round(rx * rr * math.cos(a)))
            r = cy + int(round(ry * rr * math.sin(a)))
            if 1 <= r <= 9:
                cv.put(r, c, ch, style)
            rr += 0.06
    cv.put(cy, cx, "+", colors["accent"])
    # Contacts
    for theta, radius, flash in blips:
        c = cx + int(round(rx * radius * math.cos(theta)))
        r = cy + int(round(ry * radius * math.sin(theta)))
        if flash:
            cv.put(r, c, "●", f"{colors['primary']} bold")
        else:
            cv.put(r, c, "•", colors["secondary"])
    # The gull, at the moment of its unmasking (and departure)
    if gull is not None:
        row, col, flap = gull
        cv.put(row, col, "~v~" if flap % 2 == 0 else "_w_",
               f"{colors['warning']} bold")
    if log1:
        cv.put(10, 2, log1, colors["muted"])
    if log2:
        cv.put(11, 2, log2, f"{colors['success']}")
    return cv.group()


def _radar_room(seed: Seed, escalation: int,
                width: int) -> Tuple[List[Frame], Renderable]:
    frames: List[Frame] = []
    rng = _rng(seed, "radar")
    cx, cy, rx, ry = _radar_geometry(width)
    # Two honest contacts...
    b1 = (rng.uniform(0.0, 2 * math.pi), rng.uniform(0.45, 0.8))
    b2 = (rng.uniform(0.0, 2 * math.pi), rng.uniform(0.35, 0.7))
    # ...and one closing from the left-ish sector (so it can exit stage left)
    g_theta = rng.uniform(2.6, 3.7)
    sweep0 = rng.uniform(0.0, 2 * math.pi)
    brg = int(math.degrees(g_theta) % 360)
    log_track = f"> CONTACT 03 ── BRG {brg:03d} ── CLOSING ── TRACK UNSTABLE"
    log_gull = "> CONTACT RECLASSIFIED: GULL (FORMAL COMPLAINT LODGED)"

    def near(sweep: float, theta: float) -> bool:
        return abs((sweep - theta + math.pi) % (2 * math.pi) - math.pi) < 0.55

    n_track = 20
    for i in range(n_track):
        sweep = sweep0 + i * 0.38
        g_r = 0.95 - 0.033 * i
        blips = [(b1[0], b1[1], near(sweep, b1[0])),
                 (b2[0], b2[1], near(sweep, b2[0])),
                 (g_theta, g_r, near(sweep, g_theta))]
        frames.append((_radar_stage(seed, width, sweep, blips, None,
                                    log1=log_track if i >= 8 else ""),
                       0.09))
    # Close approach: the contact resolves. It has feathers.
    g_r = 0.95 - 0.033 * n_track
    g_col = cx + int(round(rx * g_r * math.cos(g_theta)))
    g_row = min(9, max(1, cy + int(round(ry * g_r * math.sin(g_theta)))))
    sweep = sweep0 + n_track * 0.38
    blips2 = [(b1[0], b1[1], False), (b2[0], b2[1], False)]
    frames.append((_radar_stage(seed, width, sweep, blips2,
                                (g_row, g_col, 0), log1=log_track), 0.55))
    # It exits screen-left, flapping, unhurried
    for j in range(1, 7):
        sweep = sweep0 + (n_track + j) * 0.38
        col = g_col - 7 * j
        frames.append((_radar_stage(seed, width, sweep, blips2,
                                    (g_row, col, j) if col > -3 else None,
                                    log1=log_track), 0.10))
    # Beat. The room composes itself.
    sweep = sweep0 + (n_track + 7) * 0.38
    frames.append((_radar_stage(seed, width, sweep, blips2, None,
                                log1=log_track), 0.55))
    # For the record:
    final = _radar_stage(seed, width, sweep0 + (n_track + 8) * 0.38, blips2,
                         None, log1=log_track, log2=log_gull)
    frames.append((final, 1.45))
    return frames, final


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

_BUILDERS: Dict[str, Builder] = {
    "tea_round": _tea_round,
    "periscope": _periscope,
    "teleprinter": _teleprinter,
    "red_phone": _red_phone,
    "radar_room": _radar_room,
}

VIGNETTE_NAMES: Tuple[str, ...] = tuple(_BUILDERS)


def build_interstitial(name: str, seed: Seed = 0, escalation: int = 0,
                       width: int = DEFAULT_WIDTH,
                       ) -> Tuple[List[Frame], Renderable]:
    """Build (animation frames, characteristic final still) for a vignette.

    Deterministic per (name, seed, escalation): every random choice flows
    through a seeded RNG. Durations are data; nothing here sleeps.
    """
    if name not in _BUILDERS:
        raise KeyError(f"unknown interstitial {name!r}; "
                       f"choose from {', '.join(VIGNETTE_NAMES)}")
    escalation = max(0, min(100, int(escalation)))
    return _BUILDERS[name](seed, escalation, width)


def choose_interstitial(seed: Seed = 0, avoid: Optional[str] = None) -> str:
    """Seeded vignette selection; never returns ``avoid`` (the previous
    pick), so consecutive turns always vary."""
    pool = [n for n in VIGNETTE_NAMES if n != avoid] or list(VIGNETTE_NAMES)
    rng = _rng(seed, "interstitial-pick")
    return pool[rng.randrange(len(pool))]


def play_interstitial(console: Optional[Console] = None, seed: Seed = 0,
                      escalation: int = 0, name: Optional[str] = None,
                      avoid: Optional[str] = None,
                      width: int = DEFAULT_WIDTH) -> str:
    """Play one between-turn vignette (3-6s, any-key skip).

    Args:
        console: Target console (defaults to the shared game console).
        seed: Deterministic seed - derive from stable game state.
        escalation: 0-100; tenser board, tenser vignettes.
        name: Force a specific vignette; None = seeded selection.
        avoid: Vignette name to exclude from selection (pass the previous
            turn's pick so the same joke never plays twice in a row).

    Returns:
        The name of the vignette that played (feed back in as ``avoid``).

    Non-TTY stdout prints the vignette's single characteristic still with
    zero sleeps; legacy Windows consoles do the same.
    """
    if name is None:
        name = choose_interstitial(seed, avoid=avoid)
    frames, final = build_interstitial(name, seed=seed,
                                       escalation=escalation, width=width)
    cin._play(frames, final, console)
    return name
