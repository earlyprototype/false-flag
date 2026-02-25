import time
import argparse
import os
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.live import Live
from rich.layout import Layout

# Final version: Pure rich.Live implementation for flicker-free animation.

# --- Import local pipeline tools ---
# --- Import local pipeline tools ---
# Add project root to sys.path to ensure 'Graphics' is importable
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from Graphics.Animations.tools.encode_halfblock import encode_halfblock
except ImportError:
    print("Error: Could not import 'encode_halfblock'.")
    print("Please ensure you are running this script from the project's root directory.")
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

# --- Main Demo ---
def run_demo(fps: int):
    console = Console()
    
    try:
        sprite_frames = load_and_encode_sprites()
    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        return

    # Create the master layout with three columns
    layout = Layout()
    layout.split_row(
        Layout(name="left_sprite", size=34),
        Layout(name="dialogue", ratio=1),
        Layout(name="right_sprite", size=34)
    )

    script_turn = 0
    turn_timer = 0
    player_anim_state = "idle"
    diplomat_anim_state = "idle"
    
    current_full_text = ""
    current_displayed_text = ""

    frame_delay = 1 / fps

    with Live(layout, console=console, screen=True, transient=True, refresh_per_second=fps) as live:
        while script_turn < len(CONVERSATION_SCRIPT):
            
            # --- Update State ---
            current_turn_info = CONVERSATION_SCRIPT[script_turn]
            speaker = current_turn_info["speaker"]
            
            if speaker != "pause" and current_full_text != current_turn_info["text"]:
                current_full_text = current_turn_info["text"]
                current_displayed_text = ""

            player_anim_state = "talk" if speaker == "player" else "idle"
            diplomat_anim_state = "talk" if speaker == "diplomat" else "idle"

            if len(current_displayed_text) < len(current_full_text):
                current_displayed_text += current_full_text[len(current_displayed_text)]

            player_anim_frame_index = turn_timer % len(sprite_frames[player_anim_state])
            diplomat_anim_frame_index = turn_timer % len(sprite_frames[diplomat_anim_state])

            # --- Prepare Renderables ---
            player_sprite_art = sprite_frames[player_anim_state][player_anim_frame_index]
            diplomat_sprite_art = sprite_frames[diplomat_anim_state][diplomat_anim_frame_index]
            
            if speaker == "player":
                diplomat_sprite_art = diplomat_sprite_art[:12]
            elif speaker == "diplomat":
                player_sprite_art = player_sprite_art[:12]

            player_sprite = Text("\n".join(player_sprite_art), style="white")
            diplomat_sprite = Text("\n".join(diplomat_sprite_art), style="bright_blue")

            dialogue_panel = Panel("")
            if speaker == "diplomat":
                dialogue_panel = Panel(
                    Text.from_markup(current_displayed_text),
                    title="President | United States", border_style="bright_blue", height=10
                )
            elif speaker == "player":
                dialogue_panel = Panel(
                    Text.from_markup(current_displayed_text),
                    title="You (Prime Minister)", border_style="white", height=10
                )
            
            # --- Update Layout ---
            layout["left_sprite"].update(Align.center(diplomat_sprite, vertical="bottom"))
            layout["right_sprite"].update(Align.center(player_sprite, vertical="bottom"))
            layout["dialogue"].update(Align.center(dialogue_panel, vertical="middle"))

            # --- Advance Script ---
            turn_timer += 1
            if len(current_displayed_text) == len(current_full_text) and turn_timer % (fps * 2) == 0: # Pause for 2s after typing
                turn_timer = 0
                current_full_text = ""
                current_displayed_text = ""
                script_turn += 1

            time.sleep(frame_delay)

if __name__ == "__main__":
    run_demo(fps=20)