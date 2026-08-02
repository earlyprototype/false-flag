"""Operation Tuman choreographed cinematics.

Animated sequences built on the static primitives in ``cli.aesthetics``:

* ``play_title_sequence`` - the centrepiece. Fog banks drift across the
  frame, the FALSE FLAG masthead *condenses out of the fog* cell by cell in
  a random scatter (the thematic inversion of a binary dissolve), holds
  with a residual "breathing" shimmer, wipes thin, then the classification
  strip stamps in, the tagline types word by word and the secure-terminal
  boot log ticks through its ``····· OK`` lines.
* ``play_scene_stamp`` - intro scene cards assemble fast: chrome first,
  then the title and coordinates strips type in.
* ``play_turn_transition`` - a fog band rolls through the turn banner
  region and clears (~1s).
* ``play_debrief_reveal`` - heavier, slower condense of the after-action
  frame for campaign endings.
* ``setup_banner`` - static compact header for the setup menus.

Conventions (shared with ``cli.aesthetics``):

* Frame *content* is deterministic per seed - every random choice flows
  through a seeded ``Random``. Only timing uses the wall clock.
* Any keypress skips an animation straight to its final frame
  (``cli.keyboard.key_pressed``; non-interactive stdin never blocks).
* When stdout is not a TTY the final frame is printed instantly with zero
  sleeps, matching the repo's non-TTY typewriter fast path, so piped and
  CI runs stay fast and clean.
* Colors are read from ``cli.theme.theme_manager`` at frame-build time.
* All lines are no-wrap/crop, so narrow consoles clip instead of crashing.
"""

from __future__ import annotations

import math
import sys
import time
from io import StringIO
from typing import Iterable, Iterator, List, Optional, Tuple, Union

from rich.console import Console, Group
from rich.style import Style
from rich.text import Text

from cli import aesthetics as ae
from cli.aesthetics import DEFAULT_WIDTH, Seed, _rng, _seed_int
from cli.keyboard import key_pressed
from cli.theme import theme_manager

# A frame is (renderable, seconds to hold it on screen)
Frame = Tuple[Union[Text, Group], float]

# Cell in a captured character grid: (char, style)
Cell = Tuple[str, Optional[Union[str, Style]]]

# "Any key skips": pass every printable ASCII char plus the usual specials
# to key_pressed so whatever the player hits registers as a skip.
_SKIP_KEYS = tuple(chr(c) for c in range(32, 127)) + ("\n", "\r", "\t", "\x1b")


def _interactive() -> bool:
    """True when stdout is a real terminal (animations allowed)."""
    try:
        return sys.stdout.isatty()
    except (AttributeError, ValueError):
        return False


# ---------------------------------------------------------------------------
# Fog field: continuous value-noise the animations sample per frame
# ---------------------------------------------------------------------------

def _fog_char(v: float, density: float) -> str:
    """Map a noise value + density to the fog ramp (same curve as
    aesthetics._fog_rows)."""
    level = v * max(0.0, min(1.0, density)) * 1.7
    if level < 0.16:
        return " "
    if level < 0.38:
        return "·"
    if level < 0.66:
        return "░"
    if level < 0.92:
        return "▒"
    return "▓"


class _FogField:
    """Deterministic smoothed noise field, wider than the viewport so frames
    can slide a window across it - that horizontal slide is the drift."""

    def __init__(self, seed: Seed, salt: str, width: int, height: int,
                 span: int = 160):
        rng = _rng(seed, salt)
        self.width = width
        self.total = width + span
        step = 6
        n_ctrl = self.total // step + 2
        ctrl = [rng.random() for _ in range(n_ctrl)]
        self.rows: List[List[float]] = []
        for _y in range(max(1, height)):
            ctrl = [min(1.0, max(0.0, v + rng.uniform(-0.16, 0.16)))
                    for v in ctrl]
            row = []
            for x in range(self.total):
                i = x / step
                i0 = int(i)
                t = i - i0
                t = (1 - math.cos(t * math.pi)) / 2
                row.append(ctrl[i0] * (1 - t) + ctrl[i0 + 1] * t)
            self.rows.append(row)

    def char(self, r: int, c: int, offset: int, density: float) -> str:
        row = self.rows[r % len(self.rows)]
        return _fog_char(row[(c + offset) % self.total], density)


def _fog_style_map() -> dict:
    colors = theme_manager.get_colors()
    return {
        "·": colors["muted"],
        "░": colors["muted"],
        "▒": colors["secondary"],
        "▓": colors["accent"],
    }


# ---------------------------------------------------------------------------
# Cell-grid capture and re-emission
# ---------------------------------------------------------------------------

def _grid(renderable, width: int) -> List[List[Cell]]:
    """Capture a renderable as a per-cell (char, style) grid.

    Lets the animations reveal any styled aesthetics component cell by cell
    while keeping its exact colors.
    """
    capture = Console(file=StringIO(), width=width, force_terminal=True,
                      legacy_windows=False)
    lines = capture.render_lines(renderable,
                                 capture.options.update_width(width),
                                 pad=True)
    grid: List[List[Cell]] = []
    for segments in lines:
        row: List[Cell] = []
        for seg in segments:
            if seg.control:
                continue
            for ch in seg.text:
                row.append((ch, seg.style))
        row = row[:width]
        row += [(" ", None)] * (width - len(row))
        grid.append(row)
    return grid


def _row_text(cells: Iterable[Cell]) -> Text:
    """Build a no-wrap Text line from cells, merging same-style runs."""
    text = Text()
    run: List[str] = []
    run_style: Optional[Union[str, Style]] = None
    for ch, style in cells:
        if style != run_style and run:
            text.append("".join(run), style=run_style)
            run = []
        run_style = style
        run.append(ch)
    if run:
        text.append("".join(run), style=run_style)
    text.no_wrap = True
    text.overflow = "crop"
    return text


def _smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------------------
# Frame player
# ---------------------------------------------------------------------------

def _frame_ansi(console: Console, renderable) -> str:
    """Render one frame to an ANSI string with per-line clear-to-EOL.

    The trailing ``ESC[K`` on every line erases residue from the previous
    frame when a line shrinks, so redraws never leave ghost glyphs.
    """
    with console.capture() as capture:
        console.print(renderable)
    out = capture.get()
    if out.endswith("\n"):
        out = out[:-1]
    return "\x1b[K\n".join(out.split("\n")) + "\x1b[K\n"


def _play(frames: Iterable[Frame], final, console: Optional[Console] = None,
          skippable: bool = True) -> None:
    """Play frames with cortex-style in-place redraws (cursor-up + rewrite).

    Any keypress skips straight to the final frame. Non-TTY stdout prints
    the final frame instantly with zero sleeps. Raw ANSI redraw is used
    (rather than rich.live.Live) because the game console deliberately runs
    ``force_interactive=False`` for its keyboard model, and Live suppresses
    per-frame refreshes on non-interactive consoles.
    """
    if console is None:
        from cli.rich_ui import console as default_console
        console = default_console
    # Legacy Windows consoles don't speak raw ANSI cursor movement
    if not _interactive() or getattr(console, "legacy_windows", False):
        console.print(final)
        return

    write = console.file.write
    height: Optional[int] = None
    skipped = False
    try:
        write("\x1b[?25l")  # hide cursor for the duration
        for renderable, duration in frames:
            frame_text = _frame_ansi(console, renderable)
            if height is not None:
                write(f"\x1b[{height}F")  # back to the top of the region
            write(frame_text)
            console.file.flush()
            height = frame_text.count("\n")
            deadline = time.monotonic() + duration
            while True:
                if skippable and key_pressed(_SKIP_KEYS):
                    skipped = True
                    break
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                time.sleep(min(0.03, remaining))
            if skipped:
                break
        final_text = _frame_ansi(console, final)
        if height is not None:
            write(f"\x1b[{height}F")
        write(final_text)
        if height is not None and final_text.count("\n") < height:
            write("\x1b[0J")  # final frame shorter than region: clear below
    finally:
        write("\x1b[?25h")  # restore cursor
        console.file.flush()


# ---------------------------------------------------------------------------
# Title sequence
# ---------------------------------------------------------------------------

class _TitleScene:
    """Shared state for the title sequence (frames + final frame).

    Fixed 17-row layout so the Live region never changes height:

        row 0      classification strip (stamps in late)
        rows 1-7   fog margin / masthead block (5 rows) / fog margin
        row 8      blank
        row 9      tagline (types word by word)
        row 10     blank
        rows 11-16 boot log lines
    """

    DRIFT = 2  # fog columns of drift per frame

    def __init__(self, seed: Seed, width: int):
        self.seed = seed
        self.width = width
        self.mast = ae._MASTHEAD_ROWS
        self.mast_h = len(self.mast)
        self.mast_w = len(self.mast[0])
        self.pad_left = max(0, (width - self.mast_w) // 2)
        self.field = _FogField(seed, "title-fog", width, self.mast_h + 2)
        self.pixmap = [(r, c)
                       for r in range(self.mast_h)
                       for c in range(self.mast_w)
                       if self.mast[r][c] != " "]
        _rng(seed, "title-scatter").shuffle(self.pixmap)
        self.revealed = [[False] * self.mast_w for _ in range(self.mast_h)]
        self.n_revealed = 0
        self.frame_no = 0  # drives fog drift
        self.tagline_words = ae._TAGLINE.split()
        self.boot = list(ae._BOOT_LINES)
        # Boot steps: each line first appears bare, then (if it has a
        # status) its dot leaders and OK tick stamp in.
        self.boot_steps: List[Tuple[int, bool]] = []
        for i, (_label, status) in enumerate(self.boot):
            self.boot_steps.append((i, False))
            if status:
                self.boot_steps.append((i, True))

    # -- row builders -------------------------------------------------------

    def _reveal_to(self, n: int) -> None:
        while self.n_revealed < min(n, len(self.pixmap)):
            r, c = self.pixmap[self.n_revealed]
            self.revealed[r][c] = True
            self.n_revealed += 1

    def _mast_rows(self, density: float, offset: int,
                   cleared_above: Optional[int] = None,
                   floor: float = 0.16) -> List[Text]:
        """Rows 1-7: fog margins and the (partially revealed) masthead."""
        colors = theme_manager.get_colors()
        style_map = _fog_style_map()
        mast_style = f"{colors['primary']} bold"
        rows = []
        for fr in range(self.mast_h + 2):
            cells: List[Cell] = []
            mr = fr - 1
            for c in range(self.width):
                mc = c - self.pad_left
                on_mast = 0 <= mr < self.mast_h and 0 <= mc < self.mast_w
                target = on_mast and self.mast[mr][mc] != " "
                if target and self.revealed[mr][mc]:
                    cells.append((self.mast[mr][mc], mast_style))
                    continue
                d = density
                if cleared_above is not None and fr < cleared_above:
                    d = floor
                if target:
                    d = min(1.0, d * 1.35)  # fog clings where letters form
                ch = self.field.char(fr, c, offset, d)
                cells.append((ch, style_map.get(ch)))
            rows.append(_row_text(cells))
        return rows

    def _strip_row(self, stage: str) -> Text:
        colors = theme_manager.get_colors()
        if stage == "off":
            return Text("")
        if stage == "rule":
            t = Text("─" * self.width, style=colors["muted"])
            t.no_wrap = True
            t.overflow = "crop"
            return t
        return ae.classification_strip(seed=self.seed, width=self.width,
                                       edge="bare")

    def _tagline_row(self, n_words: int, cursor: bool = False) -> Text:
        if n_words <= 0:
            return Text("")
        colors = theme_manager.get_colors()
        full = " ".join(self.tagline_words)
        shown = " ".join(self.tagline_words[:n_words])
        pad = " " * max(0, (self.width - len(full)) // 2)
        t = Text(pad)
        t.append(shown, style=colors["muted"])
        if cursor and n_words < len(self.tagline_words):
            t.append(" ▌", style=colors["accent"])
        t.no_wrap = True
        t.overflow = "crop"
        return t

    def _boot_rows(self, steps_done: int) -> List[Text]:
        """One row per boot line; unreached lines render blank."""
        done = self.boot_steps[:max(0, min(steps_done, len(self.boot_steps)))]
        stage_by_line = {}
        for line_i, with_status in done:
            stage_by_line[line_i] = with_status or stage_by_line.get(line_i,
                                                                     False)
        rows = []
        for i, (label, status) in enumerate(self.boot):
            if i not in stage_by_line:
                rows.append(Text(""))
            elif stage_by_line[i]:
                rows.append(ae._boot_line(label, status, i == 0, self.width))
            else:
                rows.append(ae._boot_line(label, None, i == 0, self.width))
        return rows

    def _frame(self, strip: str, mast_rows: List[Text], tag_words: int,
               boot_steps: int, tag_cursor: bool = False) -> Group:
        rows: List[Union[Text, Group]] = [self._strip_row(strip)]
        rows.extend(mast_rows)
        rows.append(Text(""))
        rows.append(self._tagline_row(tag_words, cursor=tag_cursor))
        rows.append(Text(""))
        rows.extend(self._boot_rows(boot_steps))
        return Group(*rows)

    # -- choreography -------------------------------------------------------

    # Stage tuning (frame counts x per-frame seconds):
    #   roll-in    10 x 0.055  fog banks drift in, thickening
    #   condense   28 x 0.055  masthead locks in, scattered, fog thinning
    #   breathe    10 x 0.070  residual fog shimmers around the letters
    #   wipe        7 x 0.060  fog clears top-to-bottom
    #   stamp       2 x ~0.11  classification strip stamps in
    #   tagline     7 x 0.100  types word by word
    #   boot       11 x 0.085  log lines + OK ticks
    #   settle      1 x 0.400
    ROLL_IN, CONDENSE, BREATHE, WIPE = 10, 28, 10, 7
    AMBIENT = 0.62      # peak fog density
    RESIDUAL = 0.24     # density during the breathing hold
    FAINT = 0.15        # fog left behind after the wipe

    def _offset(self) -> int:
        self.frame_no += 1
        return self.frame_no * self.DRIFT

    def frames(self) -> Iterator[Frame]:
        # 1. Fog rolls in
        for i in range(self.ROLL_IN):
            density = self.AMBIENT * (i + 1) / self.ROLL_IN
            yield self._frame("off", self._mast_rows(density, self._offset()),
                              0, 0), 0.055
        # 2. The masthead condenses out of the fog
        for j in range(self.CONDENSE):
            ease = _smoothstep((j + 1) / self.CONDENSE)
            self._reveal_to(int(ease * len(self.pixmap)))
            density = self.AMBIENT * (1 - 0.58 * ease)
            yield self._frame("off", self._mast_rows(density, self._offset()),
                              0, 0), 0.055
        self._reveal_to(len(self.pixmap))
        # 3. Breathing hold: residual fog shimmers
        for k in range(self.BREATHE):
            pulse = self.RESIDUAL + 0.10 * math.sin(2 * math.pi * k
                                                    / self.BREATHE)
            yield self._frame("off", self._mast_rows(pulse, self._offset()),
                              0, 0), 0.07
        # 4. Fog thins, wiping top to bottom
        for w in range(1, self.WIPE + 1):
            rows = self._mast_rows(self.RESIDUAL, self._offset(),
                                   cleared_above=w, floor=self.FAINT)
            yield self._frame("off", rows, 0, 0), 0.06
        # Post-wipe: fog frozen faint; later stages reuse this exact state
        self.final_offset = self._offset()
        faint = self._mast_rows(self.FAINT, self.final_offset)
        # 5. Classification strip stamps in (rule, then the full strip)
        yield self._frame("rule", faint, 0, 0), 0.10
        yield self._frame("strip", faint, 0, 0), 0.12
        # 6. Tagline types word by word
        for n in range(1, len(self.tagline_words) + 1):
            yield self._frame("strip", faint, n, 0, tag_cursor=True), 0.10
        # 7. Boot log ticks through
        for s in range(1, len(self.boot_steps) + 1):
            yield self._frame("strip", faint, len(self.tagline_words),
                              s), 0.085
        # 8. Settle
        yield self._frame("strip", faint, len(self.tagline_words),
                          len(self.boot_steps)), 0.40

    def final(self) -> Group:
        """The completed title card (identical to the last animation state)."""
        self._reveal_to(len(self.pixmap))
        offset = getattr(self, "final_offset", None)
        if offset is None:
            # Not animated (non-TTY): fixed deterministic offset
            offset = (self.ROLL_IN + self.CONDENSE + self.BREATHE
                      + self.WIPE + 1) * self.DRIFT
        faint = self._mast_rows(self.FAINT, offset)
        return self._frame("strip", faint, len(self.tagline_words),
                           len(self.boot_steps))


def title_frames(seed: Seed = 0, width: int = DEFAULT_WIDTH) -> Iterator[Frame]:
    """Animation frames of the title sequence (for tests/recording)."""
    return _TitleScene(seed, width).frames()


def title_final(seed: Seed = 0, width: int = DEFAULT_WIDTH) -> Group:
    """Static final frame of the title sequence (non-TTY render)."""
    return _TitleScene(seed, width).final()


def play_title_sequence(console: Optional[Console] = None, seed: Seed = 0,
                        width: int = DEFAULT_WIDTH) -> None:
    """Play the full FALSE FLAG title sequence (skippable, ~6s)."""
    # Separate instances: building the final frame reveals every masthead
    # cell, which must not leak into the animation's own reveal state.
    scene = _TitleScene(seed, width)
    final = _TitleScene(seed, width).final()
    _play(scene.frames(), final, console)


# ---------------------------------------------------------------------------
# Generic condense (used by the debrief reveal)
# ---------------------------------------------------------------------------

def condense_frames(target, seed: Seed = 0, width: int = DEFAULT_WIDTH, *,
                    pre: int = 6, reveal: int = 30, hold: int = 8,
                    ambient: float = 0.7, tempo: float = 0.06,
                    drift: int = 2) -> Iterator[Frame]:
    """Condense any renderable out of drifting fog, cell by cell.

    The target is captured as a styled character grid; non-space cells
    reveal in seeded scatter order while unrevealed space fills with fog
    that thins as the reveal progresses, then breathes and wipes clean.
    """
    grid = _grid(target, width)
    height = len(grid)
    if height == 0:
        yield Group(), tempo
        return
    pixmap = [(r, c) for r in range(height) for c in range(width)
              if grid[r][c][0] != " "]
    _rng(seed, "condense-scatter").shuffle(pixmap)
    field = _FogField(seed, "condense-fog", width, height)
    revealed = [[False] * width for _ in range(height)]
    n_revealed = 0
    frame_no = 0

    def reveal_to(n: int) -> None:
        nonlocal n_revealed
        while n_revealed < min(n, len(pixmap)):
            r, c = pixmap[n_revealed]
            revealed[r][c] = True
            n_revealed += 1

    def rows(density: float, offset: int,
             cleared_above: Optional[int] = None) -> Group:
        style_map = _fog_style_map()
        out = []
        for r in range(height):
            cells: List[Cell] = []
            for c in range(width):
                ch, st = grid[r][c]
                if ch != " " and revealed[r][c]:
                    cells.append((ch, st))
                    continue
                d = density
                if cleared_above is not None and r < cleared_above:
                    d = 0.0
                if ch != " ":
                    d = min(1.0, d * 1.35)
                fog = field.char(r, c, offset, d)
                cells.append((fog, style_map.get(fog)))
            out.append(_row_text(cells))
        return Group(*out)

    def offset() -> int:
        nonlocal frame_no
        frame_no += 1
        return frame_no * drift

    for i in range(pre):
        yield rows(ambient * (i + 1) / pre, offset()), tempo
    for j in range(reveal):
        ease = _smoothstep((j + 1) / reveal)
        reveal_to(int(ease * len(pixmap)))
        yield rows(ambient * (1 - 0.6 * ease), offset()), tempo
    reveal_to(len(pixmap))
    for k in range(hold):
        pulse = 0.26 + 0.10 * math.sin(2 * math.pi * k / max(1, hold))
        yield rows(pulse, offset()), tempo + 0.02
    wipe_step = max(1, height // 6)
    for top in range(wipe_step, height + wipe_step, wipe_step):
        yield rows(0.22, offset(), cleared_above=top), tempo


def play_debrief_reveal(title: str, subtitle: Optional[str] = None,
                        lines: Optional[List[str]] = None, seed: Seed = 0,
                        console: Optional[Console] = None,
                        width: int = DEFAULT_WIDTH,
                        header: str = "AFTER ACTION ── OPERATION TUMAN") -> None:
    """Heavier, slower condense reveal of the debrief frame (~4s)."""
    final = ae.debrief_frame(title, subtitle=subtitle, lines=lines,
                             seed=seed, width=width, header=header)
    frames = condense_frames(final, seed=seed, width=width,
                             pre=8, reveal=36, hold=10,
                             ambient=0.78, tempo=0.06)
    _play(frames, final, console)


# ---------------------------------------------------------------------------
# Turn transition: a fog band rolls through the banner region
# ---------------------------------------------------------------------------

def turn_transition_frames(turn: int, seed: Seed = None,
                           width: int = DEFAULT_WIDTH,
                           n_frames: int = 14) -> Iterator[Frame]:
    """A dense fog front sweeps left to right, revealing the turn banner
    behind it."""
    if seed is None:
        seed = f"turn-{turn}"
    banner = ae.turn_banner(turn, seed=seed, width=width)
    grid = _grid(banner, width)
    height = len(grid)
    field = _FogField(seed, "roll-fog", width, height)
    trail = max(8, width // 6)
    span = width + 2 * trail
    for i in range(n_frames):
        style_map = _fog_style_map()
        front = int((i + 1) / n_frames * span) - trail
        rows = []
        for r in range(height):
            cells: List[Cell] = []
            for c in range(width):
                d = front - c
                if d < 0:
                    cells.append((" ", None))       # ahead of the front
                elif d < trail:                     # inside the fog band
                    density = 0.95 * math.sin(math.pi * (d / trail))
                    ch = field.char(r, c, i * 2, max(0.18, density))
                    cells.append((ch, style_map.get(ch)))
                else:                               # cleared behind it
                    cells.append(grid[r][c])
            rows.append(_row_text(cells))
        yield Group(*rows), 0.05


def play_turn_transition(turn: int, seed: Seed = None,
                         console: Optional[Console] = None,
                         width: int = DEFAULT_WIDTH) -> None:
    """Roll a fog band through the turn banner region (~0.8s)."""
    if seed is None:
        seed = f"turn-{turn}"
    final = ae.turn_banner(turn, seed=seed, width=width)
    _play(turn_transition_frames(turn, seed=seed, width=width), final,
          console)


# ---------------------------------------------------------------------------
# Scene stamp-in
# ---------------------------------------------------------------------------

def scene_stamp_frames(number, title: str, location: str = "",
                       timestamp: str = "", seed: Seed = None,
                       width: int = DEFAULT_WIDTH) -> Iterator[Frame]:
    """Scene card assembles fast: chrome, then title/coordinates type in,
    then the fog underline fades up. Total ~0.6s - must not slow reading."""
    if seed is None:
        seed = f"scene-{number}-{title}"
    card = ae.scene_card(number, title, location=location,
                         timestamp=timestamp, seed=seed, width=width)
    grid = _grid(card, width)
    height = len(grid)
    revealed = [[False] * width for _ in range(height)]

    # Row roles (see aesthetics.scene_card): 0 strip, 1 blank wall,
    # 2 title, 3 meta (when present), then blank wall, bottom border, fog x2
    n_fog = 2
    bottom_row = height - n_fog - 1
    text_rows = list(range(2, bottom_row - 1))

    def show_row(r: int, c0: int = 0, c1: Optional[int] = None) -> None:
        c1 = width if c1 is None else c1
        for c in range(c0, min(c1, width)):
            revealed[r][c] = True

    def frame() -> Group:
        rows = []
        for r in range(height):
            cells = [(grid[r][c] if revealed[r][c] else (" ", None))
                     for c in range(width)]
            rows.append(_row_text(cells))
        return Group(*rows)

    # 1. Chrome stamps in: strip, side walls, bottom border
    show_row(0)
    show_row(bottom_row)
    for r in range(1, bottom_row):
        show_row(r, 0, 2)
        show_row(r, width - 2, width)
    show_row(1)               # blank wall rows fill immediately
    show_row(bottom_row - 1)
    yield frame(), 0.07

    # 2. Title and meta lines type in fast, left to right
    for r in text_rows:
        chunks = 3
        for k in range(1, chunks + 1):
            show_row(r, 0, 2 + (width - 4) * k // chunks + 2)
            yield frame(), 0.045

    # 3. Fog underline fades up
    for r in range(bottom_row + 1, height):
        show_row(r)
    yield frame(), 0.06


def play_scene_stamp(number, title: str, location: str = "",
                     timestamp: str = "", seed: Seed = None,
                     console: Optional[Console] = None,
                     width: int = DEFAULT_WIDTH) -> None:
    """Stamp in an intro scene card (~0.6s, skippable)."""
    if seed is None:
        seed = f"scene-{number}-{title}"
    final = ae.scene_card(number, title, location=location,
                          timestamp=timestamp, seed=seed, width=width)
    _play(scene_stamp_frames(number, title, location=location,
                             timestamp=timestamp, seed=seed, width=width),
          final, console)


# ---------------------------------------------------------------------------
# Static setup-menu banner
# ---------------------------------------------------------------------------

def setup_banner(title: str, seed: Seed = None,
                 width: int = DEFAULT_WIDTH) -> Group:
    """Compact classification-strip header for the setup menus.

    Replaces the repeated plain ``# FALSE FLAG`` + ``====`` header without
    eating vertical space the menus need.
    """
    colors = theme_manager.get_colors()
    if seed is None:
        seed = f"setup-{title}"
    label = Text("  ")
    label.append("FALSE FLAG", style=f"{colors['primary']} bold")
    label.append(" ── ", style=colors["muted"])
    label.append(title.upper(), style=f"{colors['highlight']} bold")
    label.no_wrap = True
    label.overflow = "crop"
    return Group(
        ae.classification_strip(seed=seed, width=width, edge="bare"),
        label,
        ae.sonar_divider(seed=seed, width=width),
    )
