"""Visual demo of the Operation Tuman aesthetic engine (cli/aesthetics.py).

Renders every component for every theme so the full language can be
eyeballed in a terminal:

    .venv/bin/python dev-scripts/aesthetics_demo.py            # all themes
    .venv/bin/python dev-scripts/aesthetics_demo.py defcon     # one theme
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rich.console import Console

from cli import aesthetics as ae
from cli.theme import THEMES, theme_manager

console = Console()


def section(label: str) -> None:
    console.print()
    console.print(f"[bold underline]{label}[/bold underline]")
    console.print()


def demo_theme(name: str) -> None:
    theme_manager.set_theme(name)
    console.rule(f"[bold]THEME: {name}[/bold]")

    section("MASTHEAD (title screen)")
    console.print(ae.masthead(seed="title"))

    section("BOOT SCREEN (static render; animate_boot() for TTY)")
    console.print(ae.boot_screen(seed="boot"))

    section("FOG BANDS (density 0.2 / 0.5 / 0.9)")
    for density in (0.2, 0.5, 0.9):
        console.print(ae.fog_band(height=3, density=density, seed=42))
        console.print()

    section("CLASSIFICATION STRIPS")
    console.print(ae.classification_strip(seed="scene-1", edge="top"))
    console.print(ae.classification_strip(seed="scene-1", edge="bottom"))
    console.print(ae.classification_strip(seed="scene-2", edge="bare"))

    section("SONAR DIVIDERS (three seeds)")
    for s in (1, 2, 3):
        console.print(ae.sonar_divider(seed=s))

    section("SCENE CARDS")
    console.print(ae.scene_card(
        1, "Severomorsk Naval Base, Russia",
        location="69°04'N 033°25'E",
        timestamp="02 OCT 25 │ 03:15 LOCAL"))
    console.print(ae.scene_card(
        3, "Cabinet Office Briefing Room A (COBRA)",
        location="51°30'N 000°07'W",
        timestamp="05 OCT 25 │ 17:00 LONDON"))

    section("TURN BANNERS (turns 1-3: seeded per-turn trim)")
    for turn in (1, 2, 3):
        console.print(ae.turn_banner(turn))
        console.print()

    section("PHASE BANNERS")
    for phase in ("BRIEFING", "DISCUSSION", "DECISION", "ADJUDICATION"):
        console.print(ae.phase_banner(phase, turn=3))

    section("BOOT FRAMES (first and mid frame, for animated use)")
    frames = ae.boot_sequence_frames(seed="boot")
    console.print(frames[0])
    console.print()
    console.print(frames[len(frames) // 2])

    section("DEBRIEF / ENDING FRAME")
    console.print(ae.debrief_frame(
        "Uneasy Peace",
        subtitle="The fog lifts. The fleet turns for home.",
        lines=[
            "Escalation contained below the nuclear threshold.",
            "NATO cohesion held: Article 4 consultations concluded.",
            "Casualties: 12 military, 0 civilian.",
        ],
        seed="ending-1"))
    console.print()


def main() -> None:
    names = sys.argv[1:] or list(THEMES.keys())
    original = theme_manager.current_theme_name
    try:
        for name in names:
            demo_theme(name)
    finally:
        theme_manager.set_theme(original)


if __name__ == "__main__":
    main()
