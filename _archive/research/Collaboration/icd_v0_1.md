# Interface Control Document (ICD) — v0.1

Status: Draft
Owner: Coordinator

Scope: Shared data models and call boundaries for Teams A (Engine & Rules), B (Agents & LLM I/O), and C (Scenario & Ingestion).

## Python data models (authoritative v0.1)
```python
from typing import Dict, List, Protocol
from pydantic import BaseModel

class Metrics(BaseModel):
    escalation_risk: int
    domestic_stability: int
    alliance_cohesion: int
    mission_progress: int
    casualties_civ: int = 0
    casualties_mil: int = 0

class WorldState(BaseModel):
    scene: int  # scene index (podcast-style pacing)
    metrics: Metrics
    flags: Dict[str, bool] = {}
    posture: Dict[str, str] = {}

class EffectRange(BaseModel):
    metric: str
    delta_min: int
    delta_max: int

class AdvisorProposal(BaseModel):
    action_id: str
    agenda_cost: int  # consumes one agenda decision slot in the scene
    rationale: str
    expected_effects: List[EffectRange]
    risks: List[str] = []
    preconditions: Dict[str, str] = {}

class Agent(Protocol):
    def propose(self, world: WorldState) -> List[AdvisorProposal]: ...
```

## Engine boundaries
- Engine → Advisors (Team B): `propose(world_state) -> List[AdvisorProposal]`
- Engine → Leader plugin: selects 0–2 `AdvisorProposal` per scene according to mode (human, llm, mixed)
- Engine → Rules: rules-first adjudication (update → modify → apply), then optional control-cell override

## Ingestion outputs (Team C)
- `data/scenarios/<id>/initial_conditions.yaml`
- `data/scenarios/<id>/events.yaml`
- `data/scenarios/<id>/role_briefs/*.md`
- Static panels in `assets/placeholders/*.txt`

## Determinism
- Seeded runs; per-scene sub-seeds should include scene index and stable IDs (event/action ids).
- Cache LLM outputs by prompt hash during evaluation runs.

## Logging and provenance
- Log: model name, token counts, prompt/response hashes, and cost if available.
- Store original transcripts and notes under `@filing/` with source links and hashes.

## Change control
- Any schema change requires two-team approval and ICD update in the same pull request.


