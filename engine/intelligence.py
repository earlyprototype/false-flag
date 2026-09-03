"""Intelligence briefing system for immersive narrative mode.

Generates intelligence reports from hidden metrics and actor states. The
server visibility projector removes the detailed actor relationship score from
public API responses; the engine retains it for facilitator/internal use.
"""

from typing import List
from random import Random
from models.world import WorldState
from models.narrative_state import NarrativeState

def generate_intelligence_briefing(
    narrative_state: NarrativeState,
    world: WorldState,
    rng: Random,
    detailed: bool = False
) -> List[str]:
    """
    Generate intelligence briefing based on hidden metrics and actor states.
    
    Args:
        narrative_state: Current narrative state with hidden metrics
        world: World state with flags, posture, actor system
        rng: Random number generator for variation
        detailed: If True, include more detail (for /intel command)

    Returns:
        List of plain-text briefing lines. No console markup: this text
        crosses the HTTP API and the browser as-is (ER-068), so styling
        is each front end's job — the CLIs re-apply emphasis via
        cli.formatters.style_intel_line.
    """
    lines = []
    
    # Header
    lines.append("═" * 79)
    lines.append(f"         INTELLIGENCE SUMMARY - Turn {narrative_state.turn}, {narrative_state.game_time}")
    lines.append("         Classification: TOP SECRET - EYES ONLY")
    lines.append("═" * 79)
    lines.append("")
    
    # Economic indicators (maps to domestic stability)
    lines.extend(_generate_economic_indicators(narrative_state, rng))
    lines.append("")
    
    # Diplomatic intelligence (maps to alliance cohesion + actor states)
    lines.extend(_generate_diplomatic_intelligence(narrative_state, world, rng))
    lines.append("")
    
    # Military posture (maps to escalation risk)
    lines.extend(_generate_military_assessment(narrative_state, world, rng))
    lines.append("")
    
    # Media/public sentiment (maps to domestic stability)
    if detailed:
        lines.extend(_generate_media_monitoring(narrative_state, rng))
        lines.append("")
    
    # Bottom line assessment
    assessment = _generate_bottom_line_assessment(narrative_state)
    lines.append(f"ASSESSMENT: {assessment}")
    lines.append("═" * 79)
    
    return lines


def _generate_economic_indicators(narrative_state: NarrativeState, rng: Random) -> List[str]:
    """Generate economic intelligence hints."""
    stability = narrative_state.hidden_metrics.domestic_stability
    escalation = narrative_state.hidden_metrics.escalation_risk
    
    lines = ["ECONOMIC INDICATORS (GCHQ Financial Intelligence):"]
    
    # Stock market
    if stability > 70:
        ftse_change = rng.uniform(-2.0, 0.5)
        lines.append(f"• FTSE 100: {ftse_change:+.1f}% (mild volatility, markets confident)")
    elif stability > 40:
        ftse_change = rng.uniform(-8.0, -3.0)
        lines.append(f"• FTSE 100: {ftse_change:+.1f}% (significant sell-off in defence/energy sectors)")
    else:
        ftse_change = rng.uniform(-15.0, -9.0)
        lines.append(f"• FTSE 100: {ftse_change:+.1f}% (SEVERE - panic selling, circuit breakers triggered)")
    
    # Currency
    if stability > 70:
        lines.append("• Sterling: £1 = $1.27 (stable)")
    elif stability > 40:
        lines.append(f"• Sterling: £1 = $1.18 (-{rng.uniform(2.5, 4.5):.1f}% - flight to safe havens)")
    else:
        lines.append("• Sterling: £1 = $1.09 (CRITICAL - BoE emergency intervention imminent)")
    
    # Russian markets (indicator of escalation)
    if escalation > 70:
        lines.append("• Moscow Exchange: Suspended trading (war footing)")
    elif escalation > 40:
        lines.append(f"• Russian defence stocks: +{rng.uniform(10, 20):.0f}% (mobilization underway)")
    
    # Consumer behavior
    if stability < 40:
        lines.append(f"• UK supermarkets: Panic buying reported in {rng.randint(60, 85)}% of stores")
    
    return lines


def _generate_diplomatic_intelligence(
    narrative_state: NarrativeState, 
    world: WorldState, 
    rng: Random
) -> List[str]:
    """Generate diplomatic SIGINT based on alliance cohesion and actor states."""
    cohesion = narrative_state.hidden_metrics.alliance_cohesion
    
    lines = ["DIPLOMATIC SIGNAL INTELLIGENCE (MI6 Cable Traffic):"]
    
    # Check if actor system is available
    if world.actor_system:
        # Use individual actor states for specific intelligence
        usa = world.actor_system.get_actor("USA")
        fra = world.actor_system.get_actor("FRA")
        deu = world.actor_system.get_actor("DEU")
        pol = world.actor_system.get_actor("POL")
        
        if usa:
            if usa.relationship_uk > 70:
                lines.append(f"• Washington-London hotline: Active coordination ({rng.randint(15, 25)} calls today)")
            elif usa.relationship_uk > 40:
                lines.append("• US NSA to UK Ambassador: \"Need more evidence before commitment\"")
            else:
                lines.append("• Washington-London hotline: Radio silence (ABNORMAL)")
        
        if fra:
            if fra.relationship_uk < 50:
                baseline = rng.randint(250, 400)
                lines.append(f"• Paris-Berlin encrypted comms: {baseline}% above baseline (UNUSUAL)")
                if "secret_russia_backchannel" in fra.hidden_agendas:
                    lines.append("• French Ambassador: Off-diary meeting with Russian counterpart (SIGINT)")
            elif fra.relationship_uk > 60:
                lines.append("• Paris echoing UK messaging on Russian aggression")
        
        if deu:
            if deu.relationship_uk < 50:
                lines.append(f"• German Chancellor's office: Cancelled UK PM call ({rng.randint(2, 4)}x this week)")
            elif deu.relationship_uk > 60:
                lines.append("• Berlin coordinating closely with London")
        
        if pol:
            if pol.relationship_uk > 70:
                lines.append(f"• Polish PM attempted UK PM call x{rng.randint(2, 5)} (eager to coordinate)")
            elif pol.relationship_uk > 50:
                lines.append("• Warsaw: Unqualified support, forces on standby")
    else:
        # Fallback: generic intelligence based on aggregate cohesion
        if cohesion > 70:
            lines.append("• NATO: High coordination, Article 5 readiness confirmed")
            lines.append("• Allied capitals: Unified messaging on Russian aggression")
        elif cohesion > 40:
            lines.append("• NATO: Divisions emerging, some members urge caution")
            lines.append("• Paris-Berlin coordination increasing (UK excluded)")
        else:
            lines.append("• NATO: SEVERE DIVISIONS - emergency session postponed")
            lines.append("• Multiple allies privately distancing from UK position")
    
    # NATO institutional response
    if cohesion > 60:
        lines.append("• NATO Secretary General: \"Unshakeable Article 5 commitment\"")
    elif cohesion > 30:
        lines.append("• NATO Secretary General: \"Extremely concerned by divisions\"")
    else:
        lines.append("• NATO: Emergency session postponed - consensus impossible")
    
    return lines


def _generate_military_assessment(
    narrative_state: NarrativeState,
    world: WorldState,
    rng: Random
) -> List[str]:
    """Generate military intelligence based on escalation risk."""
    escalation = narrative_state.hidden_metrics.escalation_risk
    
    lines = ["MILITARY POSTURE ASSESSMENT (Northwood Joint Ops):"]
    
    # Russian posture
    if escalation > 80:
        lines.append("• Russian Northern Fleet: ATTACK FORMATION - weapons hot")
        lines.append("• Strategic Rocket Forces: Increased alert status (CRITICAL)")
    elif escalation > 50:
        lines.append("• Russian Northern Fleet: Maintaining aggressive posture")
        lines.append(f"• Russian air patrols: {rng.randint(200, 300)}% above baseline")
    else:
        lines.append("• Russian Northern Fleet: Defensive posture, holding position")
    
    # Allied response
    if escalation > 60:
        lines.append(f"• US carrier group: En route UK waters, ETA {rng.randint(18, 36)}hrs")
    else:
        lines.append(f"• US carrier group: Speed reduced, holding {rng.randint(150, 250)}nm from UK waters")
    
    # Specific ally behavior (if actor system available)
    if world.actor_system:
        fra = world.actor_system.get_actor("FRA")
        if fra and fra.relationship_uk < 50:
            lines.append("• French submarine: Departed patrol zone (ABNORMAL)")
    
    # UK readiness
    if escalation > 70:
        lines.append("• UK forces: BIKINI BLACK SPECIAL - combat imminent")
    elif escalation > 40:
        lines.append("• UK forces: Elevated readiness, defensive posture")
    
    return lines


def _generate_media_monitoring(narrative_state: NarrativeState, rng: Random) -> List[str]:
    """Generate media/public sentiment intelligence."""
    stability = narrative_state.hidden_metrics.domestic_stability
    
    lines = ["MEDIA & PUBLIC SENTIMENT (GCHQ Monitoring):"]
    
    if stability > 70:
        lines.append("• BBC/Sky: Calm coverage, experts praising government response")
        lines.append(f"• Social media sentiment: {rng.randint(60, 75)}% supportive of government")
    elif stability > 40:
        lines.append(f"• BBC Question Time: Audience divided, {rng.randint(40, 60)}% critical")
        lines.append("• Social media: Rising panic, misinformation spreading rapidly")
    else:
        lines.append("• Media: Openly questioning government competence")
        lines.append(f"• BBC Question Time: Audience poll {rng.randint(60, 75)}% \"government out of depth\"")
        lines.append("• Social media: Calls for PM resignation trending")
    
    # Russian media (always hostile)
    if stability < 50:
        lines.append("• Russian state TV: \"UK regime collapsing under pressure\"")
    
    return lines


def _generate_bottom_line_assessment(narrative_state: NarrativeState) -> str:
    """Generate bottom-line assessment summary."""
    escalation = narrative_state.hidden_metrics.escalation_risk
    stability = narrative_state.hidden_metrics.domestic_stability
    cohesion = narrative_state.hidden_metrics.alliance_cohesion
    
    # Determine most critical issue
    issues = []
    
    if escalation > 75:
        issues.append("IMMINENT COMBAT")
    elif escalation > 50:
        issues.append("Crisis escalating")
    
    if cohesion < 40:
        issues.append("Allied support CRITICAL")
    elif cohesion < 60:
        issues.append("Allied support uncertain")
    
    if stability < 40:
        issues.append("Domestic crisis developing")
    elif stability < 60:
        issues.append("Domestic pressure mounting")
    
    if not issues:
        return "Situation stable, monitoring ongoing."
    
    assessment = ". ".join(issues) + ". Time-critical decisions required."
    return assessment


def generate_actor_detailed_assessment(
    actor_code: str,
    world: WorldState,
    turn: int
) -> List[str]:
    """Generate detailed intelligence assessment for specific actor (for /intel command)."""
    if not world.actor_system:
        return ["Error: Actor system not initialized"]
    
    actor = world.actor_system.get_actor(actor_code)
    if not actor:
        return [f"Error: No intelligence available for {actor_code}"]
    
    lines = []
    lines.append("═" * 79)
    lines.append(f"         DETAILED ASSESSMENT - {actor.full_name}")
    lines.append(f"         Turn {turn}")
    lines.append("═" * 79)
    lines.append("")
    
    # Relationship trend
    trend_display = {
        "improving": "IMPROVING ↗",
        "stable": "STABLE →",
        "declining": "DECLINING ↘"
    }
    lines.append(f"Relationship Trend: {trend_display.get(actor.trust_trajectory, 'UNKNOWN')}")
    lines.append(f"Current Assessment: {actor.relationship_uk}/100")
    lines.append("")
    
    # Recent indicators
    lines.append("Recent Indicators:")
    
    # Behavioral indicators based on relationship
    if actor.relationship_uk > 70:
        lines.append("• Consistent support in diplomatic channels")
        lines.append(f"• Active intelligence sharing ({actor.intelligence_sharing})")
        lines.append("• Military coordination proceeding smoothly")
    elif actor.relationship_uk > 40:
        lines.append("• Mixed signals in diplomatic communications")
        lines.append(f"• Intelligence sharing: {actor.intelligence_sharing}")
        lines.append("• Some hesitation in public statements")
    else:
        lines.append("• Minimal diplomatic engagement")
        lines.append(f"• Intelligence sharing: {actor.intelligence_sharing} (restrictive)")
        lines.append("• Public statements lack commitment")
    
    # Recent actions
    if actor.recent_actions:
        lines.append("")
        lines.append("Recent Actions:")
        for action in actor.recent_actions:
            lines.append(f"• {action}")
    
    # Assessment
    lines.append("")
    if actor.relationship_uk > 70:
        lines.append("Analyst Assessment: Reliable ally. Can be counted on for support.")
    elif actor.relationship_uk > 50:
        lines.append("Analyst Assessment: Supportive but cautious. Likely to follow major powers.")
    elif actor.relationship_uk > 30:
        lines.append("Analyst Assessment: Unreliable. May undermine UK position diplomatically.")
    else:
        lines.append("Analyst Assessment: ADVERSARIAL. Actively working against UK interests.")
    
    lines.append("")
    lines.append("═" * 79)
    
    return lines
