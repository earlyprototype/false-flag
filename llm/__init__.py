"""Provider-agnostic LLM router and drivers.

This package intentionally ships with a deterministic mock driver so that
`--leader llm` mode can operate without external API dependencies while
preserving transcript determinism under a fixed RNG seed.
"""

__all__ = [
    "router",
]


