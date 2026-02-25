# Day‑1 Spec — Team B (Agents & LLM I/O)

Status: Draft
Owner: Team B

## Purpose
Provide heuristic advisor proposals and leader selection logic that conform to the interface, so Engine can progress without real model calls.

## Inputs and outputs
- Inputs: models/world.py
- Outputs: agents/advisors.py, agents/leader.py

## Allowed tools and permissions
- Edit Python under agents/

## Interfaces touched
- AdvisorProposal(action_id, agenda_cost, rationale, expected_effects[])

## Steps (60–90 minutes)
- Ensure advisors return ≥2 proposals with agenda_cost and ranges.
- Ensure leader plugin supports modes: human (no choice), mixed (one proposal), llm (choose legal agenda option).

## Acceptance tests
- Given fixed WorldState, get_advisor_proposals returns valid proposals.
- choose_actions returns one proposal in mixed and llm modes.

## Prompt contract
- None (heuristic only for Day‑1).

## Budgets and limits
- Time: 60 minutes

## Self-check rubric
- Schema compliance and stability across runs.

## Handoff triggers
- If schema change seems necessary, stop and hand over.


