"""Intelligence briefing system for immersive narrative mode.

Generates realistic intelligence reports from hidden metrics and actor states,
allowing players to infer situation without seeing raw numbers.
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
        List of formatted briefing lines (with Rich tags)
    """
    lines = []
    
    # Header
    lines.append("═" * 79)
    lines.append(f"         [bold]INTELLIGENCE SUMMARY[/bold] - Turn {narrative_state.turn}, {narrative_state.game_time}")
    lines.append("         Classification: [bold red]TOP SECRET - EYES ONLY[/bold red]")
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
    lines.append(f"[bold]ASSESSMENT:[/bold] {assessment}")
    lines.append("═" * 79)
    
    return lines


def _generate_economic_indicators(narrative_state: NarrativeState, rng: Random) -> List[str]:
    """Generate economic intelligence hints."""
    stability = narrative_state.hidden_metrics.domestic_stability
    escalation = narrative_state.hidden_metrics.escalation_risk
    
    lines = ["[bold cyan]ECONOMIC INDICATORS[/bold cyan] (GCHQ Financial Intelligence):"]
    
    # Stock market
    if stability > 70:
        ftse_change = rng.uniform(-2.0, 0.5)
        lines.append(f"• FTSE 100: [green]{ftse_change:+.1f}%[/green] (mild volatility, markets confident)")
    elif stability > 40:
        ftse_change = rng.uniform(-8.0, -3.0)
        lines.append(f"• FTSE 100: [red]{ftse_change:+.1f}%[/red] (significant sell-off in defence/energy sectors)")
    else:
        ftse_change = rng.uniform(-15.0, -9.0)
        lines.append(f"• FTSE 100: [bold red]{ftse_change:+.1f}% (SEVERE - panic selling, circuit breakers triggered)[/bold red]")
    
    # Currency
    if stability > 70:
        lines.append("• Sterling: £1 = $1.27 ([green]stable[/green])")
    elif stability > 40:
        lines.append(f"• Sterling: £1 = $1.18 ([yellow]-{rng.uniform(2.5, 4.5):.1f}%[/yellow] - flight to safe havens)")
    else:
        lines.append("• Sterling: £1 = $1.09 ([bold red]CRITICAL - BoE emergency intervention imminent[/bold red])")
    
    # Russian markets (indicator of escalation)
    if escalation > 70:
        lines.append("• Moscow Exchange: [bold red]Suspended trading (war footing)[/bold red]")
    elif escalation > 40:
        lines.append(f"• Russian defence stocks: [red]+{rng.uniform(10, 20):.0f}% (mobilization underway)[/red]")
    
    # Consumer behavior
    if stability < 40:
        lines.append(f"• UK supermarkets: [yellow]Panic buying reported in {rng.randint(60, 85)}% of stores[/yellow]")
    
    return lines


def _generate_diplomatic_intelligence(
    narrative_state: NarrativeState, 
    world: WorldState, 
    rng: Random
) -> List[str]:
    """Generate diplomatic SIGINT based on alliance cohesion and actor states."""
    cohesion = narrative_state.hidden_metrics.alliance_cohesion
    
    lines = ["[bold cyan]DIPLOMATIC SIGNAL INTELLIGENCE[/bold cyan] (MI6 Cable Traffic):"]
    
    # Check if actor system is available
    if world.actor_system:
        # Use individual actor states for specific intelligence
        usa = world.actor_system.get_actor("USA")
        fra = world.actor_system.get_actor("FRA")
        deu = world.actor_system.get_actor("DEU")
        pol = world.actor_system.get_actor("POL")
        
        if usa:
            if usa.relationship_uk > 70:
                lines.append(f"• Washington-London hotline: [green]Active coordination ({rng.randint(15, 25)} calls today)[/green]")
            elif usa.relationship_uk > 40:
                lines.append("• US NSA to UK Ambassador: \"Need more evidence before commitment\"")
            else:
                lines.append("• Washington-London hotline: [red]Radio silence (ABNORMAL)[/red]")
        
        if fra:
            if fra.relationship_uk < 50:
                baseline = rng.randint(250, 400)
                lines.append(f"• Paris-Berlin encrypted comms: [yellow]{baseline}% above baseline (UNUSUAL)[/yellow]")
                if "secret_russia_backchannel" in fra.hidden_agendas:
                    lines.append("• French Ambassador: [bold red]Off-diary meeting with Russian counterpart (SIGINT)[/bold red]")
            elif fra.relationship_uk > 60:
                lines.append("• Paris echoing UK messaging on Russian aggression")
        
        if deu:
            if deu.relationship_uk < 50:
                lines.append(f"• German Chancellor's office: [yellow]Cancelled UK PM call ({rng.randint(2, 4)}x this week)[/yellow]")
            elif deu.relationship_uk > 60:
                lines.append("• Berlin coordinating closely with London")
        
        if pol:
            if pol.relationship_uk > 70:
                lines.append(f"• Polish PM attempted UK PM call x{rng.randint(2, 5)} ([green]eager to coordinate[/green])")
            elif pol.relationship_uk > 50:
                lines.append("• Warsaw: Unqualified support, forces on standby")
    else:
        # Fallback: generic intelligence based on aggregate cohesion
        if cohesion > 70:
            lines.append("• NATO: [green]High coordination, Article 5 readiness confirmed[/green]")
            lines.append("• Allied capitals: Unified messaging on Russian aggression")
        elif cohesion > 40:
            lines.append("• NATO: [yellow]Divisions emerging, some members urge caution[/yellow]")
            lines.append("• Paris-Berlin coordination increasing (UK excluded)")
        else:
            lines.append("• NATO: [bold red]SEVERE DIVISIONS - emergency session postponed[/bold red]")
            lines.append("• Multiple allies privately distancing from UK position")
    
    # NATO institutional response
    if cohesion > 60:
        lines.append("• NATO Secretary General: \"Unshakeable Article 5 commitment\"")
    elif cohesion > 30:
        lines.append("• NATO Secretary General: \"Extremely concerned by divisions\"")
    else:
        lines.append("• NATO: [red]Emergency session postponed - consensus impossible[/red]")
    
    return lines


def _generate_military_assessment(
    narrative_state: NarrativeState,
    world: WorldState,
    rng: Random
) -> List[str]:
    """Generate military intelligence based on escalation risk."""
    escalation = narrative_state.hidden_metrics.escalation_risk
    
    lines = ["[bold cyan]MILITARY POSTURE ASSESSMENT[/bold cyan] (Northwood Joint Ops):"]
    
    # Russian posture
    if escalation > 80:
        lines.append("• Russian Northern Fleet: [bold red]ATTACK FORMATION - weapons hot[/bold red]")
        lines.append("• Strategic Rocket Forces: [bold red]Increased alert status (CRITICAL)[/bold red]")
    elif escalation > 50:
        lines.append("• Russian Northern Fleet: [red]Maintaining aggressive posture[/red]")
        lines.append(f"• Russian air patrols: {rng.randint(200, 300)}% above baseline")
    else:
        lines.append("• Russian Northern Fleet: Defensive posture, holding position")
    
    # Allied response
    if escalation > 60:
        lines.append(f"• US carrier group: [green]En route UK waters, ETA {rng.randint(18, 36)}hrs[/green]")
    else:
        lines.append(f"• US carrier group: Speed reduced, holding {rng.randint(150, 250)}nm from UK waters")
    
    # Specific ally behavior (if actor system available)
    if world.actor_system:
        fra = world.actor_system.get_actor("FRA")
        if fra and fra.relationship_uk < 50:
            lines.append("• French submarine: [yellow]Departed patrol zone (ABNORMAL)[/yellow]")
    
    # UK readiness
    if escalation > 70:
        lines.append("• UK forces: [bold red]BIKINI BLACK SPECIAL - combat imminent[/bold red]")
    elif escalation > 40:
        lines.append("• UK forces: Elevated readiness, defensive posture")
    
    return lines


def _generate_media_monitoring(narrative_state: NarrativeState, rng: Random) -> List[str]:
    """Generate media/public sentiment intelligence."""
    stability = narrative_state.hidden_metrics.domestic_stability
    
    lines = ["[bold cyan]MEDIA & PUBLIC SENTIMENT[/bold cyan] (GCHQ Monitoring):"]
    
    if stability > 70:
        lines.append("• BBC/Sky: Calm coverage, experts praising government response")
        lines.append(f"• Social media sentiment: [green]{rng.randint(60, 75)}% supportive[/green] of government")
    elif stability > 40:
        lines.append(f"• BBC Question Time: Audience divided, [yellow]{rng.randint(40, 60)}% critical[/yellow]")
        lines.append("• Social media: Rising panic, misinformation spreading rapidly")
    else:
        lines.append("• Media: [red]Openly questioning government competence[/red]")
        lines.append(f"• BBC Question Time: Audience poll {rng.randint(60, 75)}% \"government out of depth\"")
        lines.append("• Social media: [bold red]Calls for PM resignation trending[/bold red]")
    
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
        issues.append("[bold red]IMMINENT COMBAT[/bold red]")
    elif escalation > 50:
        issues.append("[red]Crisis escalating[/red]")
    
    if cohesion < 40:
        issues.append("[red]Allied support CRITICAL[/red]")
    elif cohesion < 60:
        issues.append("[yellow]Allied support uncertain[/yellow]")
    
    if stability < 40:
        issues.append("[red]Domestic crisis developing[/red]")
    elif stability < 60:
        issues.append("[yellow]Domestic pressure mounting[/yellow]")
    
    if not issues:
        return "[green]Situation stable, monitoring ongoing.[/green]"
    
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
    lines.append(f"         [bold]DETAILED ASSESSMENT - {actor.full_name}[/bold]")
    lines.append(f"         Turn {turn}")
    lines.append("═" * 79)
    lines.append("")
    
    # Relationship trend
    trend_display = {
        "improving": "[green]IMPROVING ↗[/green]",
        "stable": "[yellow]STABLE →[/yellow]",
        "declining": "[red]DECLINING ↘[/red]"
    }
    lines.append(f"Relationship Trend: {trend_display.get(actor.trust_trajectory, 'UNKNOWN')}")
    lines.append(f"Current Assessment: {actor.relationship_uk}/100")
    lines.append("")
    
    # Recent indicators
    lines.append("[bold]Recent Indicators:[/bold]")
    
    # Behavioral indicators based on relationship
    if actor.relationship_uk > 70:
        lines.append("• [green]Consistent support in diplomatic channels[/green]")
        lines.append(f"• Active intelligence sharing ({actor.intelligence_sharing})")
        lines.append("• Military coordination proceeding smoothly")
    elif actor.relationship_uk > 40:
        lines.append("• [yellow]Mixed signals in diplomatic communications[/yellow]")
        lines.append(f"• Intelligence sharing: {actor.intelligence_sharing}")
        lines.append("• Some hesitation in public statements")
    else:
        lines.append("• [red]Minimal diplomatic engagement[/red]")
        lines.append(f"• Intelligence sharing: {actor.intelligence_sharing} (restrictive)")
        lines.append("• Public statements lack commitment")
    
    # Recent actions
    if actor.recent_actions:
        lines.append("")
        lines.append("[bold]Recent Actions:[/bold]")
        for action in actor.recent_actions:
            lines.append(f"• {action}")
    
    # Assessment
    lines.append("")
    if actor.relationship_uk > 70:
        lines.append("Analyst Assessment: [green]Reliable ally. Can be counted on for support.[/green]")
    elif actor.relationship_uk > 50:
        lines.append("Analyst Assessment: [yellow]Supportive but cautious. Likely to follow major powers.[/yellow]")
    elif actor.relationship_uk > 30:
        lines.append("Analyst Assessment: [red]Unreliable. May undermine UK position diplomatically.[/red]")
    else:
        lines.append("Analyst Assessment: [bold red]ADVERSARIAL. Actively working against UK interests.[/bold red]")
    
    lines.append("")
    lines.append("═" * 79)
    
    return lines
