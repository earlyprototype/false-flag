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
        """Convert to visual representation (themed glyphs, no emoji)"""
        filled = "●" * self.level
        empty = "○" * (5 - self.level)
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


class PlayedEvent(BaseModel):
    """One inject that has been staged, and what became of it.

    The rolling ``situation_summary`` compresses several turns into a few
    sentences, so whether a thread was *closed* survives only as prose the
    generator has to infer. That inference failed in live play - the same
    submarine surfaced on four consecutive turns, one of them after the
    player had it escorted out of UK waters (issue #25). The ledger states
    the disposition outright instead.
    """

    turn: int
    title: str
    disposition: Literal["open", "advanced", "resolved"] = "open"
    note: str = ""  # one line: what the player did about it

    # Structured consequences, written at adjudication time (ER-077). All
    # optional with empty defaults so saves written before they existed load
    # clean. The disposition says how the thread was left; these say what it
    # cost - the referee's one-sentence verdict, which way each metric moved,
    # and who in the room objected.
    outcome: str = ""  # one sentence from the quality assessment's reasoning
    effects_direction: Dict[str, str] = Field(
        default_factory=dict,
        description='metric name -> "up" | "down" | "steady"')
    objectors: List[str] = Field(
        default_factory=list,
        description="advisor roles that raised pushback against the decision")


# Compact metric names for one-line ledger rendering - the full attribute
# names ("escalation_risk") are engine identifiers, not prose.
_METRIC_SHORT_NAMES = {
    "escalation_risk": "risk",
    "alliance_cohesion": "cohesion",
    "domestic_stability": "stability",
}


def format_event_consequences(outcome: str,
                              effects_direction: Optional[Dict[str, str]],
                              objectors: Optional[List[str]]) -> str:
    """One compact clause per consequence field, '' when none are present.

    e.g. "outcome: Escorting the boat out held the line.; effects: risk up,
    cohesion steady; objectors: Foreign Secretary". Shared by both ledger
    renderers (the EVENTS ALREADY PLAYED block and DECISIONS AND OUTCOMES)
    so the two never drift apart in format.
    """
    clauses = []
    if outcome:
        clauses.append(f"outcome: {outcome}")
    if effects_direction:
        moves = ", ".join(
            f"{_METRIC_SHORT_NAMES.get(metric, str(metric).replace('_', ' '))} "
            f"{direction}"
            for metric, direction in effects_direction.items())
        clauses.append(f"effects: {moves}")
    if objectors:
        clauses.append("objectors: " + ", ".join(objectors))
    return "; ".join(clauses)


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

    # Ledger of injects staged so far and how each was left. Append-only,
    # oldest first. Absent from saves written before issue #25; defaults to
    # empty so old campaigns load unchanged.
    event_ledger: List[PlayedEvent] = Field(default_factory=list)
    
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

    def render_decisions_and_outcomes(self) -> str:
        """DECISIONS AND OUTCOMES block from the event ledger, or '' when empty.

        One line per staged event: turn, title, how the thread was left, and
        the note record_event_disposition attached — which carries the
        (truncated) decision the player took about it. Entries adjudicated
        since ER-077 carry a second, indented line with the structured
        consequences: the referee's one-sentence outcome, which way each
        metric moved, and who objected. This is the memory the adjudication
        prompts fold in: what happened, what the player did, what it cost.
        """
        if not self.event_ledger:
            return ""
        lines = ["DECISIONS AND OUTCOMES (turn | event | how it was left | what the PM did):"]
        for entry in self.event_ledger:
            line = f"- Turn {entry.turn} | {entry.title} | {entry.disposition.upper()}"
            if entry.note:
                line += f" | {entry.note}"
            lines.append(line)
            consequences = format_event_consequences(
                entry.outcome, entry.effects_direction, entry.objectors)
            if consequences:
                lines.append(f"  {consequences}")
        return "\n".join(lines)

    def _llm_context(self, include_characters: bool) -> str:
        """Shared body of to_llm_context / to_actor_context."""
        m = self.hidden_metrics

        parts = [f"""Current Situation Metrics (hidden from player):
- Escalation Risk: {m.escalation_risk}/100 ({"CRITICAL" if m.escalation_risk >= 85 else "HIGH" if m.escalation_risk >= 70 else "MODERATE"})
- Alliance Cohesion: {m.alliance_cohesion}/100 ({"STRONG" if m.alliance_cohesion >= 70 else "MODERATE" if m.alliance_cohesion >= 40 else "WEAK"})
- Domestic Stability: {m.domestic_stability}/100 ({"STABLE" if m.domestic_stability >= 70 else "WAVERING" if m.domestic_stability >= 40 else "FRAGILE"})
- Casualties: {m.casualties_mil} military, {m.casualties_civ} civilian"""]

        if self.situation_summary:
            parts.append(f"SITUATION SUMMARY:\n{self.situation_summary}")

        parts.append("Recent Events:\n" + "\n".join(
            f"- {event}" for event in self.recent_events[-3:]))

        parts.append("Active Crises:\n" + "\n".join(
            f"- {crisis}" for crisis in self.active_crises))

        ledger_block = self.render_decisions_and_outcomes()
        if ledger_block:
            parts.append(ledger_block)

        if include_characters:
            parts.append("Character Relationships:\n" + "\n".join(
                f"- {char.name}: {char.relationship.upper()} (trust: {char.trust}/100)"
                for char in self.characters.values()))

        return "\n\n".join(parts).strip()

    def to_llm_context(self) -> str:
        """
        Generate context string for LLM with hidden metrics.

        This gives the LLM numerical guidance without showing player, plus
        the campaign memory: the rolling situation summary and the ledger of
        decisions and outcomes (ER-010, ER-017). The stale game clock is
        gone — the turn is already shown on every ledger line.
        """
        return self._llm_context(include_characters=True)

    def to_actor_context(self) -> str:
        """Context for a foreign state actor's roleplay prompt.

        Identical to to_llm_context minus the Character Relationships block:
        the UK cabinet's private trust scores are internal state and must not
        reach a foreign government's reasoning (ER-014).
        """
        return self._llm_context(include_characters=False)
    
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

    def record_played_event(self, turn: int, title: str) -> None:
        """Log an inject as staged on ``turn``, disposition still open.

        Re-recording the same turn overwrites rather than duplicating, so a
        retried or regenerated inject leaves one entry.
        """
        title = (title or "").strip() or f"Turn {turn} development"
        for entry in self.event_ledger:
            if entry.turn == turn:
                entry.title = title
                return
        self.event_ledger.append(PlayedEvent(turn=turn, title=title))

    def close_event(self, turn: int, disposition: str, note: str = "") -> None:
        """Set how the event staged on ``turn`` was left.

        Unknown dispositions are ignored rather than coerced: a wrong
        "resolved" would suppress a live thread, which is worse than the
        repetition this ledger exists to prevent.
        """
        if disposition not in ("open", "advanced", "resolved"):
            return
        for entry in self.event_ledger:
            if entry.turn == turn:
                entry.disposition = disposition
                if note:
                    entry.note = note.strip()
                return

    def record_event_consequences(self, turn: int, outcome: str = "",
                                  effects_direction: Optional[Dict[str, str]] = None,
                                  objectors: Optional[List[str]] = None) -> None:
        """Attach this turn's adjudicated consequences to its ledger entry.

        Written whatever the disposition ends up as - an event can stay OPEN
        and still have cost the player something. Only truthy values are
        written, so a retried adjudication cannot blank fields an earlier
        pass filled in.
        """
        for entry in self.event_ledger:
            if entry.turn == turn:
                if outcome:
                    entry.outcome = outcome.strip()
                if effects_direction:
                    entry.effects_direction = {
                        str(metric): direction
                        for metric, direction in effects_direction.items()
                        if direction in ("up", "down", "steady")
                    }
                if objectors:
                    entry.objectors = [str(role).strip() for role in objectors
                                       if str(role).strip()]
                return

    def recent_played_events(self, n: Optional[int] = None) -> List["PlayedEvent"]:
        """Ledger entries, oldest first - **all of them** unless ``n`` says otherwise.

        This used to default to the last six, which was the wrong instinct
        applied twice. The ledger is one line per event: it *is* the
        compression of the transcript, the thing that survives when the
        prose window slides past. Truncating it is compressing the
        compression, and it re-opens the exact bug the ledger exists to
        close - an event older than the window becomes invisible to the
        generator and can be restaged as fresh.

        The cost of keeping it whole is negligible. One entry is about 94
        characters, so a full 18-turn campaign is roughly 420 tokens and a
        60-turn one about 1,400 - set against advisor prompts of 500 lines.
        There was never anything to save here.

        ``n`` is kept for callers that genuinely want a slice; ``n <= 0``
        still yields nothing.

        Named to avoid colliding with the ``recent_events`` field above,
        which holds player-facing event prose rather than dispositions.
        """
        if n is None:
            return list(self.event_ledger)
        if n <= 0:
            return []
        return self.event_ledger[-n:]
    
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
        # Seeded so the Attorney General participates in the trust economy:
        # without a character here, AG pushback could be overridden at no
        # cost and no panel ever tracked the relationship.
        "uk_attorney_general": CharacterAttitude(
            character_id="uk_attorney_general",
            name="Attorney General",
            trust=70,
            relationship="neutral",
            stance_summary="Guardian of legality - international law first"
        ),
    }
    
    # Initial situation summary. This text is the anchor for every fold that
    # follows (ER-048): it must state each event with its own place and
    # attribution, because the fold is instructed to preserve them verbatim
    # and a fragment like "F-35 pilots murdered" invites the summariser to
    # invent a culprit from whatever else is in its context.
    situation_summary = (
        "Two RAF F-35 pilots were murdered in Norfolk; intelligence assesses "
        "a Russian special-forces operation as likely, though confidence is "
        "low at this stage. Separately, a "
        "terrorist attack on the Severomorsk naval base killed over a hundred "
        "Russian sailors; GCHQ attributes it to Dagestani extremists, but "
        "Moscow falsely blames the United Kingdom and is using it as a pretext. "
        "A Russian submarine surge is under way in the North Atlantic, cyber "
        "attacks on UK infrastructure are climbing, and Russian diplomats are "
        "leaving London. NATO's commitment to a collective response is not yet "
        "certain."
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



