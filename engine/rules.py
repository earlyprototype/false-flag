"""Engine rules placeholder.

This module exists to align the repository structure with the plan and to
provide a stable import location for Team A to implement rule helpers.

Behaviour: no side effects; safe to import anywhere.
"""

from __future__ import annotations


def get_rulebook_version() -> str:
    """Return a human-readable ruleset version string.

    Team A may evolve this as rules mature; callers should treat it as
    metadata only and not branch logic on it.
    """

    return "0.1"



def deterministic_midpoint(min_value: int, max_value: int) -> int:
    """Return the integer midpoint of [min_value, max_value].

    Deterministic helper for adjudication: floor((min+max)/2).
    Swaps inputs if provided out of order; no randomness involved.
    """

    if min_value > max_value:
        min_value, max_value = max_value, min_value
    return (min_value + max_value) // 2
