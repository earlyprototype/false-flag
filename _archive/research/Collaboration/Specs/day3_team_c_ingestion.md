# Day‑3 Spec — Team C (Scenario & Ingestion)

Status: Draft
Owner: Team C

## Purpose
Extend scenario ingestion with scaffolds (transcripts → segments → events), add a safe early‑scene inject, and keep gate checks green and deterministic (seed=42).

## Inputs and outputs
- Inputs: public transcript links (placeholder), existing `data/scenarios/war_game_2025/*`
- Outputs: `ingestion/transcripts.py`, `ingestion/segmenter.py`, `ingestion/extract_events.py`, `@filing/transcripts/day3_sample.md`, updated `events.yaml`, new panel in `assets/placeholders/`

## Allowed tools and permissions
- Edit under `ingestion/`, `data/scenarios/war_game_2025/`, `assets/placeholders/`, and `@filing/`

## Interfaces touched
- Reads: none wired yet (scaffolds only)
- Data shape (events.yaml items):
  ```yaml
  - id: <string>
    when: { scene_eq: <int> }
    trigger: { always: true }
    channel: <string>
    effects:
      - metric: <Metrics field>
        delta: <int or "-a..+b">  # midpoint chosen deterministically
    image: assets/placeholders/<id>.md
  ```

## Steps (60–90 minutes)
- Create ingestion scaffolds with no external dependencies:
  - `transcripts.py`: load local text and normalise
  - `segmenter.py`: naive paragraph splitter
  - `extract_events.py`: placeholder that returns an empty list or sample
- Add `@filing/transcripts/day3_sample.md` (provenance placeholder)
- Add a new panel `assets/placeholders/briefing_slide_01.md`
- Append a safe inject to `events.yaml` referencing the new panel (scene 1), appended at end to avoid order changes

## Acceptance tests
- Gate: `python scripts/gate_runner.py` → all sections empty arrays
- CLI smoke: `python -m cli.main --scenario war_game_2025 --seed 42 --leader llm` continues to show `Inject: media_leak_01` and effect line; deterministic across runs
- All `image` paths in `events.yaml` end with `.md` and exist

## Edge cases
- Missing transcript file → scaffold functions return empty outputs (no exceptions)
- Malformed YAML not introduced; events appended preserve indentation and order

## Verification notes (PowerShell)
- `python scripts\gate_runner.py`
- `python -m cli.main --scenario war_game_2025 --seed 42 --leader llm`

## Risks and rollback
- Low: scaffolds are unused by engine; event appended at end preserves existing behaviour. To rollback: remove the appended block and panel file.


