import time
import os
import sys
import random
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from blessed import Terminal

# War Room Multi-Character Demo: All cabinet members visible simultaneously

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# --- Import local pipeline tools ---
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from Graphics.Animations.tools.encode_halfblock import encode_halfblock
except ImportError as e:
    print(f"Error: Could not import 'encode_halfblock': {e}")
    print("Please run from the project root.")
    exit(1)

# --- Configuration ---
# Character positions with DEPTH (closer = lower on screen, larger, in focus)
# Using 3 depth layers: background, middle, foreground
CHARACTERS = {
    "pm": {
        "name": "Prime Minister",
        "sprite_path": "assets/anchor_small",
        "prefix": "anchor",
        "position": {"x": 55, "y": 4},  # FOREGROUND - close to camera
        "depth": "foreground",
        "crop": None,  # Full height when speaking
        "color": "white"
    },
    "defence": {
        "name": "Defence Secretary",
        "sprite_path": "assets/diplomat_grey",
        "prefix": "diplomat_grey",
        "position": {"x": 5, "y": 2},  # BACKGROUND - far from camera (higher Y = farther)
        "depth": "background",
        "crop": 20,  # Show only top 20 lines (partial view, farther away)
        "color": "cyan"
    },
    "foreign": {
        "name": "Foreign Secretary",
        "sprite_path": "assets/diplomat_female_senior",
        "prefix": "diplomat_female_senior",
        "position": {"x": 80, "y": 2},  # BACKGROUND - far from camera
        "depth": "background",
        "crop": 20,  # Partial view
        "color": "bright_blue"
    },
    "nsa": {
        "name": "National Security Advisor",
        "sprite_path": "assets/diplomat_female_dark",
        "prefix": "diplomat_female_dark",
        "position": {"x": 25, "y": 3},  # MIDDLE - medium distance
        "depth": "middle",
        "crop": 30,  # More visible than background
        "color": "blue"
    }
}

CONVERSATION_SCRIPT = [
    {
        "speaker": "pm",
        "text": "The Americans have imposed a naval quarantine. Our submarines are exposed. I need options - now."
    },
    {
        "speaker": "defence",
        "text": "Prime Minister, extraction under quarantine is high-risk. We estimate a 40% chance of engagement if we move."
    },
    {
        "speaker": "foreign",
        "text": "We cannot act unilaterally. I recommend immediate consultation with NATO allies and direct communication with Washington."
    },
    {
        "speaker": "nsa",
        "text": "Our latest intelligence indicates the Americans have positioned destroyers at all exit vectors. They're anticipating our response."
    },
    {
        "speaker": "pm",
        "text": "Foreign Secretary, open channels with State Department. Defence, prepare contingency extraction plans. NSA, continue monitoring. Report back in 90 minutes."
    },
    {
        "speaker": "pause",
        "text": ""
    }
]

# --- Helper Functions ---
def load_and_encode_sprites(sprite_path: str, frame_prefix: str) -> dict:
    """Loads PNGs, converts them to half-block text, and returns a dict of frames."""
    encoded_frames = {"idle": [], "talk": []}
    neutral_path = os.path.join(sprite_path, f"{frame_prefix}_neutral_01.png")
    blink_path = os.path.join(sprite_path, f"{frame_prefix}_blink_01.png")
    
    if not os.path.exists(neutral_path) or not os.path.exists(blink_path):
        raise FileNotFoundError(f"Cannot find assets in {sprite_path}")
    
    neutral_frames = encode_halfblock(neutral_path, mode="16", palette="db16")
    blink_frames = encode_halfblock(blink_path, mode="16", palette="db16")
    
    for _ in range(60): 
        encoded_frames["idle"].append(neutral_frames)
    for _ in range(4): 
        encoded_frames["idle"].append(blink_frames)
    
    talk_frames = ["a", "e", "o"]
    for viseme in talk_frames:
        path = os.path.join(sprite_path, f"{frame_prefix}_talk_{viseme}_01.png")
        frames = encode_halfblock(path, mode="16", palette="db16")
        for _ in range(8): 
            encoded_frames["talk"].append(frames)
    
    return encoded_frames

def render_sprite(term: Terminal, x: int, y: int, sprite_art: list[str]):
    for i, line in enumerate(sprite_art):
        print(term.move_xy(x, y + i) + str(Text.from_markup(line)), end="")

def render_bubble(console: Console, text: str, title: str, border_color: str, width: int, height: int = None) -> list[str]:
    if height:
        lines_needed = height - 2
        if text:
            temp_console = Console(width=width - 4, legacy_windows=False)
            with temp_console.capture() as capture:
                temp_console.print(Text.from_markup(text))
            actual_lines = len(capture.get().splitlines())
            padding_lines = max(0, lines_needed - actual_lines)
            text = text + "\n" * padding_lines
        else:
            text = "\n" * (lines_needed - 1) if lines_needed > 0 else ""
    
    panel = Panel(Text.from_markup(text), title=f"[bold white]{title}[/bold white]", border_style=border_color, width=width)
    with console.capture() as capture:
        console.print(panel)
    return capture.get().splitlines()

def clear_region(term: Terminal, x: int, y: int, width: int, height: int):
    empty_line = " " * width
    for i in range(height):
        print(term.move_xy(x, y + i) + empty_line, end="")

def calculate_bubble_height(text: str, bubble_width: int, console: Console, min_height: int = 3, max_height: int = 8) -> int:
    inner_width = bubble_width - 4
    temp_console = Console(width=inner_width, legacy_windows=False)
    with temp_console.capture() as capture:
        temp_console.print(Text.from_markup(text))
    text_lines = capture.get().splitlines()
    required_height = len(text_lines) + 2
    return max(min_height, min(required_height, max_height))

# --- Main Demo ---
def run_demo(fps: int):
    term = Terminal()
    console = Console(width=term.width)

    # Load all character sprites
    character_frames = {}
    print("Loading sprites...")
    for char_id, char_info in CHARACTERS.items():
        try:
            frames = load_and_encode_sprites(char_info["sprite_path"], char_info["prefix"])
            character_frames[char_id] = frames
        except FileNotFoundError as e:
            print(f"Error loading {char_info['name']} sprites: {e}")
            return

    script_turn = 0
    turn_timer = 0
    previous_speaker = None
    text_reveal_counter = 0
    last_text_reveal_counter = -1
    bubble_border_drawn = False
    current_bubble_x = 0
    current_bubble_y = 0
    current_bubble_width = 0
    current_bubble_height = 0
    rendered_text_lines = []
    
    with term.cbreak(), term.hidden_cursor():
        while True:
            key = term.inkey(timeout=1/fps)
            if key.lower() == 'q' or script_turn >= len(CONVERSATION_SCRIPT):
                break

            current_turn_info = CONVERSATION_SCRIPT[script_turn]
            speaker = current_turn_info["speaker"]
            
            if speaker != previous_speaker:
                print(term.clear)
                previous_speaker = speaker
                text_reveal_counter = 0
                last_text_reveal_counter = -1
                rendered_text_lines = []
                bubble_border_drawn = False
            else:
                print(term.home, end="")

            # --- Render ALL characters with DEPTH (background to foreground) ---
            # Render in depth order: background -> middle -> foreground
            depth_order = ["background", "middle", "foreground"]
            
            for depth_layer in depth_order:
                for char_id, char_info in CHARACTERS.items():
                    if char_info["depth"] != depth_layer:
                        continue
                        
                    frames = character_frames[char_id]
                    pos = char_info["position"]
                    crop = char_info.get("crop", None)
                    
                    # Determine if this character is speaking
                    if speaker == char_id:
                        # Speaking - use random talk frame, show full height
                        anim_frame = random.choice(frames["talk"])
                        # Speaking characters move to foreground (no crop)
                        render_sprite(term, pos["x"], pos["y"], anim_frame)
                    else:
                        # Idle - use sequential idle animation
                        anim_frame = frames["idle"][turn_timer % len(frames["idle"])]
                        # Apply depth cropping for non-speakers
                        if crop:
                            cropped_frame = anim_frame[:crop]  # Show only top N lines
                            render_sprite(term, pos["x"], pos["y"], cropped_frame)
                        else:
                            render_sprite(term, pos["x"], pos["y"], anim_frame)

            # --- Speech Bubble (only for current speaker) ---
            if speaker != "pause" and speaker in CHARACTERS:
                speaker_info = CHARACTERS[speaker]
                char_pos = speaker_info["position"]
                
                # Position bubble above the speaker
                bubble_x = char_pos["x"]
                bubble_width = 30
                bubble_y = max(0, char_pos["y"] - 9)  # 9 lines above sprite
                
                if not bubble_border_drawn:
                    full_text = current_turn_info["text"]
                    bubble_area_height = calculate_bubble_height(full_text, bubble_width, console)
                    
                    clear_region(term, bubble_x, bubble_y, bubble_width, bubble_area_height)
                    bubble_lines = render_bubble(console, "", speaker_info["name"], speaker_info["color"], bubble_width, bubble_area_height)
                    for i, line in enumerate(bubble_lines):
                        print(term.move_xy(bubble_x, bubble_y + i) + line, end="")
                    
                    bubble_border_drawn = True
                    current_bubble_x = bubble_x
                    current_bubble_y = bubble_y
                    current_bubble_width = bubble_width
                    current_bubble_height = bubble_area_height
                
                # Stream text inside bubble
                if text_reveal_counter != last_text_reveal_counter:
                    full_text = current_turn_info["text"]
                    chars_to_reveal = min(text_reveal_counter, len(full_text))
                    revealed_text = full_text[:chars_to_reveal]
                    
                    inner_x = current_bubble_x + 2
                    inner_y = current_bubble_y + 1
                    inner_width = current_bubble_width - 4
                    inner_height = current_bubble_height - 2
                    
                    temp_console = Console(width=inner_width, legacy_windows=False)
                    with temp_console.capture() as capture:
                        temp_console.print(Text.from_markup(revealed_text))
                    new_text_lines = capture.get().splitlines()
                    
                    for i, line in enumerate(new_text_lines):
                        if i < inner_height:
                            if i >= len(rendered_text_lines) or rendered_text_lines[i] != line:
                                print(term.move_xy(inner_x, inner_y + i) + line, end="")
                                if i >= len(rendered_text_lines):
                                    rendered_text_lines.append(line)
                                else:
                                    rendered_text_lines[i] = line
                    
                    last_text_reveal_counter = text_reveal_counter
            
            # --- Advance Script ---
            turn_timer += 1
            if turn_timer % 2 == 0:
                text_reveal_counter += 3
            
            if turn_timer >= (fps * 7):
                turn_timer = 0
                script_turn += 1
                text_reveal_counter = 0
                last_text_reveal_counter = -1
    
    print(term.clear)

if __name__ == "__main__":
    run_demo(fps=20)

