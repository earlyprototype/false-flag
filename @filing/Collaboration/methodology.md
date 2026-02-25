# Collaboration Methodology

Status: Draft
Owner: Coordinator

## Overview
This methodology defines a general development map (coarse roadmap) plus per‑team specifications and stage gates. It enables parallel execution by three specialised teams with clear handoffs and verification before integration.

## Teams (specialisation)
- Team A — Engine & Rules
- Team B — Agents & Large Language Model I/O
- Team C — Scenario & Ingestion

## Governance
- Interface Control Document (ICD) pinned for models and APIs; changes require two‑team approval.
- Stage gates with entry/exit criteria; coordinator runs a daily 10‑minute check.
- Work packets sized for 60–90 minutes; acceptance tests included in pull requests (PRs).
- Decision Charter applies: follow `Collaboration/decision_charter.md` for pre‑approved actions and escalation rules.

## General development map (coarse)
1) Foundations
   - Repository structure, tooling, Python 3.11 baseline.
   - Minimal Typer CLI scaffold; seedable random number generator (RNG) utility; Pydantic base models.
   - Gate F1: `wargame new; status; end-scene` works without a large language model (LLM).
2) Core Mechanics
   - Event scheduler, rules tables, rules‑first adjudication (update→modify→apply) with control‑cell override, persistence.
   - Heuristic advisor; metrics/scoring; static panels referenced.
   - Gate F2: deterministic replay (seed=42) across three scenes with invariants passing.
3) Agents & Large Language Models
   - Agent framework, proposal schema, LLM router/drivers, budgets.
   - Golden transcript tests; fault handling and timeouts.
   - Gate F3: advisors generate structured proposals under budget; transcripts saved.
4) Scenario & Ingestion
   - Transcript ingestion (public transcript first → automatic speech recognition (ASR) fallback), segmentation, YAML extraction.
   - Scenario template, Master Scenario Events List (MSEL) injects, placeholder assets wired.
   - Gate F4: scenario pack validates; sample run uses event images.
5) Evaluation & Hardening
   - Headless batch runs; coverage metrics; logs/provenance hashing.
   - Gate F5: N=50 headless runs pass smoke; reproducibility confirmed.

## Per‑team Specs (tailored workflows)

### Team A — Engine & Rules
Scope: `models/*`, `engine/*`, persistence.
Inputs: ICD types, `events.yaml`, `initial_conditions.yaml` (stubs ok).
Outputs: scene loop, adjudicator (rules‑first with override), scoring, save/load.
Stage tasks:
- A1: Define `Metrics`, `WorldState`, RNG utilities, clamps.
- A2: Implement scheduler and gating predicates; rules table arithmetic.
- A3: Rules‑first adjudication (update→modify→apply) with control‑cell override; Action–Reaction–Counteraction (ARC) expansion (depth ≤ 2); persistence.
Gate checks:
- GA1: Seeded replay deterministic; metrics in [0,100]; no negative casualties.
- GA2: Trigger predicates and cooldowns pass unit tests.

### Team B — Agents & Large Language Model I/O
Scope: `agents/*`, `llm/*`, heuristic advisor, golden tests.
Inputs: ICD types, `WorldState` from Team A.
Outputs: advisor proposals, LLM router/drivers, budget/timeout handling.
Stage tasks:
- B1: Agent base and heuristic advisor (no LLM) matching `AdvisorProposal` schema.
- B2: `client.py` + `router.py` interfaces; drivers stubs; cost caps.
- B3: Golden tests for stable outputs; error/backoff policies.
Gate checks:
- GB1: Given fixed `WorldState`, heuristic returns ≥1 valid proposal.
- GB2: Golden tests hash‑stable with seed=42.

### Team C — Scenario & Ingestion
Scope: `ingestion/*`, `data/scenarios/*`, `assets/placeholders/*`, `@filing/`.
Inputs: public transcript links; coordinator provides seed.
Outputs: initial conditions YAML, events YAML with images, provenance notes.
Stage tasks:
- C1: `transcripts.py` fetch public transcript; plan Whisper fallback.
- C2: `segmenter.py` + `extract_events.py` produce YAML stubs.
- C3: Create 3–5 placeholder panels and reference them from events.
Gate checks:
- GC1: YAML validates; at least one event references an existing panel.
- GC2: Scenario pack runs through three scenes deterministically with Team A.

## Stage gate template (reusable)
```
Gate ID: Fx/Gx (Foundations/Team Gate)
Entry: prerequisites satisfied
Exit: acceptance tests pass, checklist signed by coordinator
Artifacts: PR link, test logs, seed/hash values, notes
Rollback: revert branch or disable feature flag
```

## ICD snapshot (v0.1)
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
    turn: int  # represents scene index in v0.1; will be renamed to `scene` in code
    metrics: Metrics
    flags: Dict[str, bool] = {}
    posture: Dict[str, str] = {}

class EffectRange(BaseModel):
    metric: str
    delta_min: int
    delta_max: int

class AdvisorProposal(BaseModel):
    action_id: str
    agenda_cost: int  # consumes one agenda decision slot for the scene
    rationale: str
    expected_effects: List[EffectRange]
    risks: List[str] = []
    preconditions: Dict[str, str] = {}

class Agent(Protocol):
    def propose(self, world: WorldState) -> List[AdvisorProposal]: ...
```

## Review cadence
- Daily: 10 minutes stand‑up, surface blockers.
- Twice weekly: integration review on `develop` with smoke tests.
- Weekly: risk/roadmap adjust and gate planning.

## Definition of Done (per PR)
- Tests passing, seeds and hashes recorded, schema unchanged or ICD updated with approvals.
- Docs touched: method summary in PR; if new file type, add to ICD section.


