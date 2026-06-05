import time
import argparse
import os
import json
from PIL import Image
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from blessed import Terminal

# This is the final prototype, combining all our design decisions and technical solutions.

# --- Import local pipeline tools ---
# Add project root to sys.path to ensure 'Graphics' is importable
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from Graphics.Animations.tools.encode_halfblock import encode_halfblock

# --- Configuration ---
SPRITE_ASSET_PATH = "assets/anchor_small"
SPRITE_FRAMES_TO_LOAD = {
    "neutral": "anchor_neutral_01.png",
    "blink": "anchor_blink_01.png",
    "talk": ["anchor_talk_a_01.png", "anchor_talk_o_01.png", "anchor_talk_e_01.png"]
}

CONVERSATION_SCRIPT = [
    {"speaker": "diplomat", "text": "Prime Minister. My government is formally protesting your naval blockade. It is an act of aggression."},
    {"speaker": "player", "text": "This is not a blockade. It is a defensive quarantine in response to your [red]unannounced submarine movements[/]."},
    {"speaker": "diplomat", "text": "These are routine patrols in international waters. Your response is disproportionate and dangerous."},
    {"speaker": "player", "text": "These are not routine patrols. Our intelligence on the [yellow]Suwałki Gap[/] suggests otherwise."},
    {"speaker": "diplomat", "text": "Your 'intelligence' is mistaken. You must stand down your fleet immediately, or we will have no choice but to escalate."},
    {"speaker": "player", "text": "And we will have no choice but to respond in kind. This conversation is over."},
    {"speaker": "pause", "text": ""}
]

# --- Helper Functions ---

def load_and_encode_sprites() -> dict:
    """Loads PNGs, converts them to half-block text, and returns a dict of frames."""
    encoded_frames = {"idle": [], "talk": []}
    
    neutral_path = os.path.join(SPRITE_ASSET_PATH, SPRITE_FRAMES_TO_LOAD["neutral"])
    blink_path = os.path.join(SPRITE_ASSET_PATH, SPRITE_FRAMES_TO_LOAD["blink"])
    if not os.path.exists(neutral_path) or not os.path.exists(blink_path):
        raise FileNotFoundError(f"Cannot find placeholder assets in {SPRITE_ASSET_PATH}. Please run generate_small_sprites.py first.")

    neutral_frames = encode_halfblock(neutral_path, palette="db16")
    blink_frames = encode_halfblock(blink_path, palette="db16")
    for _ in range(50): encoded_frames["idle"].append(neutral_frames)
    for _ in range(3): encoded_frames["idle"].append(blink_frames)

    for frame_file in SPRITE_FRAMES_TO_LOAD["talk"]:
        path = os.path.join(SPRITE_ASSET_PATH, frame_file)
        frames = encode_halfblock(path, palette="db16")
        for _ in range(5): encoded_frames["talk"].append(frames)
    
    return encoded_frames

def render_sprite(term: Terminal, x: int, y: int, sprite_frame: list[str], tint_markup: str):
    """Draws a single pre-encoded sprite frame at a given location with a tint."""
    for i, line in enumerate(sprite_frame):
        line_to_print = f"[{tint_markup}]{line}[/{tint_markup}]"
        print(term.move_xy(x, y + i) + str(Text.from_markup(line_to_print)), end="")

def render_bubble(console: Console, text: str, title: str, border_color: str) -> list[str]:
    """Renders a rich Panel 'off-screen' and returns its text lines."""
    panel = Panel(Text.from_markup(text), title=f"[bold white]{title}[/bold white]", border_style=border_color, width=50)
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
        print(f"Error: {e}")
        return

    script_turn = 0
    turn_timer = 0
    player_anim_state = "idle"
    diplomat_anim_state = "idle"
    player_anim_frame = 0
    diplomat_anim_frame = 0
    
    current_full_text = ""
    current_displayed_text = ""

    # Define layout coordinates
    SPRITE_WIDTH = 32
    BUBBLE_WIDTH = 50
    H_PADDING = 2

    diplomat_sprite_x = 2
    player_sprite_x = term.width - SPRITE_WIDTH - 2
    bubble_x = diplomat_sprite_x + SPRITE_WIDTH + H_PADDING
    
    with term.cbreak(), term.hidden_cursor():
        while True:
            key = term.inkey(timeout=1/fps)
            if key.lower() == 'q':
                break

            current_turn_info = CONVERSATION_SCRIPT[script_turn]
            speaker = current_turn_info["speaker"]
            
            if speaker != "pause" and current_full_text != current_turn_info["text"]:
                current_full_text = current_turn_info["text"]
                current_displayed_text = ""

            player_anim_state = "talk" if speaker == "player" else "idle"
            diplomat_anim_state = "talk" if speaker == "diplomat" else "idle"

            if len(current_displayed_text) < len(current_full_text):
                current_displayed_text += current_full_text[len(current_displayed_text)]

            player_anim_frame = (player_anim_frame + 1) % len(sprite_frames[player_anim_state])
            diplomat_anim_frame = (diplomat_anim_frame + 1) % len(sprite_frames[diplomat_anim_state])
            
            print(term.home + term.clear, end="")

            # Draw Header
            console.print(Text("[bold red]LIVE[/] | SECURE DIPLOMATIC CHANNEL", justify="center"))

            # Draw Sprites
            render_sprite(term, diplomat_sprite_x, 4, sprite_frames[diplomat_anim_state][diplomat_anim_frame], "bright_blue")
            render_sprite(term, player_sprite_x, 4, sprite_frames[player_anim_state][player_anim_frame], "white")
            
            # Render the correct speech bubble
            if speaker == "diplomat":
                bubble_lines = render_bubble(console, current_displayed_text, "President | United States", "bright_blue")
                for i, line in enumerate(bubble_lines):
                    print(term.move_xy(bubble_x, 3 + i) + line, end="")
            elif speaker == "player":
                bubble_lines = render_bubble(console, current_displayed_text, "You (Prime Minister)", "white")
                for i, line in enumerate(bubble_lines):
                    print(term.move_xy(bubble_x, 13 + i) + line, end="")
            
            # Draw Footer
            print(term.move_xy(0, term.height - 2), end="")
            console.print(Text("Final dialogue prototype. Press 'q' to quit.", justify="center"))
            
            turn_timer += 1
            if turn_timer > (len(current_full_text) + 30):
                turn_timer = 0
                current_displayed_text = ""
                script_turn = (script_turn + 1) % len(CONVERSATION_SCRIPT)
    
    print(term.clear)

if __name__ == "__main__":
    # The argparse import was missing. It is now included at the top of the file.
    parser = argparse.ArgumentParser(description="Final dialogue scene prototype.")
    parser.add_argument("--fps", type=int, default=20, help="Frames per second.")
    args = parser.parse_args()
    try:
        run_demo(fps=args.fps)
    except Exception as e:
        term = Terminal()
        print(term.clear)
        print(f"An error occurred: {e}")