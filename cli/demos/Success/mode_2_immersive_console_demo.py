
import time
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich.table import Table
from rich.text import Text

def create_header_panel(turn: int) -> Panel:
    """Creates the main header panel."""
    header_left = Text("[COBRA SYSTEM CONSOLE] - EYES ONLY", justify="left")
    header_right = Text(f"TURN: {turn:02d}", justify="right")
    
    header_table = Table.grid(expand=True)
    header_table.add_column()
    header_table.add_column()
    header_table.add_row(header_left, header_right)

    return Panel(header_table, style="bold white", border_style="bold white", height=3)

def create_status_panel() -> Panel:
    """Creates the status bar panel."""
    content = "TIME: 17:00 HRS  |  DATE: 2025-11-23  |  UK ALERT STATE: AMBER"
    return Panel(Text(content, justify="center"), title="[ STATUS ]", title_align="left", border_style="white")

def create_assessment_panel() -> Panel:
    """Creates the Immersive Mode situation assessment panel."""
    content = (
        "[bold]RISK:[/bold] Severe; rapidly escalating.\n"
        "[bold]ALLIANCE:[/bold] Wavering; key partners are hesitant to commit.\n"
        "[bold]DOMESTIC:[/bold] Anxious; public confidence is falling."
    )
    return Panel(content, title="[ SITUATION ASSESSMENT ]", title_align="left", border_style="white", padding=(1,2))

def create_observations_panel() -> Panel:
    """Creates the key observations panel."""
    content = "> The Foreign Secretary notes the US seems unusually non-committal."
    return Panel(content, title="[ KEY OBSERVATIONS ]", title_align="left", border_style="white", padding=(1,1))

def create_command_panel() -> Panel:
    """Creates the command menu panel."""
    content = "/advise   /call <country>   /resources   /intel   /save   /decide"
    return Panel(Text(content, justify="center"), title="[ COMMAND MENU ]", title_align="left", border_style="white")

def run_demo(duration: int, speed: float):
    """Runs the Immersive Console demo."""
    console = Console()
    
    # --- Ticker Setup ---
    ticker_text = " +++ Russian Armor movements near Suwałki Gap +++ Unrest in Dover reported by Home Office +++ Unconfirmed reports of naval skirmish in North Sea +++ "
    ticker_width = 80  # Assumed width for the ticker panel
    frame = 0

    # --- Main Layout Setup ---
    layout = Layout()
    layout.split(
        Layout(name="header", size=3),
        Layout(name="main_body"),
        Layout(name="footer", size=3),
    )
    layout["main_body"].split(
        Layout(name="upper_body", ratio=3),
        Layout(name="intel_stream", size=3),
    )
    layout["upper_body"].split(
        Layout(name="status_bar", size=3),
        Layout(name="assessment", ratio=1),
        Layout(name="observations", ratio=1),
    )
    
    # --- Populate Static Panels ---
    layout["header"].update(create_header_panel(turn=4))
    layout["status_bar"].update(create_status_panel())
    layout["assessment"].update(create_assessment_panel())
    layout["observations"].update(create_observations_panel())
    layout["footer"].update(create_command_panel())

    try:
        with Live(layout, console=console, screen=True, redirect_stderr=False, transient=True) as live:
            start_time = time.time()
            while time.time() - start_time < duration:
                # Animate the ticker
                display_text = (ticker_text * 3)[frame : frame + ticker_width]
                ticker_panel = Panel(
                    Text(display_text, justify="left"), 
                    title="[ INTEL STREAM ]", 
                    title_align="left", 
                    border_style="white"
                )
                layout["intel_stream"].update(ticker_panel)
                
                frame = (frame + 1) % len(ticker_text)
                time.sleep(speed)
    
    except KeyboardInterrupt:
        pass
    finally:
        console.print("Demo finished.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demonstrate the Immersive 'Console' UI mode.")
    parser.add_argument(
        "--duration",
        type=int,
        default=20,
        help="How long the demo should run in seconds. Default: 20",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=0.1,
        help="Ticker scroll speed (delay between frames). Lower is faster. Default: 0.1",
    )
    args = parser.parse_args()

    run_demo(duration=args.duration, speed=args.speed)
