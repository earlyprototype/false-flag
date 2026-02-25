"""LLM driver protocol for text generation.

Defines the interface that all LLM drivers must implement.
"""

from typing import Protocol
from random import Random


class LlmDriver(Protocol):
    """Protocol for LLM drivers that generate text responses.
    
    All drivers must implement generate_text method for conversational system.
    """
    
    def generate_text(self, prompt: str, rng: Random) -> str:
        """Generate text response from prompt.
        
        Drivers must be deterministic under a fixed RNG seed; external API
        variance should be gated behind caching in later phases.
        
        Args:
            prompt: Input prompt text
            rng: Random number generator for determinism
        
        Returns:
            Generated text response
        """


