"""Rich UI components for enhanced CLI display.

Provides professional ASCII-only tables, panels, and formatting while preserving
compatibility with existing narrative scrolling and keyboard systems.
"""

import os
import sys
from typing import Optional, Any, List, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.tree import Tree
from rich.markdown import Markdown
from rich import box

from cli.theme import theme_manager, SYMBOLS, BOX, WIDTH, progress_bar
from cli.formatters import format_metric_status

# Environment variable killswitch for instant rollback
RICH_ENABLED = os.getenv("WARGAME_RICH_UI", "true").lower() == "true"

# Initialize console with Windows compatibility
# CRITICAL: force_interactive=False to preserve msvcrt.kbhit() behavior
console = Console(
    legacy_windows=(sys.platform == "win32"),
    force_terminal=True,
    force_interactive=False,  # Essential for SPACE-to-skip!
    color_system="windows" if sys.platform == "win32" else "auto"  # Force Windows colour support
)


def format_markdown(text: str) -> Markdown:
    """Format markdown text for Rich display.
    
    Args:
        text: Markdown-formatted text string
        
    Returns:
        Rich Markdown object for rendering
    """
    return Markdown(text)


def phase_header(phase_name: str, turn: int) -> str:
    """Generate clean phase header with ASCII rounded box.
    
    Args:
        phase_name: Name of phase (BRIEFING, DISCUSSION, DECISION, ADJUDICATION)
        turn: Current turn number
        
    Returns:
        Formatted header string or Panel object
    """
    if not RICH_ENABLED:
        return f"TURN {turn}: {phase_name} PHASE"
    
    # Get dynamic colors
    COLORS = theme_manager.get_colors()
    
    # Phase colors
    phase_colors = {
        "BRIEFING": COLORS["accent"],
        "DISCUSSION": COLORS["primary"],
        "DECISION": "magenta",
        "ADJUDICATION": COLORS["success"]
    }
    
    color = phase_colors.get(phase_name, COLORS["success"]) # Default fallback safe color
    
    return Panel(
        f"[bold]TURN {turn} │ {phase_name} PHASE[/bold]",
        style=f"{color}",
        box=box.ROUNDED,
        padding=(0, 2),
        expand=False
    )


def metrics_table(world, show_deltas: bool = False, 
                  previous_metrics: Optional[Any] = None) -> Table:
    """Generate professional metrics display with ASCII symbols and bars.
    
    Args:
        world: WorldState object
        show_deltas: If True and previous_metrics provided, show changes
        previous_metrics: Previous Metrics object for delta calculation
        
    Returns:
        Rich Table object or plain string if Rich disabled
    """
    if not RICH_ENABLED:
        # Fallback to plain text
        lines = []
        lines.append(f"Turn: {world.turn}")
        lines.append(f"Phase: {world.phase}")
        lines.append(f"Escalation Risk: {world.metrics.escalation_risk}/100")
        lines.append(f"Domestic Stability: {world.metrics.domestic_stability}/100")
        lines.append(f"Alliance Cohesion: {world.metrics.alliance_cohesion}/100")
        lines.append(f"Military Casualties: {world.metrics.casualties_mil}")
        lines.append(f"Civilian Casualties: {world.metrics.casualties_civ}")
        return "\n".join(lines)
    
    COLORS = theme_manager.get_colors()
    
    # Title with turn and phase
    phase_display = world.phase.upper() if hasattr(world, 'phase') else "UNKNOWN"
    title = f"[{COLORS['accent']} bold]SITUATION REPORT │ Turn {world.turn} │ {phase_display} PHASE[/{COLORS['accent']} bold]"
    
    table = Table(title=title, border_style=COLORS["secondary"], show_header=True, padding=(0, 1), box=box.ROUNDED)
    table.add_column("", style=COLORS["secondary"], no_wrap=True, width=3)  # Symbol
    table.add_column("Metric", style=COLORS["normal"], no_wrap=True)
    table.add_column("Value", justify="right", style=COLORS["normal"], width=6)
    table.add_column("Bar", justify="left", width=12)
    table.add_column("Status", justify="left", style=COLORS["normal"], width=10)
    
    if show_deltas and previous_metrics:
        table.add_column("Change", justify="right", style=COLORS["warning"], width=8)
    
    def format_risk_value(value: int) -> str:
        """Color-code risk value (high is bad)."""
        if value >= 70:
            return f"[{COLORS['metric_critical']}]{value}[/{COLORS['metric_critical']}]"
        elif value >= 50:
            return f"[{COLORS['metric_bad']}]{value}[/{COLORS['metric_bad']}]"
        else:
            return f"[{COLORS['metric_good']}]{value}[/{COLORS['metric_good']}]"
    
    def format_stability_value(value: int) -> str:
        """Color-code stability/cohesion value (low is bad)."""
        if value <= 30:
            return f"[{COLORS['metric_critical']}]{value}[/{COLORS['metric_critical']}]"
        elif value <= 50:
            return f"[{COLORS['metric_bad']}]{value}[/{COLORS['metric_bad']}]"
        else:
            return f"[{COLORS['metric_good']}]{value}[/{COLORS['metric_good']}]"
    
    def format_delta(delta: int) -> str:
        """Format delta with color and sign."""
        if delta > 0:
            return f"[{COLORS['success']}]+{delta}[/{COLORS['success']}]"
        elif delta < 0:
            return f"[{COLORS['danger']}]{delta}[/{COLORS['danger']}]"
        else:
            return f"[{COLORS['muted']}]±0[/{COLORS['muted']}]"
    
    # Escalation Risk (high is bad)
    risk_val = world.metrics.escalation_risk
    risk_str = format_risk_value(risk_val)
    risk_bar = progress_bar(risk_val, 100, 10)
    risk_status = format_metric_status(risk_val, 'risk')
    
    row = [SYMBOLS["risk"], "Escalation Risk", risk_str, risk_bar, risk_status]
    if show_deltas and previous_metrics:
        delta = risk_val - previous_metrics.escalation_risk
        row.append(format_delta(delta))
    table.add_row(*row)
    
    # Domestic Stability (low is bad)
    stability_val = world.metrics.domestic_stability
    stability_str = format_stability_value(stability_val)
    stability_bar = progress_bar(stability_val, 100, 10)
    stability_status = format_metric_status(stability_val, 'stability')
    
    row = [SYMBOLS["stability"], "Domestic Stability", stability_str, stability_bar, stability_status]
    if show_deltas and previous_metrics:
        delta = stability_val - previous_metrics.domestic_stability
        row.append(format_delta(delta))
    table.add_row(*row)
    
    # Alliance Cohesion (low is bad)
    cohesion_val = world.metrics.alliance_cohesion
    cohesion_str = format_stability_value(cohesion_val)
    cohesion_bar = progress_bar(cohesion_val, 100, 10)
    cohesion_status = format_metric_status(cohesion_val, 'cohesion')
    
    row = [SYMBOLS["cohesion"], "Alliance Cohesion", cohesion_str, cohesion_bar, cohesion_status]
    if show_deltas and previous_metrics:
        delta = cohesion_val - previous_metrics.alliance_cohesion
        row.append(format_delta(delta))
    table.add_row(*row)
    
    # Casualties
    casualties_total = world.metrics.casualties_mil + world.metrics.casualties_civ
    casualties_str = f"{casualties_total}"
    casualties_detail = f"{world.metrics.casualties_mil} mil │ {world.metrics.casualties_civ} civ"
    
    row = [SYMBOLS["casualties"], "Casualties", casualties_str, casualties_detail, ""]
    if show_deltas and previous_metrics:
        row.append("")  # No delta for casualties
    table.add_row(*row)
    
    # Calculate and add influence
    influence_raw = (world.metrics.domestic_stability + world.metrics.alliance_cohesion) / 2.0
    influence = int((influence_raw - 50) / 5)
    influence = max(-10, min(10, influence))
    
    # Color-code influence
    if influence >= 5:
        influence_str = f"[{COLORS['metric_good']}]+{influence}[/{COLORS['metric_good']}]"
    elif influence >= 0:
        influence_str = f"[{COLORS['metric_neutral']}]+{influence}[/{COLORS['metric_neutral']}]"
    elif influence >= -5:
        influence_str = f"[{COLORS['metric_bad']}]{influence}[/{COLORS['metric_bad']}]"
    else:
        influence_str = f"[{COLORS['metric_critical']}]{influence}[/{COLORS['metric_critical']}]"
    
    influence_status = format_metric_status(influence, 'influence')
    
    row = [SYMBOLS["influence"], "Influence", influence_str, "", influence_status]
    if show_deltas and previous_metrics:
        row.append("")  # No delta for influence (it's derived)
    table.add_row(*row)
    
    return table


def advisor_menu_panel() -> Panel:
    """Generate formatted advisor hierarchy panel using Tree view.
    
    Returns:
        Rich Panel object
    """
    if not RICH_ENABLED:
        return "Use /menu to see advisor list"
    
    COLORS = theme_manager.get_colors()
    
    # Create tree structure
    tree = Tree(f"[{COLORS['accent']} bold]COBRA CABINET STRUCTURE[/]", guide_style=COLORS['secondary'])
    
    # Strategic/Intel Node
    strategic = tree.add(f"[{COLORS['primary']} bold]Strategic & Intelligence[/]")
    strategic.add(f"[{COLORS['highlight']}]National Security Advisor (NSA)[/]\n[dim]Threat analysis, strategic coordination[/]")
    
    # Military Node
    military = tree.add(f"[{COLORS['danger']} bold]Military Operations[/]")
    military.add(f"[{COLORS['highlight']}]Chief of the Defence Staff (CDS)[/]\n[dim]Force deployment, military options[/]")
    
    # Diplomatic Node
    diplomatic = tree.add(f"[{COLORS['success']} bold]Foreign Affairs[/]")
    diplomatic.add(f"[{COLORS['highlight']}]Foreign Secretary[/]\n[dim]Diplomacy, alliances, NATO[/]")
        
    # Domestic/Legal Node
    domestic = tree.add(f"[{COLORS['warning']} bold]Domestic & Legal[/]")
    domestic.add(f"[{COLORS['highlight']}]Home Secretary[/]\n[dim]Civil order, public messaging[/]")
    domestic.add(f"[{COLORS['highlight']}]Attorney General[/]\n[dim]Legal frameworks, international law[/]")
    
    return Panel(
        tree,
        title=f"[{COLORS['accent']} bold]ADVISOR HIERARCHY[/]",
        border_style=COLORS['accent'],
        box=box.ROUNDED,
        padding=(1, 2)
    )


def diplomatic_contacts_table(contacts: List[Tuple[str, str, str]]) -> Panel:
    """Generate diplomatic contacts panel using a tree view.
    
    Args:
        contacts: List of (country, access_level, title) tuples
        
    Returns:
        Rich Panel object with Tree
    """
    if not RICH_ENABLED:
        return "Diplomatic contacts available"
    
    COLORS = theme_manager.get_colors()
    
    if not contacts:
        return Panel(
            f"[{COLORS['muted']}]No diplomatic contacts available (Alliance Cohesion too low)[/]",
            title=f"[{COLORS['success']} bold]DIPLOMATIC CHANNELS[/]",
            border_style=COLORS['success'],
            box=box.ROUNDED
        )
    
    # Define groupings
    alliances = {
        "NATO Allies": ["US", "France", "Germany", "Poland"],
        "Adversaries": ["Russia"],
        "Partners & Others": ["Ukraine", "Ireland"]
    }
    
    tree = Tree(f"[{COLORS['success']} bold]DIPLOMATIC CHANNELS[/{COLORS['success']} bold]", guide_style=COLORS['secondary'])
    
    # Create nodes
    nodes = {
        "NATO Allies": tree.add(f"[{COLORS['secondary']} bold]NATO Alliance[/]"),
        "Adversaries": tree.add(f"[{COLORS['danger']} bold]Adversaries[/]"),
        "Partners & Others": tree.add(f"[{COLORS['muted']} bold]Partners & Others[/]")
    }
    
    # Sort contacts to ensure consistent order
    contacts.sort(key=lambda x: x[0])
    
    for country, access_level, title in contacts:
        # Determine group
        group = "Partners & Others"
        for g_name, countries in alliances.items():
            if country in countries:
                group = g_name
                break
        
        # Format status
        if access_level == "leader":
            marker = SYMBOLS["leader"]
            status = f"[{COLORS['warning']}]LEADER[/]"
        else:
            marker = SYMBOLS["diplomat"]
            status = f"[{COLORS['muted']}]DIPLOMAT[/]"
            
        # Add to appropriate node
        # Format: [Symbol] Country: Title (STATUS) -> /command
        nodes[group].add(
            f"{marker} {country}: {title} ({status})  [{COLORS['primary']}]/call {country.lower()}[/]"
        )
    
    # Remove empty nodes
    # Rich Tree doesn't support easy removal, so we rebuild if we want to be clean,
    # or just leave them (showing empty categories is fine for info).
    # Let's leave them to show structure.
    
    return Panel(
        tree,
        title=f"[{COLORS['success']} bold]SECURE LINES[/]",
        border_style=COLORS['success'],
        box=box.ROUNDED,
        padding=(0, 1)
    )


def resources_tables(initial_conditions: dict) -> Tuple[Table, Table]:
    """Generate forces and stockpiles tables.
    
    Args:
        initial_conditions: Initial conditions dict with uk_forces and stockpiles
        
    Returns:
        Tuple of (forces_table, stockpiles_table)
    """
    if not RICH_ENABLED:
        return ("UK Forces", "UK Stockpiles")
    
    COLORS = theme_manager.get_colors()
    
    # Forces table
    forces_table = Table(
        title=f"[{COLORS['accent']} bold]UK MILITARY FORCES[/{COLORS['accent']} bold]",
        border_style=COLORS["secondary"],
        show_header=True,
        box=box.ROUNDED
    )
    forces_table.add_column("Unit", style=COLORS["secondary"], no_wrap=True)
    forces_table.add_column("Type", style=COLORS["normal"])
    forces_table.add_column("Location", style=COLORS["muted"])
    forces_table.add_column("Status", style=COLORS["normal"])
    
    uk_forces = initial_conditions.get("uk_forces", {})
    
    # Naval forces
    for unit in uk_forces.get("naval", []):
        unit_id = unit.get("id", "Unknown").replace("_", " ")
        unit_type = unit.get("type", "").replace("_", " ")
        location = unit.get("location", "").replace("_", " ")
        status = unit.get("status", "").replace("_", " ")
        
        # Color-code status
        if "operational" in status.lower():
            status_colored = f"[{COLORS['success']}]{status}[/{COLORS['success']}]"
        elif "limited" in status.lower():
            status_colored = f"[{COLORS['warning']}]{status}[/{COLORS['warning']}]"
        else:
            status_colored = status
        
        forces_table.add_row(unit_id, unit_type, location, status_colored)
    
    # Air forces
    for unit in uk_forces.get("air", []):
        unit_id = unit.get("id", "Unknown").replace("_", " ")
        unit_type = unit.get("type", "").replace("_", " ")
        location = unit.get("location", "").replace("_", " ")
        status = unit.get("status", "").replace("_", " ")
        
        # Add aircraft count if present
        aircraft_count = unit.get("aircraft_count")
        operational_aircraft = unit.get("operational_aircraft")
        if aircraft_count is not None:
            if operational_aircraft is not None:
                unit_type += f" ({operational_aircraft}/{aircraft_count})"
            else:
                unit_type += f" ({aircraft_count})"
        
        # Color-code status
        if "operational" in status.lower():
            status_colored = f"[{COLORS['success']}]{status}[/{COLORS['success']}]"
        elif "limited" in status.lower() or "reduced" in status.lower():
            status_colored = f"[{COLORS['warning']}]{status}[/{COLORS['warning']}]"
        else:
            status_colored = status
        
        forces_table.add_row(unit_id, unit_type, location, status_colored)
    
    # Stockpiles table (USING TREE STRUCTURE NOW)
    stockpiles = initial_conditions.get("stockpiles", {})
    
    stock_tree = Tree(
        f"[{COLORS['accent']} bold]AMMUNITION STOCKPILES[/{COLORS['accent']} bold]",
        guide_style=COLORS['secondary']
    )
    
    # Group stockpiles by category
    categories = [
        ("Air Defence", ["aster_15", "aster_30", "sea_ceptor"]),
        ("Naval Strike", ["tomahawk_cruise_missiles", "harpoon_anti_ship"]),
        ("Air-Launched", ["storm_shadow_cruise_missiles", "paveway_laser_guided_bombs"]),
        ("Anti-Submarine", ["spearfish_torpedoes", "stingray_lightweight_torpedoes"]),
    ]
    
    for category, weapons in categories:
        cat_node = stock_tree.add(f"[{COLORS['emphasis']}]{category}[/]")
        
        for weapon_key in weapons:
            weapon_data = stockpiles.get(weapon_key, {})
            if weapon_data:
                name = weapon_key.replace('_', ' ').title()
                count = weapon_data.get("count", 0)
                note = weapon_data.get("note", "")
                
                # Color-code count
                if count >= 100:
                    count_colored = f"[{COLORS['success']}]{count}[/{COLORS['success']}]"
                elif count >= 50:
                    count_colored = f"[{COLORS['warning']}]{count}[/{COLORS['warning']}]"
                else:
                    count_colored = f"[{COLORS['danger']}]{count}[/{COLORS['danger']}]"
                
                cat_node.add(f"{name}: {count_colored} [italic muted]({note})[/]")
    
    # Return formatted panel instead of table for consistency
    stockpiles_panel = Panel(
        stock_tree,
        border_style=COLORS["secondary"],
        box=box.ROUNDED,
        padding=(1, 2)
    )
    
    return (forces_table, stockpiles_panel)


def command_menu() -> Panel:
    """Generate command reference menu.
    
    Returns:
        Rich Panel object
    """
    if not RICH_ENABLED:
        return "Commands: /status /menu /advise /resources /call /decide /save /quit"
    
    COLORS = theme_manager.get_colors()
    
    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column("Command", style=COLORS['primary'])
    table.add_column("Description", style=COLORS['muted'])
    
    # Commands
    commands = [
        ("/status", "Show current metrics and situation"),
        ("/menu", "Display this help"),
        ("/advise", "Get input from all advisors"),
        ("/resources", "View UK forces and stockpiles"),
        ("/call <country>", "Contact foreign leader"),
        ("/decide", "Make your decision"),
        ("/theme", "Change UI color theme"),
        ("/llm", "Configure LLM model settings (Pro/Flash)"),
        ("/save", "Save game"),
        ("/quit", "Exit game"),
    ]
    
    for cmd, desc in commands:
        table.add_row(cmd, desc)
        
    return Panel(
        table,
        title="[magenta bold]COMMANDS[/]",
        border_style="magenta",
        box=box.ROUNDED,
        padding=(0, 2)
    )


def metrics_guide_panel() -> Panel:
    """Generate metrics explanation panel.
    
    Returns:
        Rich Panel object
    """
    if not RICH_ENABLED:
        return "Metrics guide available in /menu"
    
    COLORS = theme_manager.get_colors()
    
    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column("Metric", style=f"{COLORS['secondary']} bold", ratio=1)
    table.add_column("Description", style=COLORS['muted'], ratio=2)
    
    # Metrics
    metrics = [
        (f"{SYMBOLS['risk']} Escalation Risk", 
         "Likelihood of full-scale war.\n[bold]HIGH = Danger[/]"),
        (f"{SYMBOLS['stability']} Domestic Stability",
         "Public confidence & economy.\n[bold]LOW = Unrest[/]"),
        (f"{SYMBOLS['cohesion']} Alliance Cohesion",
         "NATO solidarity.\n[bold]LOW = Isolation[/]"),
        (f"{SYMBOLS['influence']} Influence",
         "Political capital.\nDerived from Stability + Cohesion"),
    ]
    
    for name, desc in metrics:
        table.add_row(name, desc)
        table.add_row("", "") # Spacer
        
    return Panel(
        table,
        title=f"[{COLORS['warning']} bold]METRICS GUIDE[/]",
        border_style=COLORS['warning'],
        box=box.ROUNDED,
        padding=(0, 2)
    )
