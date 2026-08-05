# Engine routing issues register

Open register of defects and design gaps in how the engine assembles context, routes calls and
consumes results. Append to it; do not rewrite closed entries.

## Conventions

Each entry gets a permanent `ER-nnn` id, allocated in sequence and never reused. Status is one
of `open`, `in-progress`, `fixed`, `wontfix` or `invalid`. An entry that turns out to be wrong
becomes `invalid` with a note — it is not deleted, so the id stays stable in anything that cites
it.

Every entry states what is observed, the file:line that establishes it, and what it causes.
An entry without evidence is not ready to file.

Areas: `context` (prompt assembly and windowing), `routing` (model and provider selection),
`dispatch` (concurrency, rate limits, failure handling), `parsing` (consuming model output),
`state` (data maintained but unreached), `data` (scenario and config content).

| id | status | sev | area | summary |
|---|---|---|---|---|
| ER-001 | open | high | context | Empty event ledger removes the do-not-restage rule |
| ER-002 | open | high | context | Decision interpretation never reaches the omissions prompt |
| ER-003 | open | high | context | No prompt holds both campaign history and event ledger |
| ER-004 | open | high | dispatch | Inject generation can fire twice in one turn on a resumed save |
| ER-005 | open | med | routing | Five of twelve call families bypass the model configuration |
| ER-006 | open | med | parsing | Effects parser can absorb prose from the reasoning paragraph |
| ER-007 | open | med | state | Advisor trust updates on one adjudication path only |
| ER-008 | open | med | context | Two context builders apply no size limit |
| ER-009 | open | low | context | Three metrics rendered three times in every dossier prompt |
| ER-010 | open | med | state | Situation summary costs a call per turn and reaches no prompt |
| ER-011 | open | low | dispatch | Narrator output constraints dropped on some drivers |
| ER-012 | open | med | data | Faction stances reach no prompt and barely match the actor roster |
| ER-013 | open | low | state | Advisor pushback mutates nothing |
| ER-014 | open | med | context | State-actor prompt carries UK internal advisor trust |

---

## ER-001 — Empty event ledger removes the do-not-restage rule

- **Status:** open · **Severity:** high · **Area:** context
- **Observed:** Continuity rule 8 is appended to the inject prompt only under
  `if event_ledger:`. An empty list is falsy, so an empty ledger omits both the EVENTS ALREADY
  PLAYED block and the instruction not to restage resolved events.
- **Evidence:** `llm/prompts.py:422` · `models/narrative_state.py:88` · `engine/persistence.py:134`
- **Reachable when:** a fresh campaign before the first event is recorded; any save written
  before `event_ledger` existed, which reloads with the empty default.
- **Effect:** The failure mode is unguarded rather than degraded. This is the condition in which
  a resolved event can be restaged as a fresh discovery.
- **Raised by:** context audit 2026-08-05

## ER-002 — Decision interpretation never reaches the omissions prompt

- **Status:** open · **Severity:** high · **Area:** context
- **Observed:** `check_critical_omissions` accepts `interpretation` as a parameter.
  `build_critical_omissions_prompt` neither accepts nor interpolates it. Advisor `personality` is
  read into a local on the same path and likewise never interpolated.
- **Evidence:** `engine/sim_loop.py:569` · `agents/conversation.py:376-381` ·
  `llm/prompts.py:462-553`, `:491`
- **Effect:** Five advisors judging whether a decision omitted something catastrophic work from
  the raw typed text rather than the structured reading produced for that purpose moments
  earlier.
- **Raised by:** context audit 2026-08-05

## ER-003 — No prompt holds both campaign history and event ledger

- **Status:** open · **Severity:** high · **Area:** context
- **Observed:** The ledger reaches `build_inject_generation_prompt` only. That prompt contains no
  GAME HISTORY block. The eight prompts that do carry history do not receive the ledger.
- **Evidence:** `llm/context_builder.py:285-355` (dossier, no ledger) ·
  `llm/context_builder.py:391-439` (inject context, no history)
- **Effect:** On a campaign past the 320,000-character budget the dossier prompts lose the
  elided turns entirely — turns 2–11 on the measured save — and the one structure that states
  each past event's disposition in a single line is not among what survives. Cost of including
  it: ~1,600 characters against 13,351 left unspent by the window.
- **Raised by:** context audit 2026-08-05

## ER-004 — Inject generation can fire twice in one turn on a resumed save

- **Status:** open · **Severity:** high · **Area:** dispatch
- **Observed:** The generation branch of `run_turn_briefing` has no `replay` guard; `replay` is
  consulted only for effects and the diplomatic encounter. Loading a save taken mid-turn re-runs
  the briefing with `replay=True`.
- **Evidence:** `engine/sim_loop.py:311-324`, `:384`, `:396` · `cli/main.py:729`, `:859`
- **Effect:** A second event is generated for a turn that already has one, and a second ledger
  entry is written for that turn.
- **Raised by:** context audit 2026-08-05

## ER-005 — Five of twelve call families bypass the model configuration

- **Status:** open · **Severity:** medium · **Area:** routing
- **Observed:** The narrator, action quality assessment, advisor reactions, situation summary and
  state actors pass no `context=`, so the router leaves `model_name` as `None` and the driver
  default applies. `LLMContext.CHARACTER_RESPONSE` is defined and mapped to FLASH but has no live
  call site — `generate_group` is invoked positionally at the reactions call site, so `context`
  keeps its default. No `STATE_ACTOR` member exists.
- **Evidence:** `llm/router.py:231-234`, `:331-335` · `llm/model_config.py:10-38` ·
  `engine/narrative_adjudication.py:545` · `engine/actor_simulation.py:131`
- **Effect:** The per-context tier table and the `/llm` settings menu govern the other seven
  families only. The adjudication half of a turn is outside them.
- **Raised by:** context audit 2026-08-05

## ER-006 — Effects parser can absorb prose from the reasoning paragraph

- **Status:** open · **Severity:** medium · **Area:** parsing
- **Observed:** The effects branch accepts any line containing a colon and the substring
  `escalation`, `alliance` or `stability`. A continuation line of the REASONING paragraph in that
  shape is read as a metric effect. Separately, a multiplier parsing to exactly 1.0, or absent,
  is overridden by the quality-to-multiplier table.
- **Evidence:** `engine/narrative_adjudication.py:374-381`, `:383-399`
- **Effect:** Narrative prose can move hidden metrics. A casualties line is silently discarded by
  the same filter, since only those three substrings are accepted.
- **Raised by:** context audit 2026-08-05

## ER-007 — Advisor trust updates on one adjudication path only

- **Status:** open · **Severity:** medium · **Area:** state
- **Observed:** `_update_character_attitudes` is called on the narrative adjudication path and
  never on the actor-simulation path. The two paths also derive base effects differently —
  LLM-suggested effects on one, a keyword heuristic merged 60/40 with actor effects on the other.
- **Evidence:** `engine/narrative_adjudication.py:788`, `:928-943`, `:865-876`
- **Effect:** Advisor trust responds to decision quality in one mode and not the other.
- **Raised by:** context audit 2026-08-05

## ER-008 — Two context builders apply no size limit

- **Status:** open · **Severity:** medium · **Area:** context
- **Observed:** `get_diplomatic_context` applies no bound to its filtered transcript. The
  narrator takes the last 20 transcript elements with no character cap; one element can be an
  unwrapped paragraph.
- **Evidence:** `llm/context_builder.py:441-512` · `llm/prompts.py:587`
- **Effect:** Same shape as the overrun already corrected in the advisor window, where 400 long
  lines reached 792,572 characters against a 320,000 budget. Prompt size is unbounded by input.
- **Raised by:** context audit 2026-08-05

## ER-009 — Three metrics rendered three times in every dossier prompt

- **Status:** open · **Severity:** low · **Area:** context
- **Observed:** Raw values out of 100, prose bands, and KEY INTELLIGENCE FLAGS. The flags are
  five booleans thresholded from those same three metrics, in a dict replaced rather than
  accumulated each turn.
- **Evidence:** `llm/context_builder.py:335-341`, `:351-352` · `engine/flags.py:15-40`
- **Effect:** The third rendering carries no information the first two do not.
- **Raised by:** context audit 2026-08-05

## ER-010 — Situation summary costs a call per turn and reaches no prompt

- **Status:** open · **Severity:** medium · **Area:** state
- **Observed:** `update_situation_summary` issues an LLM call and overwrites
  `NarrativeState.situation_summary`. That field is absent from `to_llm_context()`, is not
  written to the save transcript, and is read only by emergent-mode display and three CLI render
  sites. The call also does not receive the previous summary it replaces.
- **Evidence:** `engine/narrative_adjudication.py:675-689` · `models/narrative_state.py:233-234`
- **Effect:** One call per turn produces text no model ever sees.
- **Raised by:** context audit 2026-08-05

## ER-011 — Narrator output constraints dropped on some drivers

- **Status:** open · **Severity:** low · **Area:** dispatch
- **Observed:** The narrator passes `system_instruction`, `temperature` and `max_tokens=150`.
  None is honoured on the gemini, mock or offline drivers.
- **Evidence:** `engine/narrator.py:39-41`
- **Effect:** The length cap on the bridge text is not enforced.
- **Raised by:** context audit 2026-08-05

## ER-012 — Faction stances reach no prompt and barely match the actor roster

- **Status:** open · **Severity:** medium · **Area:** data
- **Observed:** `NarrativeConfig.to_llm_context()` is always called without a country argument,
  so per-country secret motive, public posture, economic leverage and intelligence-sharing level
  are skipped everywhere. Separately, stances are defined for RUS, USA, CHN and IRL while the
  state actors are USA, FRA, DEU, POL and RUS.
- **Evidence:** `llm/context_builder.py:323` · `models/narrative.py:46-67` ·
  `data/state_actors.yaml:5, 36, 69, 99`
- **Effect:** Authored per-country content is never used. Only USA and RUS appear in both sets:
  CHN and IRL have stances no actor can voice, and FRA, DEU and POL respond with no scripted
  stance behind them.
- **Raised by:** context audit 2026-08-05

## ER-013 — Advisor pushback mutates nothing

- **Status:** open · **Severity:** low · **Area:** state
- **Observed:** No metric, flag, trust value or ledger entry is written from pushback output
  anywhere. It drives the confirm gate and the transcript only. In the API path every entry is
  given the canned recommendation "Consider revising your approach."
- **Evidence:** `engine/game_manager.py:213-219`
- **Effect:** A cabinet objection has no mechanical consequence.
- **Raised by:** context audit 2026-08-05

## ER-014 — State-actor prompt carries UK internal advisor trust

- **Status:** open · **Severity:** medium · **Area:** context
- **Observed:** Every UK advisor's name, relationship label and trust score is interpolated into
  the prompt sent as a foreign government's private assessment.
- **Evidence:** `engine/actor_simulation.py:32-85`
- **Effect:** A foreign actor reasons from the UK cabinet's internal state.
- **Raised by:** context audit 2026-08-05
