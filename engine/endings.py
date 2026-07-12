"""Terminal conditions and debrief for classic mode.

Classic mode's selection screen promises "clear thresholds and win
conditions"; this module provides them. Immersive and emergent modes are
open-ended by design and never call into these checks.

Threshold endings can fire on any turn; when the scripted scenario has run
its course (scripted turns plus a short stochastic epilogue), the campaign
is graded on where the player left the crisis.
"""

from typing import Dict, List, Optional

from models.world import WorldState


# Turns of stochastic play after the scripted scenario before the campaign
# is graded (threshold endings can still fire during these turns)
EPILOGUE_TURNS = 4


class Ending:
    """A terminal outcome: identity, verdict, and debrief narrative."""

    def __init__(self, ending_id: str, title: str, verdict: str, narrative: str):
        self.ending_id = ending_id
        self.title = title
        self.verdict = verdict  # "victory" | "partial" | "defeat"
        self.narrative = narrative


def check_ending(world: WorldState, final_turn: int) -> Optional[Ending]:
    """Check whether the campaign has reached a terminal state.

    Args:
        world: Current world state (checked after adjudication)
        final_turn: Turn on which the campaign is graded if no threshold
            ending fired earlier (scripted turns + EPILOGUE_TURNS)

    Returns:
        An Ending, or None if the campaign continues.
    """
    m = world.metrics

    if m.escalation_risk >= 100:
        return Ending(
            "war",
            "THE GUNS OF OCTOBER",
            "defeat",
            "The escalation spiral has passed the point of no return. Russian "
            "and NATO forces are exchanging fire in the North Atlantic, and "
            "the first strikes against the British mainland are under way. "
            "Whatever happens next is no longer a crisis — it is a war, and "
            "history will ask whether it had to happen.",
        )

    if m.domestic_stability <= 0:
        return Ending(
            "collapse",
            "A GOVERNMENT FALLS",
            "defeat",
            "The country has stopped listening. Panic buying, blackouts and "
            "street disorder have outrun every reassurance, and this morning "
            "the Cabinet concluded the Government can no longer command the "
            "confidence of the House. Your resignation is expected by noon. "
            "The crisis will be someone else's to finish.",
        )

    if m.alliance_cohesion <= 0:
        return Ending(
            "isolation",
            "ALONE IN THE STORM",
            "defeat",
            "One by one, the capitals stopped returning calls. NATO's "
            "consultations have collapsed into recrimination, Washington is "
            "publicly 'reviewing its commitments', and Moscow knows it. The "
            "United Kingdom now faces a superpower's coercion campaign "
            "alone — which was the object of the exercise all along.",
        )

    if world.turn >= final_turn:
        # Scenario complete: grade the resolution
        if m.escalation_risk < 50 and m.alliance_cohesion >= 50:
            return Ending(
                "resolution",
                "THE LINE HELD",
                "victory",
                "The submarines are returning north. With the alliance intact "
                "and the escalation contained, Moscow's coercion campaign has "
                "quietly run out of road. There will be inquiries, and the "
                "dead will not come back — but the United Kingdom faced down "
                "a superpower without a war, and NATO is stronger for it.",
            )
        if m.escalation_risk < 70 and m.alliance_cohesion >= 30:
            return Ending(
                "uneasy_peace",
                "AN UNEASY PEACE",
                "partial",
                "The immediate crisis has passed, but nobody is calling it a "
                "victory. The alliance held — barely — and the North Atlantic "
                "remains a more dangerous place than it was a month ago. The "
                "next test will come, and both sides know it.",
            )
        return Ending(
            "weakness",
            "TESTED AND FOUND WANTING",
            "defeat",
            "The shooting never started, but the verdict is in. Allies hedge, "
            "adversaries probe, and the country doubts itself. Moscow set out "
            "to demonstrate that NATO's resolve was hollow — and the record "
            "of these weeks will be taught, for years, as the proof.",
        )

    return None


def build_debrief_lines(
    world: WorldState,
    ending: Ending,
    initial_metrics: Dict[str, int],
    transcript: List[str],
) -> List[str]:
    """Compose the plain-text debrief shown when a campaign ends."""
    m = world.metrics
    lines: List[str] = []
    lines.append("=" * 60)
    lines.append(f"CAMPAIGN OVER — {ending.title}")
    lines.append(f"Verdict: {ending.verdict.upper()}  |  Turns played: {world.turn}")
    lines.append("=" * 60)
    lines.append("")
    lines.append(ending.narrative)
    lines.append("")
    lines.append("FINAL SITUATION (change from start):")

    def delta(name: str, value: int) -> str:
        start = initial_metrics.get(name, value)
        return f"  {name.replace('_', ' ').title():<20} {value:>3}  ({value - start:+d})"

    lines.append(delta("escalation_risk", m.escalation_risk))
    lines.append(delta("domestic_stability", m.domestic_stability))
    lines.append(delta("alliance_cohesion", m.alliance_cohesion))
    lines.append(f"  {'Casualties':<20} {m.casualties_mil} military, {m.casualties_civ} civilian")
    lines.append("")

    # Decision recap from the transcript
    decisions = [
        line.split(":", 1)[1].strip()
        for line in transcript
        if line.startswith("Prime Minister's Decision:")
    ]
    if decisions:
        lines.append("YOUR DECISIONS:")
        for i, decision in enumerate(decisions[-10:], 1):
            lines.append(f"  {i}. {decision}")
        lines.append("")

    return lines
