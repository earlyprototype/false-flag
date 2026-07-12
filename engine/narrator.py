"""Narrator system for generating atmospheric bridges between turns."""

from typing import List
from random import Random

from models.world import WorldState
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
            system_instruction="You are a master storyteller for a political thriller. Be concise, atmospheric, and serious.",
            temperature=0.7,
            max_tokens=150
        )
        return bridge_text.strip()
    except Exception:
        # Graceful fallback if LLM fails
        return "Time passes. The situation develops..."

