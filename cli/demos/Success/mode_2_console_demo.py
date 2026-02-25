
import time
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.table import Table
from rich.text import Text
from rich.live import Live

def create_main_panel(layout: Layout) -> Panel:
    """Creates the main outer panel styled as a monitor bezel."""
    return Panel(layout, border_style="white")

def create_header_panel(turn: int) -> Panel:
    """Creates the main header panel with turn count."""
    header_grid = Table.grid(expand=True)
    header_grid.add_column(justify="left")
    header_grid.add_column(justify="right")
    header_grid.add_row("[bold cyan]COBRA SYSTEM CONSOLE[/] - EYES ONLY", f"TURN: {turn:02d}")
    return Panel(header_grid, style="bold white", border_style="white", height=3, padding=(0,1))

def create_status_panel() -> Panel:
    """Creates the status bar panel."""
    content = "TIME: 17:00 HRS  |  DATE: 2025-11-23  |  UK ALERT STATE: [bold yellow]AMBER[/]"
    return Panel(Text(content, justify="center"), title="[ STATUS ]", title_align="left", border_style="white")

def create_classic_stats_panel() -> Panel:
    """Creates the Classic Mode vital statistics panel."""
    content = "RISK: [bold red]78[/] [dim](Critical)[/dim]   STABILITY: [bold yellow]45[/] [dim](Poor)[/dim]   CASUALTIES: [bold]Mil 2, Civ 0[/bold]"
    return Panel(Text(content, justify="center"), title="[ VITAL STATISTICS ]", title_align="left", border_style="white")

def create_flags_panel() -> Panel:
    """Creates the active flags panel."""
    content = "> US_COMMITMENT_UNCERTAIN"
    return Panel(content, title="[ ACTIVE FLAGS ]", title_align="left", border_style="white", padding=(0, 1))

def create_command_panel() -> Panel:
    """Creates the command menu panel."""
    content = "/advise   /call <country>   /resources   /intel   /save   /decide"
    return Panel(Text(content, justify="center"), title="[ COMMAND MENU ]", title_align="left", border_style="white")

def run_demo(duration: int, speed: float):
    """Runs the Classic Console demo."""
    console = Console()
    
    # --- Ticker Setup ---
    ticker_text = " +++ Russian Armor movements near Suwałki Gap +++ Unrest in Dover reported by Home Office +++ Unconfirmed reports of naval skirmish in North Sea +++ "
    ticker_width = 100 
    frame = 0

    # --- Main Layout Setup ---
    console_layout = Layout()
    console_layout.split(
        Layout(create_header_panel(turn=4), name="header", size=3),
        Layout(name="body", ratio=1),
    )
    console_layout["body"].split(
        Layout(create_status_panel(), name="s_bar", size=3),
        Layout(create_classic_stats_panel(), name="v_stats", size=3),
        Layout(create_flags_panel(), name="flags", size=3),
        Layout(name="intel", ratio=1),
        Layout(create_command_panel(), name="commands", size=3),
    )
    
    try:
        with Live(create_main_panel(console_layout), console=console, screen=True, redirect_stderr=False, transient=True) as live:
            start_time = time.time()
            while time.time() - start_time < duration:
                # Animate the ticker
                display_text = (ticker_text * 3)[frame : frame + ticker_width]
                ticker_panel = Panel(
                    Text(display_text, justify="left", no_wrap=True),
                    title="[ INTEL STREAM ]", 
                    title_align="left", 
                    border_style="white"
                )
                console_layout["intel"].update(ticker_panel)
                
                frame = (frame + 1) % len(ticker_text)
                time.sleep(speed)
    
    except KeyboardInterrupt:
        pass
    finally:
        console.print("Demo finished.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demonstrate the Classic 'Console' UI mode.")
    parser.add_argument(
        "--duration", type=int, default=20, help="How long the demo should run in seconds."
    )
    parser.add_argument(
        "--speed", type=float, default=0.08, help="Ticker scroll speed (delay between frames)."
    )
    args = parser.parse_args()
    run_demo(duration=args.duration, speed=args.speed)
