"""Offline LLM driver stub for testing without LLM access.

Used when WARGAME_LLM=offline to simulate no model access.
"""

from random import Random


class OfflineDriver:
    """Offline stub: returns minimal responses.

    Used when `WARGAME_LLM=offline` to simulate no model access.
    """

    def generate_text(self, prompt: str, rng: Random, **kwargs) -> str:
        """Return minimal offline response.

        Args:
            prompt: Input prompt
            rng: Random number generator
            **kwargs: Generation options (system_instruction, temperature,
                max_tokens) accepted and ignored, so the router forwards
                uniformly to every driver

        Returns:
            Minimal response indicating offline mode
        """
        _ = (prompt, rng, kwargs)
        return "[Offline mode: No LLM response available]"




