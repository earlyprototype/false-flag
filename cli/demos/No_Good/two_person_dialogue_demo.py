import time
import json
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from blessed import Terminal

# --- Mock Assets ---
# This simulates loading pre-rendered ASCII art frames for a character.
# In a real app, this would come from a compiled artifact JSON.
SPRITE_DATA = {
    "neutral": [
        "   _______   ",
        "  /       \\  ",
        " /  o   o  \\ ",
        " |    ^    | ",
        " \  `---'  / ",
        "  \\_______/  ",
        "  /\\       \\  ",
        " /  \\-----/   ",
        " |  SHIRT  |   ",
        " |   TIE   |   ",
        " |  JACKET |   ",
        "  \\       /    ",
        "   \\_____/     "
    ],
    "blink": [
        "   _______   ",
        "  /       \\  ",
        " /  -   -  \\ ",
        " |    ^    | ",
        " \  `---'  / ",
        "  \\_______/  ",
        "  /\\       \\  ",
        " /  \\-----/   ",
        " |  SHIRT  |   ",
        " |   TIE   |   ",
        " |  JACKET |   ",
        "  \\       /    ",
        "   \\_____/     "
    ],
    "talk": [
        "   _______   ",
        "  /       \\  ",
        " /  o   o  \\ ",
        " |    ^    | ",
        " \  `o o'  / ", # Mouth open
        "  \\_______/  ",
        "  /\\       \\  ",
        " /  \\-----/   ",
        " |  SHIRT  |   ",
        " |   TIE   |   ",
        " |  JACKET |   ",
        "  \\       /    ",
        "   \\_____/     "
    ]
}

# A pre-scripted conversation for the demo
CONVERSATION_SCRIPT = [
    {"speaker": "diplomat", "line": "Mr. Prime Minister, we must de-escalate.\nMy government sees your naval movements\nas a provocation.", "duration": 80},
    {"speaker": "player", "line": "Our movements are purely defensive. The\nprovocation was the [red]unannounced\nsubmarine activity[/].", "duration": 80},
    {"speaker": "diplomat", "line": "A matter of perspective. We need to\nestablish a dialogue, not a blockade.", "duration": 70},
    {"speaker": "player", "line": "Agreed. What does your government propose?", "duration": 40},
    {"speaker": "pause", "duration": 30}
]

def render_sprite(term: Terminal, x: int, y: int, frames: dict, anim_state: str, tint_color: str):
    """Draws a specific sprite frame at a given location with color."""
    sprite_art = frames.get(anim_state, frames["neutral"])
    for i, line in enumerate(sprite_art):
        # Apply a simple tint to the suit/tie for character differentiation
        line_to_print = line.replace("JACKET", f"[{tint_color}]JACKET[/]").replace("TIE", f"[{tint_color}]TIE[/]")
        print(term.move_xy(x, y + i) + str(Text.from_markup(line_to_print)), end="")

def render_bubble(console: Console, text_content: str, title: str, border_color: str) -> list[str]:
    """Renders a rich Panel 'off-screen' and returns its text lines."""
    panel = Panel(Text(text_content, justify="left"), title=title, border_style=border_color, width=45)
    with console.capture() as capture:
        console.print(panel)
    return capture.get().splitlines()

def run_demo(fps: int):
    """Runs the two-person dialogue demo."""
    term = Terminal()
    # Use a fixed width console for predictable layout rendering
    console = Console(width=120) 
    
    script_step = 0
    step_timer = 0
    player_anim = "neutral"
    diplomat_anim = "neutral"

    with term.cbreak(), term.hidden_cursor():
        print(term.clear)
        while True:
            key = term.inkey(timeout=1/fps)
            if key.lower() == 'q':
                break

            # --- Update animation states based on who is 'speaking' ---
            current_line_info = CONVERSATION_SCRIPT[script_step]
            
            if current_line_info["speaker"] == "player":
                player_anim = "talk" if (step_timer // 4) % 2 == 0 else "neutral"
                diplomat_anim = "blink" if (step_timer % 70) < 3 else "neutral"
            elif current_line_info["speaker"] == "diplomat":
                diplomat_anim = "talk" if (step_timer // 4) % 2 == 0 else "neutral"
                player_anim = "blink" if (step_timer % 60) < 3 else "neutral"
            else: # Pause state
                player_anim = "blink" if (step_timer % 60) < 3 else "neutral"
                diplomat_anim = "blink" if (step_timer % 70) < 3 else "neutral"

            # --- Manual Rendering on each frame ---
            print(term.home, end="") 

            # Render Sprites
            render_sprite(term, 2, 4, SPRITE_DATA, diplomat_anim, "bright_blue")
            render_sprite(term, term.width - 22, 4, SPRITE_DATA, player_anim, "white")
            
            # Render the correct speech bubble for the current line
            if current_line_info["speaker"] == "diplomat":
                bubble_lines = render_bubble(console, current_line_info["line"], "President | United States", "bright_blue")
                for i, line in enumerate(bubble_lines):
                    print(term.move_xy(25, 4 + i) + line, end="")
            elif current_line_info["speaker"] == "player":
                bubble_lines = render_bubble(console, current_line_info["line"], "You (Prime Minister)", "white")
                for i, line in enumerate(bubble_lines):
                    print(term.move_xy(term.width - 70, 4 + i) + line, end="")

            # Draw header and footer
            print(term.move_xy(0, 0) + str(Text("[bold red]LIVE[/] | SECURE DIPLOMATIC CHANNEL", justify="center", width=term.width)), end="")
            print(term.move_xy(0, term.height - 2) + "A non-interactive demo of a two-person dialogue scene. Press 'q' to quit.", end="")
            
            # --- Update Timers to advance the script ---
            step_timer += 1
            if step_timer >= current_line_info["duration"]:
                step_timer = 0
                script_step = (script_step + 1) % len(CONVERSATION_SCRIPT)

    print(term.clear)

if __name__ == "__main__":
    run_demo(fps=20)