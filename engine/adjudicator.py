"""Adjudication logic for Team A.

Applies advisor-selected action effects to the world deterministically using
midpoints of declared effect ranges.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
from random import Random

from models.world import WorldState
from agents.advisors import AdvisorProposal, EffectRange
from engine.rules import deterministic_midpoint
from engine.utils import clamp, clamp_metrics


def adjudicate_actions(
    world: WorldState, actions: List[AdvisorProposal], rng: Random | None = None
) -> List[str]:
    """Apply effects from chosen actions to the world deterministically.

    Returns transcript lines describing applied (or skipped) effects.
    Determinism is guaranteed by midpoint selection; ``rng`` is accepted for
    interface symmetry but is not used.
    """

    _ = rng  # not used; interface placeholder for future stochastic rules

    transcript: List[str] = []

    if not actions:
        return transcript

    for action in actions:
        # If no effects, emit a lightweight note and continue
        if not action.expected_effects:
            transcript.append(f"Adjudicated: {action.action_id} -> no effects")
            continue

        for eff in action.expected_effects:
            try:
                if not isinstance(eff, EffectRange):
                    transcript.append(
                        f"Skipped effect: invalid spec for action '{action.action_id}'"
                    )
                    continue

                metric_name = eff.metric
                delta_value = deterministic_midpoint(eff.delta_min, eff.delta_max)

                # Apply to world metric if present
                if hasattr(world.metrics, metric_name):
                    current = getattr(world.metrics, metric_name)
                    if isinstance(current, int):
                        updated = clamp(current + delta_value)
                        setattr(world.metrics, metric_name, updated)
                        clamp_metrics(world.metrics)
                        final_val = getattr(world.metrics, metric_name)
                        transcript.append(
                            f"Adjudicated: {action.action_id} -> {metric_name} {delta_value:+d} (-> {final_val})"
                        )
                    else:
                        transcript.append(
                            f"Skipped effect: non-integer metric '{metric_name}' for action '{action.action_id}'"
                        )
                else:
                    transcript.append(
                        f"Skipped effect: unknown metric '{metric_name}' for action '{action.action_id}'"
                    )
            except Exception:
                transcript.append(
                    f"Skipped effect: error applying effect for action '{action.action_id}'"
                )

    return transcript


def adjudicate_decisions(world: Dict[str, Any], actions: List[Dict[str, Any]], rng: Any) -> Dict[str, Any]:
    """Backward-compatible no-op wrapper retained for external imports.

    Prefer using ``adjudicate_actions`` with typed models.
    """

    _ = (actions, rng)
    return world


