"""Game setup flow and screen rendering for the CLI.

This module handles:
- Standardized screen rendering (12-line minimum, bordered panels)
- Scenario selection
- Gameplay mode selection
- Game intro sequences
"""

import typer
from pathlib import Path
from rich import box
from rich.panel import Panel
from rich.console import Console
from rich.text import Text
from rich.layout import Layout
from cli.theme import theme_manager

# ASCII Art Title
TITLE_ART = """
[bold]
███████╗ █████╗ ██╗     ███████╗███████╗
██╔════╝██╔══██╗██║     ██╔════╝██╔════╝
█████╗  ███████║██║     ███████╗█████╗  
██╔══╝  ██╔══██║██║     ╚════██║██╔══╝  
██║     ██║  ██║███████╗███████║███████╗
╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝
   
   █████╗ ██╗      █████╗  ██████╗ 
  ██╔══██╗██║     ██╔══██╗██╔════╝ 
  ███████║██║     ███████║██║  ███╗
  ██╔══██║██║     ██╔══██║██║   ██║
  ██║  ██║███████╗██║  ██║╚██████╔╝
  ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝ 
[/bold]
"""

def get_defcon_colors():
    """Get standardized DEFCON colors."""
    return {
        "primary": "#FF6B35",        # Deep Orange
        "secondary": "#004E89",      # Navy Blue
        "accent": "#1A659E",         # Steel Blue
        "success": "#00D9A3",        # Teal
        "warning": "#FFB627",        # Amber
        "danger": "#FF0000",         # Pure Red
        "muted": "#457B9D",          # Muted Blue
        "bg": "#0A0E27",             # Dark Navy Background
    }

def render_screen(console: Console, title: str, content: str, pause_text: str = None, stream: bool = False):
    """Render a standardized full-screen panel with fixed minimum height.
    
    Args:
        console: Rich Console instance
        title: Screen title
        content: Main content text
        pause_text: Optional text to show at bottom (e.g. "Press SPACE...")
        stream: If True, stream text character by character
    """
    import time
    import msvcrt
    import sys
    
    colors = get_defcon_colors()
    
    # Clear screen first
    console.clear()
    
    # Ensure minimum height by padding content
    lines = content.split('\n')
    min_height = 12
    if len(lines) < min_height:
        padding = "\n" * (min_height - len(lines))
    else:
        padding = ""
        
    # Create header
    header_text = f"[reverse][{colors['warning']} bold] COBRA COMMAND: {title} [/][/reverse]"
    
    # Function to render panel
    def get_panel(text):
        return Panel(
            text + padding,
            title=header_text,
            border_style=f"bold {colors['primary']}",
            box=box.HEAVY,
            style=f"on {colors['bg']}",
            padding=(1, 2)
        )

    if stream:
        # Draw initial empty panel
        console.print(get_panel(""))
        
        # Move cursor back up to redraw in place
        # (Rich Live is better for this, but let's try simple cursor movement first or just Live)
        from rich.live import Live
        
        current_text = ""
        # Use Live context for smooth updates
        with Live(get_panel(""), console=console, refresh_per_second=20, transient=True) as live:
            for char in content:
                # Allow skip
                if msvcrt.kbhit():
                    if msvcrt.getch() == b' ':
                        current_text = content
                        live.update(get_panel(current_text))
                        break
                
                current_text += char
                live.update(get_panel(current_text))
                time.sleep(0.01)  # Fast typing speed
        
        # Final static print to ensure it stays
        console.clear()
        console.print(get_panel(content))
    else:
        console.print(get_panel(content))
    
    if pause_text:
        console.print(f"[{colors['muted']}]{pause_text}[/]")

def select_scenario_variant_screen(console: Console, scenarios: list) -> str:
    """Render standardized scenario selection screen.
    
    Returns:
        Selected variant key
    """
    colors = get_defcon_colors()
    
    # Custom scenario list for simplified view (0.1)
    display_options = [
        {
            "key": "standard",
            "name": "Paced Start",
            "desc": "Standard timeline - 6 scripted turns."
        },
        {
            "key": "fast_start", 
            "name": "Fast Start",
            "desc": "Compressed Timeline - 3 scripted turns."
        }
    ]
    
    content = f"{TITLE_ART}\n\n"
    content += f"[{colors['primary']} bold]SELECT SCENARIO[/]\n\n"
    
    for idx, opt in enumerate(display_options, 1):
        content += f"[{colors['warning']} bold]{idx}. {opt['name']}[/]\n"
        content += f"   {opt['desc']}\n\n"
        
    render_screen(console, "SYSTEM INITIALISATION", content)
    
    # Get input with screen refresh
    while True:
        try:
            console.print(f"\n[{colors['primary']}]Select scenario (1-{len(display_options)}): [/]", end="")
            choice = input().strip()
            
            # Redraw screen to prevent scrolling artifacts
            # Only redraw if invalid input (prevents flashing on success)
            if not choice.isdigit() or not (1 <= int(choice) <= len(display_options)):
                render_screen(console, "SYSTEM INITIALISATION", content)
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(display_options):
                    return display_options[idx]["key"]
        except (KeyboardInterrupt, EOFError):
            raise typer.Exit()

def select_play_mode_screen(console: Console) -> str:
    """Render standardized gameplay mode selection screen.
    
    Returns:
        Selected mode key
    """
    colors = get_defcon_colors()
    
    modes = [
        ("classic", "Classic Wargame", "Traditional experience with visible metrics."),
        ("immersive", "Immersive Narrative", "Character-driven drama with hidden metrics."),
        ("emergent", "Emergent Drama", "Maximum LLM freedom (Experimental).")
    ]
    
    content = f"[{colors['primary']} bold]SELECT GAMEPLAY MODE[/]\n\n"
    
    for idx, (key, name, desc) in enumerate(modes, 1):
        content += f"[{colors['warning']} bold]{idx}. {name}[/]\n"
        content += f"   {desc}\n\n"
        
    render_screen(console, "CONFIGURE PARAMETERS", content)
    
    while True:
        try:
            console.print(f"\n[{colors['primary']}]Select mode (1-{len(modes)}): [/]", end="")
            choice = input().strip()
            
            # Redraw screen to keep UI clean
            # Only redraw if invalid input
            if not choice.isdigit() or not (1 <= int(choice) <= len(modes)):
                render_screen(console, "CONFIGURE PARAMETERS", content)
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(modes):
                    return modes[idx][0]
        except (KeyboardInterrupt, EOFError):
            raise typer.Exit()

