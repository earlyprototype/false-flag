"""Save and load game state for multi-turn gameplay.

Provides JSON-based persistence for WorldState and game transcript.
"""

import json
from pathlib import Path
from typing import List, Optional, Tuple

from models.world import WorldState
from models.narrative_state import NarrativeState


def save_game(
    world: WorldState,
    transcript: List[str],
    scenario_id: str,
    save_name: str = "autosave",
    root_path: Optional[Path] = None,
    play_mode: str = "immersive",
    narrative_state: Optional[NarrativeState] = None,
    variant: str = "standard"
) -> Path:
    """Save game state and transcript to JSON file.

    Args:
        world: Current world state
        transcript: Full game transcript
        scenario_id: Scenario identifier
        save_name: Save file name (without extension)
        root_path: Optional root path override (for testing)
        play_mode: Gameplay mode (classic/immersive/emergent)
        narrative_state: Optional narrative state to persist
        variant: Scenario variant (standard/fast_start) — needed on load to
            pick the right turn files and stochastic transition point

    Returns:
        Path to saved file
    """
    if root_path is None:
        root_path = Path(__file__).resolve().parents[1]

    saves_dir = root_path / "saves"
    saves_dir.mkdir(exist_ok=True)

    save_path = saves_dir / f"{scenario_id}_{save_name}.json"

    save_data = {
        "scenario_id": scenario_id,
        "world": world.model_dump(),
        "transcript": transcript,
        "play_mode": play_mode,
        "narrative_state": narrative_state.model_dump() if narrative_state else None,
        "variant": variant,
        "version": "2.1"  # 2.1: adds scenario variant
    }

    save_path.write_text(json.dumps(save_data, indent=2), encoding="utf-8")
    return save_path


def read_save_variant(save_path: Path) -> str:
    """Read just the scenario variant from a save file.

    Kept separate from load_game so its return shape stays stable for
    existing callers. Old saves (pre-2.1) default to "standard".
    """
    try:
        save_data = json.loads(Path(save_path).read_text(encoding="utf-8"))
        return save_data.get("variant", "standard")
    except (OSError, json.JSONDecodeError):
        return "standard"


def load_game(save_path: Path) -> Tuple[str, WorldState, List[str], str, Optional[NarrativeState]]:
    """Load game state and transcript from JSON file.
    
    Args:
        save_path: Path to save file
    
    Returns:
        Tuple of (scenario_id, world_state, transcript, play_mode, narrative_state)
    
    Raises:
        FileNotFoundError: If save file doesn't exist
        ValueError: If save file is invalid
    """
    if not save_path.exists():
        raise FileNotFoundError(f"Save file not found: {save_path}")
    
    try:
        raw = save_path.read_text(encoding="utf-8")
        save_data = json.loads(raw)
        
        scenario_id = save_data.get("scenario_id", "unknown")
        world_dict = save_data.get("world", {})
        transcript = save_data.get("transcript", [])
        play_mode = save_data.get("play_mode", "immersive")  # Default for old saves
        narrative_state_dict = save_data.get("narrative_state")
        
        # Reconstruct WorldState from dict
        world = WorldState(**world_dict)
        
        # Reconstruct NarrativeState if present
        narrative_state = None
        if narrative_state_dict:
            narrative_state = NarrativeState(**narrative_state_dict)
        
        return scenario_id, world, transcript, play_mode, narrative_state
    
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        raise ValueError(f"Invalid save file format: {e}")


def list_saves(scenario_id: Optional[str] = None, root_path: Optional[Path] = None) -> List[Path]:
    """List available save files.
    
    Args:
        scenario_id: Optional filter by scenario
        root_path: Optional root path override (for testing)
    
    Returns:
        List of save file paths
    """
    if root_path is None:
        root_path = Path(__file__).resolve().parents[1]
    
    saves_dir = root_path / "saves"
    if not saves_dir.exists():
        return []
    
    if scenario_id:
        pattern = f"{scenario_id}_*.json"
    else:
        pattern = "*.json"
    
    return sorted(saves_dir.glob(pattern))

