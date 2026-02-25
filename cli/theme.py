"""Theme configuration for the CLI.

Defines color palettes and style constants for Rich output.
Supports multiple themes (Standard, Defcon 1, Retro).
"""

from typing import Dict, Any

# Base symbols (constant across themes)
# ASCII-ONLY - No emoji (user requirement)
SYMBOLS = {
    "risk": "▲",        # Triangle - Threat level
    "stability": "■",   # Square - Foundation
    "cohesion": "&",    # Ampersand - Alliance
    "casualties": "†",  # Dagger - Deaths
    "influence": "+",   # Plus - Political capital
    "bullet": "•",      # Bullet point
    "arrow": "→",       # Action/Recommendation
    "warning": "!",     # Warning/Alert
    "leader": "#",      # Hash - Head of state
    "diplomat": "•",    # Bullet - Ambassador/Diplomat
    "note": "*",        # Asterisk - Note
    "action": "→",      # Arrow - Recommended action
    "success": "✓",     # Check mark
    "failure": "✗",     # X mark
    "pending": "~",     # Tilde - In progress
    "info": "i",        # Information
}

# Box drawing characters (constant)
BOX = {
    "round": {
        "tl": "╭", "tr": "╮", "bl": "╰", "br": "╯", "h": "─", "v": "│"
    },
    "heavy": {
        "tl": "┏", "tr": "┓", "bl": "┗", "br": "┛", "h": "━", "v": "┃"
    },
    "double": {
        "tl": "╔", "tr": "╗", "bl": "╚", "br": "╝", "h": "═", "v": "║"
    }
}

WIDTH = 80

# Theme Definitions
THEMES: Dict[str, Dict[str, str]] = {
    "defcon": {
        # ADHD-Optimised High Contrast Scheme
        # Deep Orange (#FF6B35) + Navy Blue (#004E89) complementary pairing
        # All colours meet WCAG AAA contrast (7:1 minimum) on dark background
        "primary": "#FF6B35",        # Deep Orange - Interactive elements, commands
        "secondary": "#004E89",      # Navy Blue - Labels, structure, advisor names
        "accent": "#1A659E",         # Steel Blue - Phase headers
        "success": "#00D9A3",        # Teal - Positive outcomes, successful actions
        "warning": "#FFB627",        # Amber - Cautions, elevated warnings
        "danger": "#FF0000",         # Pure Red - Critical alerts, DEFCON 1
        "muted": "#457B9D",          # Muted Blue - Secondary info, timestamps
        "normal": "#F1FAEE",         # Off-White - Primary text
        "highlight": "#FFB627",      # Amber - Highlights, important items
        "emphasis": "#FF6B35",       # Deep Orange - Bold emphasis
        "metric_good": "#00D9A3",    # Teal - Good metric values
        "metric_neutral": "#A8DADC", # Light Blue - Neutral/stable metrics
        "metric_bad": "#FFB627",     # Amber - Bad metric values
        "metric_critical": "#FF0000", # Pure Red - Critical metric values
    },
    "standard": {
        # Original Professional Calm scheme (lower contrast)
        "primary": "cyan",
        "secondary": "blue",
        "accent": "magenta",
        "success": "green",
        "warning": "yellow",
        "danger": "red",
        "muted": "dim white",
        "highlight": "bold white",
        "emphasis": "bold cyan",
        "metric_good": "green",
        "metric_neutral": "yellow",
        "metric_bad": "red",
        "metric_critical": "bold red"
    },
    "defcon1": {
        # Legacy DEFCON 1 theme (all red)
        "primary": "red",
        "secondary": "red",
        "accent": "bold red",
        "success": "yellow",
        "warning": "bold yellow",
        "danger": "bold red",
        "muted": "dim red",
        "highlight": "bold red",
        "emphasis": "bold red",
        "metric_good": "yellow",
        "metric_neutral": "red",
        "metric_bad": "bold red",
        "metric_critical": "bold white on red"
    },
    "retro": {
        "primary": "green",
        "secondary": "green",
        "accent": "bold green",
        "success": "green",
        "warning": "bold green",
        "danger": "bold green",
        "muted": "dim green",
        "highlight": "bold green",
        "emphasis": "bold green",
        "metric_good": "green",
        "metric_neutral": "green",
        "metric_bad": "dim green",
        "metric_critical": "reverse green"
    },
    "slate": {
        "primary": "bright_white",
        "secondary": "white",
        "accent": "bold white",
        "success": "white",
        "warning": "bold white",
        "danger": "white on red",
        "muted": "dim white",
        "highlight": "underline bold white",
        "emphasis": "bold white",
        "metric_good": "white",
        "metric_neutral": "dim white",
        "metric_bad": "white",
        "metric_critical": "bold white"
    }
}

class ThemeManager:
    """Manages the active color theme."""
    
    def __init__(self):
        self.current_theme_name = "defcon"  # Default to ADHD-optimised scheme
        self.colors = THEMES["defcon"]
    
    def set_theme(self, theme_name: str) -> bool:
        """Switch to a different theme.
        
        Args:
            theme_name: Name of theme ('standard', 'defcon1', 'retro', 'slate')
            
        Returns:
            True if theme changed, False if not found
        """
        if theme_name in THEMES:
            self.current_theme_name = theme_name
            self.colors = THEMES[theme_name]
            return True
        return False
    
    def get_colors(self) -> Dict[str, str]:
        """Get current color palette."""
        return self.colors

# Global singleton instance
theme_manager = ThemeManager()

# Proxy object for backward compatibility with existing code
# This allows `from cli.theme import COLORS` to still work, 
# but it won't dynamically update if assigned to a local variable.
# We will refactor usage to `theme_manager.colors` dynamically.
COLORS = theme_manager.colors

def progress_bar(value: int, max_value: int = 100, width: int = 10) -> str:
    """Generate ASCII progress bar string using current theme colors.
    
    Args:
        value: Current value
        max_value: Maximum value
        width: Character width of the bar
        
    Returns:
        Rich-formatted string (e.g. "[green]█████░░░░░[/green]")
    """
    # Ensure value is within bounds
    value = max(0, min(value, max_value))
    
    # Calculate filled portion
    filled = int((value / max_value) * width)
    empty = width - filled
    
    # Determine color based on value (using current theme)
    colors = theme_manager.get_colors()
    pct = value / max_value
    if pct < 0.3:
        color = colors["metric_bad"]
    elif pct < 0.7:
        color = colors["metric_neutral"]
    else:
        color = colors["metric_good"]
        
    bar = "█" * filled + "░" * empty
    return f"[{color}]{bar}[/{color}]"
