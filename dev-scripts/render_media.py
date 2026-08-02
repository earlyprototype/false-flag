"""Render the FALSE FLAG terminal-UI reference media (docs/media/*).

Drives the committed aesthetic/cinematic generators (cli/aesthetics.py,
cli/cinematics.py) through a recording Rich console, exports each frame as
SVG (Rich's terminal-window chrome, title "FALSE FLAG"), rasterises the
SVGs to PNG with Playwright/Chromium at 2x device scale, and assembles the
animated sequences into GIFs whose per-frame durations match the
choreography timings in cli/cinematics.py (quantised to GIF's 10 ms units
with cumulative error correction; loop forever).

Regenerate everything:

    .venv/bin/python dev-scripts/render_media.py

Regenerate a subset (by asset stem):

    .venv/bin/python dev-scripts/render_media.py title_sequence masthead

Everything is seeded, so output is reproducible bit-for-bit apart from PNG
encoder details. No live terminal is involved: only the frame generators
are used, never the interactive players.
"""

from __future__ import annotations

import io
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from PIL import Image, ImageStat  # noqa: E402
from rich.console import Console, Group  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.terminal_theme import TerminalTheme  # noqa: E402
from rich.text import Text  # noqa: E402

from cli import aesthetics as ae  # noqa: E402
from cli import cinematics as cin  # noqa: E402
from cli.theme import THEMES, theme_manager  # noqa: E402

OUT_DIR = REPO / "docs" / "media"
CONSOLE_WIDTH = 80          # components render at DEFAULT_WIDTH = 78 inside
SCALE = 2                   # device pixels per CSS pixel for rasterisation
GIF_COLORS = 256            # global palette size
GIF_SIZE_BUDGET = 8 * 1024 * 1024   # per-GIF ceiling; downscale 2x -> 1x if hit
WINDOW_TITLE = "FALSE FLAG"
BACKGROUND = (13, 17, 23)   # flattened behind the SVG's rounded corners

# Dark terminal theme for the SVG export. The defcon palette is pure hex so
# it passes through untouched; the ANSI slots below only matter for the
# named-color themes (standard/defcon1/retro/slate) in themes.png.
EXPORT_THEME = TerminalTheme(
    BACKGROUND,
    (241, 250, 238),
    [
        (40, 46, 52), (224, 82, 82), (80, 200, 120), (250, 189, 47),
        (86, 156, 214), (198, 120, 221), (86, 182, 194), (211, 218, 225),
    ],
    [
        (90, 99, 108), (255, 110, 110), (110, 220, 140), (255, 210, 80),
        (120, 180, 255), (220, 150, 240), (110, 210, 220), (241, 250, 238),
    ],
)

# The exported SVG references Fira Code from a CDN; rasterisation is
# offline, so swap in a locally installed monospace with full coverage of
# the box-drawing / block-element set (▄ ▀ █ ░ ▒ ▓ ─ ━ ═ ● ○ ▌ …).
FONT_STACK = "'DejaVu Sans Mono', 'Liberation Mono', monospace"


# ---------------------------------------------------------------------------
# Recording + rasterisation
# ---------------------------------------------------------------------------

def record_svg(*renderables) -> str:
    """Render objects on a fresh 80-col recording console, export as SVG."""
    console = Console(record=True, width=CONSOLE_WIDTH, file=io.StringIO(),
                      force_terminal=True, color_system="truecolor",
                      legacy_windows=False)
    for r in renderables:
        console.print(r)
    svg = console.export_svg(title=WINDOW_TITLE, theme=EXPORT_THEME,
                             clear=True)
    # Drop the CDN @font-face rules (rasterisation is offline; leaving them
    # in stalls Chromium's load event on the dead network fetches) and swap
    # in the locally installed monospace stack.
    svg = re.sub(r"@font-face\s*\{[^}]*\}", "", svg)
    svg = svg.replace("Fira Code, monospace", FONT_STACK)
    return svg


class Rasterizer:
    """One Chromium instance that turns SVG strings into PNG files."""

    def __init__(self, scale: int = SCALE):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self._browser = None
        try:
            launch_args = ["--no-sandbox", "--force-color-profile=srgb"]
            try:
                self._browser = self._pw.chromium.launch(args=launch_args)
            except Exception:
                # Preinstalled browser revision differs from the playwright
                # package's pin: use the stable symlink directly (overridable
                # via PW_CHROMIUM_PATH for other environments).
                self._browser = self._pw.chromium.launch(
                    executable_path=os.environ.get(
                        "PW_CHROMIUM_PATH", "/opt/pw-browsers/chromium"),
                    args=launch_args)
            self._page = self._browser.new_page(
                device_scale_factor=scale,
                viewport={"width": 1400, "height": 2400})
        except Exception:
            # Don't leak the Playwright node process if startup fails midway
            if self._browser is not None:
                self._browser.close()
            self._pw.stop()
            raise

    def rasterize(self, svg: str, path: Path) -> None:
        html = ("<!doctype html><html><body style='margin:0'>"
                f"{svg}</body></html>")
        self._page.set_content(html, wait_until="domcontentloaded")
        self._page.locator("svg").screenshot(path=str(path), omit_background=True)

    def close(self) -> None:
        self._browser.close()
        self._pw.stop()


# ---------------------------------------------------------------------------
# GIF assembly
# ---------------------------------------------------------------------------

def _flatten(img: Image.Image) -> Image.Image:
    """RGBA screenshot -> RGB over the terminal background color."""
    if img.mode != "RGBA":
        return img.convert("RGB")
    base = Image.new("RGB", img.size, BACKGROUND)
    base.paste(img, mask=img.split()[3])
    return base


def _pad_to(img: Image.Image, size: Tuple[int, int]) -> Image.Image:
    if img.size == size:
        return img
    out = Image.new("RGB", size, BACKGROUND)
    out.paste(img, (0, 0))
    return out


def quantize_durations(seconds: Sequence[float]) -> List[int]:
    """Seconds -> GIF frame durations in ms (10 ms units), error-corrected
    so the total run time matches the choreography's total."""
    out: List[int] = []
    err = 0.0
    for s in seconds:
        target = s * 1000 + err
        ms = max(20, int(round(target / 10.0)) * 10)
        err = target - ms
        out.append(ms)
    return out


def assemble_gif(png_paths: Sequence[Path], seconds: Sequence[float],
                 out_path: Path) -> None:
    frames = [_flatten(Image.open(p)) for p in png_paths]
    size = (max(f.width for f in frames), max(f.height for f in frames))
    frames = [_pad_to(f, size) for f in frames]

    def encode(imgs: List[Image.Image]) -> None:
        # Global palette from a sample strip (first/middle/last frames) so
        # every frame shares one palette: smaller file, no color flicker.
        sample_idx = sorted({0, len(imgs) // 2, len(imgs) - 1})
        strip = Image.new("RGB", (size[0], size[1] * len(sample_idx)),
                          BACKGROUND)
        for i, si in enumerate(sample_idx):
            strip.paste(imgs[si], (0, i * size[1]))
        palette = strip.quantize(colors=GIF_COLORS)
        quant = [im.quantize(palette=palette, dither=Image.Dither.NONE)
                 for im in imgs]
        quant[0].save(out_path, save_all=True, append_images=quant[1:],
                      duration=quantize_durations(seconds), loop=0,
                      optimize=True, disposal=1)

    encode(frames)
    if out_path.stat().st_size > GIF_SIZE_BUDGET:
        # Fall back to 1x: downscale the 2x rasters.
        half = (size[0] // 2, size[1] // 2)
        frames = [f.resize(half, Image.Resampling.LANCZOS) for f in frames]
        size = half
        encode(frames)


# ---------------------------------------------------------------------------
# Animated deliverables (frame data straight from cli/cinematics.py)
# ---------------------------------------------------------------------------

# Hold on the final resolved frame before the GIF loops (presentation-only;
# in the game the final frame simply persists).
FINAL_HOLDS = {"title_sequence": 1.5, "debrief_reveal": 2.0,
               "turn_transition": 1.2}

DEBRIEF_TITLE = "The Guns of October"
DEBRIEF_SUBTITLE = "DEFEAT ── 7 TURNS"
DEBRIEF_LINES = [
    "The first exchange came at 04:11 GMT. No recall order was received.",
    "NATO cohesion collapsed; Article 5 was invoked, then overtaken.",
    "Casualties: incalculable. The fog did not lift.",
]
DEBRIEF_SEED = "guns-of-october"


def title_sequence_frames() -> List[cin.Frame]:
    frames = list(cin.title_frames(seed=42))
    frames.append((cin.title_final(seed=42), FINAL_HOLDS["title_sequence"]))
    return frames


def debrief_reveal_frames() -> List[cin.Frame]:
    final = ae.debrief_frame(DEBRIEF_TITLE, subtitle=DEBRIEF_SUBTITLE,
                             lines=DEBRIEF_LINES, seed=DEBRIEF_SEED)
    # Same tuning play_debrief_reveal passes to condense_frames.
    frames = list(cin.condense_frames(final, seed=DEBRIEF_SEED,
                                      pre=8, reveal=36, hold=10,
                                      ambient=0.78, tempo=0.06))
    frames.append((final, FINAL_HOLDS["debrief_reveal"]))
    return frames


def turn_transition_frames() -> List[cin.Frame]:
    frames = list(cin.turn_transition_frames(3, seed="turn-3"))
    frames.append((ae.turn_banner(3, seed="turn-3"),
                   FINAL_HOLDS["turn_transition"]))
    return frames


ANIMATED = {
    "title_sequence": title_sequence_frames,
    "debrief_reveal": debrief_reveal_frames,
    "turn_transition": turn_transition_frames,
}


# ---------------------------------------------------------------------------
# Static deliverables
# ---------------------------------------------------------------------------

SCENE_ARGS = (1, "Severomorsk Naval Base, Russia")
SCENE_KW = {"location": "69°04'N 033°25'E",
            "timestamp": "02 OCT 25 │ 03:15 LOCAL"}


def _label(s: str) -> Text:
    colors = theme_manager.get_colors()
    t = Text()
    t.append("── ", style=colors["muted"])
    t.append(s, style=f"{colors['highlight']} bold")
    t.no_wrap = True
    return t


def static_masthead():
    return [ae.masthead(seed="title")]


def static_boot_screen():
    return [ae.boot_screen(seed="boot")]


def static_scene_card():
    return [ae.scene_card(*SCENE_ARGS, **SCENE_KW)]


def static_turn_phase_banners():
    parts = [ae.turn_banner(3), Text()]
    for phase in ("BRIEFING", "DISCUSSION", "DECISION", "ADJUDICATION"):
        parts.append(ae.phase_banner(phase, turn=3))
    return parts


def static_fog_densities():
    parts = []
    for density in (0.2, 0.5, 0.9):
        parts.append(_label(f"DENSITY {density:.1f}"))
        parts.append(ae.fog_band(height=3, density=density, seed=42))
        parts.append(Text())
    return parts[:-1]


def static_sonar_dividers():
    parts = []
    for s in (1, 2, 3, 4, 5):
        parts.append(ae.sonar_divider(seed=s))
        parts.append(Text())
    return parts[:-1]


def static_themes():
    parts = []
    original = theme_manager.current_theme_name
    try:
        for name in THEMES:
            theme_manager.set_theme(name)
            colors = theme_manager.get_colors()
            head = Text()
            head.append("━━━ ", style=colors["muted"])
            head.append(f"THEME: {name.upper()}",
                        style=f"{colors['emphasis']} bold")
            head.append(" " + "━" * max(1, 60 - len(name)),
                        style=colors["muted"])
            head.no_wrap = True
            parts.extend([head, Text(),
                          ae.masthead(seed="title"), Text(),
                          ae.scene_card(*SCENE_ARGS, **SCENE_KW), Text()])
    finally:
        theme_manager.set_theme(original)
    return parts


def _vibe_line(name: str, level: int, descriptor: str, trend: str) -> Text:
    """Mirror of cli.display_utils.format_vibe_line (not imported: that
    module is game-runtime and mid-refactor; the visual contract is the
    5-dot ●○ row coloured by severity with a trend arrow)."""
    colors = theme_manager.get_colors()
    arrow = {"rising": "↗", "falling": "↘", "stable": "→"}.get(trend, "→")
    if level >= 4:
        dot_color = colors["danger"]
    elif level >= 2:
        dot_color = colors["warning"]
    else:
        dot_color = colors["success"]
    t = Text(f"{name:<20} ")
    t.append("●" * level, style=dot_color)
    t.append("○" * (5 - level), style=colors["muted"])
    t.append(f" {descriptor} {arrow}")
    t.no_wrap = True
    return t


def static_gameplay_collage():
    """In-context panels rebuilt from the committed aesthetics vocabulary +
    the Rich panel styles the game uses (YOUR DECISION: white border,
    OPERATIONAL ORDER: cyan border, SITUATION ASSESSMENT: phase banner +
    ●○ vibe rows)."""
    colors = theme_manager.get_colors()
    seed = "turn-3-intel"

    briefing_body = Text()
    briefing_body.append(
        "  Norwegian P-8 crews report loss of contact with two Northern\n"
        "  Fleet submarines, last plotted south of Bear Island. GCHQ flags\n"
        "  a spike in encrypted traffic on Northern Fleet command nets.\n",
        style=colors["normal"])
    briefing_body.append("  ASSESSMENT: ", style=f"{colors['warning']} bold")
    briefing_body.append("deliberate dispersal ahead of operations against\n"
                         "  North Atlantic cable infrastructure.",
                         style=colors["normal"])
    briefing = Group(
        ae.phase_banner("BRIEFING", turn=3),
        Text(),
        ae.classification_strip(seed=seed, edge="top"),
        briefing_body,
        ae.classification_strip(seed=seed, edge="bottom"),
    )

    decision = Panel(
        Text("Surge two Astute-class boats to the GIUK gap, keep rules of "
             "engagement defensive, and open a backchannel to Moscow via "
             "the embassy in Helsinki.", style="italic"),
        title="[bold]YOUR DECISION[/bold]", border_style="white")

    order_body = Text()
    order_body.append("UK attack submarines move to blocking positions while "
                      "diplomacy runs on a parallel track.\n\n")
    order_body.append("Forces Deployed:\n", style=colors["success"])
    order_body.append("  • HMS Astute ── GIUK patrol box NORTH\n")
    order_body.append("  • HMS Ambush ── GIUK patrol box SOUTH\n")
    order_body.append("  • RAF Poseidon MRA1 x2 ── surveillance relay\n\n")
    order_body.append("Estimated Timeline:", style=colors["accent"])
    order_body.append(" 36 hours to station")
    order = Panel(order_body, title="[bold]OPERATIONAL ORDER[/bold]",
                  border_style="cyan")

    assessment = Group(
        ae.phase_banner("SITUATION ASSESSMENT"),
        Text(),
        _vibe_line("NATO COHESION", 2, "Strained but holding", "stable"),
        _vibe_line("ESCALATION RISK", 4, "Dangerous and climbing", "rising"),
        _vibe_line("HOME FRONT", 3, "Press asking questions", "rising"),
        _vibe_line("FLEET READINESS", 1, "Assets on station", "stable"),
        Text(),
        ae.sonar_divider(seed="3-adv"),
    )

    return [briefing, Text(), decision, Text(), order, Text(), assessment]


STATIC = {
    "masthead": static_masthead,
    "boot_screen": static_boot_screen,
    "scene_card": static_scene_card,
    "turn_phase_banners": static_turn_phase_banners,
    "fog_densities": static_fog_densities,
    "sonar_dividers": static_sonar_dividers,
    "themes": static_themes,
    "gameplay_collage": static_gameplay_collage,
}


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify(produced: List[Path]) -> None:
    """Check the assets produced by THIS run; the size budget stays dir-wide
    (a partial regeneration must not push docs/media past the ceiling)."""
    print("\n── VERIFY " + "─" * 50)
    for path in sorted(produced):
        size = path.stat().st_size
        img = Image.open(path)
        if path.suffix == ".gif":
            n = getattr(img, "n_frames", 1)
            assert n > 1, f"{path.name}: GIF does not animate ({n} frame)"
            durations = []
            for i in range(n):
                img.seek(i)
                durations.append(img.info.get("duration", 0))
            assert all(d >= 20 for d in durations), \
                f"{path.name}: zero/short frame durations"
            img.seek(n // 2)
            var = ImageStat.Stat(img.convert("L")).stddev[0]
            assert var > 3, f"{path.name}: mid frame looks blank (σ={var:.1f})"
            print(f"  {path.name:<26} {img.size[0]}x{img.size[1]}  "
                  f"{n} frames  {sum(durations)/1000:.2f}s  "
                  f"{size/1024:.0f} KB")
        else:
            var = ImageStat.Stat(img.convert("L")).stddev[0]
            assert var > 3, f"{path.name}: looks blank (σ={var:.1f})"
            print(f"  {path.name:<26} {img.size[0]}x{img.size[1]}  "
                  f"{size/1024:.0f} KB")
    total = sum(p.stat().st_size for p in OUT_DIR.iterdir()
                if p.suffix in (".gif", ".png"))
    assert total <= 25 * 1024 * 1024, f"docs/media exceeds 25 MB ({total})"
    print(f"  total {total / (1024 * 1024):.1f} MB (budget 25 MB)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(only: Optional[Iterable[str]] = None) -> None:
    wanted = set(only) if only else None

    def selected(name: str) -> bool:
        return wanted is None or name in wanted

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    theme_manager.set_theme("defcon")
    ras = Rasterizer()
    produced: List[Path] = []
    try:
        for name, build in STATIC.items():
            if not selected(name):
                continue
            out = OUT_DIR / f"{name}.png"
            print(f"render {out.name}")
            ras.rasterize(record_svg(*build()), out)
            produced.append(out)

        for name, gen in ANIMATED.items():
            if not selected(name):
                continue
            out = OUT_DIR / f"{name}.gif"
            frames = gen()
            print(f"render {out.name} ({len(frames)} frames)")
            with tempfile.TemporaryDirectory() as td:
                paths = []
                for i, (renderable, _hold) in enumerate(frames):
                    p = Path(td) / f"f{i:04d}.png"
                    ras.rasterize(record_svg(renderable), p)
                    paths.append(p)
                assemble_gif(paths, [hold for _, hold in frames], out)
            produced.append(out)
    finally:
        ras.close()

    verify(produced)


if __name__ == "__main__":
    main(sys.argv[1:] or None)
