
import time
import argparse
from collections import deque
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from blessed import Terminal

# --- Mock Assets ---
ADVISOR_NAME = "National Security Advisor"
SPRITE_NEUTRAL = [
    "   _______   ",
    "  /       \  ",
    " /  o   o  \ ",
    " |    ^    | ",
    " \  `---'  / ",
    "  \_______/  ",
]
SPRITE_TALKING = [
    "   _______   ",
    "  /       \  ",
    " /  o   o  \ ",
    " |    ^    | ",
    " \  `---'  / ",
    "  \___o___/  ", # Mouth open
]

def create_speech_bubble(message: str, speaker: str, is_player: bool) -> Panel:
    """Creates a styled panel for a dialogue message."""
    if is_player:
        return Panel(
            message,
            title="You (Prime Minister)",
            title_align="left",
            border_style="white",
            width=60
        )
    else:
        return Panel(
            Text(message, justify="left"),
            title=speaker,
            title_align="left",
            border_style="bright_blue",
            width=60
        )

def run_demo(fps: int):
    """Runs the interactive Council Mode demo."""
    term = Terminal()
    console = Console()

    dialogue_history = deque(maxlen=10) # Holds (speaker, message) tuples
    dialogue_history.append((ADVISOR_NAME, "Good evening, Prime Minister. We have a situation."))
    
    input_buffer = ""
    is_advisor_replying = False
    advisor_reply_full = ""
    advisor_reply_current = ""
    advisor_anim_state = 0

    frame_delay = 1 / fps

    with term.cbreak(), term.hidden_cursor():
        console.clear()
        
        while True:
            # --- 1. Handle Input (Non-Blocking) ---
            key = term.inkey(timeout=0)
            if key:
                if key.is_sequence:
                    if key.name == "KEY_ENTER":
                        if input_buffer and not is_advisor_replying:
                            dialogue_history.append(("player", input_buffer))
                            input_buffer = ""
                            is_advisor_replying = True
                            # Mock response
                            advisor_reply_full = "Understood. The primary threat is from three [red]Typhoon-class submarines[/]. We must act."
                            advisor_reply_current = ""
                    elif key.name in ("KEY_BACKSPACE", "KEY_DELETE"):
                        input_buffer = input_buffer[:-1]
                    elif key.name == "KEY_ESCAPE":
                        break
                else:
                    input_buffer += key
            
            # --- 2. Update State ---
            if is_advisor_replying:
                advisor_anim_state = (advisor_anim_state + 1) % 2 # Toggle between 0 and 1
                if len(advisor_reply_current) < len(advisor_reply_full):
                    advisor_reply_current += advisor_reply_full[len(advisor_reply_current)]
                else:
                    dialogue_history.append((ADVISOR_NAME, advisor_reply_current))
                    is_advisor_replying = False
                    advisor_anim_state = 0 # Return to neutral
            
            # --- 3. Render Screen ---
            # Move cursor to home position instead of clearing to reduce flicker
            print(term.home, end="")
            
            # Render dialogue history
            for speaker, message in dialogue_history:
                is_player = (speaker == "player")
                bubble = create_speech_bubble(message, speaker, is_player)
                align = Align.right if is_player else Align.left
                console.print(align(bubble))
            
            # Render the currently streaming advisor reply
            if is_advisor_replying:
                sprite = SPRITE_TALKING if advisor_anim_state == 1 else SPRITE_NEUTRAL
                sprite_renderable = Text("\n".join(sprite), justify="center")
                
                bubble = create_speech_bubble(advisor_reply_current, ADVISOR_NAME, False)
                
                # Use a table to align sprite and bubble
                grid = Table.grid(expand=True)
                grid.add_column(width=15)
                grid.add_column()
                grid.add_row(sprite_renderable, bubble)
                console.print(Align.left(grid))

            # Render the input prompt
            prompt_panel = Panel(f"> {input_buffer}", title="[green]Your Input[/]", border_style="green")
            console.print(prompt_panel)
            console.print("Press ESC to exit.")

            time.sleep(frame_delay)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demonstrate the interactive 'Council' UI mode.")
    parser.add_argument(
        "--fps",
        type=int,
        default=20,
        help="Frames per second for the animation loop. Default: 20",
    )
    args = parser.parse_args()
    run_demo(fps=args.fps)
