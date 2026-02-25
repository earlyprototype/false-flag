"""Dashboard layout manager using Rich.Live and Rich.Layout.

This module provides a persistent terminal UI with fixed zones:
- Header: Turn, Phase, Time (always visible)
- Sidebar: Live metrics (updates in-place)
- Main: Scrolling dialogue
- Footer: Available commands
"""

from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich import box
from typing import List

class WargameDashboard:
    """Manages the persistent dashboard layout."""
    
    def __init__(self, world, console):
        """Initialize dashboard with world state and console.
        
        Args:
            world: WorldState object
            console: Rich Console instance
        """
        self.world = world
        self.console = console
        
        # Use DEFCON colors locally (don't change global theme)
        self.COLORS = {
            "primary": "#FF6B35",        # Deep Orange
            "secondary": "#004E89",      # Navy Blue
            "accent": "#1A659E",         # Steel Blue
            "success": "#00D9A3",        # Teal
            "warning": "#FFB627",        # Amber
            "danger": "#FF0000",         # Pure Red
            "muted": "#457B9D",          # Muted Blue
            "emphasis": "#FF6B35",       # Deep Orange
            "metric_good": "#00D9A3",    # Teal
            "metric_neutral": "#A8DADC", # Light Blue
            "metric_bad": "#FFB627",     # Amber
            "metric_critical": "#FF0000", # Pure Red
        }
        self.conversation_log = []
        
        # Create layout structure
        # Give more space to body by reducing header/footer
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=2)  # Reduced from 3 to 2
        )
        self.layout["body"].split_row(
            Layout(name="sidebar", size=30),  # Reduced from 32 to 30
            Layout(name="main", ratio=1)
        )
    
    def render_header(self) -> Panel:
        """Render top bar: TURN | PHASE | TIME.
        
        Returns:
            Rich Panel with header content
        """
        # Format: TURN 004 | DISCUSSION PHASE | 17:00 HRS with dramatic styling
        content = f"[reverse][{self.COLORS['emphasis']} bold] TURN {self.world.turn:03d} │ DISCUSSION PHASE │ 17:00 HRS [/][/reverse]"
        
        return Panel(
            content,
            style=f"bold {self.COLORS['primary']} on #0A0E27",
            box=box.HEAVY,
            padding=(0, 0)  # Minimal padding to maximize space
        )
    
    def render_sidebar(self) -> Panel:
        """Render left panel with live metrics.
        
        Returns:
            Rich Panel with metrics table
        """
        from cli.theme import SYMBOLS, progress_bar
        
        # Check if we should hide metrics (Immersive/Emergent modes)
        # This requires knowing the play mode, which isn't directly in dashboard state
        # We'll check if metrics are hidden by looking at world.metrics visibility flags if they existed
        # For now, we'll render a simplified view if needed
        
        # Create metrics table
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Label", style=self.COLORS['secondary'])
        table.add_column("Value", justify="right")
        table.add_column("Bar", width=10)
        
        # Risk
        risk = self.world.metrics.escalation_risk
        risk_color = self.COLORS['metric_critical'] if risk >= 70 else self.COLORS['metric_bad'] if risk >= 50 else self.COLORS['metric_good']
        table.add_row(
            f"{SYMBOLS['risk']} Risk",
            f"[{risk_color}]{risk}[/]",
            progress_bar(risk, 100, 10)
        )
        
        # Stability
        stability = self.world.metrics.domestic_stability
        stab_color = self.COLORS['metric_critical'] if stability <= 30 else self.COLORS['metric_bad'] if stability <= 50 else self.COLORS['metric_good']
        table.add_row(
            f"{SYMBOLS['stability']} Stability",
            f"[{stab_color}]{stability}[/]",
            progress_bar(stability, 100, 10)
        )
        
        # Cohesion
        cohesion = self.world.metrics.alliance_cohesion
        coh_color = self.COLORS['metric_critical'] if cohesion <= 30 else self.COLORS['metric_bad'] if cohesion <= 50 else self.COLORS['metric_good']
        table.add_row(
            f"{SYMBOLS['cohesion']} Cohesion",
            f"[{coh_color}]{cohesion}[/]",
            progress_bar(cohesion, 100, 10)
        )
        
        # Casualties
        casualties = self.world.metrics.casualties_mil + self.world.metrics.casualties_civ
        table.add_row(
            f"{SYMBOLS['casualties']} Casualties",
            f"{casualties}",
            f"{self.world.metrics.casualties_mil}m {self.world.metrics.casualties_civ}c"
        )
        
        return Panel(
            table,
            title=f"[reverse][{self.COLORS['warning']} bold] SITREP [/][/reverse]",
            border_style=f"bold {self.COLORS['primary']}",
            box=box.HEAVY,
            padding=(0, 1),
            style="on #0A0E27"
        )
    
    def render_main(self) -> Panel:
        """Render centre panel with live scrolling conversation feed.
        
        Returns:
            Rich Panel with recent dialogue (streaming style)
        """
        # Show last 100 messages - much more capacity!
        if not self.conversation_log:
            content = f"[dim]═══ COBRA COMMAND FEED ═══\n\nAwaiting intelligence...[/]"
        else:
            # Check if we have more messages than we're showing
            total_messages = len(self.conversation_log)
            messages_to_show = min(100, total_messages)  # Doubled from 50
            recent = self.conversation_log[-messages_to_show:]
            
            # Add scroll indicator at top if there's more content
            if total_messages > messages_to_show:
                hidden_count = total_messages - messages_to_show
                scroll_hint = f"[{self.COLORS['muted']} dim]▲ {hidden_count} earlier messages - use /briefing for full log ▲[/]\n"
                recent.insert(0, scroll_hint)
            
            content = "\n".join(recent)
        
        return Panel(
            content,
            title=f"[reverse][{self.COLORS['accent']} bold] ⬤ COBRA BRIEFING FEED [/][/reverse]",  # Added ⬤ for "live" indicator
            border_style=f"bold {self.COLORS['accent']}",
            box=box.HEAVY,
            padding=(1, 1),
            style="on #0A0E27"  # Force dark navy background
        )
    
    def render_footer(self) -> Panel:
        """Render bottom bar with available commands.
        
        Returns:
            Rich Panel with command hints
        """
        commands = f"[{self.COLORS['primary']} bold]/status[/] │ [{self.COLORS['primary']} bold]/menu[/] │ [{self.COLORS['primary']} bold]/advise[/] │ [{self.COLORS['primary']} bold]/resources[/] │ [{self.COLORS['primary']} bold]/briefing[/] │ [{self.COLORS['success']} bold]/decide[/] │ [{self.COLORS['danger']} bold]/quit[/]"
        
        return Panel(
            commands,
            style=f"{self.COLORS['primary']} on #0A0E27",  # Orange on dark navy
            box=box.HEAVY,
            padding=(0, 1)  # Reduced padding to save vertical space
        )
    
    def update(self):
        """Refresh all dashboard panels."""
        self.layout["header"].update(self.render_header())
        self.layout["sidebar"].update(self.render_sidebar())
        self.layout["main"].update(self.render_main())
        self.layout["footer"].update(self.render_footer())
    
    def add_message(self, speaker: str, message: str, stream: bool = False):
        """Add a message to the conversation log.
        
        Args:
            speaker: Who is speaking (PM, NSA, CDS, etc.)
            message: The message content
            stream: If True, message will appear with streaming effect
        """
        if speaker == "PM":
            formatted = f"[{self.COLORS['emphasis']}]PM:[/] {message}"
        else:
            formatted = f"[{self.COLORS['secondary']}]{speaker}:[/] {message}"
        
        self.conversation_log.append(formatted)
        
        # Keep log size manageable (max 200 messages for more history)
        if len(self.conversation_log) > 200:
            self.conversation_log = self.conversation_log[-200:]
    
    def stream_message(self, speaker: str, message: str, console, live, delay: float = 0.02):
        """Stream a message into the conversation log character by character.
        
        Args:
            speaker: Who is speaking
            message: The message content
            console: Rich Console instance
            live: Rich Live instance
            delay: Delay between characters (seconds)
        """
        import time
        
        if speaker == "PM":
            prefix = f"[{self.COLORS['emphasis']}]PM:[/] "
        else:
            prefix = f"[{self.COLORS['secondary']}]{speaker}:[/] "
        
        # Add prefix immediately
        current_line = prefix
        
        # Stream message character by character
        for char in message:
            current_line += char
            
            # Update the last line in conversation log
            if self.conversation_log and self.conversation_log[-1].startswith(prefix.replace('[/', '').replace(']', '')):
                self.conversation_log[-1] = current_line
            else:
                self.conversation_log.append(current_line)
            
            # Refresh display
            self.update()
            live.refresh()
            time.sleep(delay)
        
        # Keep log size manageable
        if len(self.conversation_log) > 200:
            self.conversation_log = self.conversation_log[-200:]

