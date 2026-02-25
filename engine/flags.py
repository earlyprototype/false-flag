from __future__ import annotations

"""Risk flag mapping for Team A (Day-4).

Maps numeric metrics on the `WorldState` to deterministic boolean flags under
`world.flags`. Thresholds are inclusive at boundary values and derived solely
from metrics; no randomness and no side effects outside the flags dict.
"""

from typing import Dict

from models.world import Metrics, WorldState


def compute_risk_flags(metrics: Metrics) -> Dict[str, bool]:
    """Compute risk flags from metrics using fixed, deterministic thresholds.

    Inclusive thresholds ensure stable toggling at exact boundary values.
    """
    flags: Dict[str, bool] = {}

    # Escalation risk high when risk >= 60
    flags["risk_escalation"] = metrics.escalation_risk >= 60

    # Domestic unrest when stability <= 40
    flags["risk_unrest"] = metrics.domestic_stability <= 40

    # Alliance fragile when cohesion <= 40
    flags["risk_alliance_fragile"] = metrics.alliance_cohesion <= 40

    # Civilian and military losses present when counts > 0
    flags["risk_civilian_harm"] = getattr(metrics, "casualties_civ", 0) > 0
    flags["risk_military_losses"] = metrics.casualties_mil > 0

    return flags


def update_world_flags(world: WorldState) -> None:
    """Recompute and replace `world.flags` based on current metrics."""
    world.flags = compute_risk_flags(world.metrics)











