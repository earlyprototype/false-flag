"""Terminal wait indicator in the Operation Tuman language.

A sonar ping sweeps a short trace line while the game waits on an LLM
call. The classic ``Spinner(message)`` API is preserved (start/stop,
context manager, optional custom frames); only the default look changed.

Character discipline follows docs/AESTHETIC_LANGUAGE.md: box-drawing and
geometric glyphs only, no emoji. On non-TTY stdout the spinner emits
nothing at all, so piped and CI transcripts stay clean.
"""

import sys
import time
import threading
from typing import List, Optional


def sonar_sweep_frames(width: int = 9) -> List[str]:
    """Frames of a sonar ping sweeping a short trace and returning.

    e.g. ``[●•·······]`` -> ``[·•●•·····]`` -> ... -> ``[·······•●]``
    """
    frames = []
    forward = list(range(width))
    backward = list(range(width - 2, 0, -1))
    for positions, direction in ((forward, 1), (backward, -1)):
        for p in positions:
            cells = ["·"] * width
            trail = p - direction  # fading return behind the ping
            if 0 <= trail < width:
                cells[trail] = "•"
            cells[p] = "●"
            frames.append("[" + "".join(cells) + "]")
    return frames


def fog_pulse_frames() -> List[str]:
    """Alternative wait style: a fog bank thickening and thinning."""
    ramp = [" ", "·", "░", "▒", "▓"]
    frames = []
    for i in list(range(len(ramp))) + list(range(len(ramp) - 2, 0, -1)):
        frames.append("[" + ramp[i] * 3 + "]")
    return frames


class Spinner:
    """Sonar-sweep wait animation for terminal output.

    Shows the Tuman sonar trace while waiting for operations to complete.
    """

    def __init__(self, message: str = "Thinking", frames: Optional[list] = None):
        """Initialize spinner.

        Args:
            message: Text to display before the trace
            frames: List of frame strings to cycle through
                (default: sonar ping sweep)
        """
        self.message = message
        self.frames = frames or sonar_sweep_frames()
        self._stop = False
        self._thread: Optional[threading.Thread] = None

    def _spin(self):
        """Internal method to animate the trace."""
        idx = 0
        while not self._stop:
            frame = self.frames[idx % len(self.frames)]
            sys.stdout.write(f'\r{self.message} {frame} ')
            sys.stdout.flush()
            time.sleep(0.08)
            idx += 1

    def start(self):
        """Start the animation (no-op on non-TTY stdout)."""
        try:
            if not sys.stdout.isatty():
                return  # piped/CI output: emit nothing
        except (AttributeError, ValueError):
            return
        self._stop = False
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self, clear: bool = True):
        """Stop the animation.

        Args:
            clear: If True, clear the spinner line
        """
        self._stop = True
        if self._thread:
            self._thread.join(timeout=0.2)
            if clear:
                # Clear the line (message + space + frame + trailing space)
                span = len(self.message) + max(len(f) for f in self.frames) + 4
                sys.stdout.write('\r' + ' ' * span + '\r')
                sys.stdout.flush()
        self._thread = None

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
