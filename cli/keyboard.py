"""Cross-platform keyboard input for pacing prompts.

Replaces the direct msvcrt usage that made the game Windows-only. Three
strategies, picked at runtime:

- Windows console: msvcrt kbhit/getch (as before, plus a small sleep so the
  wait loop no longer spins at 100% CPU).
- POSIX terminal: termios/tty cbreak mode with a select() timeout.
- Non-interactive stdin (pipes, CI, some IDE consoles): fall back to a plain
  input() line read so scripted runs never hang waiting for a keypress.
"""

import sys
import time

try:
    import msvcrt  # Windows
    _WINDOWS = True
except ImportError:
    _WINDOWS = False
    import select
    import termios
    import tty


def _stdin_is_tty() -> bool:
    try:
        return sys.stdin.isatty()
    except (AttributeError, ValueError):
        return False


def key_pressed(keys=(" ",)) -> bool:
    """Non-blocking check: has one of `keys` been pressed?

    Used inside streaming loops to let the player skip ahead. Consumes the
    keypress when it matches. Returns False on non-interactive stdin.
    """
    if _WINDOWS:
        if msvcrt.kbhit():
            ch = msvcrt.getch()
            try:
                return ch.decode(errors="ignore") in keys
            except AttributeError:
                return False
        return False

    if not _stdin_is_tty():
        return False

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        ready, _, _ = select.select([sys.stdin], [], [], 0)
        if ready:
            ch = sys.stdin.read(1)
            return ch in keys
        return False
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def wait_for_key(prompt: str = "Press SPACE to continue...", keys=(" ",)) -> None:
    """Block until one of `keys` is pressed.

    On non-interactive stdin, reads a line instead so piped input and CI
    runs proceed rather than soft-locking.
    """
    print("")
    print(prompt)

    if _WINDOWS:
        while True:
            if msvcrt.kbhit():
                ch = msvcrt.getch()
                try:
                    if ch.decode(errors="ignore") in keys:
                        print("")
                        return
                except AttributeError:
                    pass
            time.sleep(0.02)

    if not _stdin_is_tty():
        # Piped/redirected input (scripts, CI): don't block and don't consume
        # stdin — lines belong to the game's real prompts, not pacing gates.
        print("")
        return

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        while True:
            ready, _, _ = select.select([sys.stdin], [], [], 0.05)
            if ready:
                ch = sys.stdin.read(1)
                if ch in keys or ch in ("\n", "\r"):
                    print("")
                    return
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
