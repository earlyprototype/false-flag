# Verification Matrix — live evidence for yesterday's work

## Why this document exists

The 2026-08-06 campaign closed 48 of 49 register entries and the test suite is green
(471 passing). Six turns of live play then surfaced four basic defects — a vanishing
phone call, a truncated synopsis, silent actor voices, a confabulated seed. The lesson
is not those four defects; it is that **a green suite was treated as proof that the
game works, and it is not**. Mocks encode the failure shapes we have already imagined.
The live model is the only adversarial input generator that produces the ones we
haven't.

This matrix therefore re-opens the question for every register entry: the entry's
*fix* may be merged and tested, but its *why* — the player-visible improvement the fix
was for — has evidence or it doesn't. A row without evidence stays open, whatever the
suite says.

Status vocabulary:

- `no-evidence` — merged and unit-tested, but nothing has demonstrated the why in play.
- `mock-only` — the why is fully checkable without a live model (pure mechanics), and a
  deterministic test demonstrates it end-to-end. This is the ceiling for a small set of
  rows; it is explicitly *not* claimed for anything a live model could still break.
- `live-verified` — demonstrated in a recorded live run; the evidence column says where.
- `content-open` — authored-content work still to do (not a code defect).

## The instrument

One tap in `llm/router.py` (env-gated, e.g. `WARGAME_CALL_LOG=<path>`) writes one JSONL
record per LLM call:

```
{turn, seq, family, tier, resolved_model, prompt, raw_reply, finish_reason,
 latency_ms, parsed, parse_misses_delta, residue_lines}
```

This single log yields evidence for four different columns at once:

- **input-side** — grep the prompt for the block a fix was supposed to deliver
  ("does the quality prompt at turn 5 contain the turn-3 decision?");
- **output-side** — diff `raw_reply` against `parsed`; `residue_lines` counts
  non-empty reply lines no parser consumed;
- **routing** — `resolved_model` per family vs the tier table;
- **truncation** — `finish_reason == "length"` anywhere is a finding.

Supplemented by: per-turn `GameManager.to_dict` state dumps; per-turn parse-health
snapshots; save→load→continue probes at chosen phase boundaries; wall-clock per
decision phase; a same-seed re-run for the seeded-rng rows.

The tap depends on two Pass-1 changes: drivers must surface `finish_reason`
(truncation class), and parsers must report residue (unparsed-line accounting).
Both are engine improvements in their own right, not just instrumentation.

## A — Input side: what reaches the calls that decide

The campaign's biggest why: the three deciding families (quality assessment, actor
simulation, diplomatic outcome) were context-starved at ~6% prompt share while
advisory calls got ~89%.

| ER | The why (player-visible intent) | Evidence required in a live run | Instrument | Status |
|---|---|---|---|---|
| ER-017 | Deciding calls know what has happened in the campaign | Quality, actor and outcome prompts at turn N contain the turn N-1 decision and its outcome; SITUATION SUMMARY and DECISIONS AND OUTCOMES blocks present | call log: prompt grep per family per turn | no-evidence |
| ER-010 | The per-turn synopsis call actually feeds play | Each turn's synopsis (from the fold call) appears verbatim inside next turn's deciding prompts | call log: reply of SITUATION_SUMMARY at T ⊂ prompts at T+1 | no-evidence |
| ER-048 | The synopsis stays grounded over a full arc | 18 turns of synopses read against the event record: no merged events, no invented attributions, no mid-sentence endings | call log: content pass over all SITUATION_SUMMARY replies | no-evidence |
| ER-020 | Generated events continue the story instead of restarting it | Inject prompts contain the rolling synopsis; generated injects reference established events | call log: inject prompt grep + content read of injects | no-evidence |
| ER-002 | The omissions scan critiques the actual plan | Omissions prompt contains the interpretation text of the decision being scanned | call log: prompt grep | no-evidence |
| ER-003 | One prompt holds both campaign history and staged events | Shared prefix in deciding prompts shows the event ledger after CURRENT SITUATION | call log: prompt grep | no-evidence |
| ER-043 | The narrator reacts to what the player did | Narrator prompt contains the last decision; narrator text references it | call log + content read | no-evidence |
| ER-001 | The do-not-restage rule always applies | Turn-1 inject prompt carries rule 8 with the empty-ledger header | call log: turn 1 | no-evidence |
| ER-012 | Authored national motives shape actor behaviour | USA/RUS actor prompts contain their authored stance blocks | call log: actor prompts | no-evidence |
| ER-014 | Foreign actors don't see UK internal politics | Actor prompts contain no UK advisor-trust block | call log: negative grep | no-evidence |
| ER-018/038 | Counterparts see a sane, safe transcript slice | Encounter prompts: target-country blocks whole, zero advisor/PM-question lines, zero UK private metrics | call log: encounter prompts | no-evidence |
| ER-041 | The scripted call knows why it is calling | Encounter prompt contains the authored premise block; emergent mode shows no metrics | call log: the scripted-call turn | no-evidence |
| ER-021 | Advisors never conspire against their own PM | Mystery on: briefing-audience prompts lack the deceive block; roleplay prompts have it | call log: audience split grep | no-evidence |
| ER-008 | Context stays bounded as the transcript grows | Prompt sizes per family flat-ish across 18 turns, under their caps | call log: len(prompt) trend | no-evidence |
| ER-009/027 | The outcome assessor reads bands it is allowed to use | Outcome prompt: bands present once, contradictory instruction absent | call log: outcome prompts | no-evidence |

## B — Output side: what the engine hears back

| ER | The why | Evidence required | Instrument | Status |
|---|---|---|---|---|
| ER-015/006/034/031/039 | A decision's consequences all land, exactly once | Raw quality replies vs parsed: every effect line lands (decorated, annotated, worded); multiplier applied once; zero residue | call log diff + state dumps | no-evidence |
| ER-016/030 | A refusal costs the player, never pays them | Any live refusal parses as refusal; alliance moves the right direction | call log + state dumps | no-evidence |
| ER-049 | Foreign governments are never silent when they spoke | public_response non-empty whenever the raw reply carries prose; continuations retained | call log diff | no-evidence |
| ER-029 | Diplomatic outcomes track the conversation | Outcome enum + delta match the raw reply on every encounter | call log diff | no-evidence |
| ER-035/036 | Cabinet objections and omissions survive formatting | Any bulleted/decorated objection appears in the pushback shown; sentinels only standalone | call log diff | no-evidence |
| ER-042 | Generated events' effects apply or visibly skip | Every inject effect either lands in state or produces a transcript skip line | call log + state dumps | no-evidence |
| ER-044 | The CLI decision panel never empties on decorated output | Unit corpus + one live CLI sample | mock + spot check | no-evidence |
| ER-045 | A partial batch failure is visible | Deterministic fault-injection test (cannot be forced live) | mock | mock-only |

## C — Routing, dispatch, speed

| ER | The why | Evidence required | Instrument | Status |
|---|---|---|---|---|
| ER-019/005 | Money goes where quality matters | `resolved_model` per family matches the tier table on every call (FLASH→qwen, PRO→sonnet in the shakedown config) | call log | no-evidence |
| ER-011 | Output caps are real on every driver | Caps present in outbound requests; no family silently uncapped | call log (+ driver echo) | no-evidence |
| ER-023 | The decision phase is fast | Wall-clock per decision ≈ 3 serialized round-trips, not 7 | timing log | no-evidence |
| ER-032 | Rate limiting survives tier alternation | Thread-hammer unit (live traffic too light to show it) | mock | mock-only |
| ER-033 | The authored phone call is playable everywhere | The scripted encounter fires on the headless path, is drivable, capped, applies its delta once | live run reaches it + state dumps | no-evidence |
| ER-022 | The HTTP front end can serve a whole game | /briefing works turn 2+ under TestClient; optional live API probe | mock (+probe) | mock-only |
| ER-026 | Inject settings mean what they say | Banner only when generation enabled and firing | live run transcript | no-evidence |
| ER-004 | Resuming a save never re-runs a turn | Save mid-turn during the live run, reload, continue: no duplicate briefing, no double ledger write | save/load probe | no-evidence |

## D — State over time

| ER | The why | Evidence required | Instrument | Status |
|---|---|---|---|---|
| ER-047 | Nothing live is lost by saving | Save during an active encounter, reload, finish the call | save/load probe in the live run | no-evidence |
| ER-037/025 | A seed is a promise | Same-seed re-run: identical rng-driven draws (mystery secret, inject rolls); mid-run save/resume: identical continuation (rng path; model text exempt) | seeded re-run + probe | no-evidence |
| ER-007 | Characters remember how you treat them | Attitude values move after actor-path turns | state dumps diffed per turn | no-evidence |
| ER-013 | Overruling the cabinet has a price | Commit unamended over pushback → objectors' trust drops in the dump | state dumps | no-evidence |
| ER-024 | The transcript is a clean record | Zero duplicated question lines across 18 turns | transcript scan | no-evidence |

## E — Content and front-end truth

| Item | The why | Evidence required | Instrument | Status |
|---|---|---|---|---|
| ER-046 | Every simulated capital has authored motives | FRA/DEU/POL (exact set per auditor) get stances, or their absence is handled deliberately | authoring + call log | content-open |
| Scene-setting | The game opens with an introduction, not a cold data dump | A fresh emergent game shows narrative scene-setting before the first SITREP on every front end | per-front-end trace + live run | content-open |
| Markdown leakage | Player-facing text renders clean on every front end | Zero raw `**`/`##` artefacts in player-visible output across the run | transcript scan | no-evidence |
| British English | UK voices sound like the UK government | Content pass over advisor/narrator/synopsis text; foreign actors exempt | content pass | no-evidence |
| Tone/coherence | The game is actually good to play | Full-transcript read: tension builds, consequences bite, no non-sequiturs | content pass | no-evidence |

## F — Systemic invariants (new work, not re-verification)

These make the unseen failure classes announce themselves. They are prerequisites for
several evidence columns above and permanent engine features besides.

| Invariant | What it catches |
|---|---|
| Parse residue accounting — every non-empty reply line consumed or counted | The next ER-049 before a player ever sees it |
| Per-family semantic contracts after every parse | Structurally "successful" parses that are semantically empty |
| Driver-level finish_reason surfacing → truncation recorded | Every future cap-hit, not the one we noticed |
| Save/load completeness by introspection, not hand-listed fields | The next ER-047 at feature-add time |
| Health surfaced every turn on every front end | Silence stops being ambiguous |

## Order of work

1. Pass-1 fixes: the four auditors' class findings + the F-row invariants + the call-log
   tap. All mock-verifiable, zero API spend. **Findings shown before any merge.**
2. Pass-2 shakedown: one recorded 18-turn live campaign (seeded, mystery emergent,
   scripted-call turn included, save/load probes at chosen boundaries, same-seed
   partial re-run), then the mechanical diffs and the content pass.
3. Every row above moves to `live-verified`, `mock-only` (with justification), or gets
   a new register entry. Rows that stay `no-evidence` are said out loud, not absorbed.
