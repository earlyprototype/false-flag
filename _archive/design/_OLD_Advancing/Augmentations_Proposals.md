# Augmentations Proposals (Optional Features)

Status: Draft
Change classification: S

Purpose: List optional enhancements beyond Podcast Fidelity Mode. These can be toggled on for experiments and playtests.

## Options
- Numeric UI: display live metrics; keep off by default, reveal in After‑Action Review.
- Event decks: limited randomised injects per phase for variety, with strict gating.
- Action Points (AP): replace agenda slots with points for more granular decisions.
- Adaptive storytelling: light drama manager to maintain pacing while respecting constraints.
- Agent‑based incidents: background systemic incidents driven by posture and hazards.
- Media generator: stylised headlines or press summaries from large language models with guardrails.
- Analytics: batch headless runs, CSV/JSON exports, coverage metrics.

## Verification
- Each augmentation must be deterministic when seeded and must not break core invariants.
- Add a specific acceptance test and a configuration toggle for each feature.

## Next steps
- Prioritise 1–2 augmentations for the first playtest once core fidelity is stable.


