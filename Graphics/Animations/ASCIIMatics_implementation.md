# ASCIIMatics Implementation Guide

## Overview
ASCIIMatics is a Python library for creating terminal-based animations and user interfaces. It's ideal for creating simple, low bitrate animations like a news anchor reading the news.

## Installation
```bash
pip install asciimatics
```

## Key Components

### 1. Scenes and Effects
- **Scene**: Container for one or more effects that define what's displayed
- **Effect**: Individual animation elements (text, sprites, etc.)
- Modular approach allows for complex, organised animations

### 2. Renderers
- **StaticRenderer**: For static ASCII art frames
- **FigletText**: Large ASCII text using FIGlet fonts
- **ImageFile/ColourImageFile**: Convert images to ASCII art
- **Fire, Plasma, Kaleidoscope**: Dynamic visual effects

### 3. Sprites and Paths
- **Sprite**: Animated characters that can follow predefined paths
- **Path**: Defines movement trajectories for sprites
- Enables complex movement patterns and character animation

## Basic News Anchor Animation Example

### Simple Frame-Based Animation
```python
from asciimatics.screen import Screen
from asciimatics.scene import Scene
from asciimatics.effects import Print
from asciimatics.renderers import StaticRenderer

# Define animation frames for news anchor
frames = [
    # Frame 1: Neutral pose
    r"""
     O
    /|\
    / \
    """,
    # Frame 2: Gesturing
    r"""
     O
    -|\
    / \
    """,
    # Frame 3: Speaking
    r"""
     O
    /|\
    / \
    """
]

def demo(screen):
    effects = []
    for i, frame in enumerate(frames):
        renderer = StaticRenderer(images=[frame])
        effect = Print(
            screen, 
            renderer, 
            x=10, 
            y=5, 
            start_frame=i*20,  # 20 frame delay between poses
            stop_frame=(i+1)*20
        )
        effects.append(effect)
    
    scene = Scene(effects, -1)  # -1 = infinite loop
    screen.play([scene])

Screen.wrapper(demo)
```

### Advanced Sprite-Based Animation
```python
from asciimatics.screen import Screen
from asciimatics.scene import Scene
from asciimatics.sprites import Sprite
from asciimatics.paths import Path
from asciimatics.renderers import StaticRenderer

class NewsAnchor(Sprite):
    def __init__(self, screen):
        # Define multiple animation states
        anchor_frames = {
            "neutral": StaticRenderer(images=[
                r"""
                 O
                /|\
                / \
                """
            ]),
            "speaking": StaticRenderer(images=[
                r"""
                 O
                /|\
                / \
                """,
                r"""
                 O
                -|\
                / \
                """,
                r"""
                 O
                \|/
                / \
                """
            ])
        }
        
        super(NewsAnchor, self).__init__(
            screen,
            renderer_dict=anchor_frames,
            path=Path(),  # Static position initially
            start_frame=0
        )

def demo(screen):
    # Create news anchor sprite
    anchor = NewsAnchor(screen)
    
    # Position at centre of screen
    anchor.path = Path([(screen.width//2, screen.height//2)], loop=False)
    
    # Create scene
    scene = Scene([anchor], -1)
    screen.play([scene])

Screen.wrapper(demo)
```

## Enhanced News Anchor with Text

```python
from asciimatics.screen import Screen
from asciimatics.scene import Scene
from asciimatics.effects import Print
from asciimatics.renderers import StaticRenderer, FigletText
from asciimatics.sprites import Sprite
from asciimatics.paths import Path

class NewsAnchorWithText(Sprite):
    def __init__(self, screen):
        frames = {
            "default": StaticRenderer(images=[
                r"""
                 ___
                ( o )
                 \_/
                /|\|
                / \ 
                """,
                r"""
                 ___
                ( - )
                 \_/
                /|\|
                / \ 
                """,
                r"""
                 ___
                ( o )
                 \_/
                -|\|
                / \ 
                """
            ])
        }
        
        super(NewsAnchorWithText, self).__init__(
            screen,
            renderer_dict=frames,
            path=Path([(10, 5)], loop=False),
            start_frame=0
        )

def demo(screen):
    effects = []
    
    # Add news anchor sprite
    anchor = NewsAnchorWithText(screen)
    effects.append(anchor)
    
    # Add news ticker text
    news_text = Print(
        screen,
        FigletText("BREAKING NEWS", font='small'),
        x=2,
        y=screen.height - 8,
        colour=Screen.COLOUR_RED,
        speed=1
    )
    effects.append(news_text)
    
    # Add scrolling news content
    news_content = Print(
        screen,
        StaticRenderer(images=["Good evening, I'm your AI news anchor..."]),
        x=2,
        y=screen.height - 5,
        colour=Screen.COLOUR_WHITE,
        speed=1
    )
    effects.append(news_content)
    
    scene = Scene(effects, -1)
    screen.play([scene])

Screen.wrapper(demo)
```

## Animation Timing and Control

### Frame Control Parameters
- `start_frame`: When effect begins
- `stop_frame`: When effect ends (-1 for infinite)
- `speed`: Animation playback speed (1 = normal)

### Loop Control
```python
# Infinite loop
scene = Scene(effects, -1)

# Run for 500 frames then stop
scene = Scene(effects, 500)

# Multiple scenes with transitions
scenes = [
    Scene([intro_effect], 100),
    Scene([main_animation], -1),
    Scene([outro_effect], 50)
]
screen.play(scenes)
```

## Best Practices for Low Bitrate Animations

### 1. Optimise Frame Count
- Use fewer frames for smoother performance
- Focus on key poses rather than fluid motion
- Typical range: 3-8 frames per animation cycle

### 2. Efficient ASCII Art
- Keep character designs simple
- Use consistent character width/height
- Avoid complex shading or details

### 3. Memory Management
```python
# Pre-define frames to avoid recreation
ANCHOR_FRAMES = [
    "frame1_ascii_art",
    "frame2_ascii_art", 
    "frame3_ascii_art"
]

# Reuse renderers where possible
renderer = StaticRenderer(images=ANCHOR_FRAMES)
```

### 4. Performance Considerations
- Limit simultaneous effects
- Use appropriate sleep/delay values
- Test on target terminal environments

## Integration with LLM Automation

### Automated Frame Generation
```python
def generate_anchor_frames(llm_prompt):
    """
    Use LLM to generate ASCII art frames based on prompts
    """
    # This would integrate with your chosen LLM API
    # to generate ASCII art frames programmatically
    pass

# Example usage
frames = generate_anchor_frames("Create 3 frames of a news anchor speaking")
```

## Common Use Cases

1. **News Ticker**: Scrolling text with animated presenter
2. **Weather Report**: Character with changing weather symbols  
3. **Stock Updates**: Animated charts with presenter
4. **Interactive Menus**: Character-guided navigation
5. **Loading Screens**: Animated characters during processing

## Troubleshooting

### Common Issues
- **Terminal size**: Check screen dimensions before positioning
- **Colour support**: Test colour capabilities of target terminals
- **Performance**: Reduce frame rate if animation stutters
- **Character encoding**: Ensure proper UTF-8 support

### Debug Tips
```python
# Check screen dimensions
print(f"Screen size: {screen.width} x {screen.height}")

# Test individual frames
for frame in frames:
    print(frame)
    time.sleep(1)
```

## Resources
- [ASCIIMatics Documentation](https://asciimatics.readthedocs.io/)
- [GitHub Repository](https://github.com/peterbrittain/asciimatics)
- [Example Applications](https://github.com/peterbrittain/asciimatics/tree/master/samples)
