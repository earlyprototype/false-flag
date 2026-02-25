# Day‑2 Spec — Team B (Agents & Large Language Model I/O)

Status: Draft
Owner: Team B

## Purpose
Strengthen advisor outputs: ensure rationale is non-empty, agenda_cost ∈ {0,1,2}, and add a simple self‑check rubric.

## Inputs and outputs
- Inputs: `models/world.py`
- Outputs: `agents/advisors.py`, `agents/leader.py` (if minor tweaks)

## Allowed tools and permissions
- Edit Python under `agents/`

## Interfaces touched
- `AdvisorProposal` fields: `rationale` (non-empty), `agenda_cost` in range

## Steps (60–90 minutes)
- Validate proposals before returning:
  - Drop any proposal with empty rationale or invalid agenda_cost
- Add a self‑check helper that logs counts of valid/invalid proposals
- Keep deterministic behaviour under seed=42

## Acceptance tests
- Given fixed `WorldState`, proposals returned are all valid; count ≥ 1
- Leader still selects exactly one proposal in llm/mixed
- Gate Runner passes

## Prompt contract
- None

## Budgets and limits
- Time: 60 minutes

## Self‑check rubric
- No schema drift; deterministic selection unchanged

## Handoff triggers
- If proposal validation removes all options, add a fallback proposal

