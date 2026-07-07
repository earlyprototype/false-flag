import os
import sys
import random
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from blessed import Terminal

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# Cabinet advisors demo: PM consults his team about the crisis

# --- Import local pipeline tools ---
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from Graphics.Animations.tools.encode_halfblock import encode_halfblock
except ImportError as e:
    print(f"Error: Could not import 'encode_halfblock': {e}")
    print("Please run from the project root.")
    exit(1)

# --- Configuration ---
# PM sprite (right side, constant)
PM_SPRITE_PATH = "assets/anchor_small"
PM_FRAMES = {
    "neutral": "anchor_neutral_01.png",
    "blink": "anchor_blink_01.png",
    "talk": ["anchor_talk_a_01.png", "anchor_talk_e_01.png", "anchor_talk_o_01.png"]
}

# Cabinet advisors (left side, rotating)
ADVISORS = [
    {
        "name": "Defence Secretary",
        "sprite_path": "assets/diplomat_grey",
        "prefix": "diplomat_grey"
    },
    {
        "name": "Foreign Secretary", 
        "sprite_path": "assets/diplomat_female_senior",
        "prefix": "diplomat_female_senior"
    },
    {
        "name": "Chief of Defence Staff",
        "sprite_path": "assets/diplomat_dark",
        "prefix": "diplomat_dark"
    },
    {
        "name": "National Security Advisor",
        "sprite_path": "assets/diplomat_female_dark",
        "prefix": "diplomat_female_dark"
    }
]

CONVERSATION_SCRIPT = [
    {
        "speaker": "pm",
        "text": "Gentlemen, ladies. The Americans have imposed a naval quarantine. Our submarines in the Baltic are exposed. I need options. Defence Secretary?"
    },
    {
        "speaker": "advisor_0",
        "text": "Prime Minister, we must stand firm. Order our submarines to surface and transit through international waters. Any American interference would be an act of aggression."
    },
    {
        "speaker": "advisor_1", 
        "text": "With respect, that's reckless. We should open immediate diplomatic channels with Washington. Escalation serves no one's interests."
    },
    {
        "speaker": "advisor_2",
        "text": "Our NATO obligations are clear, but so are our national interests. I recommend we coordinate a joint response with our European allies before taking unilateral action."
    },
    {
        "speaker": "advisor_3",
        "text": "The intelligence suggests the Americans are tracking our movements in real-time. Any aggressive posture will be met with overwhelming force. We need a tactical withdrawal."
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
        raise FileNotFoundError(f"Cannot find assets in {sprite_path}. Check sprite folder.")
    
    # Use 16-color mode for better terminal compatibility (fixes blue overlay)
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

def render_sprite(term: Terminal, x: int, y: int, sprite_art: list[str], tint_markup: str):
    for i, line in enumerate(sprite_art):
        if tint_markup:
            line_to_print = f"[{tint_markup}]{line}[/{tint_markup}]"
            print(term.move_xy(x, y + i) + str(Text.from_markup(line_to_print)), end="")
        else:
            print(term.move_xy(x, y + i) + str(Text.from_markup(line)), end="")

def render_bubble(console: Console, text: str, title: str, border_color: str, width: int, height: int = None) -> list[str]:
    """Renders a speech bubble. If height is provided, pads the text to fill that height."""
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
    """Clears a rectangular region of the screen."""
    empty_line = " " * width
    for i in range(height):
        print(term.move_xy(x, y + i) + empty_line, end="")

def calculate_bubble_height(text: str, bubble_width: int, console: Console, min_height: int = 4, max_height: int = 15) -> int:
    """Calculates the required bubble height based on text content and width."""
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

    # Load PM sprites
    try:
        pm_frames = load_and_encode_sprites(PM_SPRITE_PATH, "anchor")
    except FileNotFoundError as e:
        print(f"[bold red]Error loading PM sprites:[/bold red] {e}")
        return

    # Load all advisor sprites
    advisor_frames = []
    for advisor in ADVISORS:
        try:
            frames = load_and_encode_sprites(advisor["sprite_path"], advisor["prefix"])
            advisor_frames.append(frames)
        except FileNotFoundError as e:
            print(f"[bold red]Error loading {advisor['name']} sprites:[/bold red] {e}")
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
    current_bubble_title = ""
    current_bubble_color = ""
    rendered_text_lines = []
    last_rendered_length = 0
    
    # Track transition state
    in_transition = False
    transition_timer = 0
    TRANSITION_DURATION = fps // 2  # 0.5 seconds duck time
    
    with term.cbreak(), term.hidden_cursor():
        while True:
            key = term.inkey(timeout=1/fps)
            if key.lower() == 'q' or script_turn >= len(CONVERSATION_SCRIPT):
                break

            current_turn_info = CONVERSATION_SCRIPT[script_turn]
            speaker = current_turn_info["speaker"]
            
            # Check if we need to start a transition
            if speaker != previous_speaker and previous_speaker is not None:
                if not in_transition:
                    # Start transition - clear once at the beginning
                    print(term.clear)
                    in_transition = True
                    transition_timer = 0
            
            # Handle transition
            if in_transition:
                transition_timer += 1
                if transition_timer >= TRANSITION_DURATION:
                    # Transition complete - clear for new speaker
                    in_transition = False
                    transition_timer = 0
                    print(term.clear)
                    previous_speaker = speaker
                    text_reveal_counter = 0
                    last_text_reveal_counter = -1
                    last_rendered_length = 0
                    rendered_text_lines = []
                    bubble_border_drawn = False
                else:
                    # Show ducking advisor (no additional clears, just update in place)
                    print(term.home, end="")
                    SPRITE_WIDTH = 32
                    advisor_sprite_x = 0
                    pm_sprite_x = term.width - SPRITE_WIDTH
                    
                    # Previous speaker ducks
                    if previous_speaker.startswith("advisor_"):
                        advisor_idx = int(previous_speaker.split("_")[1])
                        prev_frames = advisor_frames[advisor_idx]
                        prev_anim_frame = prev_frames["idle"][turn_timer % len(prev_frames["idle"])]
                        render_sprite(term, advisor_sprite_x, 10, prev_anim_frame[:12], "")  # Ducked
                    
                    # PM always ducked (listening)
                    pm_anim_frame = pm_frames["idle"][turn_timer % len(pm_frames["idle"])]
                    render_sprite(term, pm_sprite_x, 10, pm_anim_frame[:12], "")  # Ducked
                    
                    turn_timer += 1
                    continue
            
            if speaker != previous_speaker and previous_speaker is None:
                print(term.clear)
                previous_speaker = speaker
                text_reveal_counter = 0
                last_text_reveal_counter = -1
                last_rendered_length = 0
                rendered_text_lines = []
                bubble_border_drawn = False
            else:
                print(term.home, end="")

            # --- Layout Calculation ---
            SPRITE_WIDTH = 32
            advisor_sprite_x = 0
            pm_sprite_x = term.width - SPRITE_WIDTH
            
            # --- State Update ---
            pm_anim_state = "talk" if speaker == "pm" else "idle"
            
            # PM animation
            if pm_anim_state == "talk":
                pm_anim_frame = random.choice(pm_frames["talk"])
            else:
                pm_anim_frame = pm_frames["idle"][turn_timer % len(pm_frames["idle"])]
            
            # Advisor animation
            advisor_anim_frame = None
            if speaker.startswith("advisor_"):
                advisor_idx = int(speaker.split("_")[1])
                advisor_anim_state = "talk"
                current_advisor_frames = advisor_frames[advisor_idx]
                advisor_anim_frame = random.choice(current_advisor_frames["talk"])
            
            # --- Rendering ---
            if speaker == "pm":
                # PM speaking (full height)
                render_sprite(term, pm_sprite_x, 1, pm_anim_frame, "")
            else:
                # Advisor speaking (full height)
                if advisor_anim_frame:
                    render_sprite(term, advisor_sprite_x, 1, advisor_anim_frame, "")
                # PM listening (ducked, stays ducked)
                render_sprite(term, pm_sprite_x, 10, pm_anim_frame[:12], "")

            # --- Speech Bubble Logic ---
            bubble_y = 3
            
            if speaker == "pm":
                title = "Prime Minister | United Kingdom"
                border_color = "white"
                
                if not bubble_border_drawn:
                    bubble_x = 0
                    bubble_width = pm_sprite_x - 2
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
                
                # Stream text inside
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
                    last_rendered_length = chars_to_reveal

            elif speaker.startswith("advisor_"):
                advisor_idx = int(speaker.split("_")[1])
                title = ADVISORS[advisor_idx]["name"]
                border_color = "bright_blue"
                
                if not bubble_border_drawn:
                    bubble_x = advisor_sprite_x + SPRITE_WIDTH + 2
                    bubble_width = term.width - bubble_x
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
                
                # Stream text inside
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
                    last_rendered_length = chars_to_reveal
            
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

