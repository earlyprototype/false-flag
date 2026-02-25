from __future__ import annotations

"""
Minimal runtime to play pre-encoded half-block frames described by a scene JSON.
- Reads a compiled_scene.json with per-frame rows of strings for each layer.
- Performs dirty-region updates and single flush per frame.
- Clears dirty rows before re-draw to avoid fragments.
"""

import argparse
import json
import os
import sys
import tempfile
import time
from typing import Dict, List, Tuple
from blessed import Terminal


# --- ANSI-safe clipping helpers ---
def _clip_ansi(s: str, max_columns: int) -> str:
    """Clip a string containing ANSI SGR sequences to max visible columns.

    Ensures escape sequences are preserved and closed; appends SGR reset.
    """
    out: List[str] = []
    cols = 0
    i = 0
    # Track last SGR so we can ensure reset at end
    last_sgr_reset = False
    while i < len(s) and cols < max_columns:
        ch = s[i]
        if ch == "\x1b":
            # copy through CSI sequence
            j = i + 1
            if j < len(s) and s[j] == '[':
                j += 1
                while j < len(s) and not ('@' <= s[j] <= '~'):
                    j += 1
                if j < len(s):
                    out.append(s[i:j+1])
                    last_sgr_reset = (s[i:j+1] == "\x1b[0m")
                    i = j + 1
                    continue
            # not CSI; copy and continue
            out.append(ch)
            i += 1
            continue
        # printable
        out.append(ch)
        cols += 1
        i += 1
    # ensure reset
    if not last_sgr_reset:
        out.append("\x1b[0m")
    return "".join(out)


# --- ANSI line <-> cells helpers ---
def _parse_sgr_indices(seq: str) -> Tuple[int | None, int | None]:
    if not (seq.startswith("\x1b[") and seq.endswith("m")):
        return None, None
    try:
        code = seq[2:-1]
        parts = code.split(";")
        if len(parts) != 1:
            return None, None
        n = int(parts[0])
        if 30 <= n <= 37:
            return (n - 30), None
        if 90 <= n <= 97:
            return (n - 90 + 8), None
        if 40 <= n <= 47:
            return None, (n - 40)
        if 100 <= n <= 107:
            return None, (n - 100 + 8)
        if n == 0:
            return -1, -1
    except Exception:
        return None, None
    return None, None


def _line_to_cells(s: str) -> List[Tuple[int | None, int | None, str]]:
    cells: List[Tuple[int | None, int | None, str]] = []
    i = 0
    fg: int | None = None
    bg: int | None = None
    while i < len(s):
        ch = s[i]
        if ch == "\x1b":
            j = i + 1
            if j < len(s) and s[j] == '[':
                j += 1
                while j < len(s) and not ('@' <= s[j] <= '~'):
                    j += 1
                if j < len(s):
                    seq = s[i:j+1]
                    fgi, bgi = _parse_sgr_indices(seq)
                    if fgi is not None:
                        if fgi == -1:
                            fg = None
                            bg = None
                        else:
                            fg = fgi
                    if bgi is not None:
                        if bgi == -1:
                            fg = None
                            bg = None
                        else:
                            bg = bgi
                    i = j + 1
                    continue
            i += 1
            continue
        cells.append((fg, bg, ch))
        i += 1
    return cells


def _cells_to_line(cells: List[Tuple[int | None, int | None, str]]) -> str:
    out: List[str] = []
    last_fg: int | None = None
    last_bg: int | None = None

    def sgr16(i: int, bg: bool = False) -> str:
        base = (40 if bg else 30)
        if i >= 8:
            base += 60
            ii = i - 8
        else:
            ii = i
        return f"\x1b[{base + ii}m"

    for fg, bg, ch in cells:
        if fg is not None and fg != last_fg:
            out.append(sgr16(fg, False))
            last_fg = fg
        if bg is not None and bg != last_bg:
            out.append(sgr16(bg, True))
            last_bg = bg
        out.append(ch)
    out.append("\x1b[0m")
    return "".join(out)


def play_scene(compiled_path: str, fps: float = 14.0, duration: float | None = None, loop: bool = False, overlay: bool = False, noinput: bool = False) -> None:
    term = Terminal()
    with term.fullscreen(), term.hidden_cursor(), term.cbreak():
        w, h = term.width, term.height
        frame_time = 1.0 / fps
        last_lines: Dict[int, str] = {}
        # initial clear
        sys.stdout.write(term.home + term.clear)
        sys.stdout.flush()

        with open(compiled_path, "r", encoding="utf-8") as f:
            scene = json.load(f)
        frames: List[Dict[str, object]] = scene["frames"]
        
        # Check for ticker configuration
        ticker_text = scene.get("ticker_text", "")
        ticker_row = scene.get("ticker_row", -2)  # -2 means second from bottom
        ticker_speed = scene.get("ticker_speed", 1)  # columns per frame
        ticker_offset = 0  # scrolling position

        start_total = time.time()
        fi = 0
        while True:
            start = time.time()
            # Exit on key press (unless disabled)
            if not noinput:
                key = term.inkey(timeout=0)
                if key:
                    break

            fr = frames[fi]
            buf: List[str] = []
            # New format: bg_rows + overlays; fallback to legacy rows
            legacy_rows = fr.get("rows")
            if legacy_rows is not None:
                rows = legacy_rows  # type: ignore
            else:
                bg_rows = fr.get("bg_rows", [])  # type: ignore
                overlays = fr.get("overlays", [])  # type: ignore
                # Start from background rows
                rows_cells = [_line_to_cells(r) for r in bg_rows]
                # Apply overlays
                for ov in overlays:
                    ox = int(ov.get("x", 0))
                    oy = int(ov.get("y", 0))
                    s = str(ov.get("s", ""))
                    if 0 <= oy < len(rows_cells) and s:
                        base = rows_cells[oy]
                        ov_cells = _line_to_cells(s)
                        # Write ov_cells into base starting at ox
                        for j, cell in enumerate(ov_cells):
                            cx = ox + j
                            if 0 <= cx < w:
                                if cx < len(base):
                                    base[cx] = cell
                                else:
                                    # extend with spaces up to cx
                                    base.extend([(None, None, ' ')] * (cx - len(base)))
                                    base.append(cell)
                        rows_cells[oy] = base
                # Rebuild strings and clip to terminal width
                rows = [_cells_to_line(rc) for rc in rows_cells]
            # Clamp to terminal height
            max_rows = min(len(rows), h)
            for i in range(max_rows):
                line = rows[i]
                if last_lines.get(i) != line:
                    # Clear row with reset to prevent SGR bleed, then draw line
                    buf.append(term.move_xy(0, i) + "\x1b[0m" + (" " * w))
                    buf.append(term.move_xy(0, i) + _clip_ansi(line, w))
                    last_lines[i] = line
            
            # Render ticker if enabled
            if ticker_text:
                # Calculate ticker row (negative means from bottom)
                ticker_y = ticker_row if ticker_row >= 0 else (h + ticker_row)
                if 0 <= ticker_y < h:
                    # Prepare scrolling text with padding
                    padded_ticker = " " * w + ticker_text + " " * w
                    # Extract visible window
                    visible_start = ticker_offset % len(padded_ticker)
                    visible_text = (padded_ticker[visible_start:] + padded_ticker)[:w]
                    # Style the ticker
                    ticker_line = f"\x1b[30;47m{visible_text}\x1b[0m"  # Black on white
                    buf.append(term.move_xy(0, ticker_y) + ticker_line)
                    # Advance ticker offset
                    ticker_offset += ticker_speed
            
            if overlay:
                info = f"fps:{fps:.0f} frame:{fi+1}/{len(frames)}"
                # Clear overlay row fully with reset, then write info
                buf.append(term.move_xy(0, 0) + "\x1b[0m" + (" " * w))
                buf.append(term.move_xy(0, 0) + info)
            out_s = "".join(buf)
            try:
                # Write as UTF-8 to support block characters on Windows
                sys.stdout.buffer.write(out_s.encode("utf-8", errors="replace"))
            except Exception:
                sys.stdout.write(out_s)
            sys.stdout.flush()

            # pacing
            elapsed = time.time() - start
            if duration is not None and (time.time() - start_total) >= duration:
                break
            sleep_for = frame_time - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)

            fi += 1
            if fi >= len(frames):
                if loop:
                    fi = 0
                    last_lines.clear()
                else:
                    break


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("compiled", help="Path to compiled_scene.json")
    ap.add_argument("--fps", type=float, default=14.0)
    ap.add_argument("--duration", type=float, default=0.0, help="Seconds to auto-close (<=0 disables)")
    ap.add_argument("--loop", action="store_true", help="Loop the scene")
    ap.add_argument("--overlay", action="store_true", help="Show simple debug overlay")
    ap.add_argument("--noinput", action="store_true", help="Ignore keyboard input (useful for benchmarks)")
    ap.add_argument("--ticker", type=str, default="", help="Scrolling ticker text to display")
    ap.add_argument("--ticker-row", type=int, default=-2, help="Ticker row (-2 = second from bottom)")
    ap.add_argument("--ticker-speed", type=int, default=1, help="Ticker scroll speed (columns per frame)")
    args = ap.parse_args()
    dur = None if args.duration is not None and args.duration <= 0 else args.duration
    
    # If ticker specified, inject into scene data
    if args.ticker:
        with open(args.compiled, "r", encoding="utf-8") as f:
            scene_data = json.load(f)
        scene_data["ticker_text"] = args.ticker
        scene_data["ticker_row"] = args.ticker_row
        scene_data["ticker_speed"] = args.ticker_speed
        # Save modified scene to temp location or pass directly
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp:
            json.dump(scene_data, tmp)
            tmp_path = tmp.name
        try:
            play_scene(tmp_path, fps=args.fps, duration=dur, loop=args.loop, overlay=args.overlay, noinput=args.noinput)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
    else:
        play_scene(args.compiled, fps=args.fps, duration=dur, loop=args.loop, overlay=args.overlay, noinput=args.noinput)


