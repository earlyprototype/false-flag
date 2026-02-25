"""Load and parse initial conditions for scenarios.

Provides structured access to scenario setup including characters, forces,
stockpiles, and constraints for use by LLM prompts and game logic.
"""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def load_initial_conditions(scenario_id: str, root_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load initial conditions YAML for a scenario.
    
    Args:
        scenario_id: Scenario identifier (e.g., 'war_game_2025')
        root_path: Optional root path override (for testing)
    
    Returns:
        Dict containing parsed initial conditions, or empty dict if not found
    """
    if root_path is None:
        root_path = Path(__file__).resolve().parents[1]
    
    ic_path = root_path / "data" / "scenarios" / scenario_id / "initial_conditions.yaml"
    
    try:
        if not ic_path.exists():
            print(f"[WARNING] Initial conditions file not found: {ic_path}")
            return {}
        
        raw = ic_path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
        
        if not isinstance(data, dict):
            print(f"[WARNING] Initial conditions is not a dict: {type(data)}")
            return {}
        
        return data
    except Exception as e:
        print(f"[ERROR] Failed to load initial conditions: {e}")
        import traceback
        traceback.print_exc()
        return {}


def get_character_info(initial_conditions: Dict[str, Any], character_id: str) -> Optional[Dict[str, Any]]:
    """Extract character information from initial conditions.
    
    Args:
        initial_conditions: Parsed initial conditions dict
        character_id: Character identifier (e.g., 'chief_defence_staff')
    
    Returns:
        Character dict or None if not found
    """
    characters = initial_conditions.get("characters", {})
    return characters.get(character_id)


def get_all_uk_advisors(initial_conditions: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Get all UK advisor characters (excludes Russian team).
    
    Args:
        initial_conditions: Parsed initial conditions dict
    
    Returns:
        Dict of character_id -> character_info for UK advisors
    """
    characters = initial_conditions.get("characters", {})
    uk_advisors = {}
    
    for char_id, char_info in characters.items():
        # Exclude Russian team characters (they have 'note' field indicating control by injects)
        if isinstance(char_info, dict) and "note" not in char_info:
            uk_advisors[char_id] = char_info
    
    return uk_advisors


def get_constraints(initial_conditions: Dict[str, Any]) -> Dict[str, Any]:
    """Extract constraints section from initial conditions.
    
    Args:
        initial_conditions: Parsed initial conditions dict
    
    Returns:
        Constraints dict with capability, political, legal, time categories
    """
    return initial_conditions.get("constraints", {})


def get_uk_forces(initial_conditions: Dict[str, Any]) -> Dict[str, Any]:
    """Extract UK forces section from initial conditions.
    
    Args:
        initial_conditions: Parsed initial conditions dict
    
    Returns:
        UK forces dict with naval and air categories
    """
    return initial_conditions.get("uk_forces", {})


def get_stockpiles(initial_conditions: Dict[str, Any]) -> Dict[str, Any]:
    """Extract ammunition stockpiles from initial conditions.
    
    Args:
        initial_conditions: Parsed initial conditions dict
    
    Returns:
        Stockpiles dict with ammunition categories and counts
    """
    return initial_conditions.get("stockpiles", {})

