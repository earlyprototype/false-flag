import os
import random
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from blessed import Terminal

# v3: Final version with padding for the speech bubbles and correct alignment.

# --- Import local pipeline tools ---
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from Graphics.Animations.tools.encode_halfblock import encode_halfblock
except ImportError:
    print("Error: Could not import 'encode_halfblock'. Please run from the project root.")
    exit(1)

# --- Configuration ---
# Player sprite (PM - anchor)
PLAYER_SPRITE_PATH = "assets/anchor_small"
PLAYER_FRAMES = {
    "neutral": "anchor_neutral_01.png",
    "blink": "anchor_blink_01.png",
    "talk": ["anchor_talk_a_01.png", "anchor_talk_e_01.png", "anchor_talk_o_01.png"]
}

# Diplomat sprite (US President - senior female diplomat)
DIPLOMAT_SPRITE_PATH = "assets/diplomat_female_senior"
DIPLOMAT_FRAMES = {
    "neutral": "diplomat_female_senior_neutral_01.png",
    "blink": "diplomat_female_senior_blink_01.png",
    "talk": ["diplomat_female_senior_talk_a_01.png", "diplomat_female_senior_talk_e_01.png", "diplomat_female_senior_talk_o_01.png"]
}

CONVERSATION_SCRIPT = [
    {"speaker": "diplomat", "text": "Prime Minister. Your naval blockade is an unacceptable act of aggression. We demand you stand down your fleet."},
    {"speaker": "player", "text": "This is not a blockade. It is a defensive quarantine in response to your [red]unannounced submarine movements[/]. Stand down *your* assets."},
    {"speaker": "diplomat", "text": "These are routine patrols in international waters. Your response is disproportionate and will have severe consequences."},
    {"speaker": "player", "text": "Our intelligence on the [yellow]Suwałki Gap[/] suggests otherwise. The quarantine holds. End of discussion."},
    {"speaker": "pause", "text": ""}
]

# --- Helper Functions ---
def load_and_encode_sprites(sprite_path: str, frame_config: dict) -> dict:
    """Loads PNGs, converts them to half-block text, and returns a dict of frames."""
    encoded_frames = {"idle": [], "talk": []}
    neutral_path = os.path.join(sprite_path, frame_config["neutral"])
    blink_path = os.path.join(sprite_path, frame_config["blink"])
    if not os.path.exists(neutral_path) or not os.path.exists(blink_path):
        raise FileNotFoundError(f"Cannot find placeholder assets in {sprite_path}. Check sprite folder.")
    # Use 16-color mode for better terminal compatibility (fixes blue overlay)
    neutral_frames = encode_halfblock(neutral_path, mode="16", palette="db16")
    blink_frames = encode_halfblock(blink_path, mode="16", palette="db16")
    for _ in range(60): encoded_frames["idle"].append(neutral_frames)
    for _ in range(4): encoded_frames["idle"].append(blink_frames)
    for frame_file in frame_config["talk"]:
        path = os.path.join(sprite_path, frame_file)
        frames = encode_halfblock(path, mode="16", palette="db16")
        for _ in range(8): encoded_frames["talk"].append(frames)
    return encoded_frames

def render_sprite(term: Terminal, x: int, y: int, sprite_art: list[str], tint_markup: str):
    for i, line in enumerate(sprite_art):
        if tint_markup:
            line_to_print = f"[{tint_markup}]{line}[/{tint_markup}]"
            print(term.move_xy(x, y + i) + str(Text.from_markup(line_to_print)), end="")
        else:
            print(term.move_xy(x, y + i) + line, end="")

def render_bubble(console: Console, text: str, title: str, border_color: str, width: int, height: int = None) -> list[str]:
    """Renders a speech bubble. If height is provided, pads the text to fill that height."""
    if height:
        # Create padding to fill the desired height
        # Panel has top border + content + bottom border
        # So we need (height - 2) lines of content
        lines_needed = height - 2
        if text:
            # Calculate how many lines the text actually uses
            temp_console = Console(width=width - 4, legacy_windows=False)
            with temp_console.capture() as capture:
                temp_console.print(Text.from_markup(text))
            actual_lines = len(capture.get().splitlines())
            padding_lines = max(0, lines_needed - actual_lines)
            text = text + "\n" * padding_lines
        else:
            # Empty text - fill with blank lines
            text = "\n" * (lines_needed - 1) if lines_needed > 0 else ""
    
    panel = Panel(Text.from_markup(text), title=f"[bold white]{title}[/bold white]", border_style=border_color, width=width)
    with console.capture() as capture:
        console.print(panel)
    return capture.get().splitlines()

def clear_region(term: Terminal, x: int, y: int, width: int, height: int):
    """Clears a rectangular region of the screen."""
    empty_line = " " * width
    for i in range(height):
        print(term.move_xy(x, y + i) + empty_line, end="")

def calculate_bubble_height(text: str, bubble_width: int, console: Console, min_height: int = 4, max_height: int = 15) -> int:
    """Calculates the required bubble height based on text content and width."""
    # Calculate inner width (accounting for borders and padding)
    inner_width = bubble_width - 4
    
    # Wrap text to see how many lines it needs
    temp_console = Console(width=inner_width, legacy_windows=False)
    with temp_console.capture() as capture:
        temp_console.print(Text.from_markup(text))
    text_lines = capture.get().splitlines()
    
    # Calculate total height: top border + text lines + bottom border
    # Panel structure: 1 line top border (includes title), text content, 1 line bottom border
    required_height = len(text_lines) + 2  # +2 for top and bottom borders
    
    # Clamp to min/max bounds
    return max(min_height, min(required_height, max_height))

# --- Main Demo ---
def run_demo(fps: int):
    term = Terminal()
    console = Console(width=term.width) 

    try:
        player_frames = load_and_encode_sprites(PLAYER_SPRITE_PATH, PLAYER_FRAMES)
        diplomat_frames = load_and_encode_sprites(DIPLOMAT_SPRITE_PATH, DIPLOMAT_FRAMES)
    except FileNotFoundError as e:
        print(f"[bold red]Error:[/bold red] {e}")
        return

    script_turn = 0
    turn_timer = 0
    previous_speaker = None
    text_reveal_counter = 0
    last_text_reveal_counter = -1  # Track when text actually updates
    bubble_border_drawn = False
    current_bubble_x = 0
    current_bubble_y = 0
    current_bubble_width = 0
    current_bubble_height = 0
    current_bubble_title = ""
    current_bubble_color = ""
    rendered_text_lines = []  # Store already rendered text lines
    last_rendered_length = 0  # Track how much text has been rendered
    
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
                last_rendered_length = 0
                rendered_text_lines = []
                bubble_border_drawn = False
            else:
                print(term.home, end="")

            # --- Final Layout Calculation with Padding ---
            SPRITE_WIDTH = 32
            
            diplomat_sprite_x = 0 # Absolute left edge
            player_sprite_x = term.width - SPRITE_WIDTH # Absolute right edge
            
            # --- State Update ---
            player_anim_state = "talk" if speaker == "player" else "idle"
            diplomat_anim_state = "talk" if speaker == "diplomat" else "idle"

            # Randomize talk frames for more realism, use sequential for idle
            if player_anim_state == "talk":
                player_anim_frame = random.choice(player_frames["talk"])
            else:
                anim_speed = turn_timer * 2
                player_anim_frame = player_frames["idle"][anim_speed % len(player_frames["idle"])]
            
            if diplomat_anim_state == "talk":
                diplomat_anim_frame = random.choice(diplomat_frames["talk"])
            else:
                anim_speed = turn_timer * 2
                diplomat_anim_frame = diplomat_frames["idle"][anim_speed % len(diplomat_frames["idle"])]

            # --- Rendering ---
            if speaker == "player":
                render_sprite(term, diplomat_sprite_x, 10, diplomat_anim_frame[:12], "") # Ducked
                render_sprite(term, player_sprite_x, 1, player_anim_frame, "") # Full
            else: # Diplomat or pause
                render_sprite(term, diplomat_sprite_x, 1, diplomat_anim_frame, "") # Full
                render_sprite(term, player_sprite_x, 10, player_anim_frame[:12], "") # Ducked

            # --- L-Shape Bubble Logic with Text Streaming ---
            bubble_y = 3
            
            if speaker == "diplomat":
                title = "President | Russian Federation"
                border_color = "bright_blue"
                
                # Draw static border once
                if not bubble_border_drawn:
                    bubble_x = diplomat_sprite_x + SPRITE_WIDTH + 2  # Start after left sprite
                    bubble_width = term.width - bubble_x  # Use all remaining width to right edge
                    
                    # Calculate required height based on full text content
                    full_text = current_turn_info["text"]
                    bubble_area_height = calculate_bubble_height(full_text, bubble_width, console)
                    
                    clear_region(term, bubble_x, 2, bubble_width, bubble_area_height)
                    bubble_lines = render_bubble(console, "", title, border_color, bubble_width, bubble_area_height)
                    for i, line in enumerate(bubble_lines):
                        print(term.move_xy(bubble_x, bubble_y + i) + line, end="")
                    bubble_border_drawn = True
                    current_bubble_x = bubble_x
                    current_bubble_y = bubble_y
                    current_bubble_width = bubble_width
                    current_bubble_height = bubble_area_height
                    current_bubble_title = title
                    current_bubble_color = border_color
                
                # Stream text inside using stored dimensions - only render NEW characters
                if text_reveal_counter != last_text_reveal_counter:
                    full_text = current_turn_info["text"]
                    chars_to_reveal = min(text_reveal_counter, len(full_text))
                    revealed_text = full_text[:chars_to_reveal]
                    
                    inner_x = current_bubble_x + 2
                    inner_y = current_bubble_y + 1
                    inner_width = current_bubble_width - 4
                    inner_height = current_bubble_height - 2  # Only subtract borders (top + bottom)
                    
                    # Get the newly wrapped text with all revealed characters
                    temp_console = Console(width=inner_width, legacy_windows=False)
                    with temp_console.capture() as capture:
                        temp_console.print(Text.from_markup(revealed_text))
                    new_text_lines = capture.get().splitlines()
                    
                    # Only render new/changed lines
                    for i, line in enumerate(new_text_lines):
                        if i < inner_height:
                            # Check if this line is different from what we have
                            if i >= len(rendered_text_lines) or rendered_text_lines[i] != line:
                                print(term.move_xy(inner_x, inner_y + i) + line, end="")
                                # Update our record
                                if i >= len(rendered_text_lines):
                                    rendered_text_lines.append(line)
                                else:
                                    rendered_text_lines[i] = line
                    
                    last_text_reveal_counter = text_reveal_counter
                    last_rendered_length = chars_to_reveal

            elif speaker == "player":
                title = "You (Prime Minister)"
                border_color = "white"
                
                # Draw static border once
                if not bubble_border_drawn:
                    bubble_x = diplomat_sprite_x
                    bubble_width = player_sprite_x - 2 - diplomat_sprite_x
                    
                    # Calculate required height based on full text content
                    full_text = current_turn_info["text"]
                    bubble_area_height = calculate_bubble_height(full_text, bubble_width, console)
                    
                    clear_region(term, bubble_x, 2, bubble_width, bubble_area_height)
                    bubble_lines = render_bubble(console, "", title, border_color, bubble_width, bubble_area_height)
                    for i, line in enumerate(bubble_lines):
                        print(term.move_xy(bubble_x, bubble_y + i) + line, end="")
                    bubble_border_drawn = True
                    current_bubble_x = bubble_x
                    current_bubble_y = bubble_y
                    current_bubble_width = bubble_width
                    current_bubble_height = bubble_area_height
                    current_bubble_title = title
                    current_bubble_color = border_color
                
                # Stream text inside using stored dimensions - only render NEW characters
                if text_reveal_counter != last_text_reveal_counter:
                    full_text = current_turn_info["text"]
                    chars_to_reveal = min(text_reveal_counter, len(full_text))
                    revealed_text = full_text[:chars_to_reveal]
                    
                    inner_x = current_bubble_x + 2
                    inner_y = current_bubble_y + 1
                    inner_width = current_bubble_width - 4
                    inner_height = current_bubble_height - 2  # Only subtract borders (top + bottom)
                    
                    # Get the newly wrapped text with all revealed characters
                    temp_console = Console(width=inner_width, legacy_windows=False)
                    with temp_console.capture() as capture:
                        temp_console.print(Text.from_markup(revealed_text))
                    new_text_lines = capture.get().splitlines()
                    
                    # Only render new/changed lines
                    for i, line in enumerate(new_text_lines):
                        if i < inner_height:
                            # Check if this line is different from what we have
                            if i >= len(rendered_text_lines) or rendered_text_lines[i] != line:
                                print(term.move_xy(inner_x, inner_y + i) + line, end="")
                                # Update our record
                                if i >= len(rendered_text_lines):
                                    rendered_text_lines.append(line)
                                else:
                                    rendered_text_lines[i] = line
                    
                    last_text_reveal_counter = text_reveal_counter
                    last_rendered_length = chars_to_reveal

            # print(term.move_xy(0, term.height - 2) + "Press 'q' to quit.", end="")
            
            # --- Advance Script ---
            turn_timer += 1
            
            # Only increment text reveal every 2 frames (reduces flicker)
            if turn_timer % 2 == 0:
                text_reveal_counter += 3  # Reveal 3 characters every 2 frames
            
            if turn_timer >= (fps * 7): 
                turn_timer = 0
                script_turn += 1
                text_reveal_counter = 0
                last_text_reveal_counter = -1
    
    print(term.clear)

if __name__ == "__main__":
    run_demo(fps=20)