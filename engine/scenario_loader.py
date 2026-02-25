"""Scenario configuration loader for variant gameplay modes."""

from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml

from models.narrative import NarrativeConfig


def load_narrative_configs(scenario_id: str, root_path: Optional[Path] = None) -> List[NarrativeConfig]:
    """Load the narrative configurations from narratives.yaml.

    Args:
        scenario_id: Scenario identifier (e.g., 'war_game_2025')
        root_path: Optional root path override

    Returns:
        A list of NarrativeConfig objects.
    """
    if root_path is None:
        root_path = Path(__file__).parent.parent
    
    narrative_path = root_path / "data" / "scenarios" / scenario_id / "narratives.yaml"
    
    if not narrative_path.exists():
        return []
        
    with open(narrative_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    narrative_list = data.get("narratives", [])
    
    # Use Pydantic to parse and validate the raw dicts into NarrativeConfig objects
    return [NarrativeConfig(**n) for n in narrative_list]


def load_scenario_registry(scenario_id: str, root_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the scenario registry file.
    
    Args:
        scenario_id: Scenario identifier (e.g., 'war_game_2025')
        root_path: Optional root path override
    
    Returns:
        Dictionary of scenario variants
    """
    if root_path is None:
        root_path = Path(__file__).parent.parent
    
    registry_path = root_path / "data" / "scenarios" / scenario_id / "scenarios.yaml"
    
    if not registry_path.exists():
        # Fallback: return default standard scenario
        return {
            "scenarios": {
                "standard": {
                    "name": "Standard Campaign",
                    "description": "Default scenario",
                    "scripted_turns": 6,
                    "turn_prefix": "turn_",
                    "turn_suffix": "",
                    "stochastic_from": 7
                }
            }
        }
    
    with open(registry_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_scenario_config(scenario_id: str, variant: str = "standard", 
                       root_path: Optional[Path] = None) -> Dict[str, Any]:
    """Get configuration for a specific scenario variant.
    
    Args:
        scenario_id: Scenario identifier (e.g., 'war_game_2025')
        variant: Variant name (e.g., 'standard', 'fast_start')
        root_path: Optional root path override
    
    Returns:
        Configuration dictionary for the variant
    """
    registry = load_scenario_registry(scenario_id, root_path)
    
    if variant not in registry.get("scenarios", {}):
        # Fallback to standard
        variant = "standard"
    
    config = registry["scenarios"][variant]
    
    # Add computed fields
    config["variant"] = variant
    config["scenario_id"] = scenario_id
    
    return config


def get_turn_filename(turn_number: int, config: Dict[str, Any]) -> str:
    """Generate the turn filename based on scenario configuration.
    
    Args:
        turn_number: Turn number (1-indexed)
        config: Scenario configuration from get_scenario_config()
    
    Returns:
        Filename (e.g., 'turn_001.yaml' or 'turn_001_fast.yaml')
    """
    prefix = config.get("turn_prefix", "turn_")
    suffix = config.get("turn_suffix", "")
    
    return f"{prefix}{turn_number:03d}{suffix}.yaml"


def list_available_scenarios(scenario_id: str, root_path: Optional[Path] = None) -> list:
    """List all available scenario variants with their metadata.
    
    Args:
        scenario_id: Scenario identifier
        root_path: Optional root path override
    
    Returns:
        List of tuples: (variant_key, variant_config)
    """
    registry = load_scenario_registry(scenario_id, root_path)
    scenarios = registry.get("scenarios", {})
    
    return [(key, config) for key, config in scenarios.items()]


def list_all_scenarios(root_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Scan data/scenarios/ for available scenarios.
    
    Returns:
        List of dicts with scenario metadata (id, name, description).
    """
    if root_path is None:
        root_path = Path(__file__).parent.parent
    
    scenarios_dir = root_path / "data" / "scenarios"
    if not scenarios_dir.exists():
        return []
    
    results = []
    for path in scenarios_dir.iterdir():
        if path.is_dir():
            # Load registry to get details
            registry = load_scenario_registry(path.name, root_path)
            
            scenario_id = path.name
            name = scenario_id.replace("_", " ").title()
            description = "A crisis simulation scenario."
            
            # Use standard variant as representative
            if "scenarios" in registry and "standard" in registry["scenarios"]:
                std = registry["scenarios"]["standard"]
                name = std.get("name", name)
                description = std.get("description", description)
            
            results.append({
                "id": scenario_id,
                "name": name,
                "description": description,
                "variants": list(registry.get("scenarios", {}).keys())
            })
            
    return results
