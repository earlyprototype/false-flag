from typing import List, Dict, Optional
from pydantic import BaseModel, Field
import yaml
from pathlib import Path

class StateActor(BaseModel):
    """Individual nation-state with public and hidden state."""
    
    # === IDENTIFICATION ===
    country_code: str = Field(..., description="ISO 3166 code (USA, FRA, DEU, etc.)")
    full_name: str = Field(..., description="Official country name")
    
    # === PUBLIC STATE (player can see through diplomacy) ===
    official_position: str = Field(..., description="Public diplomatic stance")
    relationship_uk: int = Field(default=50, ge=0, le=100, description="UK relationship score")
    public_commitments: List[str] = Field(default_factory=list, description="Stated commitments")
    
    # === HIDDEN STATE (player cannot see, guides LLM) ===
    true_motivations: List[str] = Field(
        default_factory=list,
        description="Actual strategic goals (energy_security, contain_russia, avoid_war)"
    )
    hidden_agendas: List[str] = Field(
        default_factory=list,
        description="Secret plans (russia_backchannel, undermine_uk_influence)"
    )
    threat_perception: int = Field(
        default=50, ge=0, le=100,
        description="How threatened they actually feel (may differ from public)"
    )
    domestic_pressure: int = Field(
        default=50, ge=0, le=100,
        description="Internal political constraints (elections, public opinion)"
    )
    dependencies: Dict[str, str] = Field(
        default_factory=dict,
        description="Strategic vulnerabilities (RUS: natural_gas_supply)"
    )
    redlines: List[str] = Field(
        default_factory=list,
        description="Actions they will not support (offensive_action, nuclear_first_use)"
    )
    
    # === STRATEGIC CAPABILITIES ===
    military_capability: int = Field(default=50, ge=0, le=100)
    economic_leverage: int = Field(default=50, ge=0, le=100)
    diplomatic_influence: int = Field(default=50, ge=0, le=100)
    intelligence_sharing: str = Field(default="limited", description="full/selective/limited/none")
    
    # === BEHAVIORAL TRACKING ===
    recent_actions: List[str] = Field(default_factory=list, description="Last 3 actions taken")
    trust_trajectory: str = Field(default="stable", description="improving/stable/declining")
    last_contacted_turn: Optional[int] = Field(default=None)
    
    def update_relationship(self, delta: int):
        """Update relationship score and set trajectory."""
        old = self.relationship_uk
        self.relationship_uk = max(0, min(100, old + delta))
        
        if delta > 2:
            self.trust_trajectory = "improving"
        elif delta < -2:
            self.trust_trajectory = "declining"
        else:
            self.trust_trajectory = "stable"

    def add_action(self, action_desc: str):
        """Track recent action."""
        self.recent_actions.insert(0, action_desc)
        self.recent_actions = self.recent_actions[:3]


class ActorResponse(BaseModel):
    """Response from a single state actor to player action."""
    
    actor_id: str
    public_response: str = Field(..., description="What they say publicly")
    private_assessment: str = Field(..., description="What they actually think")
    trust_change: int = Field(default=0, ge=-20, le=20)
    will_support: str = Field(..., description="yes/no/conditional")
    conditions: List[str] = Field(default_factory=list, description="If conditional, what they need")
    intel_shared: Optional[str] = Field(default=None, description="Intelligence they share")
    action_taken: Optional[str] = Field(default=None, description="Specific action taken by actor")


class StateActorSystem(BaseModel):
    """Manages all state actors in the simulation."""
    
    actors: Dict[str, StateActor] = Field(default_factory=dict)
    turn: int = Field(default=1)
    
    def get_actor(self, country_code: str) -> Optional[StateActor]:
        """Get actor by country code."""
        return self.actors.get(country_code)
    
    def update_actor_relationship(self, country_code: str, delta: int):
        """Update bilateral relationship score."""
        actor = self.actors.get(country_code)
        if actor:
            actor.update_relationship(delta)


def load_actors_from_yaml(file_path: str) -> StateActorSystem:
    """Load initial actor states from YAML file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Actor definition file not found: {file_path}")
        
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        
    actors = {}
    for actor_data in data:
        actor = StateActor(**actor_data)
        actors[actor.country_code] = actor
        
    return StateActorSystem(actors=actors)
