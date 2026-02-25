import time
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.console import Group
from rich.live import Live

def create_contacts_panel(contacts: dict) -> Panel:
    """Creates the panel displaying the list of diplomatic contacts."""
    contacts_table = Table(box=None, show_header=False, expand=True, padding=(0, 2))
    contacts_table.add_column("Index", style="cyan", no_wrap=True, width=5)
    contacts_table.add_column("Contact", style="bold white", no_wrap=True, width=14)
    contacts_table.add_column("Country", no_wrap=True)
    contacts_table.add_column("Status", justify="right", no_wrap=True)

    for idx, details in contacts.items():
        status_style = "green" if details["status"] == "Online" else "red" if details["status"] == "Offline" else "yellow"
        contacts_table.add_row(f"{idx}.", details["title"], details["country"], f"[{status_style}]{details['status']}[/{status_style}]")

    info = Text("\nSimulating selection of '1. President | United States'...", style="yellow", justify="center")
    
    content_group = Group(contacts_table, info)

    return Panel(content_group, title="[bold]SECURE COMMS - CONTACTS[/]", border_style="bold white", padding=(1, 1))

def create_connecting_panel(contact_details: dict) -> Panel:
    """Creates a panel to show the 'connecting' message."""
    message = Text(f"Connecting to {contact_details['title']} | {contact_details['country']}...", style="yellow", justify="center")
    return Panel(message, border_style="yellow")

def create_call_view() -> Panel:
    """Creates a static, mocked-up panel of the conversation view."""
    foreign_leader_msg_text = (
        "Mr. Prime Minister, we need to discuss the situation on the Polish border. "
        "My intelligence suggests three [bold red]Typhoon-class submarines[/] have left port."
    )
    foreign_leader_msg = Panel(
        foreign_leader_msg_text,
        title="President | United States",
        title_align="left",
        border_style="bright_blue",
        width=60
    )

    player_msg = Panel(
        "I understand the urgency. We are monitoring the [yellow]Suwałki Gap[/] closely. What is your assessment?",
        title="Prime Minister | United Kingdom",
        title_align="left",
        border_style="white",
        width=60
    )

    conversation_group = Group(
        Align.left(foreign_leader_msg),
        Text(" "),  # Spacer
        Align.right(player_msg)
    )

    return Panel(
        conversation_group,
        title="[bold red]LIVE[/] | SECURE CHANNEL 4A",
        border_style="bold red",
        padding=(1, 2)
    )

def run_demo(connect_delay: int, final_view_duration: int):
    """Runs the Diplomacy Mode demo using a stable, state-based Live display."""
    console = Console()
    
    # This dictionary was missing from the scope of this function. It is now defined correctly.
    contacts = {
        "1": {"title": "President", "country": "United States", "status": "Online"},
        "2": {"title": "Chancellor", "country": "Germany", "status": "Online"},
        "3": {"title": "President", "country": "France", "status": "Do Not Disturb"},
        "4": {"title": "Ambassador", "country": "Russia", "status": "Offline"},
    }
    contact_to_call = contacts["1"] # Simulate choosing the first contact

    try:
        with Live(console=console, screen=True, redirect_stderr=False, transient=True) as live:
            # Stage 1: Show Menu
            live.update(create_contacts_panel(contacts))
            time.sleep(connect_delay)
            
            # Stage 2: Show Connecting
            live.update(create_connecting_panel(contact_to_call))
            time.sleep(connect_delay)

            # Stage 3: Show Final Call View
            live.update(create_call_view())
            time.sleep(final_view_duration)

    except KeyboardInterrupt:
        pass
    finally:
        console.print("Demo finished.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demonstrate the 'Diplomacy' UI mode.")
    parser.add_argument(
        "--delay",
        type=int,
        default=3,
        help="The simulated delay in seconds for each stage. Default: 3",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=5,
        help="How long the final view is shown. Default: 5",
    )
    args = parser.parse_args()

    run_demo(connect_delay=args.delay, final_view_duration=args.duration)