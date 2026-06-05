# War Game Mechanics (Primer)

Status: Draft
Change classification: M

## What is a war game?
A structured decision‑making exercise that simulates conflict and competition among actors over time. It is used for analysis, education, planning, and rehearsal. Unlike pure simulations, war games blend rules with expert judgement.

## Common formats
- Seminar: facilitated discussion; minimal rules; subject‑matter expert (SME) heavy.
- Matrix: players argue outcomes; umpire adjudicates with dice and plausibility.
- Kriegsspiel/control‑cell (command post exercise): rules‑based, hidden information, adjudicated by a control cell.
- Agent‑based/computer‑assisted: software models agents and environment; humans steer decisions.

## Core artefacts
- Initial conditions: aims, red lines, constraints, order of battle, posture (often Political, Military, Economic, Social, Information, Infrastructure (PMESII) and Diplomatic, Information, Military, Economic (DIME) framing).
- Role briefs: objectives, authorities, information access, red lines for each actor.
- Master Scenario Events List (MSEL): timed and conditional “injects” that introduce developments via channels (intelligence, diplomatic, media).
- Maps/boards/order of battle trackers; decision logs; after‑action review templates.

## Conduct of play (typical)
1) Inject phase: deliver scheduled or triggered events to relevant players.
2) Intelligence and narrative update: refine uncertainty; introduce deception or clarification.
3) Deliberation: teams discuss options; advisors prepare recommendations.
4) Decision: players issue orders within constraints and authorities.
5) Adjudication: control cell applies rules/tables and judgement; may use Action–Reaction–Counteraction (ARC).
6) Consequences: update the common operating picture and metrics; brief outcomes.

## Adjudication models
- Rules‑based tables: deterministic mappings with bounded randomness; repeatable and testable.
- Matrix with dice: plausibility arguments plus probabilistic roll; flexible and SME‑friendly.
- Hybrid (most common): rules handle routine effects; control cell overrides edge cases with rationale.

## Action–Reaction–Counteraction (ARC)
Structured expansion of a chosen action into adversary reactions and possible counters. Limits: commonly depth ≤ 2 to prevent combinatorial explosion. Used to surface second‑ and third‑order effects.

## Escalation ladders and thresholds
Predefined bands unlock classes of events (for example, signalling → cyber/proxy → conventional → strategic). Ladders guide pacing and maintain plausibility boundaries.

## Information environment
- Intelligence tiers: rumour, likely, confirmed; movement between tiers each scene.
- Deception: adversary actions can inject false signals; detection opposed by capability and luck.
- Media and public: narratives affect political will and legitimacy; press management is a tool.

## Curation workflow
1) Source material: transcripts, reporting, SME input; extract facts and constraints.
2) Build MSEL and role briefs; identify reconvergence nodes to avoid dead ends.
3) Define adjudication rules and override policy (when to invoke judgement).
4) Playtest with seeds; validate plausibility; adjust hazards and thresholds.

## The podcast as an example
The Sky News and Tortoise “War Game” presents sequential injects, expert deliberation, and decisions under constraints. Our project mirrors this with: transcript‑seeded MSEL, advisor briefings, rules‑first adjudication with bounded randomness, and logs for after‑action review.

# War Game Mechanics (Primer)

Status: Draft
Change classification: M

## What is a war game?
A structured decision‑making exercise that simulates conflict and competition among actors over time. It is used for analysis, education, planning, and rehearsal. Unlike pure simulations, war games blend rules with expert judgement.

## Common formats
- Seminar: facilitated discussion; minimal rules; SME‑heavy.
- Matrix: players argue outcomes; umpire adjudicates with dice and plausibility.
- Kriegsspiel/control‑cell (CPX): rules‑based, hidden information, adjudicated by a control cell.
- Agent‑based/computer‑assisted: software models agents and environment; humans steer decisions.

## Core artefacts
- Initial conditions: aims, red lines, constraints, order of battle, posture (often PMESII/DIME framing).
- Role briefs: objectives, authorities, information access, red lines for each actor.
- MSEL (Master Scenario Events List): timed and conditional “injects” that introduce developments via channels (intel, diplomatic, media).
- Maps/boards/order of battle trackers; decision logs; after‑action review templates.

## Conduct of play (typical)
1) Inject phase: deliver scheduled/triggered events to relevant players.
2) Intelligence/narrative update: refine uncertainty; introduce deception or clarification.
3) Deliberation: teams discuss options; advisors prepare recommendations.
4) Decision: players issue orders within constraints/authorities.
5) Adjudication: control cell applies rules/tables and judgement; may use ARC.
6) Consequences: update the common operating picture and metrics; brief outcomes.

## Adjudication models
- Rules‑based tables: deterministic mappings with bounded randomness; repeatable and testable.
- Matrix with dice: plausibility arguments + probabilistic roll; flexible and SME‑friendly.
- Hybrid (most common): rules handle routine effects; control cell overrides edge cases with rationale.

## ARC (Action–Reaction–Counteraction)
Structured expansion of a chosen action into adversary reactions and possible counters. Limits: commonly depth ≤ 2 to prevent combinatorial explosion. Used to surface second‑ and third‑order effects.

## Escalation ladders and thresholds
Predefined bands unlock classes of events (e.g., signalling → cyber/proxy → conventional → strategic). Ladders guide pacing and maintain plausibility boundaries.

## Information environment
- Intel tiers: rumour, likely, confirmed; movement between tiers each turn.
- Deception: adversary actions can inject false signals; detection opposed by capability and luck.
- Media/public: narratives affect political will and legitimacy; press management is a tool.

## Curation workflow
1) Source material: transcripts, reporting, SME input; extract facts and constraints.
2) Build MSEL and role briefs; identify reconvergence nodes to avoid dead ends.
3) Define adjudication rules and override policy (when to invoke judgement).
4) Playtest with seeds; validate plausibility; adjust hazards and thresholds.

## The podcast as an example
The Sky News/Tortoise “War Game” presents sequential injects, expert deliberation, and decisions under constraints. Our project mirrors this with: transcript‑seeded MSEL, advisor briefings, rules‑first adjudication with bounded randomness, and logs for after‑action review.


## Appendices (illustrative)

### A. Sample MSEL row
```yaml
- id: media_leak_01
  time: turn 2
  channel: media
  audience: blue_lead, blue_public
  inject: "Draft intelligence memo on naval posture leaks to press"
  expected_player_actions: [press_briefing, investigate_leak]
  adjudication_notes: "If briefing within 1 turn, reduce domestic hit by 50%"
  metrics_effects:
    domestic_stability: -4..-2
  follow_ons: [ally_reassurance_call]
```

### B. ARC example (depth ≤ 2)
```
Action: Show of force (deploy task group to GIUK)
  Reaction: Adversary maritime shadowing
    Counteraction: Broadcast ASW drills; open channel to allies
```

### C. Adjudication table snippet (illustrative)
```
Action              | Base Effects                 | Hazard Mods
------------------- | --------------------------- | ------------------------------
Sanctions (AP1)     | +2 escalation, -3 cohesion  | +10% chance adversary cyber
Show of force (AP2) | +6 escalation, +5 mission   | +15% chance maritime incident
Press briefing (AP0)| +2 stability if timely      | -50% negative media effect
```


