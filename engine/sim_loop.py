"""Game simulation loop with two-phase turn structure.

Supports:
- Briefing phase: Load and display inject
- Discussion phase: Free-form Q&A with advisors (no commitment)
- Decision phase: Player commits to action, gets interpretation and pushback
- Adjudication phase: Apply effects to world state
"""

from typing import Any, Dict, List, Optional, Tuple
from random import Random
import time
from pathlib import Path

from models.world import WorldState, Metrics
from engine.utils import clamp, clamp_metrics
from engine.events import load_inject_for_turn
from engine.initial_conditions import load_initial_conditions
from engine.flags import update_world_flags
from engine.intro import get_intro_lines
from engine.narrator import generate_narrator_bridge
from agents.conversation import (
    handle_player_question,
    interpret_player_action,
    generate_advisor_pushback,
    check_critical_omissions
)
from llm.router import generate_text
from llm.inject_generator import generate_inject
from engine.diplomacy import run_diplomatic_encounter


def display_inject(inject: Dict[str, Any], root_path: Path, display_panel: bool = True) -> List[str]:
    """Format inject for display with Rich panel and channel-based styling.
    
    Displays inject to console using Rich Panel (if enabled) and returns the
    description text as lines for scene parsing and transcript.
    
    Args:
        inject: Inject dict
        root_path: Project root path
        display_panel: If False, skip panel display and only return lines (for streaming)
    
    Returns:
        List of description lines (includes actual inject text for parsing)
    """
    try:
        from cli.rich_ui import console, RICH_ENABLED
        from cli.theme import COLORS
        from rich.panel import Panel
    except ImportError:
        RICH_ENABLED = False
    
    lines = []
    
    title = inject.get("title", "")
    description = inject.get("description", "")
    channel = inject.get("channel", "briefing")  # briefing/intel/breaking
    
    if RICH_ENABLED:
        # Channel colors
        channel_colors = {
            "briefing": COLORS["accent"],      # blue
            "intel": COLORS["warning"],        # yellow
            "breaking": COLORS["danger"]       # red
        }
        color = channel_colors.get(channel, COLORS["accent"])
        
        # Build Rich panel AND track lines for scene parser
        panel_content = []
        description_lines = []  # NEW: Track description for scene parsing
        
        if description:
            paragraphs = description.split('\n\n')
            for para in paragraphs:
                para_stripped = para.strip()
                if para_stripped:
                    # Add to panel display
                    panel_content.append(para_stripped)
                    panel_content.append("")
                    
                    # NEW: Add individual lines to return list for parsing
                    for line in para_stripped.split('\n'):
                        description_lines.append(line)
                    description_lines.append("")  # Paragraph break
        
        panel = Panel(
            "\n".join(panel_content),
            title=f"[bold]{title.upper()}[/bold]",
            border_style=color,
            padding=(1, 2)
        )
        
        lines.append("")
        if display_panel:
            console.print(panel)  # Display Rich Panel to user
        
        # NEW: Also return description lines for scene parser
        lines.extend(description_lines)
        lines.append("")
    else:
        # Fallback to plain text
        lines.append("")
        if title:
            lines.append(f"=== {title.upper()} ===")
        lines.append("")
        
        # Format description with proper paragraph spacing
        if description:
            # Split into paragraphs (separated by blank lines)
            paragraphs = description.split('\n\n')
            
            for para in paragraphs:
                # Clean up the paragraph
                para = para.strip()
                if para:
                    # Split long paragraphs into lines for better readability
                    if para.startswith("===") or para.startswith("---"):
                        # Keep separators as-is
                        lines.append(para)
                    else:
                        # Add the paragraph
                        lines.append(para)
                    
                    # Add spacing after paragraph
                    lines.append("")
    
    # Display image/panel if present
    image_path = inject.get("image")
    if isinstance(image_path, str):
        panel_path = root_path / image_path
        try:
            if panel_path.exists():
                raw_lines = panel_path.read_text(encoding="utf-8").splitlines()
                show_lines = [ln for ln in raw_lines if ln.strip()][:5]
                for ln in show_lines:
                    lines.append(ln)
                lines.append("")
            else:
                lines.append("[Panel missing]")
                lines.append("")
        except Exception:
            lines.append("[Panel unreadable]")
            lines.append("")
    
    return lines


def apply_inject_effects(world: WorldState, inject: Dict[str, Any], silent: bool = False) -> List[str]:
    """Apply inject effects with color-coded display.
    
    Applies difficulty multiplier to scenario effects based on world.difficulty setting.
    
    Args:
        world: Current world state (modified in place)
        inject: Inject dict with effects
        silent: If True, apply effects but don't display boxes (for initial briefing)
    
    Returns:
        List of transcript lines describing applied effects
    """
    try:
        from cli.rich_ui import console, RICH_ENABLED
        from cli.theme import COLORS
    except ImportError:
        RICH_ENABLED = False
    
    # Get difficulty multiplier
    difficulty_multipliers = {
        "standard": 0.5,
        "challenging": 0.7,
        "brutal": 1.0
    }
    difficulty_multiplier = difficulty_multipliers.get(world.difficulty, 0.5)
    
    lines = []
    effects = inject.get("effects", [])
    
    if not isinstance(effects, list):
        return lines
    
    for eff in effects:
        if not isinstance(eff, dict):
            continue
        
        metric_name = eff.get("metric")
        delta_spec = eff.get("delta")
        
        # Determine delta value deterministically
        delta_value: Optional[int] = None
        if isinstance(delta_spec, int):
            delta_value = delta_spec
        elif isinstance(delta_spec, str) and ".." in delta_spec:
            try:
                left_str, right_str = delta_spec.split("..", 1)
                left = int(left_str.strip())
                right = int(right_str.strip())
                delta_value = int((left + right) / 2)
            except Exception:
                delta_value = None
        
        # Apply difficulty multiplier to scenario effects (not casualties)
        if delta_value is not None and metric_name not in ["casualties_civ", "casualties_mil"]:
            delta_value = int(delta_value * difficulty_multiplier)
        
        if isinstance(metric_name, str) and delta_value is not None:
            # Update the targeted metric
            if hasattr(world.metrics, metric_name):
                current = getattr(world.metrics, metric_name)
                if isinstance(current, int):
                    updated = clamp(current + delta_value)
                    setattr(world.metrics, metric_name, updated)
                    
                    # Color-coded effect display (unless silent mode)
                    if RICH_ENABLED and not silent:
                        delta_color = COLORS["success"] if delta_value > 0 else COLORS["danger"]
                        muted_color = COLORS['muted']
                        effect_text = f"Effect: {metric_name} [{delta_color}]{delta_value:+d}[/{delta_color}] ([{muted_color}]→ {updated}[/{muted_color}])"
                        
                        # Print complete box with content
                        plain_text = f"Effect: {metric_name} {delta_value:+d} (→ {updated})"
                        top_line = "┌" + "─" * (len(plain_text) + 2) + "┐"
                        content_line = f"│ {effect_text} │"
                        bottom_line = "└" + "─" * (len(plain_text) + 2) + "┘"
                        
                        console.print(top_line)
                        console.print(content_line)
                        console.print(bottom_line)
                        
                        lines.append(top_line)
                        lines.append(f"│ {plain_text} │")  # Plain text for transcript
                        lines.append(bottom_line)
                    else:
                        # Plain text fallback
                        effect_text = f"Effect: {metric_name} {delta_value:+d} (-> {updated})"
                        lines.append("┌" + "─" * (len(effect_text) + 2) + "┐")
                        lines.append(f"│ {effect_text} │")
                        lines.append("└" + "─" * (len(effect_text) + 2) + "┘")
            else:
                lines.append(f"Skipped: unknown metric '{metric_name}'")
    
    # Clamp and update flags after all effects applied
    clamp_metrics(world.metrics)
    update_world_flags(world)
    
    return lines


def run_turn_briefing(
    world: WorldState,
    scenario_id: str,
    stochastic_injects: bool,
    rng: Random,
    root_path: Optional[Path] = None,
    full_transcript: Optional[List[str]] = None,
    get_player_input: Optional[Any] = None,
    turn_filename: Optional[str] = None,
    silent_effects: bool = False,
    suppress_display: bool = False
) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """Run briefing phase: load and display inject, handle mandatory diplomatic encounters.
    
    Args:
        world: Current world state
        scenario_id: Scenario identifier
        stochastic_injects: Whether to generate injects if file missing
        rng: Random number generator
        root_path: Optional root path override
        full_transcript: Optional full game transcript for conversation history
        get_player_input: Optional function to get player input (for diplomatic encounters)
        turn_filename: Optional custom turn filename (for scenario variants)
        silent_effects: If True, apply effects but don't display boxes (for initial Turn 1)
        suppress_display: If True, don't display inject panel (caller will stream it)
    
    Returns:
        Tuple of (inject_dict, transcript_lines)
    """
    if root_path is None:
        root_path = Path(__file__).resolve().parents[1]
    
    world.phase = "briefing"
    transcript = []
    
    transcript.append("")
    transcript.append("=" * 60)
    transcript.append(f"TURN {world.turn}")
    transcript.append("=" * 60)
    transcript.append("")
    
    # Load inject for this turn (with optional custom filename for variants)
    inject = load_inject_for_turn(scenario_id, world.turn, root_path, turn_filename)
    
    # If no inject file and stochastic mode enabled, generate one
    if inject is None and stochastic_injects:
        initial_conditions = load_initial_conditions(scenario_id, root_path)
        inject = generate_inject(world, world.turn, initial_conditions, rng, root_path, full_transcript)
        if inject:
            transcript.append("[Stochastically generated inject]")
        else:
            transcript.append("[WARNING] Failed to generate inject for this turn. Check console for errors.")
    
    if inject:
        # === STEP 1: NARRATOR INTRO BRIDGE ===
        # Generate atmospheric bridge if we have history (Turn > 1)
        if world.turn > 1 and full_transcript:
            try:
                from cli.rich_ui import console, RICH_ENABLED
                from cli.theme import COLORS
                
                bridge_text = generate_narrator_bridge(
                    world, 
                    full_transcript, 
                    inject.get("title", "Unknown Event"), 
                    rng
                )
                
                if bridge_text:
                    # Add to transcript
                    transcript.append(f"\n[Narrator] {bridge_text}\n")
                    
                    # Display to user with dramatic formatting
                    if RICH_ENABLED and not suppress_display:
                        console.print("")
                        console.print(f"[{COLORS['secondary']} italic]{bridge_text}[/{COLORS['secondary']} italic]")
                        console.print("")
                        # Dramatic pause
                        time.sleep(2.5)
            except Exception as e:
                # Fail gracefully (don't crash game on narrative flavor)
                pass

        # Display the inject
        inject_lines = display_inject(inject, root_path, display_panel=not suppress_display)
        transcript.extend(inject_lines)
        
        # Apply inject effects
        effect_lines = apply_inject_effects(world, inject, silent=silent_effects)
        transcript.extend(effect_lines)
        
        # Check for mandatory diplomatic encounter
        diplomatic_encounter = inject.get("diplomatic_encounter")
        if diplomatic_encounter and isinstance(diplomatic_encounter, dict):
            required = diplomatic_encounter.get("required", False)
            country = diplomatic_encounter.get("country")
            context = diplomatic_encounter.get("context")
            
            if required and country:
                transcript.append("\n*** MANDATORY DIPLOMATIC ENCOUNTER ***\n")
                if get_player_input:
                    input("Press ENTER to answer the call...")
                
                # Run diplomatic encounter (with real-time printing if available)
                encounter_transcript, cohesion_delta = run_diplomatic_encounter(
                    world,
                    country,
                    required=True,
                    context=context,
                    llm_generate=generate_text,
                    rng=rng,
                    root_path=root_path,
                    full_transcript=full_transcript,
                    get_player_input=get_player_input,
                    print_fn=print if get_player_input else None  # Print in real-time if interactive
                )
                
                transcript.extend(encounter_transcript)
                
                # Apply alliance cohesion change
                world.metrics.alliance_cohesion = clamp(world.metrics.alliance_cohesion + cohesion_delta)
                clamp_metrics(world.metrics)
                update_world_flags(world)
    else:
        transcript.append("No inject for this turn.")
    
    transcript.append("")
    return inject, transcript


def run_turn_discussion(
    world: WorldState,
    scenario_id: str,
    questions: List[str],
    rng: Random,
    root_path: Optional[Path] = None,
    full_transcript: Optional[List[str]] = None
) -> List[str]:
    """Run discussion phase: handle player questions.
    
    Args:
        world: Current world state
        scenario_id: Scenario identifier
        questions: List of player questions
        rng: Random number generator
        root_path: Optional root path override
        full_transcript: Optional full game transcript for conversation history
    
    Returns:
        Transcript lines
    """
    if root_path is None:
        root_path = Path(__file__).resolve().parents[1]
    
    world.phase = "discussion"
    transcript = []
    
    initial_conditions = load_initial_conditions(scenario_id, root_path)
    
    # Debug: Check if initial conditions loaded
    if not initial_conditions:
        transcript.append(f"[DEBUG] Failed to load initial conditions from {root_path / 'data' / 'scenarios' / scenario_id}")
        return transcript
    
    for question in questions:
        # Don't echo the player's question - they just typed it
        # Just store it in transcript for save files
        transcript.append(f"Prime Minister: {question}")
        
        responses = handle_player_question(
            world,
            question,
            initial_conditions,
            generate_text,
            rng,
            full_transcript
        )
        
        for role, response in responses:
            transcript.append(f"{role}: {response}")
    
    # Store discussion in world state
    world.discussion_transcript.extend(transcript)
    
    return transcript


def run_turn_decision(
    world: WorldState,
    scenario_id: str,
    action: str,
    rng: Random,
    root_path: Optional[Path] = None,
    full_transcript: Optional[List[str]] = None,
    dry_run: bool = False
) -> Tuple[str, List[Tuple[str, str]], List[Tuple[str, str, str]], List[str]]:
    """Run decision phase: interpret action, generate pushback, and check critical omissions.
    
    Args:
        world: Current world state
        scenario_id: Scenario identifier
        action: Player's action description
        rng: Random number generator
        root_path: Optional root path override
        full_transcript: Optional full game transcript for conversation history
        dry_run: If True, do not update world phase (preview mode)
    
    Returns:
        Tuple of (interpretation, pushback_list, critical_concerns, transcript_lines)
        critical_concerns: List of (advisor_role, concern, recommendation) tuples
    """
    if root_path is None:
        root_path = Path(__file__).resolve().parents[1]
    
    if not dry_run:
        world.phase = "decision"
        
    transcript = []
    
    initial_conditions = load_initial_conditions(scenario_id, root_path)
    
    # Store decision in transcript (for save files) but don't echo it
    transcript.append(f"Prime Minister's Decision: {action}")
    transcript.append("")
    
    # Interpret action
    interpretation = interpret_player_action(
        world,
        action,
        initial_conditions,
        generate_text,
        rng,
        full_transcript
    )
    
    transcript.append("Interpretation:")
    transcript.append(interpretation)
    transcript.append("")
    
    # Generate advisor pushback
    pushback = generate_advisor_pushback(
        world,
        action,
        interpretation,
        initial_conditions,
        generate_text,
        rng,
        full_transcript
    )
    
    if pushback:
        transcript.append("Advisor Concerns:")
        for role, concern in pushback:
            transcript.append(f"\n{role}: {concern}")
        transcript.append("")
    else:
        transcript.append("No advisor concerns raised.")
        transcript.append("")
    
    # Check for critical omissions (high-priority strategic gaps)
    critical_concerns = check_critical_omissions(
        world,
        action,
        interpretation,
        initial_conditions,
        generate_text,
        rng,
        full_transcript
    )
    
    if critical_concerns:
        transcript.append("CRITICAL ADVISORY:")
        for role, concern, recommendation in critical_concerns:
            transcript.append(f"\n{role}: {concern}")
            transcript.append(f"RECOMMENDATION: {recommendation}")
        transcript.append("")
    
    return interpretation, pushback, critical_concerns, transcript


def run_turn_adjudication(
    world: WorldState,
    action: str,
    interpretation: str,
    rng: Random
) -> List[str]:
    """Run adjudication phase: apply action effects to world state.
    
    Args:
        world: Current world state (modified in place)
        action: Player's action description
        interpretation: LLM's interpretation of the action
        rng: Random number generator
    
    Returns:
        Transcript lines
    """
    world.phase = "adjudication"
    transcript = []
    
    transcript.append("Adjudicating action effects...")
    
    # Capture metrics BEFORE changes
    metrics_before = {
        'risk': world.metrics.escalation_risk,
        'stability': world.metrics.domestic_stability,
        'cohesion': world.metrics.alliance_cohesion
    }
    
    # For MVP, we'll apply simple heuristic effects based on action keywords
    # In future, this could be more sophisticated or LLM-driven
    action_lower = action.lower()
    
    if "deploy" in action_lower or "surge" in action_lower:
        world.metrics.escalation_risk = clamp(world.metrics.escalation_risk + 5)
        transcript.append("Effect: Deployment raises escalation risk")
    
    if "diplomatic" in action_lower or "nato" in action_lower or "alliance" in action_lower:
        world.metrics.alliance_cohesion = clamp(world.metrics.alliance_cohesion + 5)
        transcript.append("Effect: Diplomatic engagement strengthens alliance cohesion")
    
    if "public" in action_lower or "statement" in action_lower or "reassure" in action_lower:
        world.metrics.domestic_stability = clamp(world.metrics.domestic_stability + 3)
        transcript.append("Effect: Public messaging improves domestic stability")
    
    if "nuclear" in action_lower or "strike" in action_lower:
        world.metrics.escalation_risk = clamp(world.metrics.escalation_risk + 20)
        world.metrics.alliance_cohesion = clamp(world.metrics.alliance_cohesion - 30)
        transcript.append("Effect: Aggressive action dramatically escalates crisis and fractures alliances")
    
    # Clamp and update flags
    clamp_metrics(world.metrics)
    update_world_flags(world)
    
    # Note: Metrics display is now handled by cli/main.py with Rich table
    # No need to duplicate the metrics output here
    
    return transcript


def run_full_turn(
    world: WorldState,
    scenario_id: str,
    action: str,
    questions: Optional[List[str]] = None,
    stochastic_injects: bool = False,
    rng: Optional[Random] = None,
    root_path: Optional[Path] = None
) -> List[str]:
    """Run a complete turn: briefing → discussion → decision → adjudication.
    
    Args:
        world: Current world state (modified in place)
        scenario_id: Scenario identifier
        action: Player's final action
        questions: Optional list of discussion questions
        stochastic_injects: Whether to generate injects if file missing
        rng: Optional random number generator
        root_path: Optional root path override
    
    Returns:
        Full transcript for the turn
    """
    if rng is None:
        rng = Random(42)
    
    transcript = []
    
    # Briefing phase
    inject, briefing_lines = run_turn_briefing(world, scenario_id, stochastic_injects, rng, root_path)
    transcript.extend(briefing_lines)
    
    # Discussion phase (if questions provided)
    if questions:
        discussion_lines = run_turn_discussion(world, scenario_id, questions, rng, root_path)
        transcript.extend(discussion_lines)
    
    # Decision phase
    interpretation, pushback, decision_lines = run_turn_decision(world, scenario_id, action, rng, root_path)
    transcript.extend(decision_lines)
    
    # Adjudication phase
    adjudication_lines = run_turn_adjudication(world, action, interpretation, rng)
    transcript.extend(adjudication_lines)
    
    # Advance to next turn
    world.turn += 1
    world.discussion_transcript = []  # Clear discussion for next turn
    
    return transcript


# Legacy compatibility function for old tests
def run_single_scene(scenario_id: str, seed: int, leader_mode: str) -> List[str]:
    """Legacy function for backward compatibility with existing tests.
    
    Deprecated: Use run_full_turn instead.
    """
    rng = Random(seed)
    root = Path(__file__).resolve().parents[1]
    
    # Minimal world for demo purposes
    world = WorldState(
        turn=1,
        scene=1,
        metrics=Metrics(escalation_risk=40, domestic_stability=60, alliance_cohesion=70),
        flags={},
        posture={"red_intent": "high", "tempo": "fast"},
    )
    
    transcript = []
    
    # Intro stage
    for ln in get_intro_lines(12):
        transcript.append(ln)
    
    # Run a simple turn with mock action
    turn_transcript = run_full_turn(
        world,
        scenario_id,
        action="Deploy Type-45 destroyers and establish combat air patrols",
        questions=None,
        stochastic_injects=False,
        rng=rng,
        root_path=root
    )
    
    transcript.extend(turn_transcript)
    
    return transcript


def assert_determinism_seed_42() -> None:
    """Simple gate: ensure deterministic transcript under seed=42."""
    t1 = run_single_scene(scenario_id="war_game_2025", seed=42, leader_mode="llm")
    t2 = run_single_scene(scenario_id="war_game_2025", seed=42, leader_mode="llm")
    assert t1 == t2, "Transcripts differ under same seed and inputs"
