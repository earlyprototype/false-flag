from models.world import Metrics


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


