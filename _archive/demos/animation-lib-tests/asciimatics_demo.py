from asciimatics.screen import Screen
from asciimatics.scene import Scene
from asciimatics.effects import Print
from asciimatics.renderers import StaticRenderer

frames = [
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
    """,
]

def demo(screen: Screen) -> None:
    effects = [
        Print(screen, StaticRenderer(images=[f]), x=10, y=5, start_frame=i*20, stop_frame=(i+1)*20)
        for i, f in enumerate(frames)
    ]
    scene = Scene(effects, -1)
    screen.play([scene])

if __name__ == "__main__":
    Screen.wrapper(demo)


