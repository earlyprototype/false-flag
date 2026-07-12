from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from models.narrative import NarrativeConfig


class Metrics(BaseModel):
    escalation_risk: int
    domestic_stability: int
    alliance_cohesion: int
    casualties_civ: int = 0
    casualties_mil: int = 0


# Phase types for turn structure
Phase = Literal["briefing", "discussion", "decision", "adjudication"]


from models.state_actors import StateActorSystem

class WorldState(BaseModel):
    # Turn tracking (replaces 'scene')
    turn: int = Field(default=1, description="Current turn number (1-indexed)")
    phase: Phase = Field(default="briefing", description="Current phase within the turn")
    
    # Narrative state
    narrative: Optional[NarrativeConfig] = Field(default=None, description="The secret narrative truth guiding agent behaviour.")
    
    # Legacy field for backward compatibility (will be removed)
    scene: int = Field(default=1, description="Deprecated: use 'turn' instead")
    
    # Difficulty setting for scenario effect scaling
    difficulty: str = Field(default="standard", description="Difficulty level: standard, challenging, brutal")
    
    # Game state
    metrics: Metrics
    flags: Dict[str, bool] = Field(default_factory=dict)
    posture: Dict[str, str] = Field(default_factory=dict)
    
    # Spatial state (optional, for unit tracking at named locations)
    spatial_state: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Maps location names to lists of unit IDs present there"
    )
    
    # Discussion history for current turn
    discussion_transcript: List[str] = Field(
        default_factory=list,
        description="Transcript of discussion phase for current turn"
    )

    # Recently applied injects (for critical-omissions context)
    recent_injects: List[str] = Field(
        default_factory=list,
        description="Titles/summaries of recently applied injects, most recent last"
    )
    
    # Diplomatic relationship tracking
    diplomatic_relationships: Dict[str, int] = Field(
        default_factory=dict,
        description="Maps country codes to relationship scores (affects access levels)"
    )
    
    # State actor system (multi-agent simulation)
    actor_system: Optional[StateActorSystem] = Field(
        default=None,
        description="StateActorSystem for individual country simulation (if enabled)"
    )


