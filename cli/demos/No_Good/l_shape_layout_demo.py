
import time
import argparse
import os
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from blessed import Terminal

# This demo implements the 'L-shape' layout using a manual rendering loop.

# --- Import local pipeline tools ---
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from Graphics.Animations.tools.encode_halfblock import encode_halfblock
except ImportError:
    print("Error: Could not import 'encode_halfblock'. Please run from the project root.")
    exit(1)

# --- Configuration ---
SPRITE_ASSET_PATH = "assets/anchor_small"
SPRITE_FRAMES_TO_LOAD = {
    "neutral": "anchor_neutral_01.png",
    "blink": "anchor_blink_01.png",
    "talk": ["anchor_talk_a_01.png", "anchor_talk_o_01.png"]
}

CONVERSATION_SCRIPT = [
    {"speaker": "diplomat", "text": "Prime Minister. Your naval blockade is an unacceptable act of aggression. We demand you stand down your fleet."},
    {"speaker": "player", "text": "This is a defensive quarantine in response to your [red]unannounced submarine movements[/]. Stand down *your* assets."},
    {"speaker": "diplomat", "text": "These are routine patrols in international waters. Your response is disproportionate and will have severe consequences."},
    {"speaker": "player", "text": "Our intelligence on the [yellow]Suwałki Gap[/] suggests otherwise. The quarantine holds. End of discussion."},
    {"speaker": "pause", "text": ""}
]

# --- Helper Functions ---

def load_and_encode_sprites() -> dict:
    encoded_frames = {"idle": [], "talk": []}
    
    # Idle Animation
    neutral_frames = encode_halfblock(os.path.join(SPRITE_ASSET_PATH, SPRITE_FRAMES_TO_LOAD["neutral"]), palette="db16")
    blink_frames = encode_halfblock(os.path.join(SPRITE_ASSET_PATH, SPRITE_FRAMES_TO_LOAD["blink"]), palette="db16")
    for _ in range(60): encoded_frames["idle"].append(neutral_frames)
    for _ in range(4): encoded_frames["idle"].append(blink_frames)

    # Talking Animation
    for frame_file in SPRITE_FRAMES_TO_LOAD["talk"]:
        frames = encode_halfblock(os.path.join(SPRITE_ASSET_PATH, frame_file), palette="db16")
        for _ in range(8): encoded_frames["talk"].append(frames)
    
    return encoded_frames

def render_sprite(term: Terminal, x: int, y: int, sprite_art: list[str], tint_markup: str):
    for i, line in enumerate(sprite_art):
        line_to_print = f"[{tint_markup}]{line}[/{tint_markup}]"
        print(term.move_xy(x, y + i) + str(Text.from_markup(line_to_print)), end="")

def render_bubble(console: Console, text: str, title: str, border_color: str, width: int) -> list[str]:
    panel = Panel(Text.from_markup(text), title=f"[bold white]{title}[/bold white]", border_style=border_color, width=width)
    with console.capture() as capture:
        console.print(panel)
    return capture.get().splitlines()

# --- Main Demo ---

def run_demo(fps: int):
    term = Terminal()
    console = Console(width=term.width) 

    try:
        sprite_frames = load_and_encode_sprites()
    except FileNotFoundError as e:
        print(f"[bold red]Error:[/bold red] {e}")
        return

    script_turn = 0
    turn_timer = 0
    
    with term.cbreak(), term.hidden_cursor():
        print(term.clear)
        while True:
            key = term.inkey(timeout=1/fps)
            if key.lower() == 'q' or script_turn >= len(CONVERSATION_SCRIPT):
                break

            # --- State Update ---
            current_turn_info = CONVERSATION_SCRIPT[script_turn]
            speaker = current_turn_info["speaker"]
            
            player_anim_state = "talk" if speaker == "player" else "idle"
            diplomat_anim_state = "talk" if speaker == "diplomat" else "idle"

            player_anim_frame = sprite_frames[player_anim_state][turn_timer % len(sprite_frames[player_anim_state])]
            diplomat_anim_frame = sprite_frames[diplomat_anim_state][turn_timer % len(sprite_frames[diplomat_anim_state])]
            
            # --- Flicker-Free Rendering ---
            print(term.home, end="")

            # Draw Sprites (full or ducked)
            if speaker == "player":
                render_sprite(term, 2, 15, diplomat_anim_frame[:12], "bright_blue") # Ducked
                render_sprite(term, term.width - 34, 4, player_anim_frame, "white") # Full
            else: # Diplomat or pause
                render_sprite(term, 2, 4, diplomat_anim_frame, "bright_blue") # Full
                render_sprite(term, term.width - 34, 15, player_anim_frame[:12], "white") # Ducked

            # --- L-Shape Bubble Logic ---
            # Clear previous bubble areas before drawing a new one
            bubble_area_height = 10
            # Clear left side
            for i in range(bubble_area_height): print(term.move_xy(20, 2 + i) + " " * 80, end="")
            # Clear right side (is not needed if left is big enough)
            
            if speaker == "diplomat":
                bubble_lines = render_bubble(console, current_turn_info["text"], "President | United States", "bright_blue", width=80)
                for i, line in enumerate(bubble_lines):
                    print(term.move_xy(20, 2 + i) + line, end="")
            elif speaker == "player":
                bubble_lines = render_bubble(console, current_turn_info["text"], "You (Prime Minister)", "white", width=80)
                for i, line in enumerate(bubble_lines):
                    print(term.move_xy(20, 2 + i) + line, end="")

            # Draw Footer
            print(term.move_xy(0, term.height - 2) + "L-Shape Layout Demo. Press 'q' to quit.", end="")
            
            # --- Advance Script ---
            turn_timer += 1
            if turn_timer >= 120: # Advance every 6 seconds approx (120 frames / 20 fps)
                turn_timer = 0
                script_turn += 1
    
    print(term.clear)

if __name__ == "__main__":
    run_demo(fps=20)
