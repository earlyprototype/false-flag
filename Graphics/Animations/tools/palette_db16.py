"""
DB16 palette utilities and terminal-colour mapping.

Provides:
- DB16_PALETTE: 16-colour LucasArts-adjacent palette (hex tuples)
- TERMINAL_16: Standard 16 SGR colours (approx RGB tuples)
- quantise_to_palette(rgb, palette)
- nearest_terminal_colour(rgb)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple


RGB = Tuple[int, int, int]


# DawnBringer 16 (DB16) palette (hex RGB)
DB16_HEX = [
    0x140C1C, 0x442434, 0x30346D, 0x4E4A4E,
    0x854C30, 0x346524, 0xD04648, 0x757161,
    0x597DCE, 0xD27D2C, 0x8595A1, 0x6DAA2C,
    0xD2AA99, 0x6DC2CA, 0xDAD45E, 0xDEEEDE,
]


def _hex_to_rgb(x: int) -> RGB:
    return (x >> 16 & 0xFF, x >> 8 & 0xFF, x & 0xFF)


DB16_PALETTE: List[RGB] = [_hex_to_rgb(x) for x in DB16_HEX]


# Standard 16 terminal colours (approx) in RGB
TERMINAL_16: List[RGB] = [
    (0x00, 0x00, 0x00),  # 0 black
    (0x80, 0x00, 0x00),  # 1 red
    (0x00, 0x80, 0x00),  # 2 green
    (0x80, 0x80, 0x00),  # 3 yellow
    (0x00, 0x00, 0x80),  # 4 blue
    (0x80, 0x00, 0x80),  # 5 magenta
    (0x00, 0x80, 0x80),  # 6 cyan
    (0xC0, 0xC0, 0xC0),  # 7 white (light gray)
    (0x80, 0x80, 0x80),  # 8 bright black (gray)
    (0xFF, 0x00, 0x00),  # 9 bright red
    (0x00, 0xFF, 0x00),  # 10 bright green
    (0xFF, 0xFF, 0x00),  # 11 bright yellow
    (0x00, 0x00, 0xFF),  # 12 bright blue
    (0xFF, 0x00, 0xFF),  # 13 bright magenta
    (0x00, 0xFF, 0xFF),  # 14 bright cyan
    (0xFF, 0xFF, 0xFF),  # 15 bright white
]


def _dist2(a: RGB, b: RGB) -> int:
    dr, dg, db = a[0] - b[0], a[1] - b[1], a[2] - b[2]
    return dr * dr + dg * dg + db * db


def quantise_to_palette(rgb: RGB, palette: Sequence[RGB]) -> RGB:
    """Return the nearest colour in palette to rgb (Euclidean in RGB)."""
    best = palette[0]
    best_d = _dist2(rgb, best)
    for c in palette[1:]:
        d = _dist2(rgb, c)
        if d < best_d:
            best, best_d = c, d
    return best


def nearest_terminal_index(rgb: RGB) -> int:
    """Return the nearest terminal 16-colour index for rgb."""
    best_i = 0
    best_d = _dist2(rgb, TERMINAL_16[0])
    for i in range(1, len(TERMINAL_16)):
        d = _dist2(rgb, TERMINAL_16[i])
        if d < best_d:
            best_i, best_d = i, d
    return best_i


__all__ = [
    "DB16_PALETTE",
    "TERMINAL_16",
    "quantise_to_palette",
    "nearest_terminal_index",
]


