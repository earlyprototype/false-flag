# Initial Advance Mechanics

Status: Draft
Change classification: S

## Scene phases (podcast‑style v1)
1) Inject
- Deliver scheduled or triggered events from the Master Scenario Events List (MSEL).
- No random deck by default (for fidelity); optional variety can be toggled later.
- Enforce gating (mutual exclusions and cooldown windows).

2) Intelligence update
- Consolidate rumours into likely into confirmed with decay probabilities.
- Insert deception where adversary flags allow.

3) Deliberation (agents)
- Advisors (Defence, Treasury, Foreign Secretary, Communications) generate proposals with:
  - action identifier, rationale, expected effects (ranges), risks, preconditions.
- Private adversary and allied planning runs in the background.

4) Decision (player)
- Player makes one or two agenda decisions for the scene (no action points).
- User interface shows locked or active options and any cooldown timers.

5) Adjudication (rules then override)
- Update: compute base effects from rules tables.
- Modify: apply hazard draws (escalation or miscalculation), posture multipliers, media modifiers.
- Apply: clamp values, schedule follow‑on events (Action–Reaction–Counteraction depth ≤ 2), set cooldowns and flags.
- Control‑cell override: allow a manual or LLM‑assisted note to adjust edge cases with a short rationale.

6) Consequences
- Update metrics and world state, advance clocks.
- Log transcript with advisor briefs, chosen actions, seed values, and diffs.
- Display static panel if configured.

## Determinism and RNG
- Seeded per run; per-turn sub-seeds include turn index and event/action IDs.
- Reproducible with same seed, scenario, and model/router settings.

## Hazards and draws (sketch)
- Escalation draw: p = base_hazard + k1*(risk/100) + k2*tempo_factor; cap [0, 0.6].
- Miscalculation draw on crisis: p = miscalc_base * stress_multiplier.
- Effect deltas sampled from configured ranges (triangular or uniform).

## Advisors: structured outputs (example)
```yaml
advisor: defence
proposal:
  action_id: show_of_force
  agenda_cost: 1  # consumes one agenda decision slot for the scene
  rationale: Deter further incursions without crossing red lines.
  expected_effects:
    mission_progress: +4..+7
    escalation_risk: +3..+8
  risks: [adversary_cyber_reprisal_soon]
  preconditions: [assets_available: true, sea_zone: GIUK]
```

## Action constraints
- Preconditions: resources, posture flags, zone availability.
- Cooldowns: actions set timers on completion.
- Unlocks: thresholds enable emergency tools or diplomatic channels.

## Autosave and transcripts
- Autosave after each turn (snapshot of `WorldState`).
- Transcript includes:
  - RNG seeds, injects drawn, advisor briefs, decision, outcomes, metrics diffs.
  - Provenance of any LLM calls (model, cost), or heuristic mode flag.

## Static panels (assets)
- Major injects/actions reference `assets/placeholders/*.md`.
- Fallback: descriptive text if terminal rendering unsupported.

## Edge cases
- No legal actions: provide “hold posture” fallback with small passive effects.
- Conflicting injects: later inject deferred if gating violated.
- Rapid escalation: emergency comms auto-unlock at risk ≥ 80.

## Verification
- With seed=42 and no LLM, first two turns remain deterministic and pass invariants.
- Deck draws never exceed per-phase caps; cooldowns enforced.
- ARC depth limited to 2; no infinite scheduling chains.

