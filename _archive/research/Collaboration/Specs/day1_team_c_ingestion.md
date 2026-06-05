# Day‑1 Spec — Team C (Scenario & Ingestion)

Status: Draft
Owner: Team C

## Purpose
Prepare scenario stubs and verify references so Engine can run a sample scene.

## Inputs and outputs
- Inputs: public podcast transcript links (to be provided later)
- Outputs: data/scenarios/war_game_2025/initial_conditions.yaml, events.yaml; assets/placeholders/*.txt (at least one referenced)

## Allowed tools and permissions
- Edit YAML under data/scenarios/war_game_2025/
- Add .txt assets under assets/placeholders/

## Interfaces touched
- events.yaml fields: when/trigger/channel/effects/image

## Steps (60–90 minutes)
- Ensure events.yaml validates and references an existing placeholder image.
- Add at least one media inject (scene 1) with a panel reference.

## Acceptance tests
- `media_leak_01` exists; referenced `assets/placeholders/media_leak.txt` exists.

## Prompt contract
- None for Day‑1.

## Budgets and limits
- Time: 60 minutes

## Self-check rubric
- YAML loads without errors; file paths are correct.

## Handoff triggers
- If more inputs required (transcripts), prepare a Handover Capsule listing needed links.


