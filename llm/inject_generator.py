"""Stochastic inject generation for turns beyond podcast content.

Uses LLM to generate plausible next events based on current world state,
informed by realistic scenario patterns from the podcast.
"""

from typing import Any, Dict, List, Optional
from random import Random
from pathlib import Path
import yaml

from models.world import WorldState
from llm.prompts import build_inject_generation_prompt
from llm.router import generate_text
from llm.model_config import LLMContext


def _load_scenario_library(root_path: Path) -> Dict[str, Any]:
    """Load the scenario library for LLM context.
    
    Provides realistic scenario patterns mined from podcast episodes.
    Returns empty dict if file doesn't exist (graceful degradation).
    """
    library_path = root_path / "data" / "scenarios" / "war_game_2025" / "scenario_library.yaml"
    try:
        if library_path.exists():
            return yaml.safe_load(library_path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def generate_inject(
    world: WorldState,
    turn_number: int,
    initial_conditions: Dict[str, Any],
    rng: Random,
    root_path: Optional[Path] = None,
    transcript: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """Generate a plausible inject for the given turn using LLM.
    
    Args:
        world: Current world state
        turn_number: Turn number for which to generate inject
        initial_conditions: Parsed initial conditions
        rng: Random number generator for determinism
        root_path: Optional root path override
        transcript: Optional full game transcript for conversation history
    
    Returns:
        Generated inject dict, or None if generation fails
    """
    if root_path is None:
        root_path = Path(__file__).resolve().parents[1]
    
    # Load scenario library to inform LLM generation
    scenario_library = _load_scenario_library(root_path)
    
    prompt = build_inject_generation_prompt(world, turn_number, initial_conditions, scenario_library, transcript)
    
    try:
        response = generate_text(prompt, rng, context=LLMContext.INJECT_GENERATION)
    except Exception as e:
        print(f"[ERROR] LLM generation failed: {e}")
        return None
    
    if not response or not response.strip():
        print(f"[ERROR] LLM returned empty response for turn {turn_number}")
        return None
    
    # Parse YAML from response
    try:
        # Extract YAML block from markdown code fence if present
        if "```yaml" in response:
            yaml_start = response.find("```yaml") + 7
            yaml_end = response.find("```", yaml_start)
            yaml_text = response[yaml_start:yaml_end].strip()
        elif "```" in response:
            # Generic code fence
            yaml_start = response.find("```") + 3
            yaml_end = response.find("```", yaml_start)
            yaml_text = response[yaml_start:yaml_end].strip()
        else:
            # Assume entire response is YAML
            yaml_text = response.strip()
        
        inject_data = yaml.safe_load(yaml_text)
        
        if not isinstance(inject_data, dict):
            print(f"[ERROR] LLM response was not valid YAML dict for turn {turn_number}")
            print(f"[DEBUG] Response preview: {response[:200]}")
            return None
        
        # Always stamp a deterministic per-turn id so generated injects
        # (e.g. the mock driver's hardcoded id) never collide across turns
        inject_data["id"] = f"turn_{world.turn:03d}_inject"
        
        return inject_data
    
    except (yaml.YAMLError, ValueError, IndexError) as e:
        # Generation failed, return None
        print(f"[ERROR] Failed to parse YAML from LLM response: {e}")
        print(f"[DEBUG] Response preview: {response[:500]}")
        return None

