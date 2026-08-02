"""Modal overlay system for dashboard commands.

This module provides full-screen overlays that pause the dashboard's
Live() updates, display command output, and then return to the dashboard.

Overlays speak the Operation Tuman language: a classification strip with a
thin fog trim up top, a square-ruled document panel for the content, and a
sonar trace above the return instructions. Trims are seeded from the
overlay title so each overlay's weather is deterministic.
"""

import sys

from rich.panel import Panel
from rich.console import Console, Group
from rich.layout import Layout
from rich.text import Text
from rich import box

from cli import aesthetics as ae


def show_overlay(console: Console, live, title: str, content, colors: dict) -> None:
    """Show overlay integrated with dashboard UI.

    Args:
        console: Rich Console instance
        live: Rich Live instance (from dashboard)
        title: Panel title
        content: Renderable content (Panel, Table, str, etc.)
        colors: Colour dict from theme
    """
    width = console.size.width or 100
    seed = f"overlay-{title}"

    # Create integrated overlay layout
    overlay_layout = Layout()

    # Classification strip + fog trim matching the dashboard masthead
    header = Group(
        ae.classification_strip(label=f"COBRA COMMAND ── {title}",
                                seed=seed, width=width, edge="bare"),
        ae.fog_band(width, 1, 0.3, seed),
    )

    # Content panel: square-ruled classified document with reference code
    content_panel = Panel(
        content,
        title=f"[{colors['accent']} bold]{title}[/]",
        title_align="left",
        subtitle=f"[{colors['warning']}]{ae.reference_code(seed)}[/]",
        subtitle_align="right",
        border_style=colors['muted'],
        box=box.SQUARE,
        padding=(1, 2),
    )

    # Sonar trace over the return instructions
    footer_row = Text.from_markup(
        f"[{colors['primary']} bold]Press ENTER to return to dashboard[/] │ "
        f"[{colors['muted']}]Dashboard paused[/]"
    )
    footer_row.no_wrap = True
    footer_row.overflow = "crop"
    footer = Group(
        ae.sonar_divider(seed=seed, width=width),
        footer_row,
    )

    # Build layout
    overlay_layout.split_column(
        Layout(header, size=2),
        Layout(content_panel, ratio=1),
        Layout(footer, size=2)
    )

    # Pause dashboard and show overlay
    live.stop()
    console.clear()
    console.print(overlay_layout)
    # Wait for ENTER only on interactive stdin: a piped run's next line is a
    # queued command, not an acknowledgement — consuming it here turned the
    # player's next command into a chat message. EOF just closes the overlay.
    if sys.stdin.isatty():
        try:
            console.input()
        except EOFError:
            pass

    # Resume dashboard
    console.clear()
    live.start()
