# NEW GAME TYPE SELECTION FUNCTION
# Replace select_narrative() with this in cli/main.py

def select_game_type(scenario_id: str) -> Optional[NarrativeConfig]:
    """Display game type selection menu (Original Story Mode vs Mystery Mode).
    
    Args:
        scenario_id: Base scenario identifier
    
    Returns:
        None if Original Story Mode selected,
        NarrativeConfig (randomly chosen) if Mystery Mode selected
    """
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

# Also update:
# 1. Function call: select_narrative(scenario) -> select_game_type(scenario)
# 2. Add to imports: from typing import Optional
# 3. Update comment: "Select game type (Original vs Mystery)"



