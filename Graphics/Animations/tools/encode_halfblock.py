"""
PNG → terminal half-block encoder.

Usage:
  python -m Graphics.Animations.tools.encode_halfblock input.png --mode 16 --palette db16 --dither > frame.txt

Outputs rows of SGR-coloured strings representing the frame.

Features:
- 16-colour ANSI and 24-bit truecolour output
- Optional DB16 palette quantisation with Floyd–Steinberg dithering for a LucasArts-like look
"""
from __future__ import annotations

import argparse
from typing import List, Tuple

from PIL import Image

from .palette_db16 import nearest_terminal_index, DB16_PALETTE, quantise_to_palette


def _fs_dither_to_palette(im: Image.Image, palette: List[Tuple[int, int, int]]) -> Image.Image:
    """Return a new RGBA image, quantised to palette using Floyd–Steinberg dithering.

    Transparent pixels (alpha < 8) are preserved. Error is spread only on RGB.
    """
    src = im.convert("RGBA")
    w, h = src.size
    in_px = src.load()

    # Working float buffer for error diffusion
    work = [[[float(in_px[x, y][0]), float(in_px[x, y][1]), float(in_px[x, y][2]), in_px[x, y][3]] for x in range(w)] for y in range(h)]

    def clamp(v: float) -> float:
        return 0.0 if v < 0.0 else (255.0 if v > 255.0 else v)

    for y in range(h):
        for x in range(w):
            r, g, b, a = work[y][x]
            if a < 8:  # skip transparent
                continue
            orig = (int(r), int(g), int(b))
            q = quantise_to_palette(orig, palette)
            # compute error
            er, eg, eb = r - q[0], g - q[1], b - q[2]
            # write quantised colour back
            work[y][x][0], work[y][x][1], work[y][x][2] = float(q[0]), float(q[1]), float(q[2])
            # distribute error
            def add(xi: int, yi: int, wr: float, wg: float, wb: float, k: float) -> None:
                if 0 <= xi < w and 0 <= yi < h and work[yi][xi][3] >= 8:
                    work[yi][xi][0] = clamp(work[yi][xi][0] + wr * k)
                    work[yi][xi][1] = clamp(work[yi][xi][1] + wg * k)
                    work[yi][xi][2] = clamp(work[yi][xi][2] + wb * k)

            add(x + 1, y,     er, eg, eb, 7 / 16)
            add(x - 1, y + 1, er, eg, eb, 3 / 16)
            add(x,     y + 1, er, eg, eb, 5 / 16)
            add(x + 1, y + 1, er, eg, eb, 1 / 16)

    out = Image.new("RGBA", (w, h))
    out_px = out.load()
    for y in range(h):
        for x in range(w):
            rr, gg, bb, aa = work[y][x]
            if aa < 8:
                out_px[x, y] = (0, 0, 0, 0)
            else:
                out_px[x, y] = (int(rr), int(gg), int(bb), int(aa))
    return out


def _nearest_idx(rgb: Tuple[int, int, int], mode: str) -> Tuple[int, int, int]:
    if mode == "16":
        idx = nearest_terminal_index(rgb)
        return idx, -1, -1
    # 24-bit truecolour
    return rgb[0], rgb[1], rgb[2]


def encode_halfblock(image_path: str, mode: str = "16", palette: str | None = None, dither: bool = False) -> List[str]:
    im = Image.open(image_path).convert("RGBA")
    # Optional palette quantisation pre-pass
    if palette and palette.lower() == "db16":
        im = _fs_dither_to_palette(im, DB16_PALETTE) if dither else im.point(lambda v: v)
        if not dither:
            # Non-dithered quantisation (nearest colour)
            wq, hq = im.size
            src_px = im.load()
            for yy in range(hq):
                for xx in range(wq):
                    r0, g0, b0, a0 = src_px[xx, yy]
                    if a0 < 8:
                        continue
                    q = quantise_to_palette((r0, g0, b0), DB16_PALETTE)
                    src_px[xx, yy] = (q[0], q[1], q[2], a0)
    w, h = im.size
    pixels = im.load()
    lines: List[str] = []
    for y in range(0, h, 2):
        row = []
        for x in range(w):
            # top pixel
            r1, g1, b1, a1 = pixels[x, y]
            # bottom pixel
            if y + 1 < h:
                r2, g2, b2, a2 = pixels[x, y + 1]
            else:
                r2, g2, b2, a2 = (0, 0, 0, 0)

            top_none = a1 < 8
            bot_none = a2 < 8

            if top_none and bot_none:
                # Reset SGR so background colour doesn't bleed across transparent cells
                row.append("\x1b[0m ")
                continue

            if mode == "16":
                if not top_none:
                    fi = nearest_terminal_index((r1, g1, b1))
                else:
                    fi = nearest_terminal_index((0, 0, 0))
                if not bot_none:
                    bi = nearest_terminal_index((r2, g2, b2))
                else:
                    bi = nearest_terminal_index((0, 0, 0))
                # SGR: \x1b[38;5;{fg}m FG 256? But we target 16-colour: 30-37/90-97 and 40-47/100-107
                def sgr16(i: int, bg=False) -> str:
                    base = (40 if bg else 30)
                    if i >= 8:
                        base += 60
                        i -= 8
                    return f"\x1b[{base + i}m"

                if not top_none and not bot_none:
                    row.append(sgr16(fi, False) + sgr16(bi, True) + "▀")
                elif not top_none:
                    row.append(sgr16(fi, False) + sgr16(0, True) + "▀")
                else:
                    row.append(sgr16(0, False) + sgr16(bi, True) + "▄")
            else:  # 24-bit truecolour
                def sgr24(r: int, g: int, b: int, bg=False) -> str:
                    return f"\x1b[{48 if bg else 38};2;{r};{g};{b}m"

                if not top_none and not bot_none:
                    row.append(sgr24(r1, g1, b1, False) + sgr24(r2, g2, b2, True) + "▀")
                elif not top_none:
                    row.append(sgr24(r1, g1, b1, False) + sgr24(0, 0, 0, True) + "▀")
                else:
                    row.append(sgr24(0, 0, 0, False) + sgr24(r2, g2, b2, True) + "▄")

        lines.append("".join(row) + "\x1b[0m")
    return lines


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("image", help="input PNG path")
    ap.add_argument("--mode", choices=["16", "24"], default="16")
    ap.add_argument("--palette", choices=["none", "db16"], default="db16")
    ap.add_argument("--dither", action="store_true")
    args = ap.parse_args()
    palette_arg = None if args.palette == "none" else args.palette
    for line in encode_halfblock(args.image, args.mode, palette=palette_arg, dither=args.dither):
        print(line)


if __name__ == "__main__":
    main()


