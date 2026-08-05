# Engine routing issues register

Open register of defects and design gaps in how the engine assembles context, routes calls and
consumes results.

## Conventions

Each entry carries a permanent `ER-nnn` id, allocated in sequence and never reused. Status is one
of `open`, `in-progress`, `fixed`, `wontfix` or `invalid`. An entry that turns out to be wrong is
marked `invalid` with a note rather than deleted, so anything citing that id still resolves.

Every entry states what is observed, the file and line that establishes it, and what it causes
during play. An entry without evidence is not ready to file. Where an entry quotes the result of a
demonstration, it states the exact input that produced it.

Areas: `context` (prompt assembly and windowing), `routing` (model and provider selection),
`dispatch` (concurrency, rate limits, failure handling), `parsing` (consuming model output),
`state` (data maintained but unreached), `data` (scenario and config content).

| id | status | sev | area | summary |
|---|---|---|---|---|
| ER-012 | open | high | data | Authored per-country content reaches no prompt |
| ER-032 | open | high | dispatch | The rate limiter is discarded on every model-tier switch |
| ER-033 | open | high | dispatch | The scripted diplomatic call answers itself on two front ends |
| ER-034 | open | high | parsing | An annotated number is dropped and its siblings are applied |
| ER-035 | open | high | parsing | A bulleted cabinet objection is read as no objection |
| ER-036 | open | high | parsing | Two acceptance rules discard real critical omissions |
| ER-015 | open | high | parsing | Decorated labels drop the decision's metric effects |
| ER-016 | open | high | parsing | Decorated actor replies invert a refusal |
| ER-029 | open | high | parsing | The diplomatic outcome parser shares the same defect |
| ER-030 | open | high | parsing | A worded refusal is read as conditional support |
| ER-017 | open | high | context | The calls that change the game never learn what happened in it |
| ER-018 | open | high | context | The diplomatic transcript filter is erratic in both directions |
| ER-019 | open | high | routing | The per-call model table is inert on the shipped provider |
| ER-020 | open | high | context | The story generator is given a digest instead of a synopsis |
| ER-022 | open | high | dispatch | The HTTP path serves no briefing after turn one |
| ER-002 | open | high | context | Decision interpretation never reaches the omissions prompt |
| ER-003 | open | high | context | No prompt holds both campaign history and event ledger |
| ER-004 | open | high | dispatch | A resumed mid-turn save re-runs the briefing |
| ER-045 | open | med | dispatch | A partial batch failure is invisible on the omissions scan |
| ER-037 | open | med | state | The random number position is not saved |
| ER-038 | open | med | context | A foreign counterpart is given the UK's private metrics |
| ER-041 | open | med | context | The scripted call drops its premise and shows hidden numbers |
| ER-042 | open | med | parsing | A generated event's effect is dropped when its delta is not an integer |
| ER-021 | open | med | context | Mystery Mode tells the player's own advisors to deceive them |
| ER-023 | open | med | dispatch | The decision phase runs seven waits where three would do |
| ER-025 | open | med | state | Mystery Mode draws its secret from an unseeded generator |
| ER-005 | open | med | routing | Five of twelve call families bypass the model configuration |
| ER-006 | open | med | parsing | The effects parser accepts any colon line naming a metric |
| ER-007 | open | med | state | Advisor trust updates on one adjudication path only |
| ER-008 | open | med | context | Two context builders apply no character bound |
| ER-010 | open | med | state | The situation summary costs a call per turn and reaches no prompt |
| ER-014 | open | med | context | The state-actor prompt carries UK internal advisor trust |
| ER-039 | open | low | parsing | The quality multiplier's effect is halved before it lands |
| ER-040 | open | low | context | The diplomatic exchange counter advances twice per exchange |
| ER-043 | open | low | context | The narrator is never told what the player decided |
| ER-044 | open | low | parsing | The decision summary panel empties on decorated output |
| ER-024 | open | low | context | Player questions are written to the transcript twice |
| ER-028 | open | low | routing | The play page offers no way to choose or change the model |
| ER-026 | open | low | dispatch | `--no-stochastic-injects` inverts into a banner switch |
| ER-001 | open | low | context | An empty event ledger removes the do-not-restage rule |
| ER-009 | open | low | context | The metrics are rendered twice and a third block adds nothing |
| ER-011 | open | low | dispatch | Output caps are dropped on three of four drivers |
| ER-013 | open | low | state | Advisor pushback mutates nothing |
| ER-031 | open | low | parsing | An explicit multiplier of 1.0 is indistinguishable from silence |
| ER-027 | open | low | context | An advisor instruction contradicts the outcome assessor's task |

## How the measurements below were taken

Two headless campaigns played through `dev-scripts/play_campaign.py` against the local recording
endpoint `dev-scripts/fake_openrouter.py`, one with no artificial latency and one holding every
call at 1.2 seconds. Both reached a terminal ending on turn 10 and issued 148 game calls.

Inputs: engine at commit `9f0c3fa`; scenario `war_game_2025`, default `standard` variant; seed 42;
play mode `emergent`; Mystery Mode on; endings on; one player question per turn.

```shell
python3 dev-scripts/fake_openrouter.py --port 8099 --log calls.jsonl --latency 0
# and, for the timing run, the same with --latency 1.2

WARGAME_LLM=openai_compat \
OPENAI_COMPAT_BASE_URL=http://127.0.0.1:8099/v1 \
OPENAI_COMPAT_MODEL=fake OPENAI_COMPAT_API_KEY=x \
NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost \
python3 dev-scripts/play_campaign.py --turns 18 --questions 1

python3 dev-scripts/analyse_calls.py calls.jsonl
```

Both runs ended with `play_campaign.py` reporting "no calls fell back to the mock driver", so every
one of the 148 calls in each run was answered by the endpoint under measurement rather than by the
built-in offline driver. That line is what makes the call counts and character totals mean
anything, and it should be quoted with any future measurement.

Timing figures are wall-clock and vary with the machine. The 8.5-second decision phase reproduces
across machines; the share of wall clock with exactly one call in flight measures between 76 and 80
per cent, so treat it as roughly three-quarters to four-fifths. Character counts and call counts do
not vary. Raw logs are not committed; they regenerate from the commands above in under two minutes.

---

## ER-001 — An empty event ledger removes the do-not-restage rule

- **Status:** open
- **Severity:** low
- **Area:** context
- **Observed:** Continuity rule 8, the instruction not to restage a resolved event, is appended to
  the inject prompt only under `if event_ledger:`. An empty list is falsy, so an empty ledger omits
  both the EVENTS ALREADY PLAYED block and the instruction that names it. The ledger is read at the
  top of the briefing and written further down the same call, so on any turn the generation branch
  fires the ledger already holds the earlier turns' entries.
- **Evidence:** `llm/prompts.py:422-424` (the gate); `engine/sim_loop.py:320-321` (the read) and
  `engine/sim_loop.py:334-337` (the write); `data/scenarios/war_game_2025/scenarios.yaml:31`
  (`stochastic_from: 7`) and `:48` (`stochastic_from: 4`)
- **Effect:** The rule and the data it names disappear together, which is correct behaviour for a
  rule pointing at an absent block. The exposure is narrow rather than absent: generation cannot
  fire before turn 7 in the standard variant or turn 4 in fast_start, by which point the ledger
  holds six or three entries. A variant with `stochastic_from: 1`, which the scenario file carries
  commented out at lines 58 to 63, would make the empty-ledger case live on turn one.

## ER-002 — Decision interpretation never reaches the omissions prompt

- **Status:** open
- **Severity:** high
- **Area:** context
- **Observed:** `check_critical_omissions` takes `interpretation` as its third parameter and never
  uses it. The comprehension that builds the five prompts passes `player_decision` and not
  `interpretation`, and `build_critical_omissions_prompt` has no parameter for it.
- **Evidence:** `agents/conversation.py:313` (the parameter), `agents/conversation.py:375-381` (the
  call that omits it); `llm/prompts.py:462-469` (no such parameter);
  `engine/sim_loop.py:566-575` (the caller that supplies it)
- **Effect:** Five advisors deciding whether the Prime Minister has omitted something catastrophic
  work from the raw typed sentence rather than from the structured reading, listing forces,
  resources, timeline and feasibility, produced for that purpose one call earlier. This is the most
  expensive group in the game: over a ten-turn campaign it was 53.7 per cent of every prompt
  character the engine sent.

## ER-003 — No prompt holds both campaign history and event ledger

- **Status:** open
- **Severity:** high
- **Area:** context
- **Observed:** The event ledger reaches the inject generation prompt and nothing else. That prompt
  carries no GAME HISTORY block. The four prompt families that do carry the history block never
  receive the ledger.
- **Evidence:** `llm/context_builder.py:285-355` (the shared dossier, no ledger);
  `llm/context_builder.py:391-439` (the inject context, no history block);
  `llm/context_builder.py:74-107` (`render_event_ledger`)
- **Effect:** Past a campaign of roughly 320,000 transcript characters the dossier prompts lose the
  elided middle of the campaign, and the one structure that states each past event and how it was
  left in a single line is not among what survives. On a seventeen-turn transcript the window keeps
  turn 1 and turns 12 to 17 and drops turns 2 to 11 entirely; the shape of that cut is
  input-independent, the exact leftover budget is not, because the remainder is whatever is smaller
  than one whole turn. A rendered ledger line costs about 64 characters with no closing note and
  about 160 once a disposition note is attached, so a whole 60-turn ledger is under 11,000
  characters against a 320,000-character budget.

## ER-004 — A resumed mid-turn save re-runs the briefing

- **Status:** open
- **Severity:** high
- **Area:** dispatch
- **Observed:** The dynamic-generation branch of `run_turn_briefing` tests only whether the scripted
  file is missing and whether stochastic generation is on. It has no `replay` guard; `replay` is
  consulted at the effects step and the diplomatic-encounter step only, and `record_played_event`
  runs on the replay path as well. The headless session object never passes `replay` at all, so its
  default of `False` stands and a resumed briefing there also re-applies the inject's effects and
  re-runs the mandatory diplomatic encounter.
- **Evidence:** `engine/sim_loop.py:316-329` (no guard), `:334-337` (the ledger write, ungated),
  `:384` and `:396` (the two guards that do exist), `:273` (`replay: bool = False`);
  `cli/main.py:729` and `:859`; `cli/main_dashboard.py:753` and `:862-875`;
  `engine/game_manager.py:143-154` (no `replay` argument) and `:604` (the restore)
- **Effect:** Loading a save taken mid-turn generates a second, different event for a turn that
  already had one. The first event's effects stay applied while the ledger entry for that turn is
  overwritten with the second event's title, so the record of what happened no longer matches what
  the metrics say happened. On the headless path the effects are applied twice and the scripted
  phone call runs again.

## ER-005 — Five of twelve call families bypass the model configuration

- **Status:** open
- **Severity:** medium
- **Area:** routing
- **Observed:** The narrator bridge, the action quality assessment, the advisor reactions, the
  situation summary and the state-actor simulation all dispatch without a `context=` argument, so
  the router leaves the model name as `None` and the driver's own default answers.
  `LLMContext.CHARACTER_RESPONSE` is defined, given a tier and offered in the in-game model menu,
  but is passed to nothing.
- **Evidence:** `engine/narrator.py:36-42`; `engine/narrative_adjudication.py:269`, `:545-546`,
  `:687`; `engine/actor_simulation.py:131`; `llm/router.py:229-234` and `:330-335`;
  `llm/model_config.py:19` and `:37`; `cli/model_settings_menu.py:33` and `:124`
- **Effect:** The per-context tier table and the in-game model menu govern seven families and not
  the other five. The entire adjudication half of a turn, the half that decides what happens, sits
  outside them. A sixth context-less dispatch exists at `engine/actor_simulation.py:99` with no
  caller outside tests. See ER-019: on the provider the public build uses, the table governs
  nothing at all.

## ER-006 — The effects parser accepts any colon line naming a metric

- **Status:** open
- **Severity:** medium
- **Area:** parsing
- **Observed:** The effects branch accepts any line containing a colon together with the substring
  `escalation`, `alliance` or `stability`, takes everything before the first colon as the metric
  name, and tries to read the rest as an integer. A wrapped continuation line of the REASONING
  paragraph in that shape is read as a metric effect. A casualties line is discarded by the same
  filter, because only those three substrings are accepted.
- **Evidence:** `engine/narrative_adjudication.py:374-381`; the three deltas the prompt requests at
  `:260-263`
- **Effect:** Narrative prose can move hidden metrics, and a metric the prompt did not ask for
  cannot. The same branch produces the two larger failures recorded at ER-015 and ER-034.

## ER-007 — Advisor trust updates on one adjudication path only

- **Status:** open
- **Severity:** medium
- **Area:** state
- **Observed:** `_update_character_attitudes` is called from `adjudicate_with_narrative` and from
  nowhere else. `adjudicate_with_actor_simulation` does not call it, and that is the path every
  live entry point takes whenever the state-actor file loads, which it does by default. The
  function also iterates a hardcoded list of four UK advisor ids and never touches the US National
  Security Advisor seeded alongside them.
- **Evidence:** `engine/narrative_adjudication.py:788` (the only call site), `:928-943` (the
  definition, with the four-id list at `:941`), `:799-900` (the actor path, which does not call
  it); the three production branches at `engine/game_manager.py:289`, `cli/main.py:1839` and
  `cli/main_dashboard.py:1610`; `models/narrative_state.py:404-410` (the seeded ids)
- **Effect:** Advisor trust responds to the quality of the player's decisions in the fallback
  adjudication mode and not in the one normally used. At turn nine of the measured campaign the
  four UK trust values read 75, 70, 80 and 85, byte-identical to their seeds. Those numbers are
  interpolated into the character reaction prompt and the state-actor prompt.

## ER-008 — Two context builders apply no character bound

- **Status:** open
- **Severity:** medium
- **Area:** context
- **Observed:** `get_diplomatic_context` applies no character bound to the filtered transcript it
  returns. The narrator takes the last twenty transcript elements with no character cap, and one
  element can be a full unwrapped paragraph.
- **Evidence:** `llm/context_builder.py:441-512` (the diplomatic filter, which returns a joined
  string with no bound); `llm/prompts.py:587` (the narrator's twenty-element slice);
  `llm/context_builder.py:27` (`MAX_ADVISOR_TRANSCRIPT_CHARS = 320_000`, the bound that does exist
  elsewhere) and `:61` (`MAX_INJECT_CONTINUITY_LINES = 400`)
- **Effect:** The same shape as the overrun already corrected in the inject continuity window,
  where four hundred long lines reached 792,572 characters before a character bound was added
  beside the line cap. Prompt size in these two builders is bounded by nothing but the input.

## ER-009 — The metrics are rendered twice and a third block adds nothing

- **Status:** open
- **Severity:** low
- **Area:** context
- **Observed:** The shared dossier prints escalation, stability and cohesion as raw values out of
  one hundred, then again as prose bands, then a third block headed KEY INTELLIGENCE FLAGS. That
  third block lists only the flags currently true, and the five flags are not all thresholds over
  those three metrics: two of them test the military and civilian casualty counts instead.
- **Evidence:** `llm/context_builder.py:337-341` (raw values), `:351-352` (prose bands via
  `build_world_state_summary`); `llm/prompts.py:67-71` (the flags block, filtered to active flags
  at `:68`); `engine/flags.py:23`, `:26`, `:29` (the three metric thresholds) and `:32`, `:33` (the
  two casualty thresholds)
- **Effect:** At the scenario's opening metrics the block reads "KEY INTELLIGENCE FLAGS: Risk
  Escalation, Risk Alliance Fragile, Risk Military Losses", sitting directly below the numbers two
  of those three were computed from. It restates what is already present twice and adds only a
  restatement of the casualty counts, which the prose band above has also already given.

## ER-010 — The situation summary costs a call per turn and reaches no prompt

- **Status:** open
- **Severity:** medium
- **Area:** state
- **Observed:** `update_situation_summary` issues a model call every turn and overwrites
  `NarrativeState.situation_summary`. Its docstring says the field feeds `to_llm_context()` for
  every downstream prompt. `to_llm_context()` does not include it. The readers are the emergent
  branch of `display_for_mode`, which has no production caller, and four direct echoes across the
  two terminal front ends, all of which fire only in emergent play mode.
- **Evidence:** `engine/narrative_adjudication.py:666-695` (the call and the docstring claim);
  `models/narrative_state.py:240-267` (`to_llm_context`, no summary); `:231-234`
  (`display_for_mode`); `cli/main.py:1110` and `:1962`; `cli/main_dashboard.py:1158` and `:1733`;
  `docs/py/bridge.py` contains no reader
- **Effect:** One call in roughly fifteen every turn produces text no model ever sees. On the
  browser build, which is the public deployment, no player sees it either in any of the three play
  modes the page offers, which makes "Emergent — maximum LLM freedom" and "Immersive — metrics
  hidden" indistinguishable in what they actually show.

## ER-011 — Output caps are dropped on three of four drivers

- **Status:** open
- **Severity:** low
- **Area:** dispatch
- **Observed:** Several call sites pass a system instruction, a temperature or an output cap. The
  router forwards each only to a driver whose `generate_text` signature declares it, and three of
  the four drivers declare `(prompt, rng)` alone. The batch entry point declares only `max_tokens`,
  and its sequential fallback passes no keyword arguments at all.
- **Evidence:** `engine/narrator.py:36-42` (150-token cap, temperature, system instruction);
  `engine/narrative_adjudication.py:269` (400-token cap) and `:545-546` (150-token cap);
  `llm/router.py:251-264` (the signature test), `:297-304` (the batch signature), `:398-406` (the
  sequential fallback); `llm/gemini_driver.py:106` and `:151`, `llm/mock_driver.py:1140`,
  `llm/offline_driver.py:15` (signatures that declare none); `llm/openai_compat_driver.py:150-157`
  (the one that declares all three)
- **Effect:** On Gemini every one of those caps is silently discarded and the driver's own 2048-token
  default applies, so the quality assessment budgeted at 400 tokens and the advisor reactions
  budgeted at 150 each run five to thirteen times longer than intended. The OpenAI-compatible driver
  honours them, so the public build is unaffected.

## ER-012 — Authored per-country content reaches no prompt

- **Status:** open
- **Severity:** high
- **Area:** data
- **Observed:** `NarrativeConfig.to_llm_context` resolves a country's stance by exact string match
  against the code it is handed. The scenario's narrative file writes stance codes as `USA`, `RUS`,
  `CHN` and `IRL`. The codes that reach the only call site passing one are diplomatic profile keys
  normalised to `US`, `Russia`, `China` and `Ireland`, and the scripted encounter's own inject file
  supplies `US` directly. No code that reaches the lookup ever equals a code in the stance list.
  The four other call sites pass no code at all.
- **Evidence:** `models/narrative.py:47` (the exact-match lookup);
  `data/scenarios/war_game_2025/narratives.yaml` (stance codes `USA`, `RUS`, `CHN`, `IRL`);
  `engine/diplomacy.py:124` (`normalize_country`) and `:111-121` (the alias table);
  `engine/game_manager.py:490` (normalisation before the encounter is constructed);
  `engine/diplomacy.py:354` (`self.country = country`) and `:212` (the only call site passing a
  code); `data/scenarios/war_game_2025/episodes/turn_006.yaml:31` (`country: US`);
  `llm/context_builder.py:323` and `:416`, `engine/narrative_adjudication.py:221` and `:844` (the
  four sites passing none)
- **Effect:** Every authored per-country secret motive, public posture, economic-leverage list and
  intelligence-sharing level in Mystery Mode is unreachable from every prompt in the game.
  Reproduced directly: `to_llm_context("USA")` contains a SECRET MOTIVE block and
  `to_llm_context("US")` does not, and `US` is what the engine passes. The mismatch is silent
  because the lookup returns `None` and the function simply omits the block. Note also that the
  stance list and the state-actor roster barely overlap: only USA and RUS appear in both, so CHN
  and IRL have stances no actor can voice and FRA, DEU and POL are simulated with no stance behind
  them.

## ER-013 — Advisor pushback mutates nothing

- **Status:** open
- **Severity:** low
- **Area:** state
- **Observed:** No metric, flag, trust value or ledger entry is written from pushback output
  anywhere. It drives the confirm gate in the two terminal front ends and the transcript, and
  nothing else. The headless preview method flattens pushback into the same list as the critical
  omissions with a canned recommendation attached; the method that actually commits a decision
  returns the two separately.
- **Evidence:** `agents/conversation.py:248-307` (parses the reply, writes nothing);
  `engine/sim_loop.py:556-563` (the transcript append); the two confirm gates at
  `cli/main.py:1790-1819` and `cli/main_dashboard.py:1561-1590`;
  `engine/game_manager.py:213-220` (the preview flattening) versus `:343-353` (the commit path,
  which keeps them separate)
- **Effect:** A cabinet objection has no mechanical consequence. A consumer of the headless preview
  cannot tell a pushback line from a critical-omission line.

## ER-014 — The state-actor prompt carries UK internal advisor trust

- **Status:** open
- **Severity:** medium
- **Area:** context
- **Observed:** The world context handed to a foreign government's roleplay prompt is
  `NarrativeState.to_llm_context()`, which interpolates every character's name, relationship label
  and trust score. The character dictionary is not all-UK: it also seeds a US National Security
  Advisor.
- **Evidence:** `engine/actor_simulation.py:54-55` (the `{world_context}` slot);
  `engine/narrative_adjudication.py:841`; `models/narrative_state.py:262`; `:404-438`
- **Effect:** A foreign actor reasons from the UK cabinet's private internal state. The turn-nine
  prompt in the measured campaign listed all five advisors with their trust scores.

## ER-015 — Decorated labels drop the decision's metric effects

- **Status:** open
- **Severity:** high
- **Area:** parsing
- **Observed:** `_parse_quality_response` recognises a field only when the line begins with the bare
  label: `line.startswith("QUALITY:")`, `line.startswith("REASONING:")`,
  `line.startswith("QUALITY MULTIPLIER:")`. The effects branch takes everything before the first
  colon as the metric name verbatim. Markdown emphasis on any of these misses. The comparable
  parser in `agents/conversation.py` tolerates decoration on its labels; this one does not.
- **Evidence:** `engine/narrative_adjudication.py:366`, `:371`, `:374-381`, `:383`;
  `agents/conversation.py:116-127` (the tolerant label reader);
  `engine/narrative_adjudication.py:767-776` (the narrative path applies `suggested_effects` and
  nothing else); `:441-444` (`determine_base_effects`) and `:449-498` (`apply_quality_scaling`)
- **Effect:** Demonstrated on one answer in three forms. The answer is `QUALITY: poor`, a
  one-sentence REASONING, the deltas `escalation_risk: 8`, `alliance_cohesion: -6`,
  `domestic_stability: -3`, and `QUALITY MULTIPLIER: 0.5`.

  1. Bare labels and bare delta lines: quality `poor`, multiplier 0.5, applied after scaling as
     escalation +6, cohesion -5, stability -2, and the model's critique shown to the player.
  2. The labels emphasised and the deltas as plain `- name: value` bullets: quality falls back to
     `adequate` and the multiplier to 1.0, and the metric keys become `__escalation_risk` and its
     two siblings, which no metric object has, so the `hasattr` test at `:773` rejects all three.
  3. The delta bullets emphasised as well: the `int()` at `:378` fails first and the effects
     dictionary is empty before the `hasattr` test is reached.

  Forms 2 and 3 lose the whole of the decision's effect on the three metrics by different routes,
  and the player is shown the placeholder "Action assessed." The rest of the pipeline still runs:
  the disposition is recorded, reactions are generated, attitudes are updated and crises are
  checked. On the actor path, which is the live path whenever the actor file loads, the
  keyword-derived base effects still move, and they move harder than intended, because the fallback
  multiplier of 1.0 is larger than the 0.5 the model asked for. No frequency is claimed; the
  measurement of how often a given model decorates its labels needs a run against a live provider.

## ER-016 — Decorated actor replies invert a refusal

- **Status:** open
- **Severity:** high
- **Area:** parsing
- **Observed:** `_parse_actor_response` recognises each field only from a bare label at the start of
  a line. When none matches, the defaults stand: `will_support` is `"conditional"`, `trust_change`
  is 0, and `public_response` falls back to `"{actor_id} acknowledges the action."` A
  `"conditional"` verdict is not neutral in effect: it contributes a positive alliance-cohesion
  term.
- **Evidence:** `engine/actor_simulation.py:151-152` (the two defaults), `:162-201` (the bare-label
  tests), `:204-212` (the fallback text), `:318-320` (`conditional` adds `int(2 * weight)`);
  `engine/narrative_adjudication.py:869-876` (the sixty-forty blend)
- **Effect:** Demonstrated on one reply in two forms. Bare labels, with `TRUST_CHANGE: -8` and
  `WILL_SUPPORT: no`: the public response is preserved, trust falls by 8, and the refusal costs
  cohesion. The same reply with every label emphasised: the text becomes "USA acknowledges the
  action.", trust change 0, support `conditional`, which gains cohesion. Washington's refusal to
  back the United Kingdom is rendered as a bland acknowledgement and scored as a small diplomatic
  win. The final applied value is the blend `int(actor_val * 0.6 + quality_val * 0.4)`, so whether
  the sign survives depends on the quality term: with the actor cohesion at +4 the blended result is
  +2 when the quality term is 0 and turns negative once the quality term reaches about -10. The
  call succeeded, so nothing is logged and no fallback counter moves.

## ER-017 — The calls that change the game never learn what happened in it

- **Status:** open
- **Severity:** high
- **Area:** context
- **Observed:** Five call families run the adjudication. Three decide what happens: the action
  quality assessment and the state-actor simulation set the metric changes, and the diplomatic
  outcome assessment sets the alliance delta from a call. Two are outputs of it: the advisor
  reactions, shown to the player, and the situation summary, which reaches no prompt (ER-010). Four
  of the five build their world context from `NarrativeState.to_llm_context()`; the diplomatic
  outcome assessment uses `build_world_state_summary` instead. That context contains the three
  metrics, the casualty counts, up to three entries from `recent_events`, the active-crisis list,
  character trust scores and a game clock. In Mystery Mode two of the four callers concatenate the
  hidden narrative block after it. `recent_events` is seeded once at campaign start with three
  fixed backstory lines and is thereafter written by one function only, the crisis-threshold check,
  which appends one of three fixed banner strings. No inject title, player decision, adjudication
  outcome or advisor line ever enters it. `active_crises` only grows; `resolve_crisis` has no caller
  outside tests. `game_time` is written at construction and never advances.
- **Evidence:** `models/narrative_state.py:240-267` (the context, with the casualty line at `:253`);
  `:294-299` (`add_event`); `:455-463` (the one-time seed); `:363-366` (`resolve_crisis`, no
  caller); `engine/narrative_adjudication.py:946-963` (the only writer); consumers at `:216`,
  `:605`, `:674`, `:841`; the narrative concatenation at `:221` and `:844`;
  `engine/diplomacy.py:291` (the outcome assessment's different builder)
- **Effect:** From the turn-nine prompt in the measured campaign: the "Recent Events" block held one
  turn-one backstory line and two crisis banners, and the clock read "Game Time: 17:00 (Turn 9)" for
  a crisis spanning days. The referee is told the live metric values, the casualty counts and a
  growing crisis list, and nothing else that happened: no decision the player made, no event that
  was staged, no outcome that was adjudicated. Over the ten-turn campaign the three families that
  decide the metric changes received 5.9 per cent of every prompt character the engine sent, the two
  adjudication outputs a further 1.5 per cent, against 89.0 per cent for the four advisory families
  that change nothing and 3.7 per cent for story generation. On a long campaign at the
  320,000-character history ceiling the gap widens by roughly two orders of magnitude, because the
  advisory prompts grow with the transcript and these do not.

## ER-018 — The diplomatic transcript filter is erratic in both directions

- **Status:** open
- **Severity:** high
- **Area:** context
- **Observed:** `get_diplomatic_context` promises in its docstring to exclude all internal UK COBRA
  deliberations. It carries two independent include latches and one clearing test. The first latch
  is set by any line containing `===`, the four characters `turn` followed by a space, `briefing`,
  `breaking news` or `intel report`. The second is set by any line containing the target country
  code or the word `diplomatic`. The clearing test looks for one of seven literal role markers.
  Advisor lines are written as `f"{role}: {response}"`, and the six roles in the shipped scenario
  are "Government Leader", "Military Commander", "Intelligence Coordinator", "Domestic Security",
  "Diplomatic Lead" and "Legal Advisor". None of them matches any clearing marker, so an advisor's
  line never clears the latch, while several of the clearing markers do appear on turn one from the
  scripted opening and from the player's own questions.
- **Evidence:** `llm/context_builder.py:441-512`, with the first latch at `:458`, the second at
  `:465-467`, the clearing markers at `:470-481` and the include test at `:484`;
  `engine/sim_loop.py:473` (`Prime Minister: {question}`) and `:485`
  (`f"{role}: {response}"`); `data/scenarios/war_game_2025/initial_conditions.yaml:444,454,464,474,
  484,494` (the six role labels); `data/scenarios/war_game_2025/episodes/turn_001.yaml:18,22,25,28,
  31` (scripted lines that do match clearing markers)
- **Effect:** Run against the real turn-one transcript the engine builds, taken from
  `GameManager.transcript` rather than from rendered text, the filter dropped 7 of 31 non-blank
  elements: the five cast-list entries and the player's question, which appears twice. It passed the
  Diplomatic Lead's answer through to the foreign counterpart's prompt. So the filter both leaks
  internal deliberation and redacts scripted public material, depending on where the latch was last
  set, and it leaks the material it exists to protect. The entry point where this matters most, a
  call to Washington, is offered on the public play page.

## ER-019 — The per-call model table is inert on the shipped provider

- **Status:** open
- **Severity:** high
- **Area:** routing
- **Observed:** `MODEL_NAMES` maps the two tiers to `gemini-2.5-flash` and `gemini-2.5-pro`, so
  every name the tier table can produce begins with "gemini". `OpenAICompatDriver.__init__`
  discards any model name beginning with "gemini" and uses `OPENAI_COMPAT_MODEL` instead. The
  browser build and every OpenRouter, Groq, Ollama or LM Studio configuration go through that
  driver. The one routing argument that would still work on that driver, `model_override`, is
  declared on both router entry points and passed by nothing outside tests.
- **Evidence:** `llm/model_config.py:42-45`; `llm/openai_compat_driver.py:123-128`;
  `llm/router.py:229-236`, `:208` and `:302` (`model_override`);
  `docs/py/bridge.py:523-534` (the browser build selects `openai_compat`)
- **Effect:** On the public deployment every one of the twelve call families runs on the same model
  whatever the table says. The in-game model menu edits a table that changes nothing and the
  `--flash-only` cost-saving flag saves nothing. The router also caches a separate driver instance
  per model name, so the two tier names and the no-context default build and keep three identical
  drivers, which means a misconfiguration prints its fallback warning once per key rather than once.

## ER-020 — The story generator is given a digest instead of a synopsis

- **Status:** open
- **Severity:** high
- **Area:** context
- **Observed:** The inject prompt's block headed "STORY SO FAR (HIGH-LEVEL SUMMARY)" is filled by
  `generate_summary`, which makes no model call. It emits the number of turns played, the number of
  transcript lines, and up to three transcript lines beginning with one of six prefixes,
  `[Narrator]`, `[Stochastically generated inject]`, `***`, `BREAKING`, `INTEL` or `BRIEFING`, each
  truncated to 100 characters. The `summary_prompt` argument, which asks for the significant events,
  the player's major decisions and the current diplomatic relationships, is deleted on the first
  line of the function. Making the digest mechanical is deliberate and the docstring says why: it
  removes a call whose placeholder output could leak into downstream prompts.
- **Evidence:** `llm/context_builder.py:562-600` (the digest, with `del summary_prompt` at `:570`
  and the six prefixes at `:583-584`); `llm/prompts.py:389-405` (the discarded prompt text and the
  call); `llm/context_builder.py:420-425` (the block header); `llm/prompts.py:400-405` (the
  previous-turn window)
- **Effect:** In the turn-seven prompt from the measured campaign the three "recent events" were a
  narrator atmosphere line, "INCOMING SECURE CALL: US PRESIDENT" and "MANDATORY DIPLOMATIC
  ENCOUNTER", two of them stage directions rather than events. The generator does receive the
  previous turn verbatim and the event ledger's titles, so it is not blind; what it never receives
  is any account of the campaign before the previous turn, under a heading that tells it it has one.

## ER-021 — Mystery Mode tells the player's own advisors to deceive them

- **Status:** open
- **Severity:** medium
- **Area:** context
- **Observed:** `NarrativeConfig.to_llm_context` always appends a four-line instruction block
  regardless of whether a country stance was requested: "Act according to your secret motive at all
  times", "Never explicitly reveal this information to the UK", "Your behaviour should subtly
  reflect these hidden truths", "Provide plausible deniability in all statements". That block is
  written for a foreign actor being roleplayed. It is inserted into the shared briefing dossier that
  the advisor Q&A, decision interpretation, pushback and critical-omissions prompts all open with,
  into the inject generation prompt, and into the action quality assessment prompt.
- **Evidence:** `models/narrative.py:69-78` (the unconditional block);
  `llm/context_builder.py:322-323` (into the shared dossier); `:415-417` (into the inject prompt);
  `engine/narrative_adjudication.py:219-221` (into the quality assessment); `:843-844` (into the
  actor context, where it belongs); `llm/context_builder.py:501-503` (into the diplomat prompt,
  where it belongs)
- **Effect:** In Mystery Mode the player's own cabinet is instructed to act on a secret motive and
  to give the United Kingdom plausible deniability, in the same prompt that asks them to advise the
  United Kingdom honestly. The referee that scores the decision is told the same thing, although
  that prompt adds counter-instructions of its own at `engine/narrative_adjudication.py:244-252`;
  the four advisory prompts add nothing to offset it. Mystery Mode only: `world.narrative` is `None`
  in Original Story Mode, the default on every entry point.

## ER-022 — The HTTP path serves no briefing after turn one

- **Status:** open
- **Severity:** high
- **Area:** dispatch
- **Observed:** `manager.get_turn_briefing()` appears exactly once in the HTTP server, inside the
  handler that creates a new game. No endpoint runs a later briefing; the only briefing-shaped route
  acknowledges one and sets the phase.
- **Evidence:** `api/server.py:275` (the sole call, in `POST /game/new`); `:601`
  (`POST /game/{session_id}/briefing/ack`, which changes the phase only)
- **Effect:** Over the HTTP interface, turns two and later have no inject, no inject effects, no
  narrator bridge and no mandatory diplomatic encounter. Two of the twelve call families, inject
  generation and the narrator, are unreachable on that path. The terminal front ends and the browser
  build drive the briefing themselves and are unaffected.
- **Note on severity:** `high` is set on the size of the break, not on how many people it reaches.
  This surface backs the in-development Next.js frontend and has no tests, so a case exists for
  `medium`, or for closing this `wontfix` if the HTTP server is no longer a supported way to play.

## ER-023 — The decision phase runs seven waits where three would do

- **Status:** open
- **Severity:** medium
- **Area:** dispatch
- **Observed:** Committing a decision issues seven dispatch rounds one after another: interpretation,
  pushback, the batched five-advisor omissions scan, the batched actor simulation, the quality
  assessment, the batched character reactions and the situation summary. Four of the six waits are
  not required by any data dependency. Pushback needs the interpretation, and so does the quality
  assessment. The character reactions need the quality assessment. The omissions scan does not use
  the interpretation at all (ER-002), and the actor simulation reads only the action and the
  narrative state. The situation summary reads only the action and the narrative state as well, but
  it runs after the metric mutation, so it belongs in the last round rather than the first.
- **Evidence:** `engine/sim_loop.py:532-575` (three sequential rounds);
  `engine/narrative_adjudication.py:838-898` (four more); `:228` (the quality prompt interpolates
  the interpretation); `:879-883` then `:898` (the summary runs after the mutation)
- **Effect:** Measured against a local endpoint held at 1.2 seconds per call, the decision phase took
  8.5 seconds of a 12.2-second turn, and across the campaign between 76 and 80 per cent of wall
  clock had exactly one call in flight. The dependencies permit three rounds: interpretation
  alongside the omissions scan and the actor simulation; then pushback alongside the quality
  assessment; then the character reactions alongside the situation summary. That is roughly 3.6
  seconds on the same latency. Against a real provider at several seconds a call this is the
  difference between a pause and a wait.

## ER-024 — Player questions are written to the transcript twice

- **Status:** open
- **Severity:** low
- **Area:** context
- **Observed:** `GameManager.process_question` appends `f"Prime Minister: {question_text}"` to the
  transcript and then calls `run_turn_discussion`, which appends the identical line itself; the
  returned lines are then extended onto the transcript as well. The terminal front ends do not have
  this double write.
- **Evidence:** `engine/game_manager.py:175` and `:177-186`; `engine/sim_loop.py:473`
- **Effect:** Every player question appears twice in the campaign transcript on the browser build
  and the HTTP path, and therefore twice in every prompt carrying the history block, which is the
  largest element of the eight most expensive dispatches in a turn.

## ER-025 — Mystery Mode draws its secret from an unseeded generator

- **Status:** open
- **Severity:** medium
- **Area:** state
- **Observed:** Both terminal front ends import the `random` module inside the selection function and
  call `random.choice(narratives)` on the module-level generator. The seeded generator built for the
  campaign is not used, and nothing anywhere seeds the module-level one. The headless session object
  does it correctly with `self.rng.choice`.
- **Evidence:** `cli/main.py:502-504` and `cli/main_dashboard.py:538-539`;
  `engine/game_manager.py:93-97`
- **Effect:** A campaign started from a fixed seed does not replay identically in Mystery Mode on
  either terminal path: a different hidden truth can be drawn, which changes the secret narrative
  block in every prompt that carries it and therefore changes the whole campaign. This is the entry
  that breaks the project's stated determinism guarantee.

## ER-026 — `--no-stochastic-injects` inverts into a banner switch

- **Status:** open
- **Severity:** low
- **Area:** dispatch
- **Observed:** The flag defaults to true. At the top of every turn the loop tests whether the turn
  has reached the scenario's transition point and, if so, sets the flag back to true. The one thing
  the flag still controls is the branch that prints the "ENTERING DYNAMIC SCENARIO GENERATION"
  banner and waits for a keypress: that branch runs only when the flag was false, which is only when
  the operator passed `--no-stochastic-injects`.
- **Evidence:** `cli/main.py:557` (the option), `:818-821` (the override), `:820-834` (the banner and
  the keypress wait), `:837` (the only use of the value); the same pattern at
  `cli/main_dashboard.py:835-838`
- **Effect:** The flag does not disable dynamic generation. Its sole surviving effect is inverted:
  passing the flag that asks for no generated content is what causes the game to announce that
  generated content is starting, and to pause for a keypress. A player or tester who wants a purely
  scripted campaign has no way to get one.

## ER-027 — An advisor instruction contradicts the outcome assessor's task

- **Status:** open
- **Severity:** low
- **Area:** context
- **Observed:** `build_world_state_summary` ends with four standing instructions written for a
  cabinet advisor, including "Do NOT reference 'metrics', 'game mechanics', 'scores', or 'values'".
  Carrying those instructions into the shared briefing dossier is deliberate and documented: the
  comment above the call explains that merging two context shapes must not drop the instruction from
  the four call sites that had it. Three of the four prompts built on that dossier are advisor-role
  prompts where the instruction is on-role. The problem is the fourth use, the diplomatic outcome
  assessment, which is not an advisor prompt and is asked in the same breath to answer with a
  number.
- **Evidence:** `llm/prompts.py:73-79` (the instructions); `llm/context_builder.py:345-350` (the
  comment recording the decision) and `:351-352` (the call); `engine/diplomacy.py:291` (the outcome
  assessment's use) and `:310-313` (the response format it then requires, including
  `ALLIANCE_COHESION_DELTA: [number between -15 and +15]`); `llm/prompts.py:584` (the narrator's
  use)
- **Effect:** The diplomatic outcome assessor is told not to reference values and then required to
  answer with one. The narrator is told it is a real advisor in COBRA. A direct instruction not to
  do the thing the prompt then requires is the kind of contradiction that makes a smaller model
  hedge or refuse, and it sits on one of the three calls that set metric changes.

## ER-028 — The play page offers no way to choose or change the model

- **Status:** open
- **Severity:** low
- **Area:** routing
- **Observed:** The play page sends the worker a key and a source, and no model or base URL, so the
  bridge falls through to its hardcoded defaults, `https://openrouter.ai/api/v1` and
  `openai/gpt-4o-mini`. The page has no control for either. The bridge does print the resolved model
  to the terminal when a key is supplied, so the value is visible once a game starts; what is absent
  is any way to change it. The message contract already carries `model` and `baseUrl` fields and the
  bridge already prefers them, so the page could set them without a bundle rebuild.
- **Evidence:** `docs/app.js:219` (the message sent, with neither field);
  `docs/py/bridge.py:526-532` (the fallbacks), `:534-537` (the note that names the model) and
  `:551` (where it is written out); `:1220-1222` (the message handler, which already passes both
  fields through); `docs/index.html:126-143` (the options offered, none of them a model)
- **Effect:** Every public game runs on one model chosen by a fallback rather than by a decision
  recorded anywhere. This also decides whether the prompt-ordering work in `llm/context_builder.py`
  pays off at all, since automatic prefix caching is a per-model-family property.

## ER-029 — The diplomatic outcome parser shares the same defect

- **Status:** open
- **Severity:** high
- **Area:** parsing
- **Observed:** `assess_diplomatic_outcome` reads its three fields with the same bare `startswith`
  tests as ER-015 and ER-016, and falls back to `NEUTRAL`, a delta of 0 and the string "The
  conversation concluded." when none matches. The outcome field is never validated against the
  enumeration the prompt requests. This is the third of the three call families that set metric
  changes.
- **Evidence:** `engine/diplomacy.py:325`, `:327` and `:336` (the bare-label tests); `:318-320` (the
  fallback values); `:310` (the enumeration the prompt asks for, never enforced); `:340-342` (the
  assembled return) and `:466-474` (where the assessment is displayed and the delta written to
  `world.metrics.alliance_cohesion`)
- **Effect:** Demonstrated with a stub standing in for the model, on the reply
  `OUTCOME: FAILURE` / `ALLIANCE_COHESION_DELTA: -12` / `SUMMARY: Washington refused.` With bare
  labels: outcome `FAILURE`, delta -12, and the summary shown to the player. With every label
  emphasised: outcome `NEUTRAL`, delta 0, and the placeholder "The conversation concluded." A call
  in which the United States refused the United Kingdom is recorded as neither good nor bad and
  costs nothing. As in ER-015 and ER-016 the call succeeded, so nothing is logged.

## ER-030 — A worded refusal is read as conditional support

- **Status:** open
- **Severity:** high
- **Area:** parsing
- **Observed:** The `WILL_SUPPORT:` branch of the actor parser tests
  `"no" in content and "not" not in content`. The second clause was added to stop a phrase such as
  "not conditional" registering as a refusal; it also rejects every refusal containing the word
  "not". Anything failing all three tests keeps the default, `"conditional"`, which contributes a
  positive alliance-cohesion term.
- **Evidence:** `engine/actor_simulation.py:177-185` (the branch, with the guard at `:181`); `:152`
  (the default); `:318-320` (`conditional` adds `int(2 * weight)` to cohesion);
  `engine/narrative_adjudication.py:871-877` (the sixty-forty blend); `:68` and `:76` (the prompt's
  requested enumeration, `[yes/no/conditional]`)
- **Effect:** Demonstrated on four replies with bare labels throughout and `TRUST_CHANGE: -8`. The
  bare enumerated value `no` is read correctly as a refusal. `absolutely not`, `not at this time`
  and `no, we will not assist` are all read as conditional support, so a refusal becomes a small
  alliance gain instead of a loss. This needs no decoration of any kind and is reachable on a reply
  that follows the requested shape.

## ER-031 — An explicit multiplier of 1.0 is indistinguishable from silence

- **Status:** open
- **Severity:** low
- **Area:** parsing
- **Observed:** `multiplier` is initialised to 1.0 and, after parsing, any value still equal to 1.0
  is replaced from a quality-to-multiplier table. A model answering `QUALITY: poor` and
  `QUALITY MULTIPLIER: 1.0` has its explicit answer overwritten with 0.5, because 1.0 is used both
  as the default and as a legal value.
- **Evidence:** `engine/narrative_adjudication.py:361` (the initial value), `:383-388` (the parse),
  `:391-399` (the override)
- **Effect:** Demonstrated: that exact answer yields a multiplier of 0.5. The only value the model
  cannot express is the neutral one. Low severity because the substituted value is at least in the
  right direction for every quality band.

## ER-032 — The rate limiter is discarded on every model-tier switch

- **Status:** open
- **Severity:** high
- **Area:** dispatch
- **Observed:** `get_rate_limiter` keeps one module-level limiter and replaces it whenever the
  requested requests-per-minute differs from the stored one. On Gemini that rate is auto-detected
  from the model name, 10 for Flash and 2 for anything else, so a turn that interleaves Flash and
  Pro contexts rebuilds the limiter repeatedly and each rebuild discards the record of recent
  requests. The five context-less families pass no model name, and the auto-detection test is falsy
  for `None`, so those calls are throttled at the Pro rate regardless of which model answers them.
- **Evidence:** `llm/router.py:143-146` (the rebuild), `:134-140` (the auto-detection), `:47` and
  `:59-73` (the request history the rebuild discards); `llm/model_config.py:29-45` (the tier table
  that makes the rate alternate)
- **Effect:** Reproduced directly against the shipped router: a Flash limiter with two requests
  recorded is replaced by a fresh Pro limiter with zero recorded the moment the next call resolves
  to the other tier. Established, therefore: the limiter's own cap is not enforced across a turn,
  because its record of recent requests rarely survives long enough to reach the cap.

  What follows from that is inference and was not measured, because the recording endpoint used for
  the campaign measurements enforces no cap and returns no rate-limit errors. If a provider does
  enforce one, the calls it refuses are answered by the built-in offline driver through the router's
  resilient wrapper, which returns well-formed text. A campaign would then appear to run flawlessly
  while an increasing share of it was never answered by a model, with nothing recorded beyond a
  single warning line per failure and no running count. Confirming that half needs a run against a
  provider that enforces a limit.

## ER-033 — The scripted diplomatic call answers itself on two front ends

- **Status:** open
- **Severity:** high
- **Area:** dispatch
- **Observed:** `run_diplomatic_encounter` substitutes the line "Thank you." for the player's reply
  whenever it is called without an input callback. The briefing passes its own `get_player_input`
  straight through, and the headless session object and the HTTP server both call the briefing
  without one. "Thank you." normalises into the set of closing phrases, so the encounter ends after
  a single exchange.
- **Evidence:** `engine/diplomacy.py:532-537` (the substitution) and `:419-423` (the closer test);
  `engine/sim_loop.py:403-418` (the mandatory encounter, passing `get_player_input` through);
  `engine/game_manager.py:143-154` and `api/server.py:275` (callers that supply none);
  `data/scenarios/war_game_2025/episodes/turn_006.yaml:29-33` (the only scripted encounter)
- **Effect:** On the public browser deployment the campaign's one set-piece call plays itself. The
  player watches the US President ask for assurances, watches the engine answer "Thank you." in
  their name, and is then graded on that exchange, with up to fifteen points of alliance standing at
  stake through the outcome assessment. The player is never offered a turn.

## ER-034 — An annotated number is dropped and its siblings are applied

- **Status:** open
- **Severity:** high
- **Area:** parsing
- **Observed:** Two of the three parsers that set metric changes recover their number with a bare
  `int()` over the whole remainder of the line and swallow the failure. In the quality assessment the
  failure is swallowed per line, so an annotated delta is dropped while its unannotated siblings are
  applied. In the diplomatic outcome the failure resets the delta to the zero it was initialised
  with, while the outcome and summary fields parse correctly from the same reply. Neither needs any
  markdown. The actor parser in the same codebase does this correctly, by searching for a signed
  integer rather than converting the whole remainder.
- **Evidence:** `engine/narrative_adjudication.py:378` (the `int()`) and `:380-381` (the per-line
  swallow); `engine/diplomacy.py:329-332` (the strip and `int()`) and `:334-335` (the reset to
  zero); `engine/actor_simulation.py:157` (`re.compile(r"TRUST_CHANGE:\s*([+-]?\d+)")`, the tolerant
  form already present)
- **Effect:** Demonstrated with bare labels throughout and no decoration anywhere. Quality
  assessment, on `escalation_risk: +8 (sharp rise)` / `alliance_cohesion: -6` /
  `domestic_stability: -3`: the parsed effects are cohesion -6 and stability -3, and escalation is
  gone. A partial adjudication is applied and the player is shown a complete-looking assessment.
  Diplomatic outcome, on `OUTCOME: SUCCESS` / `ALLIANCE_COHESION_DELTA: +8 (strong reassurance)` /
  `SUMMARY: good`: the outcome and summary survive and the delta is 0, so the player is told the
  call succeeded while the alliance standing does not move. Both calls succeeded, so nothing is
  logged.

## ER-035 — A bulleted cabinet objection is read as no objection

- **Status:** open
- **Severity:** high
- **Area:** parsing
- **Observed:** A pushback line is recognised only when the text before its first colon normalises to
  a known advisor role. The normaliser strips markdown emphasis and brackets but not a leading
  hyphen, so a bulleted list of objections matches nothing. Lines that match nothing before any role
  has been recognised are dropped entirely, and the function returns an empty list. The terminal
  front ends read an empty list as no pushback and skip the confirm gate.
- **Evidence:** `agents/conversation.py:293-307` (the recognition loop), `:111-113`
  (`_normalize_role_prefix`, which strips asterisks, underscores, backticks, square brackets and
  surrounding whitespace, but not a leading hyphen), `:305` (the comment recording
  that unrecognised leading lines are dropped); the consumers at `cli/main.py:1790` and `:1819`,
  and `cli/main_dashboard.py:1561` and `:1590`
- **Effect:** Demonstrated on the shipped scenario's advisor roster with the reply
  `- Military Commander: Two frigates leaves the approaches uncovered.` /
  `- Legal Advisor: No Article 51 basis.` The parser returns an empty list. A cabinet that objected
  is rendered as a cabinet that did not, and the player loses the amend-or-cancel gate, which is the
  only consequence pushback has at all (ER-013). A related case: when a role prefix is not
  recognised but some earlier line was, the unrecognised line is merged into the previous advisor's
  message, so one official is shown saying another's words.

## ER-036 — Two acceptance rules discard real critical omissions

- **Status:** open
- **Severity:** high
- **Area:** parsing
- **Observed:** The critical-omissions consumer applies two acceptance rules after its label reader
  has run. The first tests the no-concern sentinel as a substring of the whole response rather than
  as a standalone line, so any answer mentioning the sentinel anywhere is skipped. The second keeps
  a response only when both the concern and the recommendation parse, so a concern with no
  recommendation is discarded with no log and no partial record.
- **Evidence:** `agents/conversation.py:390` (the substring sentinel test); `:419`
  (`if concern and recommendation:`); `:424-427` (the exception handler, which does log, in contrast
  to these two silent paths)
- **Effect:** Demonstrated on the shipped scenario roster. A reply reading
  `CONCERN: NO_CONCERN was my first thought but NATO was not consulted before deployment.` /
  `RECOMMENDATION: Convene the NAC.` yields zero concerns. A reply reading
  `CONCERN: No NATO consultation before a deployment into the Barents.` with no recommendation also
  yields zero. This is the most expensive prompt group in the game, 53.7 per cent of all prompt
  characters (ER-002), and its entire purpose is warning the Prime Minister about something they
  forgot. Both failures point the same way, toward silence.

## ER-037 — The random number position is not saved

- **Status:** open
- **Severity:** medium
- **Area:** state
- **Observed:** Neither save format persists the random number generator or its position. The
  terminal path rebuilds the generator from the `--seed` option whether or not a save was loaded,
  and the headless session object re-enters its constructor, which builds a fresh generator from the
  seed.
- **Evidence:** `engine/persistence.py:62-71` (the save payload: scenario, world, transcript, play
  mode, narrative state, variant, initial metrics, version, and no seed or generator position);
  `cli/main.py:701` (`rng = Random(seed)`) and `:555` (the option's default of 42);
  `engine/game_manager.py:62`, reached from `:580-611`
- **Effect:** Resuming a save at turn 8 replays the draws the campaign already spent on turn 1, so
  generated content after a reload diverges from what continuous play would have produced. It also
  makes reloading free for a player who wants a different outcome, because the same reload always
  produces the same next draw. This compounds ER-025: between them, a seeded campaign is neither
  reproducible nor resumable.

## ER-038 — A foreign counterpart is given the UK's private metrics

- **Status:** open
- **Severity:** medium
- **Area:** context
- **Observed:** `get_diplomatic_context` opens the foreign counterpart's roleplay context with the
  raw game metrics, labelled as the United Kingdom's, before any transcript filtering happens.
- **Evidence:** `llm/context_builder.py:491-498` (`UK Escalation Risk`, `UK Domestic Stability`,
  `NATO Alliance Cohesion`, each out of 100); `engine/diplomacy.py:212` (where the context is built)
  and `:229` (where it is interpolated into the counterpart's prompt)
- **Effect:** The President of the United States is roleplayed knowing the British Prime Minister's
  domestic-stability score to the point. A counterpart told the United Kingdom is at 27 out of 100
  at home negotiates differently from one who is not, and the player has no way to know that number
  was handed over. In the two play modes defined by hiding those numbers from the player, they are
  still given to the foreign side.

## ER-039 — The quality multiplier's effect is halved before it lands

- **Status:** open
- **Severity:** low
- **Area:** parsing
- **Observed:** On the narrative adjudication path `apply_quality_scaling` is handed the model's
  suggested effects as its base effects, and then merges the same suggestions back into the result,
  so each metric becomes the average of the scaled value and the unscaled one.
- **Evidence:** `engine/narrative_adjudication.py:767-769` (the same dictionary passed as both
  arguments); `:470-483` (the scale, then the merge that averages a metric present in both)
- **Effect:** Demonstrated: a suggested delta of +10 lands as +7 at a multiplier of 0.5 and +15 at a
  multiplier of 2.5, rather than +5 and +25. Half of the referee's ability to distinguish an
  exceptional decision from a poor one is discarded before the effects reach the metrics. The
  direction is always right, so this is a loss of resolution rather than a wrong outcome.

## ER-040 — The diplomatic exchange counter advances twice per exchange

- **Status:** open
- **Severity:** low
- **Area:** context
- **Observed:** The counterpart's prompt is told which exchange it is on, computed as the length of
  the conversation history plus one. The history gains two entries per exchange, the counterpart's
  line and the player's, both appended before the next prompt is built.
- **Evidence:** `engine/diplomacy.py:228` (the count) and `:251` (the sentence that uses it, "this
  is exchange N of a maximum 11"); `:402` and `:414` (the two appends preceding the build at `:426`)
- **Effect:** The counterpart is told it is already at exchange 3 of 11 the moment the player first
  speaks, and instructed in the same paragraph to bring the call to a close within five to seven
  exchanges. It therefore starts winding the conversation down almost immediately, which shortens
  every diplomatic call in the game below its designed length.

## ER-041 — The scripted call drops its premise and shows hidden numbers

- **Status:** open
- **Severity:** medium
- **Area:** context
- **Observed:** Two arguments are lost on the mandatory-encounter path. The inject's authored context,
  which states why the counterpart is calling, is passed into the encounter and stored but never
  reaches the counterpart's prompt. And `show_metrics` defaults to true and is not passed by the
  briefing, so the call's closing line prints the raw alliance-cohesion delta even in the play modes
  that exist to hide it. The player-initiated call in the dashboard front end omits it too.
- **Evidence:** `engine/diplomacy.py:355` (the stored context) against `:220-262` (the prompt, which
  never interpolates it); `:352` and `:491` (the `show_metrics=True` defaults);
  `engine/sim_loop.py:407-418` and `cli/main_dashboard.py:1206-1217` (calls that omit it), against
  `cli/main.py:1197` and `engine/game_manager.py:502` (calls that pass `play_mode == "classic"`
  correctly); `data/scenarios/war_game_2025/episodes/turn_006.yaml:32-33` (the authored premise)
- **Effect:** The counterpart is roleplayed with no idea why he telephoned, so the scripted premise
  of the campaign's one set-piece scene is lost. And in immersive and emergent play, the modes
  defined by hiding the numbers, the call ends by printing one.

## ER-042 — A generated event's effect is dropped when its delta is not an integer

- **Status:** open
- **Severity:** medium
- **Area:** parsing
- **Observed:** `apply_inject_effects` accepts a delta only as a Python integer or as a string
  containing `..`. Anything else leaves the value unset and the effect is skipped with no transcript
  line and no log, unlike an unrecognised metric name, which at least emits a "Skipped" line.
- **Evidence:** `engine/sim_loop.py:207-223` (the two accepted forms and the silent fall-through);
  `:252-253` (the "Skipped: unknown metric" line, the only failure that is reported);
  `llm/prompts.py:451-453` (the YAML format the generator is asked for)
- **Effect:** From turn seven onward in the standard variant every inject is model-generated, so this
  covers the whole endgame. A generated event whose delta arrives as a quoted string or a float is
  narrated to the player in full, appears in the transcript and the event ledger, and changes
  nothing. The player sees a missile launch and no consequence, with no indication that anything was
  dropped.

## ER-043 — The narrator is never told what the player decided

- **Status:** open
- **Severity:** low
- **Area:** context
- **Observed:** The narrator prompt builder walks the previous turn's transcript backwards looking
  for a decision line, and the body of that loop is `pass`. The variable it was meant to fill is
  assigned a placeholder immediately above and read nowhere in the file.
- **Evidence:** `llm/prompts.py:577-581` (the placeholder assignment and the empty loop body);
  `:587` (the twenty-line tail the prompt actually carries); `:600-605` (the task, which asks the
  narrator to connect the player's previous choice to the passage of time)
- **Effect:** The bridge text between turns is asked to connect the player's last decision to the
  next event, and is never told what that decision was. It has to infer it from whatever falls
  inside the last twenty transcript elements, which on a long turn is the adjudication tail rather
  than the decision.

## ER-044 — The decision summary panel empties on decorated output

- **Status:** open
- **Severity:** low
- **Area:** parsing
- **Observed:** The panel that shows the player their interpreted order parses it with four bare
  `startswith` tests. Decoration on the labels misses all four, and the all-empty result falls
  through to a raw 400-character trim.
- **Evidence:** `cli/display_utils.py:179-203` (the four tests) and `:258-263` (the fallback);
  consumers at `cli/main.py:1705`, `:1713`, `:1769` and `cli/main_dashboard.py:1476`, `:1484`,
  `:1540`
- **Effect:** Display only, and on the terminal front ends only. The player confirms a decision from
  a panel that has quietly dropped the forces list, the timeline and, most importantly, any
  feasibility warning the interpretation raised.

## ER-045 — A partial batch failure is invisible on the omissions scan

- **Status:** open
- **Severity:** medium
- **Area:** dispatch
- **Observed:** On the concurrent path a per-prompt failure is returned as the string
  `"[ERROR: ...]"` in that prompt's slot rather than raised, because the driver catches it inside its
  own thread pool. The router's retry-then-fallback wrapper only sees a batch that fails as a whole.
  Two of the three consumers test for that marker; the critical-omissions consumer does not, and its
  own parse of such a string yields no concern and no recommendation, so the slot is skipped by the
  rule at ER-036.
- **Evidence:** `llm/fanout.py:44-55` (the marker and why it survives);
  `llm/gemini_driver.py:191-193` and `llm/openai_compat_driver.py:265` (where it is produced);
  `engine/actor_simulation.py:135` and `engine/narrative_adjudication.py:557` (the two consumers
  that guard); `agents/conversation.py:387-425` (the consumer that does not)
- **Effect:** The failed advisor's slot is treated as that advisor finding nothing wrong. The other
  four are unaffected and their concerns still surface, so the loss is one advisor rather than the
  group. When the remaining advisors are also clear, the result is indistinguishable at the call
  site from a genuine all-clear. It is a silent false negative on the one call family whose job is
  to warn, and the advisor most likely to be missing is unknowable after the fact.
