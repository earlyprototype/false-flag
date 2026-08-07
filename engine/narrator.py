"""Narrator system for generating atmospheric bridges between turns."""

from typing import List
from random import Random

from models.world import WorldState
from llm.model_config import LLMContext
from llm.parse_health import record_fallback
from llm.prompts import build_narrator_intro_prompt
from llm.router import generate_text

def generate_narrator_bridge(
    world: WorldState,
    transcript: List[str],
    next_inject_title: str,
    rng: Random
) -> str:
    """
    Generate a short atmospheric text bridging the previous turn to the current one.
    
    Args:
        world: Current world state
        transcript: Full game transcript (we'll use the tail)
        next_inject_title: Title of the upcoming inject
        rng: Random number generator
        
    Returns:
        String containing the narrator text (2-3 sentences)
    """
    # Only generate if we have some history
    if not transcript or len(transcript) < 5:
        return ""

    prompt = build_narrator_intro_prompt(world, transcript, next_inject_title)
    
    try:
        # Use a lower temperature for consistent tone, but enough for creativity
        bridge_text = generate_text(
            prompt,
            rng,
            context=LLMContext.NARRATOR,
            system_instruction="You are a master storyteller for a political thriller. Be concise, atmospheric, and serious.",
            temperature=0.7,
            # Backstop only (~3x the 2-3 sentences the prompt asks for);
            # hits are recorded as truncations, never silently absorbed
            max_tokens=300
        )
        bridge_text = bridge_text.strip()
        if not bridge_text:
            # The caller drops an empty bridge silently; record the drop
            record_fallback("narrator", "empty reply")
        return bridge_text
    except Exception:
        # Graceful fallback if LLM fails
        record_fallback("narrator", "exception")
        return "Time passes. The situation develops..."

