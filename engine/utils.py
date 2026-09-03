from typing import Optional

from models.world import Metrics


# Which direction of travel is *good news* for each headline metric.
#
# The five metrics do not share a polarity: escalation risk and casualties
# rising is bad, domestic stability and alliance cohesion rising is good.
# Colouring every "+N" the same way tells the player the opposite of the truth
# for half the board, so both front ends resolve polarity through here — the
# terminal (``cli/display_utils``, ``cli/rich_ui``) and the browser
# (``docs/py/bridge.py``) must never disagree about what is good news.
METRIC_RISE_IS_GOOD = {
    "escalation_risk": False,
    "casualties_mil": False,
    "casualties_civ": False,
    "domestic_stability": True,
    "alliance_cohesion": True,
}


def delta_is_good(metric: str, delta: int) -> Optional[bool]:
    """Is ``delta`` on ``metric`` good news, bad news, or neither?

    Returns ``True`` for good, ``False`` for bad, and ``None`` when no claim
    can be made — a zero move, or a metric with no declared polarity (the
    adjudicator may emit keys beyond the headline five, and inventing a
    polarity for those would be a guess shown to the player as fact).
    """
    if not delta:
        return None
    rise_is_good = METRIC_RISE_IS_GOOD.get(str(metric))
    if rise_is_good is None:
        return None
    return (delta > 0) == rise_is_good


def strip_effect_boxes(lines: list) -> list:
    """Remove numeric effect boxes without changing the source transcript."""
    out = []
    drop_bottom_border = False
    for line in lines:
        stripped = line.strip()
        if "Effect: " in stripped:
            if out and out[-1].strip() and set(out[-1].strip()) <= set("┌─┐"):
                out.pop()
            drop_bottom_border = True
            continue
        if drop_bottom_border:
            drop_bottom_border = False
            if stripped and set(stripped) <= set("└─┘"):
                continue
        out.append(line)
    return out


def clamp(value: int, low: int = 0, high: int = 100) -> int:
    if value < low:
        return low
    if value > high:
        return high
    return value


def clamp_non_negative(value: int) -> int:
    return value if value >= 0 else 0


def clamp_metrics(metrics: Metrics, minimum: int = 0, maximum: int = 100) -> Metrics:
    metrics.escalation_risk = clamp(metrics.escalation_risk, minimum, maximum)
    metrics.domestic_stability = clamp(metrics.domestic_stability, minimum, maximum)
    metrics.alliance_cohesion = clamp(metrics.alliance_cohesion, minimum, maximum)
    metrics.casualties_civ = clamp_non_negative(metrics.casualties_civ)
    metrics.casualties_mil = clamp_non_negative(metrics.casualties_mil)
    return metrics

