"""Interactive menu for configuring LLM model settings."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

from llm.model_config import (
    LLMContext, ModelTier, ModelConfig, 
    get_model_config, set_model_config, reset_to_defaults
)


console = Console()


def display_current_config(config: ModelConfig):
    """Display current model configuration in a table."""
    table = Table(title="Current LLM Model Configuration", show_header=True, header_style="bold cyan")
    table.add_column("System", style="white", width=30)
    table.add_column("Model", style="green", width=25)
    table.add_column("Tier", style="yellow", width=10)
    
    # Context descriptions
    descriptions = {
        LLMContext.ADVISOR_QA: "Advisor Q&A",
        LLMContext.DECISION_INTERPRETATION: "Decision Interpretation",
        LLMContext.ADVISOR_PUSHBACK: "Advisor Pushback",
        LLMContext.CRITICAL_OMISSIONS: "Critical Omissions",
        LLMContext.INJECT_GENERATION: "Inject Generation",
        LLMContext.DIPLOMACY_CONVERSATION: "Diplomacy Conversations",
        LLMContext.DIPLOMACY_OUTCOME: "Diplomacy Outcomes",
        LLMContext.CHARACTER_RESPONSE: "Character Responses",
    }
    
    for context in LLMContext:
        model_name = config.get_model_for_context(context)
        tier = "PRO" if "pro" in model_name.lower() else "FLASH"
        table.add_row(descriptions[context], model_name, tier)
    
    console.print(table)
    
    # Show cost estimate
    cost = config.estimate_cost_per_turn()
    console.print(f"\n[yellow]Estimated cost per turn: ${cost:.3f}[/yellow]")
    console.print(f"[yellow]Estimated cost per 15-turn game: ${cost * 15:.2f}[/yellow]\n")


def configure_individual_systems(config: ModelConfig):
    """Allow user to configure each system individually."""
    console.print("\n[bold]Configure Individual Systems[/bold]\n")
    
    descriptions = {
        LLMContext.ADVISOR_QA: "Advisor Q&A (strategic advice)",
        LLMContext.DECISION_INTERPRETATION: "Decision Interpretation (parsing)",
        LLMContext.ADVISOR_PUSHBACK: "Advisor Pushback (warnings)",
        LLMContext.CRITICAL_OMISSIONS: "Critical Omissions (strategic gaps)",
        LLMContext.INJECT_GENERATION: "Inject Generation (story events)",
        LLMContext.DIPLOMACY_CONVERSATION: "Diplomacy Conversations (leader dialogue)",
        LLMContext.DIPLOMACY_OUTCOME: "Diplomacy Outcomes (assessment)",
        LLMContext.CHARACTER_RESPONSE: "Character Responses (flavor text)",
    }
    
    for i, context in enumerate(LLMContext, 1):
        current_model = config.get_model_for_context(context)
        current_tier = "PRO" if "pro" in current_model.lower() else "FLASH"
        
        console.print(f"[cyan]{i}. {descriptions[context]}[/cyan]")
        console.print(f"   Current: {current_tier}")
        
        choice = Prompt.ask(
            "   Select model",
            choices=["flash", "pro", "skip"],
            default="skip"
        )
        
        if choice == "flash":
            config.set_model_for_context(context, ModelTier.FLASH)
            console.print("   [green]✓ Set to FLASH[/green]\n")
        elif choice == "pro":
            config.set_model_for_context(context, ModelTier.PRO)
            console.print("   [green]✓ Set to PRO[/green]\n")
        else:
            console.print("   [dim]Skipped[/dim]\n")


def show_presets_menu(config: ModelConfig):
    """Show preset configuration options."""
    console.print("\n[bold]Preset Configurations[/bold]\n")
    
    console.print("[cyan]1.[/cyan] All Flash (Cheapest - ~$0.10/game)")
    console.print("   Best for: Testing, budget-conscious play")
    console.print("")
    
    console.print("[cyan]2.[/cyan] Recommended Hybrid (Balanced - ~$0.60/game)")
    console.print("   Best for: Normal gameplay, good quality/cost balance")
    console.print("   Pro: Advisor Q&A, Critical Omissions, Inject Gen, Diplomacy")
    console.print("   Flash: Decision parsing, Pushback, Outcomes")
    console.print("")
    
    console.print("[cyan]3.[/cyan] All Pro (Best Quality - ~$1.00/game)")
    console.print("   Best for: Maximum quality, narrative richness")
    console.print("")
    
    console.print("[cyan]4.[/cyan] Custom (Configure each system individually)")
    console.print("")
    console.print("[cyan]5.[/cyan] Back to main menu")
    console.print("")
    
    choice = Prompt.ask("Select preset", choices=["1", "2", "3", "4", "5"], default="2")
    
    if choice == "1":
        config.use_flash_for_all()
        console.print("\n[green]✓ All systems set to Flash[/green]")
    elif choice == "2":
        # Recommended hybrid
        config.set_model_for_context(LLMContext.ADVISOR_QA, ModelTier.PRO)
        config.set_model_for_context(LLMContext.DECISION_INTERPRETATION, ModelTier.FLASH)
        config.set_model_for_context(LLMContext.ADVISOR_PUSHBACK, ModelTier.FLASH)
        config.set_model_for_context(LLMContext.CRITICAL_OMISSIONS, ModelTier.PRO)
        config.set_model_for_context(LLMContext.INJECT_GENERATION, ModelTier.PRO)
        config.set_model_for_context(LLMContext.DIPLOMACY_CONVERSATION, ModelTier.PRO)
        config.set_model_for_context(LLMContext.DIPLOMACY_OUTCOME, ModelTier.PRO)
        config.set_model_for_context(LLMContext.CHARACTER_RESPONSE, ModelTier.FLASH)
        console.print("\n[green]✓ Recommended hybrid configuration applied[/green]")
    elif choice == "3":
        config.use_pro_for_all()
        console.print("\n[green]✓ All systems set to Pro[/green]")
    elif choice == "4":
        configure_individual_systems(config)
    
    return choice != "5"


def model_settings_menu():
    """Main model settings menu."""
    config = get_model_config()
    
    while True:
        console.clear()
        console.print(Panel.fit(
            "[bold cyan]LLM Model Settings[/bold cyan]\n"
            "Configure which systems use Flash (fast/cheap) vs Pro (sophisticated/expensive)",
            border_style="cyan"
        ))
        
        display_current_config(config)
        
        console.print("[bold]Options:[/bold]\n")
        console.print("[cyan]1.[/cyan] Choose preset configuration")
        console.print("[cyan]2.[/cyan] Configure individual systems")
        console.print("[cyan]3.[/cyan] Reset to defaults")
        console.print("[cyan]4.[/cyan] Save and return to main menu")
        console.print("")
        
        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4"], default="4")
        
        if choice == "1":
            if not show_presets_menu(config):
                break
        elif choice == "2":
            configure_individual_systems(config)
        elif choice == "3":
            if Confirm.ask("Reset all settings to defaults?"):
                reset_to_defaults()
                config = get_model_config()
                console.print("[green]✓ Settings reset to defaults[/green]")
                console.input("\nPress Enter to continue...")
        elif choice == "4":
            set_model_config(config)
            console.print("\n[green]✓ Settings saved[/green]")
            break
    
    return config


if __name__ == "__main__":
    # Test the menu
    model_settings_menu()

