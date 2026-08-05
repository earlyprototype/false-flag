# LLM context and routing — system state, 2026-08-05

A trace of every LLM call the engine makes: what data enters each prompt, which state object and
field it comes from, how it is bounded, why the call exists, and what its output changes. Plus
the state the engine maintains that reaches no prompt.

State of the source at **`d197c44`** (branch `claude/false-flag-game-ux-2j8rea`).
Measurements against `saves/parked_campaign4_borrowed_faces.json` — 1,853 transcript lines,
729,186 characters, 17 completed turns.

## Files

| File | Contents |
|---|---|
| `SCHEMATIC.md` | The trace. Every call, every input row, marked `IN` (reaches the prompt) or `OUT` (available and not sent). 177 `IN`, 68 `OUT`. |
| `VERIFIED-NOTES.md` | 60 statements checked directly against the source. Supersede any conflicting row in `SCHEMATIC.md` or `data/maps/`. |
| `html/schematic.html` | Same material, tabbed, for browsing. |
| `data/agent-reports/` | The 14 source reports this was assembled from, verbatim — six call-group maps, six verification passes, the state-reachability pass, and `synthesis.md`, a prose account of the whole system. |
| `data/maps/` | Per-group call maps, structured. |
| `data/verification/` | Per-group verification results, structured. |
| `data/orphans.json` | State reachability, structured. |
| `data/audit.json` | Everything above in one file. |
| `data/workflow.js`, `data/gen.py`, `data/export.py` | Regenerate this folder against a later commit. |

Issues arising are filed in [`../ENGINE-ROUTING-ISSUES.md`](../ENGINE-ROUTING-ISSUES.md) as
`ER-001` to `ER-014`.

## Reading the trace

Every input row carries its source object and field, its bound (or `unbounded`), and a
`file:line`. Rows marked `OUT` are data the call site holds and does not send.

Precedence: `VERIFIED-NOTES.md` over `SCHEMATIC.md` over `data/maps/*.json`. The map files are
untouched source data; notes are filed against them rather than merged into them, so both remain
inspectable.

## System shape

Twelve distinct call families, roughly fifteen dispatches per turn.

**Context assembly.** Eight of twelve families open with the shared briefing dossier
(`build_shared_context_prefix`) and are mutually cacheable — 99.4% identical to one another on
the measured campaign. The other four build their own context: inject generation, the narrator,
the three adjudication calls, the actor group and both diplomacy calls.

**Model selection.** Eight of twelve pass no `LLMContext`, so the router leaves `model_name` as
`None` and the driver default applies. This is a different eight. The per-context tier table and
the `/llm` menu govern the discussion, decision, inject and diplomacy families only.

**Windowing.** The transcript is bounded at 320,000 characters, split 0.2 head / 0.8 tail on
whole-turn boundaries. On the measured campaign that yields turn 1 and turns 12–17, eliding turns
2–11 (1,099 lines) from every dossier-carrying prompt, with 13,351 characters of budget unspent.
The bound was chosen against a 128,000-token context window; the campaign is ~182,000 tokens
whole and a full advisor prompt built from the windowed block is ~78,700 tokens.

**State reachability.** 31 of 41 audited fields reach no prompt. The event ledger reaches one
call family; the campaign history reaches eight; no prompt holds both.

## Unverified

No call was made to a live provider from the environment this was produced in. Prefix-overlap
figures are byte comparisons of prompts the engine emits and are exact; whether a provider
reports a cache hit on a prefix of that size is unconfirmed. `file:line` references were checked
by reading, not by execution.

## Scope

Read-only. Nothing here changes engine behaviour.
