# LLM context and routing audit — 2026-08-05

A full trace of every LLM call the game makes: what data enters each prompt, where that data
comes from, how it is bounded, why the call exists, and what its output changes. Plus a list of
game state that is maintained every turn and reaches no prompt at all.

Traced against the source at **`d197c44`** (branch `claude/false-flag-game-ux-2j8rea`).
Measurements taken against `saves/parked_campaign4_borrowed_faces.json` — 1,853 transcript
lines, 729,186 characters, 17 completed turns.

## Start here

| File | What it is |
|---|---|
| **`SCHEMATIC.md`** | The trace. Every call, every input row, marked `IN` (reaches the prompt) or `OUT` (available and not sent). 177 `IN`, 68 `OUT`. |
| **`CORRECTIONS.md`** | 60 first-pass claims that a second pass overturned or corrected. **Authoritative over `SCHEMATIC.md` and `data/maps/`.** |
| **`html/schematic.html`** | The same material as a tabbed page, if you want to browse rather than grep. |
| `synthesis.md` | Narrative version of the whole audit. |
| `data/` | Structured source: per-group maps, per-group corrections, state reachability, the workflow script. |

## How to read it

Every input row carries its source object and field, its bound (or `unbounded`), and a
`file:line` reference. A row marked `OUT` is data the call site has in hand and does not send —
those are the rows worth reading first.

**Trust order.** `CORRECTIONS.md` beats `SCHEMATIC.md` beats `data/maps/*.json`. The map files
are raw first-pass output and have *not* been rewritten; the corrections are filed against them
rather than merged into them, so both are visible. Where a correction and a map row disagree,
the correction holds. `REFUTED` overturns a substantive claim; `CORRECTED` is usually a wrong
line number with the substance intact.

**What is not verified.** No call was made to a live provider from the environment this was
produced in. Prefix-overlap figures are byte comparisons of prompts the game emits, which is
exact; whether a provider *reports* a cache hit on a prefix of that size is unconfirmed. Line
references have been checked by a second pass but not by execution, except where noted.

## The shape of it

Twelve distinct call families, roughly fifteen dispatches per turn.

- **Eight of twelve** open with the shared briefing dossier (`build_shared_context_prefix`) and
  are therefore mutually cacheable — 99.4% identical to one another on the measured campaign.
  The other seven build their own context from scratch.
- **Eight of twelve** pass no `LLMContext`, so the router never consults the per-context model
  table and the driver default applies. These are a *different* eight. The `/llm` settings menu
  therefore governs the discussion, decision, inject and diplomacy families only.
- **31 of 41** audited state fields reach no prompt at all.
- The transcript is windowed at 320,000 characters. On the measured campaign that elides turns
  2–11 — 1,099 lines — from every dossier-carrying prompt, leaving turn 1 and turns 12–17.

## Headline issues

Full list with evidence at the end of `html/schematic.html` (ISSUES tab). The ones with the most
consequence:

1. **An empty event ledger removes the do-not-restage rule as well as the data.** Continuity
   rule 8 is appended only under `if event_ledger:`. Reachable on a fresh campaign and on any
   save predating the field. Unguarded, not degraded.
2. **The decision interpretation is passed to the critical-omissions check and never reaches the
   prompt.** Five advisors judge whether a decision omitted something catastrophic while working
   from the raw typed text.
3. **No prompt holds both the campaign history and the event ledger.** The eight prompts that
   lose ten turns to elision do not get the ledger; the one prompt that gets it carries no
   history block. The ledger would cost ~1,600 characters against 13,351 unspent.
4. **Inject generation can fire twice in one turn on a resumed save** — the generation branch has
   no `replay` guard.
5. **The situation summary costs a call per turn and reaches no prompt** — it is display-only.

## Reproducing it

`data/workflow.js` is the script that produced this. It fans out six mappers (one per call
group), pairs each with a reviewer instructed to refute, audits state reachability, and merges.
Re-running it against a later commit regenerates `data/`; `SCHEMATIC.md`, `CORRECTIONS.md` and
the HTML are generated from that data by the scripts noted in the commit that added this folder.

## Scope

Read-only. Nothing in this folder changes game behaviour.
