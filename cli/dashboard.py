"""Dashboard layout manager using Rich.Live and Rich.Layout.

This module provides a persistent terminal UI with fixed zones:
- Header: compact Operation Tuman masthead (classification strip + turn rule)
- Sidebar: Live metrics (updates in-place)
- Main: Scrolling dialogue with sonar-trace dividers
- Footer: Available commands over a closing classification strip

All chrome speaks the shared fog + signals-room language from
``cli/aesthetics.py``: every render is static per repaint (no frame
animation inside Live), every color is read from ``theme_manager`` at
render time, and every seeded trim derives from the turn number so each
turn's weather differs deterministically.
"""

from rich.console import Group
from rich.layout import Layout
from rich.markup import escape as rich_escape
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text
from rich import box

from cli import aesthetics as ae
from cli.theme import theme_manager


def _safe_markup(text: str) -> str:
    """Return text unchanged if it is valid Rich markup, escaped otherwise.

    Feed messages mix code-authored markup (SYSTEM banners) with free text
    from the player and the LLM. A stray closing tag in free text would crash
    the Live repaint, and bracketed text like "[REDACTED]" would be swallowed
    as an unknown style and disappear - escape anything that doesn't resolve.
    """
    try:
        parsed = Text.from_markup(text)  # raises MarkupError on broken tags
        for span in parsed.spans:
            if isinstance(span.style, str):
                Style.parse(span.style)  # raises on tags that aren't styles
        return text
    except Exception:
        return rich_escape(text)


class WargameDashboard:
    """Manages the persistent dashboard layout."""
    MAX_LOG_MESSAGES = 100

    # Rows consumed around the feed content: header (3) + footer (2) +
    # feed panel border (2) + vertical padding (2)
    FEED_CHROME_ROWS = 9
    # Columns consumed around the feed content: sidebar (30) +
    # feed panel border (2) + horizontal padding (2)
    FEED_CHROME_COLS = 34


    def __init__(self, world, console):
        """Initialize dashboard with world state and console.
        
        Args:
            world: WorldState object
            console: Rich Console instance
        """
        self.world = world
        self.console = console

        # Active theme palette (the default "defcon" theme carries the same
        # DEFCON values this dashboard used to hard-code). Kept as an
        # attribute for callers; render methods re-read theme_manager at
        # render time so /theme switches repaint the chrome instantly.
        self.COLORS = theme_manager.get_colors()
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
    
    def _chrome_width(self) -> int:
        """Full-width chrome rows follow the live console width."""
        return self.console.size.width or 100

    def _turn_seed(self, salt: str = "") -> str:
        """Stable per-turn seed so each turn's trims differ deterministically."""
        return f"dash-turn-{self.world.turn}{('-' + salt) if salt else ''}"

    def _fog_density(self) -> float:
        """Fog thickens as escalation risk climbs (0.25 calm .. 0.65 critical)."""
        risk = getattr(self.world.metrics, "escalation_risk", 50)
        return min(0.65, 0.25 + risk / 250)

    def render_header(self) -> Group:
        """Render the compact Tuman masthead: classification strip,
        title + turn/phase rule, and a thin per-turn fog trim.

        Returns:
            Rich Group, exactly three rows (the header layout's size).
        """
        colors = theme_manager.get_colors()
        width = self._chrome_width()
        phase = str(self.world.phase or "briefing").upper()
        seed = self._turn_seed()

        # ━━[ FALSE FLAG ── OPERATION TUMAN ]━━…━━[ TURN 004 │ DISCUSSION ]━━
        status = f"TURN {self.world.turn:03d} │ {phase}"
        rule = Text("━━", style=colors["accent"])
        rule.append("[ ", style=colors["accent"])
        rule.append("FALSE FLAG", style=f"{colors['primary']} bold")
        rule.append(" ── OPERATION TUMAN", style=colors["muted"])
        rule.append(" ]", style=colors["accent"])
        fill = width - rule.cell_len - len(status) - 6  # "[ " + " ]━━"
        if fill > 0:
            rule.append("━" * fill, style=colors["accent"])
        rule.append("[ ", style=colors["accent"])
        rule.append(status, style=f"{colors['highlight']} bold")
        rule.append(" ]━━", style=colors["accent"])
        rule.no_wrap = True
        rule.overflow = "crop"

        return Group(
            ae.classification_strip(width=width, seed=seed, edge="bare"),
            rule,
            ae.fog_band(width, 1, self._fog_density(), seed=seed),
        )
    
    # Interior columns of the 30-col sidebar: 30 - 2 border - 2 padding
    SIDEBAR_INNER_COLS = 26

    def render_sidebar(self) -> Panel:
        """Render left panel with live metrics.

        Returns:
            Rich Panel with metrics table
        """
        from cli.theme import SYMBOLS, progress_bar

        colors = theme_manager.get_colors()

        # Create metrics table. Column budget is tight: the 30-col sidebar
        # leaves 26 interior columns, so pad on the right only and keep the
        # bar at 8 cells — full labels ("Casualties") must never truncate.
        table = Table(show_header=False, box=None, padding=(0, 1, 0, 0))
        table.add_column("Label", style=colors['secondary'], no_wrap=True)
        table.add_column("Value", justify="right", no_wrap=True)
        table.add_column("Bar", width=8, no_wrap=True)

        # Risk
        risk = self.world.metrics.escalation_risk
        risk_color = colors['metric_critical'] if risk >= 70 else colors['metric_bad'] if risk >= 50 else colors['metric_good']
        table.add_row(
            f"{SYMBOLS['risk']} Risk",
            f"[{risk_color}]{risk}[/]",
            progress_bar(risk, 100, 8)
        )

        # Stability
        stability = self.world.metrics.domestic_stability
        stab_color = colors['metric_critical'] if stability <= 30 else colors['metric_bad'] if stability <= 50 else colors['metric_good']
        table.add_row(
            f"{SYMBOLS['stability']} Stability",
            f"[{stab_color}]{stability}[/]",
            progress_bar(stability, 100, 8)
        )

        # Cohesion
        cohesion = self.world.metrics.alliance_cohesion
        coh_color = colors['metric_critical'] if cohesion <= 30 else colors['metric_bad'] if cohesion <= 50 else colors['metric_good']
        table.add_row(
            f"{SYMBOLS['cohesion']} Cohesion",
            f"[{coh_color}]{cohesion}[/]",
            progress_bar(cohesion, 100, 8)
        )

        # Casualties
        casualties = self.world.metrics.casualties_mil + self.world.metrics.casualties_civ
        table.add_row(
            f"{SYMBOLS['casualties']} Casualties",
            f"{casualties}",
            f"{self.world.metrics.casualties_mil}m {self.world.metrics.casualties_civ}c"
        )

        # Thin per-turn fog trim under the metrics, sized to the sidebar's
        # 26-col interior; density follows escalation risk (the fog literally
        # thickens as the crisis worsens).
        seed = self._turn_seed("sitrep")
        fog = ae.fog_band(self.SIDEBAR_INNER_COLS, 1,
                          self._fog_density(), seed)

        return Panel(
            Group(table, fog),
            title=f"[{colors['danger']} bold]SITREP[/]",
            title_align="left",
            subtitle=f"[{colors['warning']}]{ae.reference_code(seed)}[/]",
            subtitle_align="right",
            border_style=colors['muted'],
            box=box.SQUARE,
            padding=(0, 1),
        )
    
    @staticmethod
    def _estimate_lines(message: str, width: int) -> int:
        """Estimate how many rendered lines a feed message occupies at a given width."""
        try:
            plain_len = Text.from_markup(message).cell_len
        except Exception:
            plain_len = len(message)
        return max(1, -(-plain_len // max(1, width)))  # ceil division

    def render_main(self) -> Panel:
        """Render centre panel with live scrolling conversation feed.

        Rich crops overflowing panel content from the BOTTOM, so the feed must
        pre-trim itself to the newest messages that fit the region - otherwise,
        once the panel fills up, fresh messages are appended below the fold and
        never become visible.

        Returns:
            Rich Panel with the most recent dialogue (streaming style)
        """
        colors = theme_manager.get_colors()
        height = self.console.size.height or 24
        width = self.console.size.width or 100
        row_budget = max(3, height - self.FEED_CHROME_ROWS)
        inner_width = max(20, width - self.FEED_CHROME_COLS)

        if not self.conversation_log:
            content = f"[{colors['muted']}]─── COBRA COMMAND FEED ───\n\nAwaiting intelligence...[/]"
        else:
            # Walk backwards from the newest message, accounting for wrapping
            selected = []
            row_counts = []
            used = 0
            for message in reversed(self.conversation_log):
                rows = self._estimate_lines(message, inner_width)
                if selected and used + rows > row_budget:
                    break
                selected.append(message)
                row_counts.append(rows)
                used += rows
                if used >= row_budget:
                    break
            selected.reverse()
            row_counts.reverse()

            # Add scroll indicator at top if there's more content
            hidden_count = len(self.conversation_log) - len(selected)
            if hidden_count > 0:
                # Make room for the hint line by dropping the oldest visible message(s)
                while len(selected) > 1 and used + 1 > row_budget:
                    used -= row_counts.pop(0)
                    selected.pop(0)
                    hidden_count += 1
                scroll_hint = f"[{colors['muted']} dim]▲ {hidden_count} earlier messages - use /briefing for full log ▲[/]"
                selected.insert(0, scroll_hint)

            content = "\n".join(selected)

        return Panel(
            content,
            title=f"[{colors['accent']} bold]● COBRA BRIEFING FEED[/]",  # ● = live contact
            title_align="left",
            subtitle=f"[{colors['muted']}]{ae.reference_code(self._turn_seed('feed'))}[/]",
            subtitle_align="right",
            border_style=colors['muted'],
            box=box.SQUARE,
            padding=(1, 1),
        )

    def render_footer(self) -> Group:
        """Render bottom bar: sonar quick-help row over the closing
        classification strip (documents close the way they open).

        Returns:
            Rich Group, exactly two rows (the footer layout's size).
        """
        colors = theme_manager.get_colors()
        width = self._chrome_width()
        # Short set only: the full list lives in /menu. The longer string
        # cropped past 80 columns in the no-wrap footer row.
        commands = f"[{colors['primary']} bold]/status[/] │ [{colors['primary']} bold]/menu[/] │ [{colors['primary']} bold]/advise[/] │ [{colors['primary']} bold]/intel[/] │ [{colors['success']} bold]/decide[/] │ [{colors['danger']} bold]/quit[/]"
        command_row = Text.from_markup(commands)
        command_row.no_wrap = True
        command_row.overflow = "crop"
        return Group(
            command_row,
            ae.classification_strip(width=width, seed=self._turn_seed(),
                                    edge="bare"),
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
        # Free text (player input, LLM output) can contain broken markup that
        # would crash the Live repaint; escape anything that doesn't parse.
        message = _safe_markup(message)
        colors = theme_manager.get_colors()
        if speaker == "PM":
            formatted = f"[{colors['emphasis']}]PM:[/] {message}"
        elif speaker == "SYSTEM":
            # System traffic is background noise in the signals room: muted,
            # like the main CLI's system lines.
            formatted = f"[{colors['muted']}]SYSTEM:[/] {message}"
        else:
            formatted = f"[{colors['secondary']}]{rich_escape(speaker)}:[/] {message}"

        self.conversation_log.append(formatted)
        self._trim_log()

    def add_divider(self, label: str = "", seed=None):
        """Append a sonar-language divider line to the feed.

        Turn and phase breaks in the feed are sonar traces
        (``──●──[ LABEL ]───── ·· ─``), not plain rules — the same language
        the main CLI uses between sections. Rendered once at add time (the
        feed is a list of markup strings), sized to the feed's interior.

        Args:
            label: Optional divider label (e.g. "TURN 3 BRIEFING"); a bare
                sonar trace is used when empty.
            seed: Deterministic seed; defaults to turn + label.
        """
        width = max(20, (self.console.size.width or 100) - self.FEED_CHROME_COLS)
        if seed is None:
            seed = f"{self._turn_seed('feed')}-{label}"
        if label:
            divider = ae.phase_banner(label, seed=seed, width=width)
        else:
            divider = ae.sonar_divider(seed=seed, width=width)
        self.conversation_log.append(divider.markup)
        self._trim_log()
    
    def _trim_log(self):
        """Keep the conversation log at most MAX_LOG_MESSAGES entries."""
        if len(self.conversation_log) > self.MAX_LOG_MESSAGES:
            self.conversation_log = self.conversation_log[-self.MAX_LOG_MESSAGES:]

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
                self._trim_log()
            
            # Refresh display
            self.update()
            live.refresh()
            time.sleep(delay)
        
        # Keep log size manageable
        if len(self.conversation_log) > 200:
            self.conversation_log = self.conversation_log[-200:]

