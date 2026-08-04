"""Live demo of the between-turn interstitials (cli/interstitials.py).

Run in a real terminal to watch the vignettes; any keypress skips:

    .venv/bin/python dev-scripts/interstitials_demo.py                # all 5
    .venv/bin/python dev-scripts/interstitials_demo.py tea_round 90   # one,
                                                       # at escalation 90
    .venv/bin/python dev-scripts/interstitials_demo.py record [name] [esc]

Vignettes: tea_round, periscope, teleprinter, red_phone, radar_room.

``record`` drives a vignette through a pty (fake TTY) and prints a few
captured intermediate frames - useful for checking the choreography from a
non-interactive session (POSIX-only).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cli import interstitials as itl
from cli.rich_ui import console


def demo(name: str, escalation: int) -> None:
    console.print(f"\n[bold underline]{name.upper()}[/bold underline] "
                  f"(escalation {escalation})\n")
    itl.play_interstitial(console=console, seed=f"demo-{name}",
                          escalation=escalation, name=name)
    console.print()


def record(name: str, escalation: int) -> None:
    """Capture a vignette through a pty and print sample frames."""
    import os
    import pty
    import re
    import select

    repo = str(Path(__file__).resolve().parents[1])
    child = (
        f"import sys; sys.path.insert(0, {repo!r});"
        "from cli.interstitials import play_interstitial;"
        "from cli.rich_ui import console;"
        f"play_interstitial(console=console, seed='demo-{name}',"
        f" escalation={escalation}, name={name!r})"
    )
    pid, fd = pty.fork()
    if pid == 0:
        os.execv(sys.executable, [sys.executable, "-c", child])
    import fcntl
    import struct
    import termios
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 30, 100, 0, 0))
    chunks = []
    timed_out = False
    while True:
        ready, _, _ = select.select([fd], [], [], 15)
        if not ready:
            timed_out = True
            break
        try:
            data = os.read(fd, 65536)
        except OSError:
            break
        if not data:
            break
        chunks.append(data)
    if timed_out:
        # Playback stalled: kill the child rather than blocking forever in
        # waitpid waiting for a process that is never going to finish.
        import signal
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    os.waitpid(pid, 0)
    raw = b"".join(chunks).decode("utf-8", errors="replace")
    frames = re.split(r"\x1b\[\d+F", raw)
    ansi = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
    print(f"captured {len(frames)} frames")
    samples = sorted({i for i in (0, len(frames) // 3, 2 * len(frames) // 3,
                                  len(frames) - 1) if 0 <= i < len(frames)})
    for i in samples:
        print(f"\n----- frame {i} -----")
        lines = [ln.rstrip() for ln in ansi.sub("", frames[i]).split("\n")]
        while lines and not lines[-1].strip():
            lines.pop()
        print("\n".join(lines))


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "record":
        record(args[1] if len(args) > 1 else "red_phone",
               int(args[2]) if len(args) > 2 else 50)
    elif args:
        demo(args[0], int(args[1]) if len(args) > 1 else 50)
    else:
        for name in itl.VIGNETTE_NAMES:
            demo(name, 50)
