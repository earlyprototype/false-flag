"""Live demo of the Operation Tuman cinematics (cli/cinematics.py).

Run in a real terminal to watch the animations; any keypress skips:

    .venv/bin/python dev-scripts/cinematics_demo.py            # everything
    .venv/bin/python dev-scripts/cinematics_demo.py title      # one sequence
    .venv/bin/python dev-scripts/cinematics_demo.py record     # pty capture

Sequences: title, scene, turn, debrief, spinner.

``record`` drives the title sequence through a pty (fake TTY) and prints a
few captured intermediate frames - useful for checking the choreography
from a non-interactive session.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cli import cinematics as cin
from cli.rich_ui import console


def demo_title() -> None:
    console.print("[bold underline]TITLE SEQUENCE[/bold underline] "
                  "(fog condenses into the masthead)\n")
    cin.play_title_sequence(console, seed=42)
    console.print()


def demo_scene() -> None:
    console.print("\n[bold underline]SCENE STAMP-IN[/bold underline]\n")
    cin.play_scene_stamp("I", "Severomorsk Naval Base, Russia",
                         "69°04'N 033°25'E",
                         "02 OCT 25 │ 03:15 LOCAL ── 72 HRS EARLIER",
                         console=console)
    console.print()


def demo_turn() -> None:
    console.print("\n[bold underline]TURN TRANSITION[/bold underline] "
                  "(fog band rolls through)\n")
    for turn in (1, 2):
        cin.play_turn_transition(turn, console=console)
        console.print()


def demo_debrief() -> None:
    console.print("\n[bold underline]DEBRIEF REVEAL[/bold underline] "
                  "(heavier condense)\n")
    cin.play_debrief_reveal(
        "The Line Held",
        subtitle="VICTORY ── 10 TURNS",
        lines=[
            "The submarines are returning north. With the alliance intact",
            "and the escalation contained, Moscow's coercion campaign has",
            "quietly run out of road.",
        ],
        seed="demo-ending",
        console=console,
    )
    console.print()


def demo_spinner() -> None:
    console.print("\n[bold underline]LLM-WAIT SPINNER[/bold underline] "
                  "(sonar sweep, 3s)\n")
    from cli.spinner import Spinner
    with Spinner("AWAITING SECURE TRAFFIC"):
        time.sleep(3)
    console.print("...traffic received.\n")


def record_title() -> None:
    """Capture the title sequence through a pty and print sample frames."""
    import os
    import pty
    import re
    import select

    child = (
        f"import sys; sys.path.insert(0, {str(Path(__file__).resolve().parents[1])!r});"
        "from cli.cinematics import play_title_sequence;"
        "from cli.rich_ui import console;"
        "play_title_sequence(console, seed=42)"
    )
    pid, fd = pty.fork()
    if pid == 0:
        os.execv(sys.executable, [sys.executable, "-c", child])
    import fcntl
    import struct
    import termios
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 30, 100, 0, 0))
    chunks = []
    while True:
        ready, _, _ = select.select([fd], [], [], 10)
        if not ready:
            break
        try:
            data = os.read(fd, 65536)
        except OSError:
            break
        if not data:
            break
        chunks.append(data)
    os.waitpid(pid, 0)
    raw = b"".join(chunks).decode("utf-8", errors="replace")
    frames = re.split(r"\x1b\[\d+F", raw)
    ansi = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
    print(f"captured {len(frames)} frames")
    for i in (5, len(frames) // 3, len(frames) // 2, len(frames) - 1):
        print(f"\n----- frame {i} -----")
        lines = [l.rstrip() for l in ansi.sub("", frames[i]).split("\n")]
        while lines and not lines[-1].strip():
            lines.pop()
        print("\n".join(lines))


DEMOS = {
    "title": demo_title,
    "scene": demo_scene,
    "turn": demo_turn,
    "debrief": demo_debrief,
    "spinner": demo_spinner,
    "record": record_title,
}


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else None
    if which:
        DEMOS[which]()
    else:
        for name, fn in DEMOS.items():
            if name != "record":
                fn()
