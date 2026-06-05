
import time
import json
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from blessed import Terminal

# A mock of the 'compiled_scene.json' artifact we discussed.
# In a real game, this would be loaded from a file.
# It contains two frames for a simple blinking animation.
MOCK_COMPILED_SCENE_JSON = r"""
{
  "frames": [
    {
      "sprite": [
        "   _______   ",
        "  /       \\  ",
        " /  o   o  \\ ",
        " |    ^    | ",
        " \\  `---'  / ",
        "  \\_______/  "
      ]
    },
    {
      "sprite": [
        "   _______   ",
        "  /       \\  ",
        " /  -   -  \\ ",
        " |    ^    | ",
        " \\  `---'  / ",
        "  \\_______/  "
      ]
    }
  ]
}
"""

def run_demo():
    """
    Demonstrates rendering a scene by manually composing animation frames
    from a loaded artifact with rich components.
    """
    term = Terminal()
    console = Console()
    
    # 1. Load the pre-compiled scene data
    scene_data = json.loads(MOCK_COMPILED_SCENE_JSON)
    animation_frames = scene_data["frames"]
    
    # 2. Pre-render the static rich component "off-screen"
    teleprompter_text = (
        "Good evening. Tonight's top story: a significant escalation in the North Atlantic. "
        "Sources report three Typhoon-class submarines have left port under suspicious circumstances. "
        "We now go live to our correspondent on the ground..."
    )
    teleprompter_panel = Panel(
        teleprompter_text,
        title="[bold yellow]AUTOCUE[/bold yellow]",
        border_style="yellow",
        width=50
    )
    # The console.capture() context manager allows us to get the string
    # representation of a rich object without printing it.
    with console.capture() as capture:
        console.print(teleprompter_panel)
    teleprompter_output = capture.get()

    tick = 0
    with term.cbreak(), term.hidden_cursor():
        print(term.clear)
        while True:
            # --- 3. Handle Input ---
            key = term.inkey(timeout=0.05) # timeout acts as our frame delay
            if key == 'q':
                break

            # --- 4. Update Animation State ---
            # Simple blink animation: 50 frames open, 5 frames closed
            frame_index = 1 if (tick % 55) > 50 else 0
            sprite_art = animation_frames[frame_index]["sprite"]

            # --- 5. Manual Composition and Rendering ---
            # Move to home, clear from cursor to end of screen
            print(term.home + term.clear_eos, end="") 
            
            # Draw the ASCII sprite line-by-line using blessed for positioning
            for i, line in enumerate(sprite_art):
                print(term.move_xy(5, 5 + i), end="")
                console.print(Text(line, style="bold white"), end="")

            # Draw the pre-rendered rich panel next to it
            for i, line in enumerate(teleprompter_output.splitlines()):
                print(term.move_xy(25, 5 + i) + line, end="")

            # Draw instructions
            print(term.move_xy(0, 20) + "This is a manually composed scene.", end="")
            print(term.move_xy(0, 21) + "An ASCII art animation is playing next to a pre-rendered Rich Panel.", end="")
            print(term.move_xy(0, 22) + "Press 'q' to quit.", end="")
            
            tick += 1
            
if __name__ == "__main__":
    try:
        run_demo()
    except Exception as e:
        # On exit, ensure terminal is clean
        term = Terminal()
        print(term.clear)
        print(f"An error occurred: {e}")
        
