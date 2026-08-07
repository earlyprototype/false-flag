"""Save and load game state for multi-turn gameplay.

Provides JSON-based persistence for WorldState and game transcript.
"""

import json
import os
from pathlib import Path
from random import Random
from typing import Any, List, Optional, Tuple

from models.world import WorldState
from models.narrative_state import NarrativeState


def _default_root() -> Path:
    """Repository root, overridable via WARGAME_SAVE_ROOT (used by tests so
    they never touch the real saves/ directory)."""
    env = os.environ.get("WARGAME_SAVE_ROOT")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[1]


def encode_rng_state(rng: Random) -> list:
    """JSON-safe encoding of ``rng.getstate()``.

    getstate() returns (version, (int, ...), gauss_next); JSON has no tuples,
    so the shape becomes [version, [int, ...], gauss_next].
    """
    version, internal, gauss_next = rng.getstate()
    return [version, list(internal), gauss_next]


def decode_rng_state(payload) -> Optional[tuple]:
    """Rebuild the tuple ``Random.setstate`` expects from the JSON encoding.

    Returns None for a missing or malformed payload — old saves (pre-2.3)
    simply have no stored position, and the caller keeps its fresh-seeded
    generator, which is exactly the pre-2.3 behaviour.
    """
    try:
        version, internal, gauss_next = payload
        return (version, tuple(internal), gauss_next)
    except (TypeError, ValueError):
        return None



def save_game(
    world: WorldState,
    transcript: List[str],
    scenario_id: str,
    save_name: str = "autosave",
    root_path: Optional[Path] = None,
    play_mode: str = "immersive",
    narrative_state: Optional[NarrativeState] = None,
    variant: str = "standard",
    initial_metrics: Optional[dict] = None,
    rng: Optional[Random] = None,
    seed: Optional[int] = None,
    ending_id: Optional[str] = None,
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
        initial_metrics: Metrics snapshot from the start of the campaign, so
            a resumed game's debrief reports deltas from the true start
        rng: Optional campaign generator; when provided its position is
            stored so a resumed game continues the draw sequence instead of
            replaying spent randomness (ER-037)
        seed: The campaign seed, so a resumed game can report it
        ending_id: The terminal ending, when the campaign has concluded.
            Without this the end-of-campaign autosave resumes as a live
            game - the debrief happens after the autosave is written, so
            the file used to have no way of knowing the campaign was over.

    Returns:
        Path to saved file
    """
    if root_path is None:
        root_path = _default_root()

    saves_dir = root_path / "saves"
    saves_dir.mkdir(parents=True, exist_ok=True)

    save_path = saves_dir / f"{scenario_id}_{save_name}.json"

    save_data = {
        "scenario_id": scenario_id,
        "world": world.model_dump(),
        "transcript": transcript,
        "play_mode": play_mode,
        "narrative_state": narrative_state.model_dump() if narrative_state else None,
        "variant": variant,
        "initial_metrics": initial_metrics,
        "rng_state": encode_rng_state(rng) if rng is not None else None,
        "seed": seed,
        "ending_id": ending_id,
        # 2.1: adds scenario variant; 2.2: adds initial_metrics;
        # 2.3: adds rng_state; 2.4: adds seed + ending_id
        "version": "2.4"
    }

    save_path.write_text(json.dumps(save_data, indent=2), encoding="utf-8")
    return save_path


def read_save_field(save_path: Path, key: str, default: Any = None) -> Any:
    """Read a single top-level field from a save file.

    Kept separate from load_game so its return shape stays stable for
    existing callers. Missing keys (old saves) and unreadable files return
    `default`. A stored null also returns `default` — old versions of this
    tooling wrote explicit nulls for absent optional fields.
    """
    try:
        save_data = json.loads(Path(save_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default
    value = save_data.get(key)
    return default if value is None else value


def read_save_variant(save_path: Path) -> str:
    """Read just the scenario variant from a save file.

    Thin wrapper over read_save_field. Old saves (pre-2.1) default to
    "standard".
    """
    return read_save_field(save_path, "variant", "standard")


def read_rng_state(save_path: Path) -> Optional[tuple]:
    """Read the saved generator position, ready for ``Random.setstate``.

    Same pattern as initial_metrics: a separate field reader, so load_game's
    return shape stays stable for existing callers. Old saves (pre-2.3)
    return None and the caller keeps its fresh-seeded generator.
    """
    return decode_rng_state(read_save_field(save_path, "rng_state"))


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
        root_path = _default_root()
    
    saves_dir = root_path / "saves"
    if not saves_dir.exists():
        return []
    
    if scenario_id:
        pattern = f"{scenario_id}_*.json"
    else:
        pattern = "*.json"
    
    return sorted(saves_dir.glob(pattern))

