"""Offline LLM driver stub for testing without LLM access.

Used when WARGAME_LLM=offline to simulate no model access.
"""

from random import Random


class OfflineDriver:
    """Offline stub: returns minimal responses.

    Used when `WARGAME_LLM=offline` to simulate no model access.
    """

    def generate_text(self, prompt: str, rng: Random) -> str:
        """Return minimal offline response.
        
        Args:
            prompt: Input prompt
            rng: Random number generator
        
        Returns:
            Minimal response indicating offline mode
        """
        _ = (prompt, rng)
        return "[Offline mode: No LLM response available]"




