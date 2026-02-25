from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from models.world import WorldState


def load_events(path: str) -> List[Dict[str, Any]]:
    """Legacy function: load all events from a single file.
    
    Deprecated in favour of episode-based loading.
    """
    events_path = Path(path)
    try:
        if not events_path.exists():
            return []
        raw = events_path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
        if not isinstance(data, list):
            return []
        return data
    except Exception:
        return []


def match_events(world: WorldState, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Legacy function: match events by scene number.
    
    Deprecated in favour of turn-based inject loading.
    """
    matched: List[Dict[str, Any]] = []
    for event in events:
        when = event.get("when", {})
        scene_eq = when.get("scene_eq")
        if scene_eq == world.scene:
            matched.append(event)
    return matched


def load_inject_for_turn(scenario_id: str, turn_number: int, root_path: Optional[Path] = None,
                         turn_filename: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Load inject for a specific turn from episode files.
    
    Searches for episodes/turn_NNN.yaml (or custom filename) in the scenario directory.
    Returns None if file doesn't exist (caller can decide whether to generate stochastically).
    
    Args:
        scenario_id: Scenario identifier (e.g., 'war_game_2025')
        turn_number: Turn number (1-indexed)
        root_path: Optional root path override (for testing)
        turn_filename: Optional custom filename (for scenario variants)
    
    Returns:
        Inject dict or None if file doesn't exist
    """
    if root_path is None:
        root_path = Path(__file__).resolve().parents[1]
    
    # Use custom filename if provided, otherwise default format
    if turn_filename is None:
        turn_filename = f"turn_{turn_number:03d}.yaml"
    
    inject_path = root_path / "data" / "scenarios" / scenario_id / "episodes" / turn_filename
    
    try:
        if not inject_path.exists():
            return None
        
        raw = inject_path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
        
        # Inject file should contain a single inject dict
        if not isinstance(data, dict):
            return None
        
        return data
    except Exception:
        return None



