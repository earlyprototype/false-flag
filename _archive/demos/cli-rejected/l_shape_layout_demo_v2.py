import time
import argparse
import os
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from blessed import Terminal

# This is v2 of the L-shape layout demo, fixing layout and flicker issues.

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
    {"speaker": "player", "text": "This is not a blockade. It is a defensive quarantine in response to your [red]unannounced submarine movements[/]. Stand down *your* assets."},
    {"speaker": "diplomat", "text": "These are routine patrols in international waters. Your response is disproportionate and will have severe consequences."},
    {"speaker": "player", "text": "Our intelligence on the [yellow]Suwałki Gap[/] suggests otherwise. The quarantine holds. End of discussion."},
    {"speaker": "pause", "text": ""}
]

# --- Helper Functions ---

def load_and_encode_sprites() -> dict:
    """Loads PNGs, converts them to half-block text, and returns a dict of frames."""
    encoded_frames = {"idle": [], "talk": []}
    neutral_path = os.path.join(SPRITE_ASSET_PATH, SPRITE_FRAMES_TO_LOAD["neutral"])
    blink_path = os.path.join(SPRITE_ASSET_PATH, SPRITE_FRAMES_TO_LOAD["blink"])
    if not os.path.exists(neutral_path) or not os.path.exists(blink_path):
        raise FileNotFoundError(f"Cannot find placeholder assets in {SPRITE_ASSET_PATH}. Run 'generate_small_sprites.py' first.")
    neutral_frames = encode_halfblock(neutral_path, palette="db16")
    blink_frames = encode_halfblock(blink_path, palette="db16")
    for _ in range(60): encoded_frames["idle"].append(neutral_frames)
    for _ in range(4): encoded_frames["idle"].append(blink_frames)
    for frame_file in SPRITE_FRAMES_TO_LOAD["talk"]:
        path = os.path.join(SPRITE_ASSET_PATH, frame_file)
        frames = encode_halfblock(path, palette="db16")
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
    previous_speaker = None
    
    with term.cbreak(), term.hidden_cursor():
        print(term.clear)
        while True:
            key = term.inkey(timeout=1/fps)
            if key.lower() == 'q' or script_turn >= len(CONVERSATION_SCRIPT):
                break

            current_turn_info = CONVERSATION_SCRIPT[script_turn]
            speaker = current_turn_info["speaker"]
            
            if speaker != previous_speaker:
                print(term.clear)
                previous_speaker = speaker
            else:
                print(term.home, end="")

            # --- Final Layout Calculation ---
            SPRITE_WIDTH = 32
            H_PADDING = 2
            diplomat_sprite_x = 0  # Absolute left edge
            player_sprite_x = term.width - SPRITE_WIDTH # Absolute right edge
            
            bubble_x = diplomat_sprite_x + SPRITE_WIDTH + H_PADDING
            bubble_width = player_sprite_x - bubble_x - H_PADDING
            
            # --- State Update ---
            player_anim_state = "talk" if speaker == "player" else "idle"
            diplomat_anim_state = "talk" if speaker == "diplomat" else "idle"

            player_anim_frame = sprite_frames[player_anim_state][turn_timer % len(sprite_frames[player_anim_state])]
            diplomat_anim_frame = sprite_frames[diplomat_anim_state][turn_timer % len(sprite_frames[diplomat_anim_state])]

            # Apply "ducking"
            if speaker == "player":
                diplomat_anim_frame = diplomat_anim_frame[:12]
            elif speaker == "diplomat":
                player_anim_frame = player_anim_frame[:12]
            
            # --- Rendering ---
            render_sprite(term, diplomat_sprite_x, 4, diplomat_anim_frame, "bright_blue")
            render_sprite(term, player_sprite_x, 4, player_anim_frame, "white")
            
            # Clear the middle dialogue area to prevent artifacts
            bubble_area_height = 20
            for i in range(bubble_area_height):
                print(term.move_xy(bubble_x, 2 + i) + " " * bubble_width, end="")
            
            # Draw the correct speech bubble
            if speaker == "diplomat":
                bubble_lines = render_bubble(console, current_turn_info["text"], "President | United States", "bright_blue", bubble_width)
                for i, line in enumerate(bubble_lines):
                    print(term.move_xy(bubble_x, 3 + i) + line, end="")
            elif speaker == "player":
                bubble_lines = render_bubble(console, current_turn_info["text"], "You (Prime Minister)", "white", bubble_width)
                for i, line in enumerate(bubble_lines):
                    print(term.move_xy(bubble_x, 13 + i) + line, end="")

            # Draw Header/Footer
            print(term.move_xy(0, 0) + str(Text("[bold red]LIVE[/]", justify="center", width=term.width)))
            print(term.move_xy(0, term.height - 2) + "Press 'q' to quit.", end="")
            
            # --- Advance Script ---
            turn_timer += 1
            if turn_timer >= (fps * 7): 
                turn_timer = 0
                script_turn += 1

    print(term.clear)

if __name__ == "__main__":
    run_demo(fps=20)