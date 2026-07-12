"""
Narrative State System
======================

Separates hidden metrics (LLM guidance) from player presentation (vibes/narrative).
Supports multiple gameplay modes with different visibility levels.
"""

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from models.world import Metrics


PlayMode = Literal["classic", "immersive", "emergent"]


class VibeLevel(BaseModel):
    """Visual representation of a metric without showing raw numbers"""
    name: str
    level: int = Field(ge=0, le=5, description="0-5 scale for visual display")
    trend: Literal["rising", "falling", "stable"] = "stable"
    descriptor: str = ""  # e.g., "CRITICAL", "MODERATE", "STABLE"
    
    def to_visual(self) -> str:
        """Convert to visual representation"""
        filled = "🔴" * self.level
        empty = "⚪" * (5 - self.level)
        return f"{filled}{empty}"
    
    def to_string(self) -> str:
        """Full display string"""
        trend_arrow = {"rising": "↗", "falling": "↘", "stable": "→"}[self.trend]
        return f"{self.name:<20} {self.to_visual()} {self.descriptor} {trend_arrow}"


class CharacterAttitude(BaseModel):
    """Tracks character's attitude toward player"""
    character_id: str
    name: str
    trust: int = Field(ge=0, le=100, description="Hidden trust metric")
    relationship: Literal["allied", "neutral", "hostile", "unknown"] = "neutral"
    last_interaction: Optional[str] = None
    stance_summary: str = ""


class NarrativeState(BaseModel):
    """
    Narrative-focused game state with hidden metrics.
    
    Hidden metrics guide LLM behavior and trigger events.
    Player sees vibes, character attitudes, and narrative summaries.
    """
    
    # === HIDDEN METRICS (LLM guidance only) ===
    hidden_metrics: Metrics
    
    # Track previous turn for trend calculation
    previous_metrics: Optional[Metrics] = None
    
    # === PLAYER-VISIBLE STATE ===
    
    # Narrative summary of current situation
    situation_summary: str = ""
    
    # Recent dramatic events
    recent_events: List[str] = Field(default_factory=list)
    
    # Character attitudes and relationships
    characters: Dict[str, CharacterAttitude] = Field(default_factory=dict)
    
    # Active crisis indicators
    active_crises: List[str] = Field(default_factory=list)
    
    # Time/turn info
    turn: int = 1
    game_time: str = ""
    
    # Gameplay mode
    play_mode: PlayMode = "immersive"
    
    # === CONFIGURATION ===
    
    class Config:
        # Allow access to hidden metrics via property
        arbitrary_types_allowed = True
    
    def __init__(self, **data):
        super().__init__(**data)
        # Initialize previous metrics
        if self.previous_metrics is None:
            self.previous_metrics = self.hidden_metrics.copy()
    
    # === HIDDEN METRIC ACCESS (for engine/LLM) ===
    
    def update_hidden_metrics(self, updates: Dict[str, int]):
        """Update hidden metrics and track for trend calculation"""
        # Store previous state
        self.previous_metrics = self.hidden_metrics.copy()
        
        # Apply updates
        for metric, value in updates.items():
            if hasattr(self.hidden_metrics, metric):
                setattr(self.hidden_metrics, metric, value)
    
    # === VIBE CALCULATION ===
    
    def calculate_vibe(self, metric_name: str, value: int, reverse: bool = False, attr_name: Optional[str] = None) -> VibeLevel:
        """
        Convert raw metric to vibe level.

        Args:
            metric_name: Display name
            value: Raw metric value (0-100)
            reverse: If True, higher value = lower vibe (e.g., escalation risk)
            attr_name: Metrics attribute backing this vibe (for trend lookup)
        """
        # Calculate level (0-5)
        if reverse:
            # High value = high danger = more red dots
            if value >= 85:
                level, descriptor = 5, "CRITICAL"
            elif value >= 70:
                level, descriptor = 4, "SEVERE"
            elif value >= 50:
                level, descriptor = 3, "ELEVATED"
            elif value >= 30:
                level, descriptor = 2, "MODERATE"
            elif value >= 15:
                level, descriptor = 1, "LOW"
            else:
                level, descriptor = 0, "MINIMAL"
        else:
            # High value = good = fewer red dots
            if value >= 70:
                level, descriptor = 0, "STRONG"
            elif value >= 55:
                level, descriptor = 1, "STABLE"
            elif value >= 40:
                level, descriptor = 2, "WAVERING"
            elif value >= 25:
                level, descriptor = 3, "WEAK"
            elif value >= 15:
                level, descriptor = 4, "FRAGILE"
            else:
                level, descriptor = 5, "CRITICAL"
        
        # Calculate trend. The arrow follows the direction of the displayed
        # quantity itself (Crisis Intensity rises when escalation_risk rises),
        # so `reverse` plays no part here — it only affects the dot colouring.
        trend = "stable"
        if self.previous_metrics and attr_name:
            prev_value = getattr(self.previous_metrics, attr_name, value)
            if value > prev_value + 3:
                trend = "rising"
            elif value < prev_value - 3:
                trend = "falling"
        
        return VibeLevel(
            name=metric_name,
            level=level,
            trend=trend,
            descriptor=descriptor
        )
    
    def get_situation_vibes(self) -> List[VibeLevel]:
        """Get vibe display for all key metrics"""
        m = self.hidden_metrics
        
        return [
            self.calculate_vibe("Crisis Intensity", m.escalation_risk, reverse=True, attr_name="escalation_risk"),
            self.calculate_vibe("Allied Unity", m.alliance_cohesion, reverse=False, attr_name="alliance_cohesion"),
            self.calculate_vibe("Domestic Support", m.domestic_stability, reverse=False, attr_name="domestic_stability"),
        ]
    
    # === DISPLAY METHODS ===
    
    def display_for_mode(self, mode: Optional[PlayMode] = None) -> List[str]:
        """
        Generate display appropriate for gameplay mode.
        
        Args:
            mode: Override current play_mode
        
        Returns:
            List of display lines
        """
        mode = mode or self.play_mode
        lines = []
        
        if mode == "classic":
            # Traditional: show raw numbers
            lines.append("═══ METRICS ═══")
            lines.append(f"Escalation Risk:      {self.hidden_metrics.escalation_risk}/100")
            lines.append(f"Domestic Stability:   {self.hidden_metrics.domestic_stability}/100")
            lines.append(f"Alliance Cohesion:    {self.hidden_metrics.alliance_cohesion}/100")
            
        elif mode == "immersive":
            # Immersive: vibes + narrative
            lines.append("═══ SITUATION ASSESSMENT ═══")
            for vibe in self.get_situation_vibes():
                lines.append(vibe.to_string())
            
            if self.active_crises:
                lines.append("")
                lines.append("Active Crises:")
                for crisis in self.active_crises:
                    lines.append(f"  • {crisis}")
        
        elif mode == "emergent":
            # Emergent: narrative only, minimal structure
            if self.situation_summary:
                lines.append(self.situation_summary)
        
        return lines
    
    # === LLM CONTEXT GENERATION ===
    
    def to_llm_context(self) -> str:
        """
        Generate context string for LLM with hidden metrics.
        
        This gives the LLM numerical guidance without showing player.
        """
        m = self.hidden_metrics
        
        context = f"""
Current Situation Metrics (hidden from player):
- Escalation Risk: {m.escalation_risk}/100 ({"CRITICAL" if m.escalation_risk >= 85 else "HIGH" if m.escalation_risk >= 70 else "MODERATE"})
- Alliance Cohesion: {m.alliance_cohesion}/100 ({"STRONG" if m.alliance_cohesion >= 70 else "MODERATE" if m.alliance_cohesion >= 40 else "WEAK"})
- Domestic Stability: {m.domestic_stability}/100 ({"STABLE" if m.domestic_stability >= 70 else "WAVERING" if m.domestic_stability >= 40 else "FRAGILE"})
- Casualties: {m.casualties_mil} military, {m.casualties_civ} civilian

Recent Events:
{chr(10).join(f"- {event}" for event in self.recent_events[-3:])}

Active Crises:
{chr(10).join(f"- {crisis}" for crisis in self.active_crises)}

Character Relationships:
{chr(10).join(f"- {char.name}: {char.relationship.upper()} (trust: {char.trust}/100)" for char in self.characters.values())}

Game Time: {self.game_time} (Turn {self.turn})
"""
        return context.strip()
    
    # === CHARACTER MANAGEMENT ===
    
    def update_character_attitude(self, character_id: str, trust_delta: int = 0, 
                                   relationship: Optional[str] = None,
                                   stance_summary: Optional[str] = None):
        """Update character's attitude based on player actions"""
        if character_id not in self.characters:
            return
        
        char = self.characters[character_id]
        char.trust = max(0, min(100, char.trust + trust_delta))
        
        if relationship:
            char.relationship = relationship
        
        if stance_summary:
            char.stance_summary = stance_summary
        
        # Auto-update relationship based on trust
        if char.trust >= 70:
            char.relationship = "allied"
        elif char.trust >= 40:
            char.relationship = "neutral"
        elif char.trust >= 20:
            char.relationship = "hostile"
    
    def add_event(self, event: str):
        """Add event to recent history"""
        self.recent_events.append(event)
        # Keep only last 10 events
        if len(self.recent_events) > 10:
            self.recent_events = self.recent_events[-10:]
    
    def add_crisis(self, crisis: str):
        """Add active crisis indicator"""
        if crisis not in self.active_crises:
            self.active_crises.append(crisis)
    
    def resolve_crisis(self, crisis: str):
        """Remove resolved crisis"""
        if crisis in self.active_crises:
            self.active_crises.remove(crisis)
    
    # === THRESHOLD CHECKS ===
    
    def check_critical_thresholds(self) -> List[str]:
        """Check if any critical thresholds breached (for triggering events)"""
        warnings = []
        m = self.hidden_metrics
        
        if m.escalation_risk >= 85:
            warnings.append("escalation_critical")
        if m.domestic_stability < 30:
            warnings.append("stability_critical")
        if m.alliance_cohesion < 25:
            warnings.append("alliance_critical")
        
        return warnings


def create_initial_narrative_state(
    metrics: Metrics,
    play_mode: PlayMode = "immersive",
    game_time: str = "Sunday 5th October 2025, 17:00"
) -> NarrativeState:
    """
    Create initial narrative state with standard characters.
    
    Args:
        metrics: Initial hidden metrics
        play_mode: Gameplay mode
        game_time: Initial game time string
    
    Returns:
        Configured NarrativeState
    """
    
    # Define key characters with initial attitudes
    characters = {
        "usa_nsa": CharacterAttitude(
            character_id="usa_nsa",
            name="US National Security Advisor",
            trust=50,  # Uncertain commitment
            relationship="neutral",
            stance_summary="Cautious - wants proof before committing"
        ),
        "uk_foreign_sec": CharacterAttitude(
            character_id="uk_foreign_sec",
            name="Foreign Secretary",
            trust=75,
            relationship="allied",
            stance_summary="Loyal but concerned about alliance unity"
        ),
        "uk_home_sec": CharacterAttitude(
            character_id="uk_home_sec",
            name="Home Secretary",
            trust=70,
            relationship="allied",
            stance_summary="Focused on domestic order and public safety"
        ),
        "uk_cds": CharacterAttitude(
            character_id="uk_cds",
            name="Chief of the Defence Staff",
            trust=80,
            relationship="allied",
            stance_summary="Professional military advisor, cautious about escalation"
        ),
        "uk_nsa": CharacterAttitude(
            character_id="uk_nsa",
            name="National Security Advisor",
            trust=85,
            relationship="allied",
            stance_summary="Your closest advisor, coordinates intelligence"
        ),
    }
    
    # Initial situation summary
    situation_summary = (
        "Russian naval forces deployed near UK waters. "
        "F-35 pilots murdered. False flag accusations from Moscow. "
        "NATO commitment uncertain."
    )
    
    # Initial crises
    active_crises = [
        "Russian Northern Fleet Exercise",
        "F-35 Pilot Murders Investigation",
        "Cyber Attacks on UK Infrastructure"
    ]
    
    return NarrativeState(
        hidden_metrics=metrics,
        previous_metrics=metrics.copy(),
        situation_summary=situation_summary,
        recent_events=[
            "Two F-35 pilots found murdered in Norfolk",
            "Russia falsely accuses UK of Severomorsk attack",
            "Russian families departing UK en masse"
        ],
        characters=characters,
        active_crises=active_crises,
        turn=1,
        game_time=game_time,
        play_mode=play_mode
    )



