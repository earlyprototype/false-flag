# Mechanics Options Inspired by Similar Games

Status: Draft
Change classification: S

## Purpose
Outline mechanics options for our game inspired by similar titles and war‑gaming practice, focusing on scenario generation, narrative control, and adjudication.

## Design principles
- Maintain plausibility under PMESII/DIME frames.
- Be reproducible (seeded RNG), auditable, and testable.
- Separate authored knowledge (MSEL, briefs) from stochastic layers (hazards, param sampling).

## Options (with references)

1) Master Scenario Events List (MSEL) injects (exercise standard; used in CPX/seminar games)
- Authored timed/triggered injects with owner, channel, expected responses.
- Pros: controllable, SME-friendly, testable.
- Cons: can be linear if over-scripted.
- Use when: you want fidelity to a reference (e.g., the podcast) with limited divergence.

2) Branching graphs with reconvergence (story‑driven strategy and narrative games)
- Pre-authored decision nodes that converge/diverge.
- Pros: curated beats; avoids combinatorial blow-up by reconvergence.
- Cons: authoring overhead; coverage risk.
- Use when: key beats must exist with alternative routes.

3) Card‑driven “deck” events (e.g., Twilight Struggle; board wargames)
- Thematic decks (cyber, naval, domestic politics); draw with constraints.
- Pros: variety and replayability; easy to balance by deck composition.
- Cons: stochastic feel if overused.
- Use when: you need spice within a phase without breaking plausibility.

4) Matrix/argument‑based adjudication (matrix games; SME‑facilitated)
- Actors propose actions/outcomes; adjudicator applies plausibility + dice.
- Pros: flexible, SME-aligned, encourages reasoning.
- Cons: less deterministic unless rules are tight.
- Use when: you want narrative richness and SME input.

5) Agent‑based/systemic emergent scenarios (computer‑assisted wargames)
- Agents interact via rules (posture, capabilities, objectives) to generate crises.
- Pros: emergent play, systemic stress tests.
- Cons: tuning/validation burden.
- Use when: exploring dynamics rather than reproducing a script.

6) GOAP/HTN + drama manager (used to maintain beats while respecting constraints)
- AI plans to goals; drama manager nudges beats under constraints.
- Pros: coherent AI; guided pacing.
- Cons: implementation complexity.
- Use when: you need adaptive narrative while staying plausible.

7) Stochastic hazard/Markov processes (risk tempo modelling; analytic sims)
- Hazard rates for escalation/miscalculation; state transitions via Markov chains.
- Pros: analyzable, tuneable, cheap to run at scale.
- Cons: can feel abstract if not grounded in domain events.
- Use when: modelling risk tempo and crisis frequency.

8) Monte Carlo parameter sampling (replayability; robustness testing)
- Sample posture knobs (intent, tolerance, tempo), resources, public mood; filter infeasible draws.
- Pros: broad coverage; supports eval harness.
- Cons: requires feasibility constraints to avoid nonsense.
- Use when: generating varied starting conditions.

9) Sandbox templates (scenario families with shared structure)
- Scenario “templates” with slots for flashpoints, inject packs, and hazard settings.
- Pros: quick generation with consistent structure.
- Cons: template bias.
- Use when: producing families of related scenarios.

## Recommended v1 blend
- Backbone: MSEL + triggers seeded from the transcript.
- Variety: small card decks per phase (e.g., media, cyber, alliance).
- Control: light branching at key beats with reconvergence.
- Replayability: parameterised template (posture, hazard rates, pace) sampled per run.

## Data skeletons (illustrative)
```yaml
# data/scenarios/war_game_2025/initial_conditions.yaml
metadata: { id: war_game_2025, version: 1, seed: 42 }
posture: { red_intent: high, blue_tolerance: medium, tempo: fast }
actors:
  - id: uk_pm
    objectives: [maintain_alliance, avoid_escalation]
    red_lines: [no_uk_home_casualties]
hazards:
  escalation_per_turn: 0.07
  miscalc_per_crisis: 0.15
public_opinion: { uk: { support: 0.55, volatility: 0.2 } }
```

```yaml
# data/scenarios/war_game_2025/events.yaml
- id: naval_incident_01
  when: { window: [3,6] }
  trigger:
    hazard: escalation_per_turn
    conditions: [{ sea_zone: GIUK }]
  channel: intel
  effects:
    - metric: escalation_risk
      delta: +8..+15
    - schedule_event: ally_emergency_call
  image: assets/placeholders/naval_incident.md
```

## Generation pipeline (v1)
1) Load template and posture knobs (seeded).
2) Sample knobs → validate constraints.
3) Load MSEL injects; activate by time/conditions.
4) Draw limited event cards each phase; apply gating rules.
5) Bake scenario pack (YAML + assets) with provenance notes.

## Acceptance criteria
- Deterministic with fixed seed; no dead-end states in first 10 turns.
- Coverage: at least 3 distinct critical paths across 20 runs.
- SME plausibility check: no inject violates actor red lines without a credible precursor.

## Open items
- Balance ranges for effect deltas (±) per metric.
- Deck sizes and per-phase draw caps.
- Reconvergence nodes (IDs, conditions).


