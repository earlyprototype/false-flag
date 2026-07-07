import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.console import Group

def create_speech_bubble(text_content: str, speaker_title: str, is_player: bool) -> Align:
    """
    Creates a rich renderable that looks like a simple, aligned panel.
    """
    # Justify the title based on who is speaking
    title_alignment = "right" if is_player else "left"

    panel = Panel(
        text_content,
        title=f"[bold white]{speaker_title}[/bold white]",
        border_style="bright_blue" if not is_player else "white",
        width=60,
        title_align=title_alignment
    )

    # Align the entire panel to the left or right
    align_direction = "right" if is_player else "left"
    return Align(panel, align=align_direction)

def run_demo():
    """Renders a static scene demonstrating the speech bubble layout."""
    console = Console()

    # --- Create the individual bubbles ---
    bubble1 = create_speech_bubble(
        "Mr. Prime Minister, the situation is critical. My intelligence suggests three [bold red]Typhoon-class submarines[/bold red] have left port.",
        "National Security Advisor",
        is_player=False
    )

    bubble2 = create_speech_bubble(
        "I understand. We are monitoring the [yellow]Suwałki Gap[/yellow] closely. What is the CDS's assessment of our readiness?",
        "You (Prime Minister)",
        is_player=True
    )
    
    bubble3 = create_speech_bubble(
        "Our forces are at readiness level 2. We can sustain air patrols, but it will stretch our resources thin within 48 hours.",
        "Chief of the Defence Staff",
        is_player=False
    )

    # --- Group them together for display ---
    conversation = Group(
        bubble1,
        Text(" "),  # Spacer
        bubble2,
        Text(" "),  # Spacer
        bubble3
    )

    # --- Print the final result ---
    console.clear()
    console.print(Panel(conversation, title="[bold yellow]COUNCIL CHAMBER[/bold yellow]", border_style="yellow", padding=(1,2)))
    console.print("\n[dim]This is a static visual demo of the speech bubble layout.[/dim]")


if __name__ == "__main__":
    run_demo()
