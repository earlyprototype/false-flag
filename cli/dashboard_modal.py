"""Modal overlay system for dashboard commands.

This module provides full-screen overlays that pause the dashboard's
Live() updates, display command output, and then return to the dashboard.
"""

from rich.panel import Panel
from rich.console import Console
from rich.layout import Layout
from rich import box
from typing import Union


def show_overlay(console: Console, live, title: str, content, colors: dict) -> None:
    """Show overlay integrated with dashboard UI.
    
    Args:
        console: Rich Console instance
        live: Rich Live instance (from dashboard)
        title: Panel title
        content: Renderable content (Panel, Table, str, etc.)
        colors: Colour dict from theme
    """
    from rich.layout import Layout
    from rich.text import Text
    
    # Create integrated overlay layout
    overlay_layout = Layout()
    
    # Header bar matching dashboard style
    header_text = f"[reverse][{colors['warning']} bold] COBRA COMMAND: {title} [/][/reverse]"
    header_panel = Panel(
        header_text,
        style=f"bold {colors['primary']} on #0A0E27",
        box=box.HEAVY,
        padding=(0, 0)
    )
    
    # Content panel
    content_panel = Panel(
        content,
        title=f"[{colors['accent']} bold]{title}[/]",
        border_style=f"bold {colors['accent']}",
        box=box.HEAVY,
        padding=(2, 4),
        style="on #0A0E27"
    )
    
    # Footer bar with instructions
    footer_text = f"[{colors['primary']} bold]Press ENTER to return to dashboard[/] │ [{colors['muted']}]Dashboard paused[/]"
    footer_panel = Panel(
        footer_text,
        style=f"{colors['primary']} on #0A0E27",
        box=box.HEAVY,
        padding=(0, 1)
    )
    
    # Build layout
    overlay_layout.split_column(
        Layout(header_panel, size=3),
        Layout(content_panel, ratio=1),
        Layout(footer_panel, size=3)
    )
    
    # Pause dashboard and show overlay
    live.stop()
    console.clear()
    console.print(overlay_layout)
    console.input()
    
    # Resume dashboard
    console.clear()
    live.start()

