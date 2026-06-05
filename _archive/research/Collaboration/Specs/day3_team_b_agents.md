# Day‑3 Spec — Team B (Agents & LLM Router)

Status: Draft
Owner: Team B

## Purpose

Introduce a provider‑agnostic LLM router with a deterministic mock driver and integrate it into `--leader llm` mode without changing behaviour or determinism.

## Inputs and outputs

- Inputs: `models/world.py`, `agents/advisors.py`
- Outputs: `llm/client.py`, `llm/router.py`, `llm/mock_driver.py`, `agents/leader.py`

## Interfaces touched

- New Protocol `LlmDriver.choose(proposals, rng) -> List[AdvisorProposal]`
- Leader delegates `llm` mode selection to router; pass through `rng` for determinism

## Steps (60–90 minutes)

- Create `llm/` package with `client.py` (protocol), `router.py` (provider selection), `mock_driver.py` (deterministic policy)
- Update `agents/leader.py` to call router in `llm` mode
- Keep transcript identical under `seed=42`

## Acceptance tests

- Gate Runner passes (`python scripts/gate_runner.py` → empty arrays)
- Determinism: two runs with `--leader llm --seed 42` produce identical transcripts; exactly one `Action taken:` line
- Default routing: without `WARGAME_LLM`, mock driver used and selection mirrors pre‑change behaviour

## Prompt contract

- None (mock driver only; no external API)

## Budgets and limits

- Time: 60 minutes
- No network/API calls; no new runtime dependencies

## Self‑check rubric

- No schema drift; CLI options unchanged; transcript unchanged under seed=42

## Risks and rollback

- Risk: transcript drift if selection policy changes; Rollback: revert `agents/leader.py` change and remove `llm/`

## Handoff triggers

- If determinism breaks or gate fails, pause and escalate to coordinator

