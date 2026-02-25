"""Simple terminal spinner for loading animations."""

import sys
import time
import threading
from typing import Optional


class Spinner:
    """Simple spinner animation for terminal output.
    
    Shows a rotating character animation while waiting for operations to complete.
    """
    
    def __init__(self, message: str = "Thinking", frames: Optional[list] = None):
        """Initialize spinner.
        
        Args:
            message: Text to display before spinner
            frames: List of characters to cycle through (default: rotating line)
        """
        self.message = message
        self.frames = frames or ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self._stop = False
        self._thread: Optional[threading.Thread] = None
    
    def _spin(self):
        """Internal method to animate spinner."""
        idx = 0
        while not self._stop:
            frame = self.frames[idx % len(self.frames)]
            sys.stdout.write(f'\r{self.message} {frame} ')
            sys.stdout.flush()
            time.sleep(0.1)
            idx += 1
    
    def start(self):
        """Start the spinner animation."""
        self._stop = False
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
    
    def stop(self, clear: bool = True):
        """Stop the spinner animation.
        
        Args:
            clear: If True, clear the spinner line
        """
        self._stop = True
        if self._thread:
            self._thread.join(timeout=0.2)
        
        if clear:
            # Clear the line
            sys.stdout.write('\r' + ' ' * (len(self.message) + 10) + '\r')
            sys.stdout.flush()
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()

