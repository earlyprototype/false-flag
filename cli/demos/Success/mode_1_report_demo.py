import time
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.live import Live

def run_rich_only_demo(speed: float):
    """
    Runs the report view demo using only the 'rich' library,
    which is robust and already a core dependency.
    """
    console = Console()
    headline = "[bold red]CLASSIFIED DISPATCH[/] | M.O.D. | [cyan]WARSAW[/]"
    body_text = (
        "Initial reports from MI6 assets in Poland indicate significant and uncoordinated movements of Russian armor "
        "near the Suwałki Gap. Communications intercepts suggest a high degree of confusion among local commanders.\n\n"
        "The Polish government has placed its 2nd Mechanised Corps on high alert but is awaiting guidance from "
        "NATO command. This activity does not align with scheduled military exercises.\n\n"
        "Further intelligence is pending. This is a developing situation."
    )

    try:
        # Buffer to hold the text as it is "typed"
        typed_text = ""

        with Live(console=console, screen=False, redirect_stderr=False, transient=True) as live:
            # Loop through the source text character by character
            for char in body_text:
                # Append the character to our buffer
                typed_text += char
                
                # Create the panel with the current state of the buffer
                panel = Panel(
                    typed_text,
                    title=headline,
                    border_style="bold white",
                    padding=(1, 2)
                )
                
                # Update the live display, forcing an immediate refresh
                live.update(panel, refresh=True)
                
                # Control the typing speed
                time.sleep(speed)
            
            # Keep the final frame visible for a moment
            time.sleep(3)

    except KeyboardInterrupt:
        pass
    finally:
        console.print("Demo finished.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demonstrate the 'Report' UI mode using only 'rich'.")
    parser.add_argument(
        "--speed",
        type=float,
        default=0.02,
        help="Typing speed (delay between characters). Lower is faster. Default: 0.02",
    )
    args = parser.parse_args()
    
    run_rich_only_demo(speed=args.speed)
