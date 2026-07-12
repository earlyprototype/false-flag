"""Interactive CLI for the wargame with two-phase turn structure.

Supports:
- Interactive mode: discussion → decision → adjudication
- Batch mode: run with pre-defined action
- Save/load game state
- Stochastic inject generation
"""

import typer
from pathlib import Path
from random import Random
from typing import Optional
import sys
import os

# CRITICAL: Import msvcrt FIRST on Windows (before Rich)
if sys.platform == "win32":
    pass

# Allow running this file directly
if __package__ is None or __package__ == "":
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# THEN import Rich (after msvcrt is loaded)
from cli.rich_ui import (
    console, phase_header, metrics_table,
    advisor_menu_panel, diplomatic_contacts_table,
    resources_tables, command_menu, metrics_guide_panel,
    format_markdown, RICH_ENABLED
)
from cli.theme import theme_manager, SYMBOLS, BOX, WIDTH
from cli.formatters import format_advisor_response
from rich.panel import Panel
from models.world import WorldState, Metrics
from models.narrative_state import create_initial_narrative_state
from models.narrative import NarrativeConfig
from engine.scenario_loader import list_available_scenarios, get_scenario_config, get_turn_filename, load_narrative_configs
from engine.sim_loop import (
    run_turn_briefing,
    run_turn_discussion,
    run_turn_decision,
    run_turn_adjudication as run_turn_adjudication_fallback,  # Renamed for fallback
    run_single_scene
)
from engine.narrative_adjudication import adjudicate_with_narrative
from engine.intro import get_intro_lines
from engine.persistence import save_game, load_game
from engine.initial_conditions import load_initial_conditions
from engine.diplomacy import run_diplomatic_encounter, list_available_diplomatic_contacts
from llm.router import generate_text
from cli.model_settings_menu import model_settings_menu

# Task 2.5: Enable Rich help panel
app = typer.Typer(
    rich_markup_mode="rich", 
    help="FALSE FLAG: THE WARGAME - LLM-driven crisis simulation",
    no_args_is_help=True
)


def scroll_text(text: str, delay: float = 0.03, allow_skip: bool = True) -> bool:
    """Print text character by character with optional skip.
    
    Args:
        text: Text to scroll
        delay: Delay between characters (seconds)
        allow_skip: If True, pressing SPACE skips to end of scene
        
    Returns:
        True if user pressed SPACE to skip, False otherwise
    """
    import msvcrt
    import sys
    
    for i, char in enumerate(text):
        # Check if user pressed SPACE to skip rest of scene
        if allow_skip and msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b' ':  # Spacebar
                # Print rest of line and return skip signal
                sys.stdout.write(text[i:])
                sys.stdout.flush()
                print()
                return True  # Signal to skip rest of scene
            # Ignore other keys, continue scrolling
        
        sys.stdout.write(char)
        sys.stdout.flush()
        
        # Slightly longer pause after punctuation
        if char in '.!?':
            import time
            time.sleep(delay * 3)
        elif char in ',;:':
            import time
            time.sleep(delay * 2)
        else:
            import time
            time.sleep(delay)
    
    print()  # Newline at end
    return False  # No skip


def wait_for_space(prompt: str = "Press SPACE to continue...") -> None:
    """Wait for user to press spacebar to continue."""
    import msvcrt  # Windows-specific
    typer.echo("")
    typer.echo(prompt)
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b' ':  # Spacebar
                typer.echo("")
                break


def strip_effect_boxes(lines: list) -> list:
    """Remove the numeric 'Effect: metric +N (-> value)' boxes from briefing lines.

    Used by immersive/emergent modes, which promise vibes instead of raw numbers.
    The boxes are three lines: a top border, the 'Effect: ...' content, and a
    bottom border.
    """
    out = []
    drop_bottom_border = False
    for line in lines:
        stripped = line.strip()
        if "Effect: " in stripped:
            # Drop the top border that preceded this content line
            if out and out[-1].strip() and set(out[-1].strip()) <= set("┌─┐"):
                out.pop()
            drop_bottom_border = True
            continue
        if drop_bottom_border:
            drop_bottom_border = False
            if stripped and set(stripped) <= set("└─┘"):
                continue
        out.append(line)
    return out


def parse_interpretation_simple(interpretation: str) -> dict:
    """Parse LLM interpretation into key sections for display.
    
    Args:
        interpretation: Full interpretation text
    
    Returns:
        Dict with parsed sections
    """
    sections = {
        "summary": "",
        "forces": [],
        "timeline": "",
        "concerns": ""
    }
    
    lines = interpretation.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        
        if line.startswith("INTERPRETATION:"):
            sections["summary"] = line.replace("INTERPRETATION:", "").strip()
        elif line.startswith("FORCES INVOLVED:"):
            current_section = "forces"
        elif line.startswith("TIMELINE:"):
            current_section = "timeline"
        elif line.startswith("FEASIBILITY:"):
            if "impossible" in line.lower() or "requires clarification" in line.lower():
                sections["concerns"] = line.replace("FEASIBILITY:", "").strip()
            current_section = None
        elif current_section == "forces" and line and line.startswith("*"):
            # Extract force name from bullet point
            force = line.lstrip("* ").split(":")[0] if ":" in line else line.lstrip("* ")
            if force and len(sections["forces"]) < 5:  # Max 5 forces shown
                sections["forces"].append(force)
        elif current_section == "timeline" and line:
            sections["timeline"] = line
    
    return sections


def display_decision_summary(action: str, interpretation: str, show_details: bool = False):
    """Display decision interpretation in player-friendly format.
    
    Args:
        action: Player's original decision text
        interpretation: Full LLM interpretation
        show_details: If True, show full interpretation
    """
    COLORS = theme_manager.get_colors()
    
    # Show player's exact words in a box
    console.print("")
    console.print(Panel(f"[italic]{action}[/italic]", title="[bold]YOUR DECISION[/bold]", border_style="white"))
    console.print("")
    
    if show_details:
        # Show full interpretation
        console.print(Panel(format_markdown(interpretation), title="[bold]FULL INTERPRETATION (DETAILED)[/bold]", border_style="blue"))
        console.print("")
    else:
        # Show simplified summary
        parsed = parse_interpretation_simple(interpretation)
        
        # Build content for panel
        content = []
        
        # Show summary if we extracted one
        if parsed["summary"]:
            content.append(parsed["summary"])
            content.append("")
        
        # Show key forces
        if parsed["forces"]:
            content.append(f"[{COLORS['success']}]Forces Deployed:[/{COLORS['success']}]")
            for force in parsed["forces"]:
                content.append(f"  • {force}")
            content.append("")
        
        # Show timeline
        if parsed["timeline"]:
            content.append(f"[{COLORS['accent']}]Estimated Timeline:[/{COLORS['accent']}] {parsed['timeline']}")
            content.append("")
        
        # Show concerns
        if parsed["concerns"]:
            content.append(f"[{COLORS['warning']}]⚠ Operational Concerns: {parsed['concerns']}[/{COLORS['warning']}]")
            content.append("")
        
        content.append(f"[{COLORS['muted']}](Type 'details' to see full interpretation)[/{COLORS['muted']}]")
        
        console.print(Panel("\n".join(content), title="[bold]📋 OPERATIONAL ORDER[/bold]", border_style="cyan"))


def display_critical_concerns_with_selection(critical_concerns: list) -> tuple:
    """Display critical concerns and let player select which to address.
    
    Args:
        critical_concerns: List of (role, concern, recommendation) tuples
    
    Returns:
        Tuple of (action_code, selected_indices)
        action_code: 'A' (all), 'S' (select), 'M' (modify), 'I' (ignore), 'D' (discussion)
        selected_indices: List of 0-based indices of selected concerns
    """
    COLORS = theme_manager.get_colors()
    
    console.print("")
    console.print(Panel(f"Advisors have raised {len(critical_concerns)} critical concerns regarding your decision.", 
                        title=f"[{COLORS['warning']} bold]⚠️ CRITICAL ADVISORIES[/]", 
                        border_style=COLORS['warning']))
    console.print("")
    
    # Display each concern with number
    for idx, (role, concern, recommendation) in enumerate(critical_concerns, 1):
        console.print(f"[{COLORS['warning']} bold][{idx}] {role}[/{COLORS['warning']} bold]")
        console.print(f"  {concern}")
        console.print(f"  [{COLORS['primary']}]→ RECOMMENDATION: \"{recommendation}\"[/{COLORS['primary']}]")
        console.print("")
        console.print(f"[{COLORS['muted']}]" + "─" * 40 + f"[/{COLORS['muted']}]")
        console.print("")
    
    # Get selection
    console.print("Which concerns would you like to address?")
    console.print("")
    console.print(f"  [{COLORS['primary']}]A[/{COLORS['primary']}] - Apply ALL recommendations to my decision")
    console.print(f"  [{COLORS['primary']}]S[/{COLORS['primary']}] - Select specific recommendations")
    console.print(f"  [{COLORS['primary']}]M[/{COLORS['primary']}] - Modify decision manually instead")
    console.print(f"  [{COLORS['primary']}]I[/{COLORS['primary']}] - Ignore all and proceed anyway")
    console.print(f"  [{COLORS['primary']}]D[/{COLORS['primary']}] - Return to discussion phase")
    console.print("")
    
    choice = typer.prompt("Choose", type=str).strip().upper()
    
    if choice == "A":
        return ('A', list(range(len(critical_concerns))))
    elif choice == "S":
        console.print("")
        console.print("Enter concern numbers separated by spaces (e.g., '1 3')")
        selection = typer.prompt("Select").strip()
        try:
            indices = [int(x) - 1 for x in selection.split()]
            valid_indices = [i for i in indices if 0 <= i < len(critical_concerns)]
            return ('S', valid_indices)
        except ValueError:
            console.print(f"[{COLORS['danger']}]Invalid selection.[/{COLORS['danger']}]")
            return ('M', [])
    elif choice == "M":
        return ('M', [])
    elif choice == "I":
        return ('I', [])
    elif choice == "D":
        return ('D', [])
    else:
        console.print(f"[{COLORS['warning']}]Invalid choice. Please try again.[/{COLORS['warning']}]")
        return display_critical_concerns_with_selection(critical_concerns)


def append_recommendations_to_decision(original_decision: str, critical_concerns: list, selected_indices: list) -> str:
    """Append selected recommendations to original decision.
    
    Args:
        original_decision: Player's original decision text
        critical_concerns: Full list of concerns
        selected_indices: Indices of concerns to address
    
    Returns:
        Enhanced decision text
    """
    if not selected_indices:
        return original_decision
    
    additions = []
    for idx in selected_indices:
        role, concern, recommendation = critical_concerns[idx]
        additions.append(f"- {recommendation}")
    
    enhanced = original_decision
    enhanced += "\n\nAdditionally:"
    enhanced += "\n" + "\n".join(additions)
    
    return enhanced


def select_scenario_variant(scenario_id: str) -> str:
    """Display interactive scenario selection menu.
    
    Args:
        scenario_id: Base scenario identifier
    
    Returns:
        Selected variant key (e.g., 'standard', 'fast_start')
    """
    COLORS = theme_manager.get_colors()
    
    typer.clear()
    console.print("")
    console.print(f"[{COLORS['danger']} bold]# FALSE FLAG: THE WARGAME[/{COLORS['danger']} bold]")
    console.print("=" * 79)
    console.print("")
    console.print(f"[{COLORS['primary']} bold]SELECT SCENARIO[/{COLORS['primary']} bold]")
    console.print("")
    
    # Load available scenarios
    scenarios = list_available_scenarios(scenario_id)
    
    if len(scenarios) == 0:
        # No scenarios.yaml found - use default
        return "standard"
    
    # Display scenario options
    for idx, (key, config) in enumerate(scenarios, 1):
        name = config.get("name", key.title())
        description = config.get("description", "")
        difficulty = config.get("difficulty", "")
        estimated_time = config.get("estimated_time", "")
        recommended = config.get("recommended_for", "")
        
        console.print(f"[{COLORS['warning']} bold]{idx}. {name}[/{COLORS['warning']} bold]")
        if difficulty:
            console.print(f"   Difficulty: {difficulty}")
        if estimated_time:
            console.print(f"   Estimated Time: {estimated_time}")
        console.print(f"   {description}")
        
        # Show key features
        features = config.get("features", [])
        if features:
            console.print("")
            for feature in features[:3]:  # Show first 3 features
                console.print(f"   - {feature}")
        
        if recommended:
            console.print("")
            console.print(f"   Recommended for: {recommended}")
        
        console.print("")
    
    # Get user selection
    console.print("")
    while True:
        try:
            choice = typer.prompt("Select scenario (enter number)", type=int)
            if 1 <= choice <= len(scenarios):
                selected_key = scenarios[choice - 1][0]
                selected_name = scenarios[choice - 1][1].get("name", selected_key)
                
                console.print("")
                console.print(f"[{COLORS['success']} bold]✓ Selected: {selected_name}[/{COLORS['success']} bold]")
                console.print("")
                
                return selected_key
            else:
                console.print(f"[{COLORS['danger']}]Please enter a number between 1 and {len(scenarios)}[/{COLORS['danger']}]")
        except (ValueError, KeyboardInterrupt):
            console.print(f"[{COLORS['danger']}]Invalid input. Please enter a number.[/{COLORS['danger']}]")


def select_play_mode() -> str:
    """Display interactive gameplay mode selection menu.
    
    Returns:
        Selected mode key (e.g., 'classic', 'immersive', 'emergent')
    """
    COLORS = theme_manager.get_colors()
    
    typer.clear()
    console.print("")
    console.print(f"[{COLORS['danger']} bold]# FALSE FLAG: THE WARGAME[/{COLORS['danger']} bold]")
    console.print("=" * 79)
    console.print("")
    console.print(f"[{COLORS['primary']} bold]SELECT GAMEPLAY MODE[/{COLORS['primary']} bold]")
    console.print("")
    
    modes = [
        ("classic", {
            "name": "Classic Wargame",
            "description": "Traditional experience with visible metrics and mechanical effects",
            "features": [
                "See numerical impact of your decisions",
                "Clear thresholds and win conditions",
                "Strategic resource management focus"
            ],
            "recommended": "Traditional wargame players, first playthrough"
        }),
        ("immersive", {
            "name": "Immersive Narrative",
            "description": "Character-driven drama with hidden metrics guiding the story",
            "features": [
                "Visual 'vibes' instead of raw numbers",
                "Character attitudes and relationships",
                "Narrative consequences take center stage"
            ],
            "recommended": "Story-focused players, replay value"
        }),
        ("emergent", {
            "name": "Emergent Drama (Experimental)",
            "description": "Maximum LLM freedom with minimal structure",
            "features": [
                "Pure narrative immersion",
                "Every playthrough unique",
                "Unpredictable emergent outcomes"
            ],
            "recommended": "Experimental players, maximum replayability"
        })
    ]
    
    for idx, (key, config) in enumerate(modes, 1):
        console.print(f"[{COLORS['warning']} bold]{idx}. {config['name']}[/{COLORS['warning']} bold]")
        console.print(f"   {config['description']}")
        console.print("")
        for feature in config['features']:
            console.print(f"   - {feature}")
        console.print("")
        console.print(f"   Recommended for: {config['recommended']}")
        console.print("")
    
    while True:
        try:
            choice = typer.prompt("Select gameplay mode (enter number)", type=int, default=2)
            if 1 <= choice <= len(modes):
                selected_key = modes[choice - 1][0]
                selected_name = modes[choice - 1][1]['name']
                
                console.print("")
                console.print(f"[{COLORS['success']} bold]✓ Selected: {selected_name}[/{COLORS['success']} bold]")
                console.print("")
                
                return selected_key
            else:
                console.print(f"[{COLORS['danger']}]Please enter a number between 1 and {len(modes)}[/{COLORS['danger']}]")
        except (ValueError, KeyboardInterrupt):
            console.print(f"[{COLORS['danger']}]Invalid input. Please enter a number.[/{COLORS['danger']}]")


def select_difficulty(scenario_id: str) -> str:
    """Display interactive difficulty selection menu.
    
    Args:
        scenario_id: Base scenario identifier
    
    Returns:
        Selected difficulty key (e.g., 'standard', 'challenging', 'brutal')
    """
    COLORS = theme_manager.get_colors()
    
    typer.clear()
    console.print("")
    console.print(f"[{COLORS['danger']} bold]# FALSE FLAG: THE WARGAME[/{COLORS['danger']} bold]")
    console.print("=" * 79)
    console.print("")
    console.print(f"[{COLORS['primary']} bold]SELECT DIFFICULTY[/{COLORS['primary']} bold]")
    console.print("")
    console.print("Difficulty affects scenario effect magnitudes (crisis intensity).")
    console.print("Player action impacts remain the same across all difficulties.")
    console.print("")
    
    # Load difficulty definitions from scenarios.yaml
    root = Path(__file__).resolve().parents[1]
    scenario_path = root / "data" / "scenarios" / scenario_id / "scenarios.yaml"
    
    difficulties = []
    if scenario_path.exists():
        try:
            import yaml
            with open(scenario_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                difficulties_dict = data.get("difficulties", {})
                # Convert to list of tuples for consistent ordering
                difficulties = [
                    ("standard", difficulties_dict.get("standard", {})),
                    ("challenging", difficulties_dict.get("challenging", {})),
                    ("brutal", difficulties_dict.get("brutal", {}))
                ]
        except Exception:
            pass
    
    # Default if no difficulties found
    if not difficulties:
        difficulties = [
            ("standard", {"name": "Standard", "description": "Balanced challenge", "multiplier": 0.65}),
            ("challenging", {"name": "Challenging", "description": "Tight margins", "multiplier": 0.85}),
            ("brutal", {"name": "Brutal", "description": "Maximum intensity", "multiplier": 1.0})
        ]
    
    # Display difficulty options
    for idx, (key, config) in enumerate(difficulties, 1):
        name = config.get("name", key.title())
        description = config.get("description", "")
        multiplier = config.get("multiplier", 1.0)
        recommended = config.get("recommended_for", "")
        
        console.print(f"[{COLORS['warning']} bold]{idx}. {name}[/{COLORS['warning']} bold]")
        console.print(f"   Effect Multiplier: {multiplier}x")
        console.print(f"   {description}")
        
        if recommended:
            console.print(f"   Recommended for: {recommended}")
        
        console.print("")
    
    # Get user selection
    while True:
        try:
            choice = typer.prompt("Select difficulty (enter number)", type=int, default=1)
            if 1 <= choice <= len(difficulties):
                selected_key = difficulties[choice - 1][0]
                selected_name = difficulties[choice - 1][1].get("name", selected_key)
                
                console.print("")
                console.print(f"[{COLORS['success']} bold]✓ Selected: {selected_name}[/{COLORS['success']} bold]")
                console.print("")
                
                return selected_key
            else:
                console.print(f"[{COLORS['danger']}]Please enter a number between 1 and {len(difficulties)}[/{COLORS['danger']}]")
        except (ValueError, KeyboardInterrupt):
            console.print(f"[{COLORS['danger']}]Invalid input. Please enter a number.[/{COLORS['danger']}]")


def select_narrative(scenario_id: str) -> Optional[NarrativeConfig]:
    """Display game type selection menu (Original Story Mode vs Mystery Mode).
    
    Args:
        scenario_id: Base scenario identifier
    
    Returns:
        None if Original Story Mode selected,
        NarrativeConfig (randomly chosen) if Mystery Mode selected
    """
    COLORS = theme_manager.get_colors()
    
    typer.clear()
    console.print("")
    console.print(f"[{COLORS['danger']} bold]# FALSE FLAG: THE WARGAME[/{COLORS['danger']} bold]")
    console.print("=" * 79)
    console.print("")
    console.print(f"[{COLORS['primary']} bold]SELECT GAME TYPE[/{COLORS['primary']} bold]")
    console.print("")
    console.print("Choose how you want to experience the crisis:")
    console.print("")
    
    # Display option 1: Original Story Mode
    console.print(f"[{COLORS['warning']} bold]1. Original Story Mode[/{COLORS['warning']} bold]")
    console.print("   Play the standard story mode as designed. Experience the crisis through")
    console.print("   the eyes of the Prime Minister as events unfold.")
    console.print("")
    
    # Display option 2: Mystery Mode
    console.print(f"[{COLORS['warning']} bold]2. Mystery Mode[/{COLORS['warning']} bold]")
    console.print("   A hidden narrative guides AI agent behaviour. Foreign leaders and")
    console.print("   diplomats may have secret motivations that aren't immediately apparent.")
    console.print("   You must deduce the truth from their actions and responses.")
    console.print("")
    console.print(f"   [{COLORS['danger']}]⚠ The narrative is randomly selected and hidden from you![/{COLORS['danger']}]")
    console.print("")
    
    # Get user selection
    while True:
        try:
            choice = typer.prompt("Select game type (enter number)", type=int, default=1)
            if choice == 1:
                # Original Story Mode - no secret narrative
                console.print("")
                console.print(f"[{COLORS['success']} bold]✓ Original Story Mode selected[/{COLORS['success']} bold]")
                console.print("")
                return None
            elif choice == 2:
                # Mystery Mode - randomly select narrative
                narratives = load_narrative_configs(scenario_id)
                
                if narratives:
                    import random
                    selected_narrative = random.choice(narratives)
                    console.print("")
                    console.print(f"[{COLORS['success']} bold]✓ Mystery Mode activated[/{COLORS['success']} bold]")
                    console.print("")
                    # DO NOT tell player which narrative was selected
                    return selected_narrative
                else:
                    # Fallback if no narratives available - treat as Original Mode
                    console.print("")
                    console.print(f"[{COLORS['warning']}]Mystery Mode unavailable - using Original Story Mode[/{COLORS['warning']}]")
                    console.print("")
                    return None
            else:
                console.print(f"[{COLORS['danger']}]Please enter 1 or 2[/{COLORS['danger']}]")
        except (ValueError, KeyboardInterrupt):
            console.print(f"[{COLORS['danger']}]Invalid input. Please enter a number.[/{COLORS['danger']}]")


@app.command(rich_help_panel="GAMEPLAY")
def play(
    scenario: str = typer.Option("war_game_2025", help="Scenario identifier"),
    seed: int = typer.Option(42, help="Random seed for determinism"),
    load_save: str = typer.Option(None, "--load", help="Load game from save file"),
    stochastic_injects: bool = typer.Option(True, "--stochastic-injects/--no-stochastic-injects", help="Generate injects dynamically (enabled by default)"),
    intro_only: bool = typer.Option(False, "--intro-only", help="Display intro and exit"),
    variant: str = typer.Option(None, "--variant", help="Scenario variant (e.g., 'standard', 'fast_start')"),
    difficulty: str = typer.Option(None, "--difficulty", help="Difficulty level (e.g., 'standard', 'challenging', 'brutal')"),
    play_mode: str = typer.Option(None, "--play-mode", help="Gameplay mode (e.g., 'classic', 'immersive', 'emergent')"),
    flash_only: bool = typer.Option(False, "--flash-only", help="Use Flash model for all LLM calls (5x faster, cheaper)"),
):
    """Play the wargame interactively."""
    
    # Get current colors for loop
    COLORS = theme_manager.get_colors()

    # Configure LLM model if flash_only flag is set
    if flash_only:
        from llm.model_config import get_model_config
        config = get_model_config()
        config.use_flash_for_all()
        typer.echo("")
        typer.echo("[Flash-only mode enabled - using gemini-2.5-flash for all calls]")
        typer.echo("")
    
    # If no variant specified and not loading a save, show selection menu
    if variant is None and load_save is None:
        variant = select_scenario_variant(scenario)
    elif variant is None:
        variant = "standard"  # Default for loaded games
    
    # If no play mode specified and not loading a save, show selection menu
    if play_mode is None and load_save is None:
        play_mode = select_play_mode()
    elif play_mode is None:
        play_mode = "immersive"  # Default for loaded games
    
    # If no difficulty specified and not loading a save, show selection menu
    if difficulty is None and load_save is None:
        difficulty = select_difficulty(scenario)
    elif difficulty is None:
        difficulty = "standard"  # Default for loaded games
    
    # Select game type (Original or Mystery mode) - only for new games
    selected_narrative = None
    if load_save is None:
        selected_narrative = select_narrative(scenario)  # Returns None for Original, NarrativeConfig for Mystery
    
    # Display intro with pauses
    if intro_only or load_save is None:
        intro_lines = get_intro_lines(200)
        
        # Split intro into sections (scenes)
        # Scene markers are lines with "## SCENE"
        current_section = []
        sections = []
        
        for line in intro_lines:
            if "===" in line and current_section:
                # Start of new scene - save previous and start new
                sections.append(current_section)
                current_section = [line]
            else:
                current_section.append(line)
        
        # Only add final section if it has content beyond just a separator
        if current_section and len([l for l in current_section if l.strip() and "===" not in l]) > 0:
            sections.append(current_section)
        
        # Display each scene
        for i, scene in enumerate(sections):
            # Clear screen at start of EVERY scene (including title)
            typer.clear()
            
            skip_rest = False
            prev_line_blank = False
            for line in scene:
                if skip_rest:
                    # User pressed SPACE - print remaining lines instantly
                    # Check if line has Rich markup
                    if "[/" in line and "[" in line:
                        console.print(line)
                    else:
                        typer.echo(line)
                    continue
                    
                if "===" in line:
                    # Structural element - print instantly
                    typer.echo(line)
                    prev_line_blank = False
                elif line.strip() == "":
                    # Blank line
                    if not prev_line_blank:
                        typer.echo("")
                    prev_line_blank = True
                elif line.strip().startswith("# "):
                    # Title - print instantly
                    typer.echo(line)
                    prev_line_blank = False
                elif line.strip().startswith("## YOUR ROLE"):
                    # Section header - print instantly
                    typer.echo(line)
                    prev_line_blank = False
                else:
                    # All other text (narrative)
                    # Check if line contains Rich markup
                    if "[/" in line and "[" in line:
                        # Has Rich markup - use console.print with brief pause
                        import time
                        console.print(line)
                        time.sleep(0.3)  # Brief pause for readability
                        prev_line_blank = False
                    else:
                        # Plain text - stream it
                        skipped = scroll_text(line, delay=0.02)
                        if skipped:
                            skip_rest = True  # Skip rest of scene
                        prev_line_blank = False
            
            # Pause after each scene
            typer.echo("")
            wait_for_space("Press SPACE to continue...")
        
        typer.echo("")
    
    if intro_only:
        return
    
    rng = Random(seed)
    root = Path(__file__).resolve().parents[1]  # cli/main.py -> project root
    
    # For NEW games, load and display Turn 1 briefing as part of intro sequence
    # This makes the COBRA briefing flow seamlessly from the YOUR ROLE section
    first_briefing_as_intro = (load_save is None)
    
    # Load or create world state
    if load_save:
        save_path = Path(load_save)
        try:
            scenario, world, transcript, loaded_play_mode, loaded_narrative_state = load_game(save_path)
            # Use loaded play_mode if available, otherwise use command-line arg
            if loaded_play_mode:
                play_mode = loaded_play_mode
            typer.echo(f"Loaded game from {save_path}")
            typer.echo(f"Resuming at Turn {world.turn}")
            typer.echo("")
            
            # Use loaded narrative state if available, otherwise create new
            if loaded_narrative_state:
                narrative_state = loaded_narrative_state
            else:
                # Create narrative state from loaded world (legacy saves)
                narrative_state = create_initial_narrative_state(
                    metrics=world.metrics.copy(),
                    play_mode=play_mode,
                    game_time=f"Turn {world.turn}"
                )
                narrative_state.turn = world.turn
            
        except (FileNotFoundError, ValueError) as e:
            typer.echo(f"Error loading save: {e}", err=True)
            raise typer.Exit(1)
    else:
        # New game
        initial_conditions = load_initial_conditions(scenario, root)
        initial_metrics = initial_conditions.get("initial_metrics", {})
        
        world = WorldState(
            turn=1,
            scene=1,
            difficulty=difficulty,
            narrative=selected_narrative,  # Set the secret narrative truth
            metrics=Metrics(
                escalation_risk=initial_metrics.get("escalation_risk", 60),
                domestic_stability=initial_metrics.get("domestic_stability", 50),
                alliance_cohesion=initial_metrics.get("alliance_cohesion", 40),
                casualties_mil=initial_metrics.get("casualties_mil", 2),
                casualties_civ=initial_metrics.get("casualties_civ", 0),
            ),
            flags={},
            posture={},
        )
        
        # Initialize state actor system for multi-agent simulation
        try:
            from models.state_actors import load_actors_from_yaml
            actor_yaml_path = root / "data" / "state_actors.yaml"
            world.actor_system = load_actors_from_yaml(str(actor_yaml_path))
            console.print(f"[{COLORS['success']}]✓ Multi-agent actor system initialized[/{COLORS['success']}]")
        except Exception as e:
            console.print(f"[{COLORS['warning']}]Warning: Could not load actor system: {e}[/{COLORS['warning']}]")
            world.actor_system = None
        
        # Initialize narrative state system
        narrative_state = create_initial_narrative_state(
            metrics=world.metrics.copy(),
            play_mode=play_mode,
            game_time=initial_conditions.get("metadata", {}).get("start_time", "Sunday 5th October 2025, 17:00")
        )
        
        transcript = []
    
    # Load scenario configuration for variant-specific turn files
    scenario_config = get_scenario_config(scenario, variant, root)
    stochastic_from_turn = scenario_config.get("stochastic_from", 7)
    
    # Main game loop
    while True:
        # Refresh colors at start of loop in case theme changed
        COLORS = theme_manager.get_colors()
        
        # Capture metrics at START of turn (before inject effects)
        from copy import deepcopy
        turn_start_metrics = deepcopy(world.metrics)
        
        # Auto-enable stochastic generation when reaching the transition point
        if world.turn >= stochastic_from_turn:
            if not stochastic_injects:
                # First time reaching stochastic content - show transition message
                stochastic_injects = True
                console.print("")
                console.print(f"[{COLORS['primary']}]" + "=" * 79 + f"[/{COLORS['primary']}]")
                console.print(f"[{COLORS['primary']} bold]ENTERING DYNAMIC SCENARIO GENERATION[/{COLORS['primary']} bold]")
                console.print(f"[{COLORS['primary']}]" + "=" * 79 + f"[/{COLORS['primary']}]")
                console.print("")
                console.print("The scripted scenario has concluded. From this point forward,")
                console.print("events will be dynamically generated based on your decisions.")
                console.print("")
                wait_for_space("Press SPACE to continue...")
                console.print("")
        
        # Determine if we should use stochastic generation for this turn
        use_stochastic = stochastic_injects and world.turn >= stochastic_from_turn
        
        # Get turn filename based on scenario variant
        turn_filename = get_turn_filename(world.turn, scenario_config)
        
        # Briefing phase (with player input function for diplomatic encounters)
        # For Turn 1 of new games: suppress panel display and effect boxes (will be streamed in intro flow)
        is_turn1_intro = (first_briefing_as_intro and world.turn == 1)
        inject, briefing_lines = run_turn_briefing(
            world,
            scenario,
            use_stochastic,
            rng,
            root,
            transcript,
            get_player_input=lambda prompt: typer.prompt(prompt).strip(),
            turn_filename=turn_filename,
            silent_effects=is_turn1_intro or play_mode != "classic",  # Hide raw-number effect boxes for Turn 1 intro and non-classic modes
            suppress_display=is_turn1_intro  # Suppress panel so we can stream the text
        )

        # Sync inject effects into the narrative state. Adjudication mutates
        # narrative_state.hidden_metrics and the result is copied back over
        # world.metrics at end of turn, so any briefing effect left only on
        # world.metrics would be silently reverted. This also snapshots
        # previous_metrics, giving the immersive-mode vibes a real trend baseline.
        narrative_state.update_hidden_metrics({
            "escalation_risk": world.metrics.escalation_risk,
            "domestic_stability": world.metrics.domestic_stability,
            "alliance_cohesion": world.metrics.alliance_cohesion,
            "casualties_mil": world.metrics.casualties_mil,
            "casualties_civ": world.metrics.casualties_civ,
        })
        
        # Non-classic modes hide raw metric numbers: strip the effect boxes from
        # the on-screen briefing. They stay in `briefing_lines`/the transcript,
        # which feeds saves and LLM context.
        if play_mode != "classic":
            briefing_display = strip_effect_boxes(briefing_lines)
        else:
            briefing_display = briefing_lines

        # Clear screen and display briefing at top
        # BUT: if this is Turn 1 of a new game, don't clear (flows from intro)
        if not (first_briefing_as_intro and world.turn == 1):
            typer.clear()
        else:
            # First briefing of new game - add separator but don't clear
            typer.echo("")
            typer.echo("=" * 79)
            typer.echo("")

        # Split briefing into scene-setting and actual briefing
        # Look for "The National Security Advisor" or similar transition line
        # BUT: for Turn 1 of new games, don't split - show everything in one flow
        scene_setting_end = -1
        if not (first_briefing_as_intro and world.turn == 1):
            for i, line in enumerate(briefing_display):
                if "National Security Advisor" in line and ("clears" in line or "begins" in line):
                    scene_setting_end = i
                    break

        # Display scene-setting part with streaming
        skip_rest = False
        for i, line in enumerate(briefing_display):
            # Stop at the transition line
            if scene_setting_end > 0 and i >= scene_setting_end:
                break
                
            if skip_rest:
                # User pressed SPACE - print rest instantly
                # Check if line has Rich markup
                if "[/" in line and "[" in line:
                    console.print(line)
                else:
                    typer.echo(line)
                continue
            
            # Scroll the turn number header
            if i == 1 and line.strip().startswith("TURN"):
                skipped = scroll_text(line, delay=0.05)
                if skipped:
                    skip_rest = True
            # Stream narrative text (not structural elements)
            elif line.strip() and not line.strip().startswith("==="):
                # Check if line contains Rich markup
                if "[/" in line and "[" in line:
                    # Has Rich markup - use console.print with brief pause
                    import time
                    console.print(line)
                    time.sleep(0.3)
                else:
                    # Plain text - stream it
                    skipped = scroll_text(line, delay=0.02)
                    if skipped:
                        skip_rest = True
            else:
                typer.echo(line)
        
        # Pause after scene-setting (only if we found a split point)
        if scene_setting_end > 0:
            typer.echo("")
            wait_for_space("Press SPACE to continue...")
            
            # Display rest of briefing (the actual intelligence report)
            typer.echo("")
            for i in range(scene_setting_end, len(briefing_display)):
                typer.echo(briefing_display[i])
        
        transcript.extend(briefing_lines)
        
        # Show intelligence briefing (Immersive/Emergent modes only)
        if play_mode in ["immersive", "emergent"] and world.turn > 1:
            from engine.intelligence import generate_intelligence_briefing
            intel_lines = generate_intelligence_briefing(narrative_state, world, rng, detailed=True)
            typer.echo("")
            for line in intel_lines:
                console.print(line)
            typer.echo("")
        
        # Pause before discussion phase
        typer.echo("")
        wait_for_space("Press SPACE to begin discussion phase...")
        
        # After Turn 1 intro briefing is shown, reset the flag
        if first_briefing_as_intro and world.turn == 1:
            first_briefing_as_intro = False
        
        # Clear screen and show discussion phase at top
        typer.clear()
        typer.echo("")  # Buffer line BEFORE Rich output
        
        if RICH_ENABLED:
            console.print(phase_header("DISCUSSION", world.turn))
            typer.echo("")
            typer.echo("  Ask questions or type /decide when ready")
            console.print(f"  [{COLORS['muted']}]Quick: /status  /menu  /advise  /resources  /llm[/{COLORS['muted']}]")
            typer.echo("")
            console.print(f"[{COLORS['muted']}]" + "─" * 79 + f"[/{COLORS['muted']}]")
        else:
            console.print("=" * 79)
            console.print(f"[{COLORS['accent']} bold]TURN {world.turn}: DISCUSSION PHASE[/{COLORS['accent']} bold]")
            console.print("=" * 79)
            console.print("")
            console.print("Ask advisors questions, or type '/decide' when ready.")
            console.print("Type '/menu' for commands, '/advise' for all advisors, '/resources' for forces.")
        
        typer.echo("")
        
        # Discussion phase loop
        questions = []
        while True:
            user_input = typer.prompt(">").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ["/decide", "decide", "decision"]:
                break
            
            if user_input.lower() in ["/quit", "quit"]:
                typer.echo("Exiting game.")
                raise typer.Exit(0)
            
            if user_input.lower() in ["/save", "save"]:
                save_path = save_game(world, transcript, scenario, f"turn_{world.turn:03d}", root, play_mode, narrative_state)
                typer.echo(f"Game saved to {save_path}")
                continue
            
            if user_input.lower() in ["/theme", "theme"]:
                typer.echo("")
                console.print("Available themes:")
                console.print("  1. Standard (Cyan/Blue)")
                console.print("  2. DEFCON 1 (Red/Alert)")
                console.print("  3. Retro (Green Phosphor)")
                console.print("  4. Slate (Black/White Monochrome)")
                typer.echo("")
                
                theme_choice = typer.prompt("Select theme (1-4)").strip()
                theme_map = {"1": "standard", "2": "defcon1", "3": "retro", "4": "slate"}
                
                if theme_choice in theme_map:
                    theme_name = theme_map[theme_choice]
                    theme_manager.set_theme(theme_name)
                    COLORS = theme_manager.get_colors()
                    console.print(f"[{COLORS['success']}]Theme changed to {theme_name.title()}[/{COLORS['success']}]")
                    # Refresh current view
                    typer.clear()
                    if RICH_ENABLED:
                        console.print(phase_header("DISCUSSION", world.turn))
                        typer.echo("")
                        typer.echo("  Ask questions or type /decide when ready")
                        console.print(f"  [{COLORS['muted']}]Quick: /status  /menu  /advise  /resources  /llm[/{COLORS['muted']}]")
                        typer.echo("")
                        console.print(f"[{COLORS['muted']}]" + "─" * 79 + f"[/{COLORS['muted']}]")
                else:
                    console.print("[bold red]Invalid selection[/bold red]")
                continue

            if user_input.lower() in ["/status", "status"]:
                typer.echo("")
                
                if RICH_ENABLED:
                    # Display based on play mode
                    if play_mode == "classic":
                        # Show metrics table (includes turn, phase, influence)
                        console.print(metrics_table(world))
                    elif play_mode == "immersive":
                        # Show vibes
                        typer.echo("═" * 60)
                        typer.echo("SITUATION ASSESSMENT")
                        typer.echo("═" * 60)
                        typer.echo("")
                        vibes = narrative_state.get_situation_vibes()
                        for vibe in vibes:
                            typer.echo(vibe.to_string())
                        typer.echo("")
                        
                        # Show character attitudes
                        typer.echo("═" * 60)
                        typer.echo("ADVISOR ATTITUDES")
                        typer.echo("═" * 60)
                        typer.echo("")
                        for char_id, char_attitude in narrative_state.characters.items():
                            trust_level = char_attitude.trust // 20
                            trust_bar = "█" * trust_level + "░" * (5 - trust_level)
                            relationship_symbol = {
                                "allied": "✓",
                                "neutral": "○",
                                "hostile": "✗",
                                "unknown": "?"
                            }.get(char_attitude.relationship, "○")
                            typer.echo(f"{char_attitude.name:<30} {trust_bar} {relationship_symbol} {char_attitude.relationship.upper()}")
                    elif play_mode == "emergent":
                        # Show narrative summary
                        typer.echo("═" * 60)
                        typer.echo(narrative_state.situation_summary)
                        typer.echo("═" * 60)
                    
                    # Show active flags if any
                    if world.flags:
                        typer.echo("")
                        console.print(f"[{COLORS['warning']} bold]ACTIVE RISK FLAGS:[/{COLORS['warning']} bold]")
                        for flag, value in world.flags.items():
                            if value:
                                console.print(f"  [{COLORS['warning']}]{SYMBOLS['warning']} {flag.replace('_', ' ').title()}[/{COLORS['warning']}]")
                else:
                    # Fallback to plain text
                    typer.echo("=" * 60)
                    typer.echo("CURRENT SITUATION")
                    typer.echo("=" * 60)
                    typer.echo("")
                    typer.echo(f"Turn: {world.turn}")
                    typer.echo(f"Phase: {world.phase}")
                    typer.echo("")
                    typer.echo("Metrics:")
                    typer.echo(f"  Escalation Risk:      {world.metrics.escalation_risk}/100")
                    typer.echo(f"  Domestic Stability:   {world.metrics.domestic_stability}/100")
                    typer.echo(f"  Alliance Cohesion:    {world.metrics.alliance_cohesion}/100")
                    typer.echo(f"  Military Casualties:  {world.metrics.casualties_mil}")
                    typer.echo(f"  Civilian Casualties:  {world.metrics.casualties_civ}")
                    typer.echo("")
                    
                    # Calculate influence
                    influence_raw = (world.metrics.domestic_stability + world.metrics.alliance_cohesion) / 2.0
                    influence = int((influence_raw - 50) / 5)
                    influence = max(-10, min(10, influence))
                    influence_sign = "+" if influence >= 0 else ""
                    typer.echo(f"Public Sentiment (Influence): {influence_sign}{influence}/10")
                    typer.echo("")
                    
                    if world.flags:
                        typer.echo("Active Risk Flags:")
                        for flag, value in world.flags.items():
                            if value:
                                typer.echo(f"  ! {flag.replace('_', ' ').title()}")
                        typer.echo("")
                
                typer.echo("")
                continue
            
            if user_input.lower().startswith("/call "):
                # Handle diplomatic call
                country_input = user_input[6:].strip().upper()
                
                # Map common names to country codes
                country_map = {
                    "US": "US", "USA": "US", "AMERICA": "US", "UNITED STATES": "US",
                    "FRANCE": "France", "FRENCH": "France",
                    "GERMANY": "Germany", "GERMAN": "Germany",
                    "POLAND": "Poland", "POLISH": "Poland",
                    "RUSSIA": "Russia", "RUSSIAN": "Russia",
                    "UKRAINE": "Ukraine", "UKRAINIAN": "Ukraine",
                    "IRELAND": "Ireland", "IRISH": "Ireland"
                }
                
                country = country_map.get(country_input, country_input.capitalize())
                
                console.print("")
                console.print(f"[{COLORS['success']} bold]Connecting to {country}...[/{COLORS['success']} bold]")
                
                # Run diplomatic encounter (with real-time printing)
                encounter_transcript, cohesion_delta = run_diplomatic_encounter(
                    world,
                    country,
                    required=False,
                    context=None,
                    llm_generate=generate_text,
                    rng=rng,
                    root_path=root,
                    full_transcript=transcript,
                    get_player_input=lambda prompt: typer.prompt(prompt).strip(),
                    print_fn=typer.echo  # Print in real-time
                )
                
                # Transcript already printed, just save it
                transcript.extend(encounter_transcript)
                
                # Apply alliance cohesion change
                from engine.utils import clamp, clamp_metrics
                from engine.flags import update_world_flags
                
                world.metrics.alliance_cohesion = clamp(world.metrics.alliance_cohesion + cohesion_delta)
                clamp_metrics(world.metrics)
                update_world_flags(world)
                
                continue
            
            if user_input.lower() in ["/advise", "advise"]:
                # Get advice from all advisors
                typer.echo("")
                
                if RICH_ENABLED:
                    # Top border
                    box = BOX["round"]
                    title = " COBRA ADVISORY PANEL "
                    title_len = len(title)
                    left_pad = (WIDTH - title_len - 2) // 2
                    right_pad = WIDTH - title_len - left_pad - 2
                    console.print(f"[{COLORS['accent']} bold]{box['tl']}{box['h'] * left_pad}{title}{box['h'] * right_pad}{box['tr']}[/{COLORS['accent']} bold]")
                    typer.echo("")
                else:
                    typer.echo("=" * 79)
                    typer.echo("COBRA ADVISORY PANEL")
                    typer.echo("=" * 79)
                    typer.echo("")
                
                typer.echo("Requesting input from all advisors on the current situation...")
                typer.echo("")
                
                # Ask each advisor for their assessment
                # Add conciseness instruction to keep responses brief
                advisors = [
                    ("National Security Advisor", "NSA, what's your assessment of the current situation and recommended course of action? [Please be concise - 3-4 sentences maximum]"),
                    ("Chief of the Defence Staff", "CDS, what are our military options and constraints? [Please be concise - 3-4 sentences maximum]"),
                    ("Foreign Secretary", "Foreign Secretary, what's the diplomatic landscape and alliance status? [Please be concise - 3-4 sentences maximum]"),
                    ("Home Secretary", "Home Secretary, what are the domestic security concerns? [Please be concise - 3-4 sentences maximum]"),
                    ("Attorney General", "Attorney General, what are the legal constraints and considerations? [Please be concise - 3-4 sentences maximum]")
                ]
                
                for advisor_name, question in advisors:
                    # Separator between advisors
                    if RICH_ENABLED:
                        console.print(f"[{COLORS['muted']}]" + "─" * 79 + f"[/{COLORS['muted']}]")
                    else:
                        typer.echo("─" * 79)
                    
                    console.print(f"  [{COLORS['secondary']} bold]{advisor_name.upper()}[/{COLORS['secondary']} bold]")
                    typer.echo("")
                    
                    # Get response from this advisor
                    discussion_lines = run_turn_discussion(world, scenario, [question], rng, root, transcript)
                    for line in discussion_lines:
                        # Skip the "Prime Minister:" echo and strip the conciseness instruction
                        if not line.startswith("Prime Minister:"):
                            # Remove the [Please be concise...] instruction from display
                            display_line = line.replace("[Please be concise - 3-4 sentences maximum]", "").strip()
                            if display_line:  # Only display non-empty lines
                                # Format response with structure
                                if ":" in display_line:
                                    advisor_role, rest = display_line.split(":", 1)
                                    if RICH_ENABLED:
                                        formatted = format_advisor_response("", rest)
                                        console.print(formatted)
                                    else:
                                        console.print(f"[{COLORS['secondary']} bold]{advisor_role}:[/{COLORS['secondary']} bold]", end="")
                                        console.print(rest)
                                else:
                                    typer.echo(display_line)
                        else:
                            # For transcript, clean up the question
                            clean_line = line.replace("[Please be concise - 3-4 sentences maximum]", "").strip()
                            transcript.append(clean_line)
                            continue
                    # Only add non-question lines to transcript (questions already added above)
                    transcript.extend([l for l in discussion_lines if not l.startswith("Prime Minister:")])
                    typer.echo("")
                
                if RICH_ENABLED:
                    # Bottom border
                    console.print(f"[{COLORS['accent']} bold]{box['bl']}{box['h'] * (WIDTH - 2)}{box['br']}[/{COLORS['accent']} bold]")
                else:
                    typer.echo("=" * 79)
                
                typer.echo("")
                continue
            
            if user_input.lower() in ["/resources", "resources"]:
                # Display UK forces and stockpiles
                initial_conditions = load_initial_conditions(scenario, root)
                
                typer.echo("")
                
                if RICH_ENABLED:
                    forces_table, stockpiles_table = resources_tables(initial_conditions)
                    console.print(forces_table)
                    typer.echo("")
                    console.print(stockpiles_table)
                    typer.echo("")
                    continue
                
                # Fallback to plain text
                typer.echo("=" * 79)
                typer.echo("UK MILITARY RESOURCES")
                typer.echo("=" * 79)
                typer.echo("")
                
                # Display stockpiles
                stockpiles = initial_conditions.get("stockpiles", {})
                if stockpiles:
                    typer.echo("AMMUNITION STOCKPILES:")
                    typer.echo("")
                    
                    # Air Defence
                    air_defence = stockpiles.get("air_defence_missiles", {})
                    if air_defence:
                        typer.echo("  Air Defence:")
                        for weapon, data in air_defence.items():
                            count = data.get("count", 0)
                            note = data.get("note", "")
                            typer.echo(f"    • {weapon.replace('_', ' ').title()}: {count}")
                            if note:
                                typer.echo(f"      {note}")
                        typer.echo("")
                    
                    # Naval Strike
                    typer.echo("  Naval Strike:")
                    tomahawk = stockpiles.get("tomahawk_cruise_missiles", {})
                    if tomahawk:
                        typer.echo(f"    • Tomahawk Cruise Missiles: {tomahawk.get('count', 0)}")
                        typer.echo(f"      {tomahawk.get('note', '')}")
                    harpoon = stockpiles.get("harpoon_anti_ship", {})
                    if harpoon:
                        typer.echo(f"    • Harpoon Anti-Ship: {harpoon.get('count', 0)}")
                        typer.echo(f"      {harpoon.get('note', '')}")
                    typer.echo("")
                    
                    # Air-Launched
                    typer.echo("  Air-Launched Precision:")
                    storm_shadow = stockpiles.get("storm_shadow_cruise_missiles", {})
                    if storm_shadow:
                        typer.echo(f"    • Storm Shadow: {storm_shadow.get('count', 0)}")
                        typer.echo(f"      {storm_shadow.get('note', '')}")
                    paveway = stockpiles.get("paveway_laser_guided_bombs", {})
                    if paveway:
                        typer.echo(f"    • Paveway LGBs: {paveway.get('count', 0)}")
                        typer.echo(f"      {paveway.get('note', '')}")
                    typer.echo("")
                    
                    # Anti-Submarine
                    typer.echo("  Anti-Submarine:")
                    spearfish = stockpiles.get("spearfish_torpedoes", {})
                    if spearfish:
                        typer.echo(f"    • Spearfish Torpedoes: {spearfish.get('count', 0)}")
                        typer.echo(f"      {spearfish.get('note', '')}")
                    stingray = stockpiles.get("stingray_lightweight_torpedoes", {})
                    if stingray:
                        typer.echo(f"    • Stingray Torpedoes: {stingray.get('count', 0)}")
                        typer.echo(f"      {stingray.get('note', '')}")
                    typer.echo("")
                
                # Display forces
                uk_forces = initial_conditions.get("uk_forces", {})
                if uk_forces:
                    naval = uk_forces.get("naval", [])
                    if naval:
                        typer.echo("NAVAL FORCES:")
                        typer.echo("")
                        for unit in naval:
                            unit_id = unit.get("id", "Unknown")
                            unit_type = unit.get("type", "")
                            location = unit.get("location", "")
                            status = unit.get("status", "")
                            typer.echo(f"  • {unit_id} ({unit_type})")
                            typer.echo(f"    Location: {location}")
                            typer.echo(f"    Status: {status}")
                            if unit.get("note"):
                                typer.echo(f"    Note: {unit.get('note')}")
                            typer.echo("")
                    
                    air = uk_forces.get("air", [])
                    if air:
                        typer.echo("AIR FORCES:")
                        typer.echo("")
                        for unit in air:
                            unit_id = unit.get("id", "Unknown")
                            unit_type = unit.get("type", "")
                            location = unit.get("location", "")
                            status = unit.get("status", "")
                            
                            # Display unit header
                            typer.echo(f"  • {unit_id}")
                            
                            # Show type and role
                            if unit_type:
                                role = unit.get("role", "")
                                if role:
                                    typer.echo(f"    Type: {unit_type} ({role})")
                                else:
                                    typer.echo(f"    Type: {unit_type}")
                            
                            # Show location if present
                            if location:
                                typer.echo(f"    Location: {location}")
                            
                            # Show aircraft counts if present
                            aircraft_count = unit.get("aircraft_count")
                            operational_aircraft = unit.get("operational_aircraft")
                            if aircraft_count is not None:
                                if operational_aircraft is not None:
                                    typer.echo(f"    Aircraft: {operational_aircraft}/{aircraft_count} operational")
                                else:
                                    typer.echo(f"    Aircraft: {aircraft_count}")
                            
                            # Show status
                            typer.echo(f"    Status: {status}")
                            
                            # Show note if present
                            if unit.get("note"):
                                typer.echo(f"    Note: {unit.get('note')}")
                            
                            typer.echo("")
                
                typer.echo("=" * 79)
                typer.echo("")
                continue
            
            if user_input.lower().startswith("/intel"):
                # Intelligence command - detailed actor assessment
                typer.echo("")
                
                # Parse command: /intel or /intel <country_code>
                parts = user_input.lower().split()
                if len(parts) == 1:
                    # Show available actors
                    if world.actor_system:
                        typer.echo("Available countries for intelligence assessment:")
                        typer.echo("")
                        for code, actor in world.actor_system.actors.items():
                            typer.echo(f"  /intel {code.lower()} - {actor.full_name}")
                        typer.echo("")
                    else:
                        typer.echo("Intelligence system not available.")
                else:
                    # Show detailed assessment for specific actor
                    country_code = parts[1].upper()
                    if world.actor_system:
                        from engine.intelligence import generate_actor_detailed_assessment
                        intel_lines = generate_actor_detailed_assessment(country_code, world, world.turn)
                        for line in intel_lines:
                            console.print(line)
                    else:
                        typer.echo("Intelligence system not available.")
                
                typer.echo("")
                continue
            
            if user_input.lower() in ["/llm", "llm", "/settings", "settings"]:
                # Open LLM model settings menu
                typer.echo("")
                typer.echo("Opening LLM Model Settings...")
                typer.echo("")
                model_settings_menu()
                # After returning from settings, clear and redisplay the discussion phase
                typer.clear()
                typer.echo("")
                if RICH_ENABLED:
                    console.print(phase_header("DISCUSSION", world.turn))
                    typer.echo("")
                    typer.echo("  Ask questions or type /decide when ready")
                    console.print(f"  [{COLORS['muted']}]Quick: /status  /menu  /advise  /resources  /intel  /llm[/{COLORS['muted']}]")
                    typer.echo("")
                    console.print(f"[{COLORS['muted']}]" + "─" * 79 + f"[/{COLORS['muted']}]")
                else:
                    console.print("=" * 79)
                    console.print(f"[{COLORS['accent']} bold]TURN {world.turn}: DISCUSSION PHASE[/{COLORS['accent']} bold]")
                    console.print("=" * 79)
                typer.echo("")
                continue
            
            if user_input.lower() in ["/menu", "menu", "/help", "help"]:
                typer.echo("")
                
                if RICH_ENABLED:
                    # Show advisor panel
                    console.print(advisor_menu_panel())
                    typer.echo("")
                    
                    # Show diplomatic contacts
                    available_contacts = list_available_diplomatic_contacts(world, root)
                    console.print(diplomatic_contacts_table(available_contacts))
                    typer.echo("")
                    
                    # Show metrics guide
                    console.print(metrics_guide_panel())
                    typer.echo("")
                    
                    # Show commands
                    console.print(command_menu())
                    typer.echo("")
                    
                    console.print(f"[{COLORS['muted']}]NOTE: You may also ask general questions without naming a specific advisor.[/{COLORS['muted']}]")
                else:
                    # Fallback to plain text
                    console.print("=" * 60)
                    console.print(f"[{COLORS['accent']} bold]AVAILABLE ADVISORS[/{COLORS['accent']} bold]")
                    console.print("=" * 60)
                    typer.echo("")
                    typer.echo("• National Security Advisor (NSA)")
                    typer.echo("  - Intelligence assessment, strategic planning, threat analysis")
                    typer.echo("  - Example: 'NSA, what's your assessment of Russian intentions?'")
                    typer.echo("")
                    typer.echo("• Chief of the Defence Staff (CDS)")
                    typer.echo("  - Military operations, force readiness, deployment options")
                    typer.echo("  - Example: 'CDS, what are our air defence capabilities?'")
                    typer.echo("")
                    typer.echo("• Foreign Secretary")
                    typer.echo("  - Diplomacy, alliance management, NATO coordination")
                    typer.echo("  - Example: 'Foreign Secretary, can we count on US support?'")
                    typer.echo("")
                    typer.echo("• Home Secretary")
                    typer.echo("  - Domestic security, civil protection, public messaging")
                    typer.echo("  - Example: 'Home Secretary, how do we reassure the public?'")
                    typer.echo("")
                    typer.echo("• Attorney General")
                    typer.echo("  - Legal framework, international law, rules of engagement")
                    typer.echo("  - Example: 'Attorney General, what are our legal constraints?'")
                    typer.echo("")
                    console.print("=" * 60)
                    console.print(f"[{COLORS['success']} bold]DIPLOMATIC CONTACTS[/{COLORS['success']} bold]")
                    console.print("=" * 60)
                    typer.echo("")
                    
                    # List available diplomatic contacts
                    available_contacts = list_available_diplomatic_contacts(world, root)
                    if available_contacts:
                        for country, access_level, title in available_contacts:
                            if access_level == "leader":
                                console.print(f"[{COLORS['warning']} bold]  * LEADER[/{COLORS['warning']} bold] - {country}: {title}")
                            else:
                                console.print(f"  • Diplomat - {country}: {title}")
                            console.print(f"    Command: /call {country.lower()}")
                            typer.echo("")
                    else:
                        typer.echo("  No diplomatic contacts available (Alliance Cohesion too low)")
                        typer.echo("")
                    
                    console.print("=" * 60)
                    console.print(f"[{COLORS['warning']} bold]METRICS GUIDE[/{COLORS['warning']} bold]")
                    console.print("=" * 60)
                    typer.echo("")
                    typer.echo("• Escalation Risk (0-100)")
                    typer.echo("  Likelihood of conflict escalating to full-scale war")
                    typer.echo("  HIGH = Danger of Russian attack or nuclear exchange")
                    typer.echo("")
                    typer.echo("• Domestic Stability (0-100)")
                    typer.echo("  Public confidence, economic stability, infrastructure security")
                    typer.echo("  LOW = Civil unrest, panic, political pressure")
                    typer.echo("")
                    typer.echo("• Alliance Cohesion (0-100)")
                    typer.echo("  Strength of NATO solidarity and allied support")
                    typer.echo("  HIGH = Access to leaders, Article 5 support likely")
                    typer.echo("  LOW = Isolated, limited diplomatic access")
                    typer.echo("")
                    typer.echo("• Influence (-10 to +10)")
                    typer.echo("  Your political capital and public sentiment")
                    typer.echo("  Derived from: (Stability + Cohesion) / 2")
                    typer.echo("  Currently: Informational only (future: affects options)")
                    typer.echo("")
                    console.print("=" * 60)
                    console.print(f"[{COLORS['accent']} bold]COMMANDS[/{COLORS['accent']} bold]")
                    console.print("=" * 60)
                    console.print("")
                    console.print(f"[{COLORS['primary']}]  /menu or /help[/{COLORS['primary']}]     - Show this menu")
                    console.print(f"[{COLORS['primary']}]  /status[/{COLORS['primary']}]            - Show current metrics and situation")
                    console.print(f"[{COLORS['primary']}]  /advise[/{COLORS['primary']}]            - Get input from all advisors at once")
                    console.print(f"[{COLORS['primary']}]  /resources[/{COLORS['primary']}]         - Show UK forces and ammunition stockpiles")
                    console.print(f"[{COLORS['primary']}]  /call <country>[/{COLORS['primary']}]    - Contact a foreign leader or diplomat")
                    console.print(f"[{COLORS['primary']}]  /decide[/{COLORS['primary']}]            - Make your decision")
                    console.print(f"[{COLORS['primary']}]  /theme[/{COLORS['primary']}]             - Change UI theme")
                    console.print(f"[{COLORS['primary']}]  /save[/{COLORS['primary']}]              - Save game and continue")
                    console.print(f"[{COLORS['primary']}]  /quit[/{COLORS['primary']}]              - Exit game")
                    typer.echo("")
                    console.print(f"[{COLORS['muted']}]NOTE: You may also ask general questions without naming a specific advisor.[/{COLORS['muted']}]")
                
                typer.echo("")
                continue
            
            # Handle question
            questions.append(user_input)
            discussion_lines = run_turn_discussion(world, scenario, [user_input], rng, root, transcript)
            
            typer.echo("")  # Space before response
            
            if RICH_ENABLED:
                console.print(f"[{COLORS['muted']}]" + "─" * 79 + f"[/{COLORS['muted']}]")
                typer.echo("")
            
            for line in discussion_lines:
                # Skip echoing the player's question (they just typed it)
                if not line.startswith("Prime Minister:"):
                    if ":" in line:
                        advisor_name, rest = line.split(":", 1)
                        
                        # Print advisor name
                        console.print(f"  [{COLORS['secondary']} bold]{advisor_name}[/{COLORS['secondary']} bold]")
                        typer.echo("")
                        
                        # Format response with structure
                        if RICH_ENABLED:
                            formatted = format_advisor_response("", rest)
                            console.print(formatted)
                        else:
                            typer.echo(rest)
                    else:
                        typer.echo(line)
            
            transcript.extend(discussion_lines)
            
            typer.echo("")  # Space after response
            
            if RICH_ENABLED:
                console.print(f"[{COLORS['muted']}]" + "─" * 79 + f"[/{COLORS['muted']}]")
            
            typer.echo("")
        
        # Decision phase loop - allows returning to discussion if decision is cancelled
        decision_confirmed = False
        while not decision_confirmed:
            # Decision phase - clear screen and start at top
            typer.clear()
            typer.echo("")  # Buffer line
            
            if RICH_ENABLED:
                console.print(phase_header("DECISION", world.turn))
                typer.echo("")
                typer.echo("  Enter your decision (or 'cancel' to return to discussion)")
            else:
                console.print("=" * 79)
                console.print(f"[{COLORS['emphasis']} bold]TURN {world.turn}: DECISION PHASE[/{COLORS['emphasis']} bold]")
                console.print("=" * 79)
                console.print("")
                console.print("Enter your decision (or 'cancel' to return to discussion):")
            
            typer.echo("")
            
            action = typer.prompt("Decision>").strip()
            
            if action.lower() == "cancel":
                # Return to discussion phase
                break
            
            if not action:
                typer.echo("No action entered. Returning to discussion.")
                typer.echo("")
                wait_for_space("Press SPACE to return to discussion...")
                break
            
            # Interpret and get pushback
            interpretation, pushback, critical_concerns, decision_lines = run_turn_decision(world, scenario, action, rng, root, transcript)
            transcript.extend(decision_lines)
            
            # Display decision with improved UX
            display_decision_summary(action, interpretation, show_details=False)
            
            # Option to see full details
            see_details = typer.prompt("", default="").strip().lower()
            if see_details == "details":
                display_decision_summary(action, interpretation, show_details=True)
                console.print("")
            
            # Handle critical omissions with selective addressing
            if critical_concerns:
                action_code, selected_indices = display_critical_concerns_with_selection(critical_concerns)
                
                if action_code == 'D':
                    # Return to discussion
                    typer.echo("")
                    typer.echo("Returning to discussion phase.")
                    typer.echo("")
                    wait_for_space("Press SPACE to return to discussion...")
                    break
                
                elif action_code == 'M':
                    # Modify manually
                    typer.echo("")
                    typer.echo("Decision cancelled. Please enter a modified decision.")
                    typer.echo("")
                    continue
                
                elif action_code in ['A', 'S'] and selected_indices:
                    # Apply selected recommendations
                    console.print("")
                    console.print(f"[{COLORS['success']}]Applying {len(selected_indices)} recommendation(s)...[/{COLORS['success']}]")
                    console.print("")
                    
                    # Append recommendations
                    enhanced_decision = append_recommendations_to_decision(action, critical_concerns, selected_indices)
                    
                    # Show enhanced decision
                    console.print(Panel(f"[italic]{enhanced_decision}[/italic]", title="[bold]ENHANCED DECISION[/bold]", border_style="white"))
                    console.print("")
                    
                    # Confirm
                    confirm = typer.confirm("Proceed with enhanced decision?", default=True)
                    
                    if not confirm:
                        console.print("")
                        console.print("Decision cancelled.")
                        console.print("")
                        continue
                    
                    # Update action for adjudication
                    action = enhanced_decision
                    
                    # Re-interpret
                    console.print("")
                    console.print("Re-interpreting enhanced decision...")
                    console.print("")
                    
                    interpretation, pushback, critical_concerns_2, decision_lines_2 = run_turn_decision(world, scenario, action, rng, root, transcript)
                    transcript.extend(decision_lines_2)
                    
                    # Display new interpretation
                    display_decision_summary(action, interpretation, show_details=False)
                    
                    # If STILL have concerns, warn
                    if critical_concerns_2:
                        console.print("")
                        console.print(f"[{COLORS['warning']}]⚠ Warning: Critical concerns remain.[/{COLORS['warning']}]")
                        console.print("")
                        # Let player proceed or go back
                        cont = typer.confirm("Proceed anyway?", default=False)
                        if not cont:
                            continue
                    
                    decision_confirmed = True
                
                else:  # 'I' - Ignore
                    typer.echo("")
                    typer.echo(f"[{COLORS['warning']}]Proceeding despite all concerns...[/{COLORS['warning']}]")
                    typer.echo("")
                    decision_confirmed = True
            
            # Confirm decision (regular pushback, if any)
            elif pushback:
                typer.echo("")
                confirm = typer.confirm("Proceed with this decision despite concerns?", default=True)
                if not confirm:
                    typer.echo("")
                    typer.echo("Decision cancelled. Returning to discussion.")
                    typer.echo("")
                    wait_for_space("Press SPACE to return to discussion...")
                    break  # Break inner loop, return to discussion
                else:
                    decision_confirmed = True  # Proceed to adjudication
            else:
                decision_confirmed = True  # No pushback, proceed to adjudication
        
        # If decision was cancelled, go back to discussion phase
        if not decision_confirmed:
            continue
        
        # Adjudication phase - clear screen and start at top
        typer.clear()
        typer.echo("")  # Buffer line
        
        if RICH_ENABLED:
            console.print(phase_header("ADJUDICATION", world.turn))
        else:
            console.print("=" * 79)
            console.print(f"[{COLORS['success']} bold]TURN {world.turn}: ADJUDICATION[/{COLORS['success']} bold]")
            console.print("=" * 79)
        
        typer.echo("")  # Buffer line
        
        # Run LLM-driven adjudication with narrative quality assessment
        try:
            actor_responses = []
            
            if world.actor_system:
                # Use multi-agent simulation
                from engine.narrative_adjudication import adjudicate_with_actor_simulation
                
                final_effects, actor_responses, character_responses, reasoning = adjudicate_with_actor_simulation(
                    narrative_state,
                    world.actor_system,
                    action,
                    interpretation,
                    rng,
                    llm_generate_fn=generate_text,
                    world_narrative=world.narrative
                )
            else:
                # Use standard narrative adjudication
                final_effects, character_responses, reasoning = adjudicate_with_narrative(
                    narrative_state,
                    action,
                    interpretation,
                    rng,
                    llm_generate_fn=generate_text,
                    world_narrative=world.narrative
                )
            
            # Display quality reasoning
            typer.echo("")
            if RICH_ENABLED:
                console.print(Panel(format_markdown(reasoning), title=f"[{COLORS['accent']} bold]ACTION ASSESSMENT[/]", border_style=COLORS['accent']))
            else:
                typer.echo("=" * 60)
                typer.echo("ACTION ASSESSMENT")
                typer.echo("=" * 60)
                typer.echo("")
                typer.echo(reasoning)
            typer.echo("")
            
            # Display effects (numeric deltas are classic-mode only; immersive and
            # emergent modes communicate consequences through vibes and narrative)
            if play_mode == "classic":
                if RICH_ENABLED:
                    console.print(f"[{COLORS['accent']} bold]EFFECTS[/]")
                    console.print(f"[{COLORS['accent']}]" + "═" * 60 + f"[/{COLORS['accent']}]")
                else:
                    typer.echo("=" * 60)
                    typer.echo("EFFECTS")
                    typer.echo("=" * 60)
                typer.echo("")

                for metric, delta in final_effects.items():
                    if RICH_ENABLED:
                        color = COLORS['success'] if delta > 0 else COLORS['danger'] if delta < 0 else COLORS['muted']
                        console.print(f"  [{color}]{metric}: {delta:+d}[/{color}]")
                    else:
                        typer.echo(f"  {metric}: {delta:+d}")
                typer.echo("")
            
            # Display character responses
            if character_responses:
                if RICH_ENABLED:
                    console.print(f"[{COLORS['accent']} bold]ADVISOR REACTIONS[/]")
                    console.print(f"[{COLORS['accent']}]" + "═" * 60 + f"[/{COLORS['accent']}]")
                else:
                    typer.echo("=" * 60)
                    typer.echo("ADVISOR REACTIONS")
                    typer.echo("=" * 60)
                typer.echo("")
                
                for char_name, response in character_responses:
                    if RICH_ENABLED:
                        console.print(f"[{COLORS['secondary']} bold]{char_name}:[/{COLORS['secondary']} bold]")
                        console.print(f"  \"{response}\"")
                    else:
                        typer.echo(f"{char_name}:")
                        typer.echo(f"  \"{response}\"")
                    typer.echo("")
            
            # Display international reactions (multi-agent simulation)
            if actor_responses:
                if RICH_ENABLED:
                    console.print(f"[{COLORS['accent']} bold]INTERNATIONAL REACTIONS[/]")
                    console.print(f"[{COLORS['accent']}]" + "═" * 60 + f"[/{COLORS['accent']}]")
                else:
                    typer.echo("=" * 60)
                    typer.echo("INTERNATIONAL REACTIONS")
                    typer.echo("=" * 60)
                typer.echo("")
                
                for response in actor_responses:
                    trust_delta = response.trust_change
                    actor_id = response.actor_id
                    
                    # Get full name if available
                    actor_name = actor_id
                    if world.actor_system:
                        actor = world.actor_system.get_actor(actor_id)
                        if actor:
                            actor_name = actor.full_name
                    
                    if RICH_ENABLED:
                        color = COLORS['success'] if trust_delta > 0 else COLORS['danger'] if trust_delta < 0 else COLORS['muted']
                        console.print(f"[{COLORS['primary']} bold]{actor_name}:[/{COLORS['primary']} bold] [{color}]({trust_delta:+d})[/{color}]")
                        console.print(f"  \"{response.public_response}\"")
                    else:
                        typer.echo(f"{actor_name}: ({trust_delta:+d})")
                        typer.echo(f"  \"{response.public_response}\"")
                    typer.echo("")
            
            # Sync world metrics with narrative state (keep both in sync)
            world.metrics.escalation_risk = narrative_state.hidden_metrics.escalation_risk
            world.metrics.domestic_stability = narrative_state.hidden_metrics.domestic_stability
            world.metrics.alliance_cohesion = narrative_state.hidden_metrics.alliance_cohesion
            world.metrics.casualties_mil = narrative_state.hidden_metrics.casualties_mil
            world.metrics.casualties_civ = narrative_state.hidden_metrics.casualties_civ
            
            # Build transcript for save file
            adjudication_lines = [
                "Action Assessment:",
                reasoning,
                "",
                "Effects:"
            ]
            for metric, delta in final_effects.items():
                adjudication_lines.append(f"  {metric}: {delta:+d}")
            adjudication_lines.append("")
            
            if character_responses:
                adjudication_lines.append("Advisor Reactions:")
                for char_name, response in character_responses:
                    adjudication_lines.append(f"{char_name}: \"{response}\"")
                adjudication_lines.append("")
                
            if actor_responses:
                adjudication_lines.append("International Reactions:")
                for response in actor_responses:
                    adjudication_lines.append(f"{response.actor_id}: \"{response.public_response}\"")
                adjudication_lines.append("")
            
            transcript.extend(adjudication_lines)
        
        except Exception as e:
            # Fallback to primitive system on error
            if RICH_ENABLED:
                console.print(f"[{COLORS['warning']}][WARNING] LLM adjudication failed: {e}[/{COLORS['warning']}]")
                console.print(f"[{COLORS['warning']}][INFO] Falling back to keyword-based adjudication[/{COLORS['warning']}]")
            else:
                typer.echo(f"[WARNING] LLM adjudication failed: {e}")
                typer.echo("[INFO] Falling back to keyword-based adjudication")
            typer.echo("")
            
            adjudication_lines = run_turn_adjudication_fallback(world, action, interpretation, rng)
            for line in adjudication_lines:
                typer.echo(line)
            transcript.extend(adjudication_lines)
            
            # Sync narrative state from world (reverse sync in fallback mode)
            narrative_state.update_hidden_metrics({
                "escalation_risk": world.metrics.escalation_risk,
                "domestic_stability": world.metrics.domestic_stability,
                "alliance_cohesion": world.metrics.alliance_cohesion,
                "casualties_mil": world.metrics.casualties_mil,
                "casualties_civ": world.metrics.casualties_civ
            })
        
        # Narrative state turn already updated by adjudicate_with_narrative()
        narrative_state.turn = world.turn
        
        # Display based on play mode
        typer.echo("")
        if play_mode == "classic":
            # Classic mode: Show raw metrics with deltas
            if RICH_ENABLED:
                console.print(metrics_table(world, show_deltas=True, previous_metrics=turn_start_metrics))
                typer.echo("")  # Buffer after table
        elif play_mode == "immersive":
            # Immersive mode: Show vibes + character attitudes
            typer.echo("═" * 60)
            typer.echo("SITUATION ASSESSMENT")
            typer.echo("═" * 60)
            typer.echo("")
            
            vibes = narrative_state.get_situation_vibes()
            for vibe in vibes:
                typer.echo(vibe.to_string())
            
            typer.echo("")
            typer.echo("═" * 60)
            typer.echo("ADVISOR ATTITUDES")
            typer.echo("═" * 60)
            typer.echo("")
            
            for char_id, char_attitude in narrative_state.characters.items():
                # Create visual trust bar
                trust_level = char_attitude.trust // 20  # 0-5 scale
                trust_bar = "█" * trust_level + "░" * (5 - trust_level)
                relationship_symbol = {
                    "allied": "✓",
                    "neutral": "○",
                    "hostile": "✗",
                    "unknown": "?"
                }.get(char_attitude.relationship, "○")
                
                typer.echo(f"{char_attitude.name:<30} {trust_bar} {relationship_symbol} {char_attitude.relationship.upper()}")
            
            typer.echo("")
        elif play_mode == "emergent":
            # Emergent mode: Narrative summary only
            typer.echo("═" * 60)
            typer.echo(narrative_state.situation_summary)
            typer.echo("═" * 60)
            typer.echo("")
        
        # Auto-save after each turn
        save_path = save_game(world, transcript, scenario, "autosave", root, play_mode, narrative_state)
        
        # Advance turn
        world.turn += 1
        world.scene = world.turn  # Keep scene in sync for legacy compatibility
        world.discussion_transcript = []
        
        typer.echo("")
        typer.echo("=" * 60)
        typer.echo(f"Turn {world.turn - 1} complete. Auto-saved to {save_path.name}")
        typer.echo("=" * 60)
        typer.echo("")
        
        # Continue to next turn with spacebar
        try:
            wait_for_space("Press SPACE to continue to next turn (or Ctrl+C to exit)...")
        except KeyboardInterrupt:
            typer.echo("\nGame paused. Use --load to resume.")
            break


@app.command(rich_help_panel="GAMEPLAY")
def batch(
    scenario: str = typer.Option("war_game_2025", help="Scenario identifier"),
    seed: int = typer.Option(42, help="Random seed"),
    action: str = typer.Option("Deploy defensive forces", help="Action to take"),
):
    """Run a single turn in batch mode (for testing)."""
    
    transcript = run_single_scene(scenario, seed, "llm")
    for line in transcript:
        typer.echo(line)


@app.command(rich_help_panel="UTILITY")
def settings():
    """Configure LLM model settings (Flash vs Pro per system)."""
    console.print("\n[bold cyan]LLM Model Settings[/bold cyan]\n")
    console.print("Configure which systems use Flash (fast/cheap) vs Pro (sophisticated/expensive)\n")
    
    model_settings_menu()


@app.command(rich_help_panel="UTILITY")
def intro():
    """Display the intro text."""
    for line in get_intro_lines(200):
        typer.echo(line)


if __name__ == "__main__":
    app()
