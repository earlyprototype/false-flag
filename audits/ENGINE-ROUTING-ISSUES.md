# Engine routing issues register

Open register of defects and design gaps in how the engine assembles context, routes calls and
consumes results. Append to it; do not rewrite closed entries.

## Conventions

Each entry gets a permanent `ER-nnn` id, allocated in sequence and never reused. Status is one
of `open`, `in-progress`, `fixed`, `wontfix` or `invalid`. An entry that turns out to be wrong
becomes `invalid` with a note. It is not deleted, so the id stays stable in anything that cites
it.

Every entry states what is observed, the file:line that establishes it, and what it causes.
An entry without evidence is not ready to file.

Areas: `context` (prompt assembly and windowing), `routing` (model and provider selection),
`dispatch` (concurrency, rate limits, failure handling), `parsing` (consuming model output),
`state` (data maintained but unreached), `data` (scenario and config content).

`ER-001` to `ER-014` were allocated by the context audit of 2026-08-05 and are restated below
with their evidence re-checked against the current source. Where re-checking changed a verdict,
the change is stated inside the entry rather than hidden. `ER-015` onward are new.

| id | status | sev | area | summary |
|---|---|---|---|---|
| ER-015 | open | high | parsing | Markdown-decorated labels zero out the whole adjudication |
| ER-016 | open | high | parsing | Markdown-decorated actor replies turn refusal into alliance gain |
| ER-029 | open | high | parsing | The diplomatic outcome parser has the same bare-label defect |
| ER-030 | open | high | parsing | A plainly worded refusal is read as conditional support |
| ER-017 | open | high | context | The calls that change the game never learn what happened in it |
| ER-018 | open | high | context | The COBRA-deliberation filter matches no shipped advisor label |
| ER-019 | open | high | routing | The per-call model table is inert on the shipped provider |
| ER-020 | open | high | context | The inject generator's "story so far" is a line count |
| ER-022 | open | high | dispatch | The HTTP path serves no briefing after turn one |
| ER-002 | open | high | context | Decision interpretation never reaches the omissions prompt |
| ER-003 | open | high | context | No prompt holds both campaign history and event ledger |
| ER-004 | open | high | dispatch | Inject generation can fire twice in one turn on a resumed save |
| ER-021 | open | med | context | Mystery Mode tells the player's own advisors to deceive them |
| ER-023 | open | med | dispatch | The decision phase runs seven waits where four would do |
| ER-025 | open | med | state | Mystery Mode draws its secret from an unseeded generator |
| ER-005 | open | med | routing | Five of twelve call families bypass the model configuration |
| ER-006 | open | med | parsing | Effects parser accepts any colon line naming a metric |
| ER-007 | open | med | state | Advisor trust updates on one adjudication path only |
| ER-008 | open | med | context | Two context builders apply no size limit |
| ER-010 | open | med | state | Situation summary costs a call per turn and reaches no prompt |
| ER-012 | open | med | data | Faction stances reach two prompts and barely match the roster |
| ER-014 | open | med | context | State-actor prompt carries UK internal advisor trust |
| ER-024 | open | low | context | Player questions are written to the transcript twice |
| ER-027 | open | low | context | An advisor instruction is pasted into four non-advisor prompts |
| ER-028 | open | low | routing | The play page pins one model through an undeclared fallback |
| ER-026 | open | low | dispatch | `--no-stochastic-injects` is overridden by the turn loop |
| ER-001 | open | low | context | Empty event ledger removes the do-not-restage rule |
| ER-009 | open | low | context | Three metrics rendered three times in every dossier prompt |
| ER-011 | open | low | dispatch | Narrator output constraints dropped on three of four drivers |
| ER-013 | open | low | state | Advisor pushback mutates nothing |
| ER-031 | open | low | parsing | An explicit multiplier of 1.0 is indistinguishable from silence |

## How the measurements below were taken

Two headless campaigns played through `dev-scripts/play_campaign.py` against the local recording
endpoint `dev-scripts/fake_openrouter.py`, one with no artificial latency and one holding every
call at 1.2 seconds. Both reached a terminal ending on turn 10 and issued 148 game calls.

Inputs, so the figures can be reproduced: engine at commit `9f0c3fa` (the merge base of this
branch; the only change on the branch is this document); scenario `war_game_2025`, default
`standard` variant; seed 42; play mode `emergent`; Mystery Mode on; endings on; one player
question per turn. Those are `play_campaign.py`'s own defaults except for the turn cap and the
question count, both passed explicitly.

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

Timing figures are wall-clock and vary with the machine. The 8.5-second decision phase and the
76 per cent single-call share below were measured on the container this register was written in;
an independent re-run on different hardware reproduced the 8.5 of 12.2 seconds exactly and put
the single-call share at 80 per cent. Treat that figure as approximately three-quarters to
four-fifths rather than as a constant. Character counts and call counts do not vary.

Both runs ended with `play_campaign.py` reporting "no calls fell back to the mock driver", so
every one of the 148 calls in each run was answered by the endpoint under measurement rather than
by the built-in offline driver. That line is the check that makes the call counts and character
totals mean anything, and it should be quoted with any future measurement.

The raw logs are not committed: `calls.jsonl` and its `.prompts` sidecar together run to several
megabytes of prompt text and regenerate deterministically from the commands above in under two
minutes. Parser behaviour in ER-015 and ER-016, and the transcript filter in ER-018, were
demonstrated by calling those functions directly on paired inputs rather than through a campaign;
each entry states the inputs it used.

---

## ER-001 — Empty event ledger removes the do-not-restage rule

- **Status:** open
- **Severity:** low
- **Area:** context
- **Observed:** Continuity rule 8, the instruction not to restage a resolved event, is appended
  to the inject prompt only under `if event_ledger:`. An empty list is falsy, so an empty ledger
  omits both the EVENTS ALREADY PLAYED block and the instruction that names it.
- **Evidence:** `llm/prompts.py:422-424`; `engine/sim_loop.py:334-340`
- **Effect:** The rule and the data it refers to disappear together, which is the correct
  behaviour for a rule that names an absent block. The exposure is narrow: `record_played_event`
  runs on every briefing that produces an inject, and all four live entry points supply a
  narrative state, so the ledger is non-empty from turn one onward. It is empty only for a save
  written before the ledger existed.
- **Raised by:** context audit 2026-08-05; re-checked by the engine LLM review of 2026-08-05,
  which lowered the severity from high to low on the reachability evidence above.

## ER-002 — Decision interpretation never reaches the omissions prompt

- **Status:** open
- **Severity:** high
- **Area:** context
- **Observed:** `check_critical_omissions` takes `interpretation` as its third parameter and
  never uses it. The list comprehension that builds the five prompts passes `player_decision` and
  not `interpretation`, and `build_critical_omissions_prompt` has no parameter for it.
- **Evidence:** `agents/conversation.py:313` (the parameter), `agents/conversation.py:375-381`
  (the call that omits it); `llm/prompts.py:462-469` (a signature with no such parameter);
  `engine/sim_loop.py:566-575` (the caller that supplies it)
- **Effect:** Five advisors deciding whether the Prime Minister has omitted something
  catastrophic work from the raw typed sentence rather than from the structured reading, listing
  forces, resources, timeline and feasibility, that was produced for that purpose one call
  earlier. This is also the most expensive group in the game: measured over a ten-turn headless
  campaign it was 53.7 per cent of every prompt character the engine sent.
- **Raised by:** context audit 2026-08-05; confirmed by the engine LLM review of 2026-08-05.

## ER-003 — No prompt holds both campaign history and event ledger

- **Status:** open
- **Severity:** high
- **Area:** context
- **Observed:** The event ledger reaches the inject generation prompt and nothing else. That
  prompt carries no GAME HISTORY block. The four prompt families that do carry the history block
  never receive the ledger.
- **Evidence:** `llm/context_builder.py:285-355` (the shared dossier, no ledger);
  `llm/context_builder.py:391-439` (the inject context, no history block)
- **Effect:** Past a campaign of roughly 320,000 transcript characters the dossier prompts lose
  the elided middle of the campaign. The one structure that states each past event and how it was
  left in a single line is not among what survives. A full ledger costs about 94 characters an
  entry.

  Measured on a synthetic seventeen-turn transcript, the window kept turn 1 and turns 12 to 17 and
  dropped turns 2 to 11 entirely, with 28,838 of the 320,000-character budget unspent. That
  synthetic transcript is 17 turns of 105 lines each between `TURN N` rulers, two lines in three
  being 36 characters and the third 1,107, which averages to the 393 characters a line the prior
  audit measured on a real save.

  The unspent figure is input-dependent and should not be quoted on its own: the leftover is
  whatever is smaller than one whole turn, so it scales with turn size. The prior audit measured
  13,351 unspent against the real save `saves/parked_campaign4_borrowed_faces.json`, 1,853 lines
  and 729,186 characters. That save is not in the repository, so neither figure can be checked
  from the tree, and the two are not in conflict: they are the same mechanism on differently
  shaped turns. What reproduces independently of the input is the shape of the cut, one turn of
  head and whole turns of tail, with the middle gone.
- **Raised by:** context audit 2026-08-05; confirmed and re-measured by the engine LLM review of
  2026-08-05.

## ER-004 — Inject generation can fire twice in one turn on a resumed save

- **Status:** open
- **Severity:** high
- **Area:** dispatch
- **Observed:** The dynamic-generation branch of `run_turn_briefing` tests only whether the
  scripted file is missing and whether stochastic generation is on. It has no `replay` guard;
  `replay` is consulted at the effects step and the diplomatic-encounter step only.
  `record_played_event` also runs on the replay path.
- **Evidence:** `engine/sim_loop.py:316-329` (no guard), `engine/sim_loop.py:334-337`
  (the ledger write, ungated), `engine/sim_loop.py:384`, `engine/sim_loop.py:396`;
  `cli/main.py:729`, `cli/main.py:859`
- **Effect:** Loading a save taken mid-turn generates a second, different event for a turn that
  already had one. The first event's effects stay applied to the metrics while the ledger entry
  for that turn is overwritten with the second event's title, so the record of what happened no
  longer matches what the metrics say happened.
- **Raised by:** context audit 2026-08-05; confirmed by the engine LLM review of 2026-08-05.

## ER-005 — Five of twelve call families bypass the model configuration

- **Status:** open
- **Severity:** medium
- **Area:** routing
- **Observed:** The narrator bridge, the action quality assessment, the advisor reactions, the
  situation summary and the state-actor simulation all dispatch without a `context=` argument, so
  the router leaves the model name as `None` and the driver's own default answers.
  `LLMContext.CHARACTER_RESPONSE` is defined, given a tier, and offered in the in-game model
  menu, but is passed to nothing anywhere in the repository.
- **Evidence:** `engine/narrator.py:36-42`; `engine/narrative_adjudication.py:269`,
  `engine/narrative_adjudication.py:545-546`, `engine/narrative_adjudication.py:687`;
  `engine/actor_simulation.py:131`; `llm/router.py:229-234`, `llm/router.py:330-335`;
  `llm/model_config.py:19`, `llm/model_config.py:37`; `cli/model_settings_menu.py:33`,
  `cli/model_settings_menu.py:124`
- **Effect:** The per-context tier table and the in-game model menu govern seven families and not
  the other five. The entire adjudication half of a turn, which is the half that decides what
  happens, sits outside them. A sixth context-less dispatch exists at
  `engine/actor_simulation.py:99` but has no caller outside tests, so five is the live count. See
  also ER-019: on the provider the public build actually uses, the table governs nothing at all.
- **Raised by:** context audit 2026-08-05; confirmed by the engine LLM review of 2026-08-05.

## ER-006 — Effects parser accepts any colon line naming a metric

- **Status:** open
- **Severity:** medium
- **Area:** parsing
- **Observed:** The effects branch accepts any line containing a colon together with the
  substring `escalation`, `alliance` or `stability`, takes everything before the first colon as
  the metric name, and tries to read the rest as an integer. A wrapped continuation line of the
  REASONING paragraph in that shape is read as a metric effect. A casualties line is silently
  discarded by the same filter, because only those three substrings are accepted.
- **Evidence:** `engine/narrative_adjudication.py:374-381`; the three deltas the prompt asks for
  are at `engine/narrative_adjudication.py:260-263`
- **Effect:** Narrative prose can move hidden metrics, and a metric the prompt did not ask for
  cannot. See ER-015 for the more damaging consequence of the same branch: the metric name is
  taken verbatim, so any decoration on the line produces a key no metric object has and the
  effect is dropped without trace.
- **Raised by:** context audit 2026-08-05; confirmed by the engine LLM review of 2026-08-05.

## ER-007 — Advisor trust updates on one adjudication path only

- **Status:** open
- **Severity:** medium
- **Area:** state
- **Observed:** `_update_character_attitudes` is called from `adjudicate_with_narrative` and from
  nowhere else. `adjudicate_with_actor_simulation` does not call it. The actor path is the one
  every live entry point takes whenever the state-actor file loads, which it does by default.
- **Evidence:** `engine/narrative_adjudication.py:788` (the only call site),
  `engine/narrative_adjudication.py:928-943` (the definition),
  `engine/narrative_adjudication.py:799-900` (the actor path, which does not call it);
  `engine/game_manager.py:289`; `cli/main.py:1839`
- **Effect:** Advisor trust responds to the quality of the player's decisions in the fallback
  adjudication mode and not in the one normally used. The trust numbers that the character
  reaction prompt and the state-actor prompt both interpolate are therefore not merely near their
  starting values, they are unchanged: at turn nine of the headless campaign they read 50, 75, 70,
  80 and 85, byte-identical to the values seeded at `models/narrative_state.py:407-435`.
- **Raised by:** context audit 2026-08-05; confirmed by the engine LLM review of 2026-08-05.

## ER-008 — Two context builders apply no size limit

- **Status:** open
- **Severity:** medium
- **Area:** context
- **Observed:** `get_diplomatic_context` applies no character bound to the filtered transcript it
  returns. The narrator takes the last twenty transcript elements with no character cap, and one
  element can be a full unwrapped paragraph.
- **Evidence:** `llm/context_builder.py:441-512`; `llm/prompts.py:587`
- **Effect:** The same shape as the overrun already corrected in the advisor window, where four
  hundred long lines reached 792,572 characters against a 320,000-character budget. Prompt size
  here is bounded by nothing but the input.
- **Raised by:** context audit 2026-08-05; confirmed by the engine LLM review of 2026-08-05.

## ER-009 — Three metrics rendered three times in every dossier prompt

- **Status:** open
- **Severity:** low
- **Area:** context
- **Observed:** The shared dossier prints escalation, stability and cohesion as raw values out of
  one hundred, then again as prose bands, then a third time as KEY INTELLIGENCE FLAGS. The flags
  are five booleans thresholded from those same metrics, in a dictionary that is replaced rather
  than accumulated on every update.
- **Evidence:** `llm/context_builder.py:337-341` (raw values), `llm/context_builder.py:351-352`
  (prose bands via `build_world_state_summary`); `llm/prompts.py:67-71` (the flags);
  `engine/flags.py:15-40` (the derivation)
- **Effect:** The third rendering carries no information the first two do not. Observed in a
  captured prompt as "KEY INTELLIGENCE FLAGS: Risk Escalation, Risk Unrest, Risk Civilian Harm,
  Risk Military Losses" sitting directly below the numbers those flags were computed from.
- **Raised by:** context audit 2026-08-05; confirmed by the engine LLM review of 2026-08-05.

## ER-010 — Situation summary costs a call per turn and reaches no prompt

- **Status:** open
- **Severity:** medium
- **Area:** state
- **Observed:** `update_situation_summary` issues an LLM call every turn and overwrites
  `NarrativeState.situation_summary`. Its own docstring says the field "feeds `to_llm_context()`
  for every downstream prompt". `to_llm_context()` does not include it. The only readers are the
  emergent branch of `display_for_mode`, which has no production caller, and four direct echoes
  across the two terminal front ends, all of which fire only in emergent play mode.
- **Evidence:** `engine/narrative_adjudication.py:666-695` (the call and the docstring claim);
  `models/narrative_state.py:240-267` (`to_llm_context`, no summary);
  `models/narrative_state.py:231-234` (`display_for_mode`, emergent branch);
  the four direct readers at `cli/main.py:1110`, `cli/main.py:1962`,
  `cli/main_dashboard.py:1158` and `cli/main_dashboard.py:1733`;
  `docs/py/bridge.py` contains no reader
- **Effect:** One call in roughly fifteen every turn produces text no model ever sees. On the
  browser build, which is the public deployment, no player sees it either, in any of the three
  play modes the page offers. That also makes the page's "Emergent — maximum LLM freedom" option
  indistinguishable from "Immersive — metrics hidden" in what it actually shows.
- **Raised by:** context audit 2026-08-05; confirmed and extended to the browser build by the
  engine LLM review of 2026-08-05.

## ER-011 — Narrator output constraints dropped on three of four drivers

- **Status:** open
- **Severity:** low
- **Area:** dispatch
- **Observed:** The narrator passes a system instruction, a temperature and a 150-token output
  cap. The router forwards each of these only to a driver whose `generate_text` signature
  declares it. Three of the four drivers declare `(prompt, rng)` alone.
- **Evidence:** `engine/narrator.py:36-42`; `llm/router.py:251-264` (the signature test);
  `llm/gemini_driver.py:106`, `llm/mock_driver.py:1140`, `llm/offline_driver.py:15` (signatures
  that take none of the three); `llm/openai_compat_driver.py:150-157` (the one that takes all
  three)
- **Effect:** The length cap on the atmospheric bridge is not enforced on Gemini. It is enforced
  on the OpenAI-compatible driver, which is what the public build uses, so the exposure is
  limited to Gemini play.
- **Raised by:** context audit 2026-08-05; re-checked by the engine LLM review of 2026-08-05,
  which narrowed the claim from "some drivers" to the three named above.

## ER-012 — Faction stances reach two prompts and barely match the roster

- **Status:** open
- **Severity:** medium
- **Area:** data
- **Observed:** The prior entry stated that `NarrativeConfig.to_llm_context()` is always called
  without a country argument. That was wrong and is corrected here: the diplomatic context
  builder does pass a country code, so a stance does reach the diplomacy prompts when the country
  has one. The other four call sites pass no code, so the per-country secret motive, public
  posture, economic leverage and intelligence-sharing level are skipped there. Separately,
  stances exist for RUS, USA, CHN and IRL while the state actors are USA, FRA, DEU, POL and RUS.
- **Evidence:** `llm/context_builder.py:502` (passes a code, correcting the prior claim);
  `llm/context_builder.py:323`, `llm/context_builder.py:416`,
  `engine/narrative_adjudication.py:221`, `engine/narrative_adjudication.py:844` (pass none);
  `models/narrative.py:46-67`; `data/scenarios/war_game_2025/narratives.yaml`;
  `data/state_actors.yaml:5,36,69,99,124`
- **Effect:** Authored per-country content reaches the diplomacy calls only. Only USA and RUS
  appear in both the stance list and the actor roster: CHN and IRL have stances no state actor
  can voice, and FRA, DEU and POL are simulated with no scripted stance behind them.
- **Raised by:** context audit 2026-08-05; corrected by the engine LLM review of 2026-08-05.

## ER-013 — Advisor pushback mutates nothing

- **Status:** open
- **Severity:** low
- **Area:** state
- **Observed:** No metric, flag, trust value or ledger entry is written from pushback output
  anywhere. It drives the confirm gate in the terminal CLI and the transcript, and nothing else.
  On the headless path every pushback line is given the same canned recommendation, "Consider
  revising your approach."
- **Evidence:** `engine/game_manager.py:213-220`; `cli/main.py:1790-1819`;
  `agents/conversation.py:248-307` (parses the reply and returns it, writes nothing)
- **Effect:** A cabinet objection has no mechanical consequence, and a consumer of the headless
  interface cannot tell a pushback line from a critical-omission line.
- **Raised by:** context audit 2026-08-05; confirmed by the engine LLM review of 2026-08-05.

## ER-014 — State-actor prompt carries UK internal advisor trust

- **Status:** open
- **Severity:** medium
- **Area:** context
- **Observed:** The world context handed to a foreign government's roleplay prompt is
  `NarrativeState.to_llm_context()`, which interpolates every character's name, relationship
  label and trust score. The character dictionary is not all-UK: it also seeds a US National
  Security Advisor.
- **Evidence:** `engine/actor_simulation.py:54-55` (the `{world_context}` slot);
  `engine/narrative_adjudication.py:841`; `models/narrative_state.py:262`;
  `models/narrative_state.py:404-438`
- **Effect:** A foreign actor reasons from the UK cabinet's private internal state. Confirmed in
  a captured turn-nine prompt, which listed all five advisors with their trust scores.
- **Raised by:** context audit 2026-08-05; confirmed by the engine LLM review of 2026-08-05.

## ER-015 — Markdown-decorated labels zero out the whole adjudication

- **Status:** open
- **Severity:** high
- **Area:** parsing
- **Observed:** `_parse_quality_response` recognises a field only when the line begins with the
  bare label: `line.startswith("QUALITY:")`, `line.startswith("REASONING:")`,
  `line.startswith("QUALITY MULTIPLIER:")`. The effects branch takes everything before the first
  colon as the metric name verbatim. If the model emits the same content with markdown emphasis,
  every one of these misses. How often a given model does that was not measured here, so no
  frequency is claimed; what is established is that the failure is total when it happens and that
  nothing detects it. The sibling parser in `agents/conversation.py` was already hardened against
  this same shape through
  `_extract_labeled_text`, which accepts `**CONCERN:**` and `- concern:`; the adjudication parser
  was not.
- **Evidence:** `engine/narrative_adjudication.py:366`, `:371`, `:374-381`, `:383`;
  the tolerant sibling at `agents/conversation.py:116-127`;
  `engine/narrative_adjudication.py:767-776` (the narrative path applies `suggested_effects` and
  nothing else)
- **Effect:** Demonstrated by running `_parse_quality_response` and then `apply_quality_scaling`
  on one answer in three forms. The answer is `QUALITY: poor`, a one-sentence REASONING, the three
  deltas `escalation_risk: 8`, `alliance_cohesion: -6`, `domestic_stability: -3`, and
  `QUALITY MULTIPLIER: 0.5`.

  1. Bare labels, bare delta lines. Quality `poor`, multiplier 0.5, parsed deltas 8, -6 and -3,
     applied after scaling as escalation +6, cohesion -5 and stability -2, and the model's own
     critique shown to the player.
  2. The same text with the labels emphasised and the deltas as plain `- name: value` bullets.
     Quality falls back to `adequate` and the multiplier to 1.0; the metric keys become
     `__escalation_risk` and its two siblings, which no metric object has, so the `hasattr` test
     at `:773` rejects all three.
  3. The same again with the delta bullets also emphasised. The `int()` at `:378` fails first, so
     the effects dictionary is empty before the `hasattr` test is ever reached.

  Forms 2 and 3 reach the same outcome by different routes: no metric effect is applied, and the
  player is shown the placeholder line "Action assessed." The rest of the pipeline still runs, so
  the turn is not inert: the event disposition is recorded, character reactions are generated,
  advisor attitudes are updated and crises are checked. What is lost is the whole of the decision's
  effect on the three metrics, which on the narrative adjudication path is the only mechanical
  consequence a decision has. On the actor path the keyword-derived base effects still move, but the
  quality multiplier is wrong in the direction of leniency. How often a given model emits any of
  these forms was not measured, so no frequency is claimed; what is established is that the
  failure is total when it happens and that nothing detects it.
- **Raised by:** engine LLM review 2026-08-05

## ER-016 — Markdown-decorated actor replies turn refusal into alliance gain

- **Status:** open
- **Severity:** high
- **Area:** parsing
- **Observed:** `_parse_actor_response` recognises each field only from a bare label at the start
  of a line. When none matches, the defaults stand: `will_support` is `"conditional"`,
  `trust_change` is 0, and `public_response` falls back to the string
  `"{actor_id} acknowledges the action."` A `"conditional"` verdict is not neutral in effect: it
  contributes a positive alliance-cohesion term.
- **Evidence:** `engine/actor_simulation.py:151-152` (the two defaults named above),
  `engine/actor_simulation.py:162-201` (the bare-label tests),
  `engine/actor_simulation.py:204-212` (the fallback text),
  `engine/actor_simulation.py:318-320` (`conditional` adds `int(2 * weight)` to cohesion)
- **Effect:** Demonstrated by running the parser on the same reply twice. Plain: public response
  preserved, trust change -8, support `no`, which costs cohesion. With markdown emphasis: the
  reply becomes "USA acknowledges the action.", trust change 0, support `conditional`, which
  gains cohesion. Washington's outright refusal to back the United Kingdom is rendered on screen
  as a bland acknowledgement and scored as a small diplomatic win. On the actor adjudication path
  the actor effects are then blended sixty-forty with the quality effects, so the realised gain is
  0.6 of the figure above; the sign is still wrong. The failure is silent: the call succeeded,
  nothing was logged, and no fallback counter moved.
- **Raised by:** engine LLM review 2026-08-05

## ER-017 — The calls that change the game never learn what happened in it

- **Status:** open
- **Severity:** high
- **Area:** context
- **Observed:** Five call families run the adjudication. Three of them decide what happens: the
  action quality assessment and the state-actor simulation set the metric changes, and the
  diplomatic outcome assessment sets the alliance delta from a call. The other two are outputs of
  the adjudication rather than inputs to it: the advisor reactions are shown to the player, and
  the situation summary reaches nobody at all (ER-010). Four of the five, all but the diplomatic
  outcome assessment, which uses `build_world_state_summary` instead (`engine/diplomacy.py:291`),
  build their world context from `NarrativeState.to_llm_context()`, which contains the three
  metrics, up to three entries from `recent_events`, the active-crisis list, character trust
  scores and a game clock, plus the hidden narrative block in Mystery Mode and nothing else.
  `recent_events` is seeded once at campaign start with three fixed
  backstory lines and is thereafter written by one function only, the crisis-threshold check,
  which appends one of three fixed banner strings. No inject title, player decision, adjudication
  outcome or advisor line ever enters it. `active_crises` only grows; `resolve_crisis` has no
  caller outside tests. `game_time` is written at construction and never advances.
- **Evidence:** `models/narrative_state.py:240-267` (the context);
  `models/narrative_state.py:294-299` (`add_event`);
  `models/narrative_state.py:455-463` (the one-time seed);
  `engine/narrative_adjudication.py:946-963` (the only writer);
  `models/narrative_state.py:363-366` (`resolve_crisis`, no caller);
  consumers at `engine/narrative_adjudication.py:216`, `:605`, `:674`, `:841`
- **Effect:** Captured from a live turn-nine prompt in a headless campaign: the "Recent Events"
  block held one turn-one backstory line and two crisis banners, and the clock read
  "Game Time: 17:00 (Turn 9)" for a crisis spanning days. The referee that sets the metrics is
  told nothing that happened in nine turns of play. Measured over the same ten-turn campaign, the
  three families that decide the metric changes received 5.9 per cent of every prompt character
  the engine sent, and the two adjudication outputs a further 1.5 per cent, against 89.0 per cent
  for the four advisory families that change nothing and 3.7 per cent for story generation. On a
  long campaign where the history window is at its 320,000-character ceiling the gap widens to
  roughly 0.5 per cent against 97.5 per cent, because the advisory prompts grow with the
  transcript and these do not.
- **Raised by:** engine LLM review 2026-08-05

## ER-018 — The COBRA-deliberation filter matches no shipped advisor label

- **Status:** open
- **Severity:** high
- **Area:** context
- **Observed:** `get_diplomatic_context` promises in its own docstring to exclude all internal UK
  COBRA deliberations. It detects them by testing each transcript line for one of seven literal
  markers: "prime minister:", "national security advisor:", "chief of the defence staff:",
  "home secretary:", "foreign secretary:", "attorney general:" and "discussion phase". The
  transcript writes an advisor's line as `f"{role}: {response}"`, and the six roles in the
  shipped scenario are "Government Leader", "Military Commander", "Intelligence Coordinator",
  "Domestic Security", "Diplomatic Lead" and "Legal Advisor". None of them matches any marker.
  Meanwhile any line containing "===" sets the include flag, and that flag stays set until a
  marker resets it.
- **Evidence:** `llm/context_builder.py:441-512` (the filter and its docstring);
  `engine/sim_loop.py:485` (`transcript.append(f"{role}: {response}")`);
  `data/scenarios/war_game_2025/initial_conditions.yaml:444,454,464,474,484,494` (the labels)
- **Effect:** The filter is erratic rather than inert, and it fails in both directions. Run over a
  hand-built single turn using the shipped role labels, the only line it removed was the Prime
  Minister's own question, and everything it exists to protect passed through: the Diplomatic Lead
  saying "I would not tell the Americans we are planning for their refusal", the Military
  Commander's true force state, the Intelligence Coordinator's private caveat on attribution, and
  the Prime Minister's decision. Run over a real campaign transcript instead, taken from the GAME
  HISTORY block of a captured prompt in the headless run described above, it dropped 14 of 51
  non-blank lines while still leaking the one advisor line carrying a shipped role label. So it
  both passes internal deliberation to a foreign government and redacts public material at random,
  depending on where the include latch was last set. That latch is set by any line containing
  `===`, the four characters `turn` followed by a space, `briefing`, `breaking news` or
  `intel report`, and cleared only by one of the seven markers that shipped data never produces.
  Note that the second of those is a substring test, not a word test: it matches inside "return to
  base", though not inside the word "return" on its own. The entry point where this matters most,
  a call to Washington, is offered on the public play page.
- **Raised by:** engine LLM review 2026-08-05

## ER-019 — The per-call model table is inert on the shipped provider

- **Status:** open
- **Severity:** high
- **Area:** routing
- **Observed:** `MODEL_NAMES` maps the two tiers to `gemini-2.5-flash` and `gemini-2.5-pro`, so
  every name the tier table can produce begins with "gemini". `OpenAICompatDriver.__init__`
  discards any model name beginning with "gemini" and uses `OPENAI_COMPAT_MODEL` instead. The
  browser build and every OpenRouter, Groq, Ollama or LM Studio configuration go through that
  driver.
- **Evidence:** `llm/model_config.py:42-45`; `llm/openai_compat_driver.py:123-128`;
  `llm/router.py:229-236`; `docs/py/bridge.py:523-534` (the browser build sets the provider to
  `openai_compat`)
- **Effect:** On the public deployment every one of the twelve call families runs on the same
  model, whatever the table says. The in-game `/llm` model menu edits a table that changes
  nothing, and the `--flash-only` cost-saving flag saves nothing. The router also caches a
  separate driver instance per model name, so the two tier names and the no-context default build
  and keep three identical drivers; a misconfiguration therefore prints its fallback warning once
  per key rather than once, which is the opposite of what that cache exists for. Note the
  interaction with ER-005: the five families that pass no context were
  already outside the table, and this puts the remaining seven outside it too.
- **Raised by:** engine LLM review 2026-08-05

## ER-020 — The inject generator's "story so far" is a line count

- **Status:** open
- **Severity:** high
- **Area:** context
- **Observed:** The inject prompt's block headed "STORY SO FAR (HIGH-LEVEL SUMMARY)" is filled by
  `generate_summary`, which makes no model call. It emits the number of turns played, the number
  of transcript lines, and up to three transcript lines that happen to begin with one of six
  prefixes: `[Narrator]`, `[Stochastically generated inject]`, `***`, `BREAKING`, `INTEL` or
  `BRIEFING`, each truncated to 100 characters. The `summary_prompt` argument, which asks for the
  significant events, the player's major decisions and the current diplomatic relationships, is
  deleted on the first line of the function. Making the digest mechanical is deliberate and the
  docstring says why: it removes a call whose placeholder output could leak into downstream
  prompts. The complaint here is not that choice but its consequence, described below.
- **Evidence:** `llm/context_builder.py:562-600` (the digest, and `del summary_prompt` at :570);
  `llm/prompts.py:389-405` (the prompt text that is discarded, and the call);
  `llm/context_builder.py:420-425` (the block header)
- **Effect:** Captured from a live turn-seven prompt: the three "recent events" were a narrator
  atmosphere line, "INCOMING SECURE CALL: US PRESIDENT" and "MANDATORY DIPLOMATIC ENCOUNTER", two
  of them stage directions rather than events. The component most responsible for the story
  hanging together is given a line count, the event titles from the ledger, and the previous turn
  verbatim. It never sees the campaign transcript at all, and it is told the block is a
  high-level summary of the story so far.
- **Raised by:** engine LLM review 2026-08-05

## ER-021 — Mystery Mode tells the player's own advisors to deceive them

- **Status:** open
- **Severity:** medium
- **Area:** context
- **Observed:** `NarrativeConfig.to_llm_context` always appends a four-line instruction block,
  regardless of whether a country stance was requested: "Act according to your secret motive at
  all times", "Never explicitly reveal this information to the UK", "Your behaviour should subtly
  reflect these hidden truths", "Provide plausible deniability in all statements". That block is
  written for a foreign actor being roleplayed. It is inserted into the shared briefing dossier
  that the advisor Q&A, decision interpretation, pushback and critical-omissions prompts all open
  with, into the inject generation prompt, and into the action quality assessment prompt.
- **Evidence:** `models/narrative.py:69-78` (the unconditional block);
  `llm/context_builder.py:322-323` (into the shared dossier);
  `llm/context_builder.py:415-417` (into the inject prompt);
  `engine/narrative_adjudication.py:219-221` (into the quality assessment);
  `engine/narrative_adjudication.py:843-844` (into the actor context, where it belongs);
  `llm/context_builder.py:501-503` (into the diplomat prompt, where it belongs)
- **Effect:** In Mystery Mode the player's own cabinet is instructed to act on a secret motive and
  to give the United Kingdom plausible deniability, in the same prompt that asks them to advise
  the United Kingdom honestly. The impartial referee that scores the decision is told the same
  thing, although that prompt at least adds counter-instructions of its own further down
  (`engine/narrative_adjudication.py:244-252`); the four advisory prompts add nothing to offset
  it. Mystery Mode only: `world.narrative` is `None` in Original Story Mode, which is the
  default on every entry point, so ordinary play is unaffected.
- **Raised by:** engine LLM review 2026-08-05

## ER-022 — The HTTP path serves no briefing after turn one

- **Status:** open
- **Severity:** high
- **Area:** dispatch
- **Observed:** `manager.get_turn_briefing()` appears exactly once in the HTTP server, inside the
  handler that creates a new game. There is no endpoint that runs a later briefing; the only
  briefing-shaped route acknowledges one and sets the phase.
- **Evidence:** `api/server.py:275` (the sole call, in `POST /game/new`);
  `api/server.py:601` (`POST /game/{session_id}/briefing/ack`, which changes the phase only)
- **Effect:** Over the HTTP interface, turns two and later have no inject, no inject effects, no
  narrator bridge and no mandatory diplomatic encounter. Two of the twelve call families, inject
  generation and the narrator, are unreachable on that path entirely. This does not affect the
  terminal CLI or the browser build, which drive the briefing themselves. Established from source;
  the server was not run.
- **Note on severity:** `high` is set on the size of the break, not on how many people it reaches.
  This surface backs the in-development Next.js frontend and has no tests, so a reasonable case
  exists for `medium`. That turns on whether the HTTP server is still a supported way to play,
  which is the operator's call: if it is not, this should be closed `wontfix` rather than
  downgraded.
- **Raised by:** engine LLM review 2026-08-05

## ER-023 — The decision phase runs seven waits where four would do

- **Status:** open
- **Severity:** medium
- **Area:** dispatch
- **Observed:** Committing a decision issues seven dispatch rounds one after another:
  interpretation, pushback, the batched five-advisor omissions scan, the batched actor
  simulation, the quality assessment, the batched character reactions and the situation summary.
  Only two of the seven dependencies are real. Pushback needs the interpretation. The character
  reactions need the quality assessment. The omissions scan does not use the interpretation at
  all (ER-002), so it can run alongside the interpretation rather than after it. The quality
  assessment does read the interpretation and must follow it, but the actor simulation reads only
  the action and the narrative state and can run beside either. The situation summary reads only
  the action and the narrative state as well, but it runs after the metric mutation and would
  summarise pre-adjudication metrics if hoisted, so it belongs in the last round beside the
  character reactions rather than in an early one.
- **Evidence:** `engine/sim_loop.py:532-575` (three sequential rounds);
  `engine/narrative_adjudication.py:838-898` (four more);
  `engine/narrative_adjudication.py:228` (the quality prompt interpolates the interpretation);
  `engine/narrative_adjudication.py:879-883` then `:898` (the summary runs after the mutation)
- **Effect:** Measured on a ten-turn headless campaign against a local endpoint held at 1.2
  seconds per call: the decision phase took 8.5 seconds of a 12.2-second turn, and across the
  whole campaign 76 per cent of wall clock had exactly one call in flight. Regrouping to four
  rounds would put the decision phase at roughly 4.8 seconds on the same latency. Against a real
  provider at several seconds a call, this is the difference between a pause and a wait.
- **Raised by:** engine LLM review 2026-08-05

## ER-024 — Player questions are written to the transcript twice

- **Status:** open
- **Severity:** low
- **Area:** context
- **Observed:** `GameManager.process_question` appends `f"Prime Minister: {question_text}"` to the
  transcript and then calls `run_turn_discussion`, which appends the identical line itself; the
  returned lines are then extended onto the transcript as well. The terminal CLI does not have
  this double write.
- **Evidence:** `engine/game_manager.py:175`, `engine/game_manager.py:177-186`;
  `engine/sim_loop.py:473`
- **Effect:** Every player question appears twice in the campaign transcript on the browser build
  and the HTTP path, and therefore twice in every prompt that carries the history block. Observed
  in a captured turn-six prompt. The waste is small per question but compounds: the history block
  is the largest element of the eight most expensive dispatches in a turn.
- **Raised by:** engine LLM review 2026-08-05

## ER-025 — Mystery Mode draws its secret from an unseeded generator

- **Status:** open
- **Severity:** medium
- **Area:** state
- **Observed:** The terminal CLI's Mystery Mode branch imports the `random` module inside the
  function and calls `random.choice(narratives)` on the module-level generator. The seeded
  generator built for the campaign is not used. `GameManager` does it correctly with
  `self.rng.choice`.
- **Evidence:** `cli/main.py:502-504`; `engine/game_manager.py:93-97`
- **Effect:** A campaign started from a fixed seed does not replay identically in Mystery Mode on
  the terminal path: a different hidden truth can be drawn, which changes the secret narrative
  block in every prompt that carries it and therefore changes the whole campaign. This is the one
  entry here that breaks the project's stated determinism guarantee.
- **Raised by:** engine LLM review 2026-08-05

## ER-026 — `--no-stochastic-injects` is overridden by the turn loop

- **Status:** open
- **Severity:** low
- **Area:** dispatch
- **Observed:** The flag defaults to true and is documented as a switch. At the top of every turn
  the loop tests whether the turn has reached the scenario's transition point and, if so, sets the
  flag back to true and prints a transition banner. That is the same turn from which the flag
  first has any effect.
- **Evidence:** `cli/main.py:557` (the option), `cli/main.py:817-821` (the override),
  `cli/main.py:837` (the only use); the same pattern at `cli/main_dashboard.py:835-838`
- **Effect:** Passing `--no-stochastic-injects` changes nothing. A player or tester who wants a
  purely scripted campaign has no way to get one.
- **Raised by:** engine LLM review 2026-08-05

## ER-027 — An advisor instruction is pasted into four non-advisor prompts

- **Status:** open
- **Severity:** low
- **Area:** context
- **Observed:** `build_world_state_summary` ends with four standing instructions written for a
  cabinet advisor: "You are a real advisor in COBRA during a national crisis", "Speak naturally
  about intelligence assessments", "Do NOT reference 'metrics', 'game mechanics', 'scores', or
  'values'", "Use professional crisis management language". The function is pasted whole into the
  shared briefing dossier, the narrator prompt, the diplomatic outcome assessment and the
  no-transcript branch of the inject prompt.
- **Evidence:** `llm/prompts.py:73-79` (the instructions); `llm/context_builder.py:351-352`;
  `llm/prompts.py:584`; `engine/diplomacy.py:291`; `llm/prompts.py:410`
- **Effect:** The narrator is told it is an advisor. The diplomatic outcome assessor is told not
  to reference values and then asked in the same prompt to answer with
  "ALLIANCE_COHESION_DELTA: [number between -15 and +15]". Observed in a captured prompt. A direct
  instruction not to do the thing the prompt then requires is the kind of contradiction that makes
  a smaller model refuse or hedge.
- **Raised by:** engine LLM review 2026-08-05

## ER-028 — The play page pins one model through an undeclared fallback

- **Status:** open
- **Severity:** low
- **Area:** routing
- **Observed:** The play page sends the worker a key and a source, and no model or base URL. The
  bridge therefore falls through to its hardcoded defaults, `https://openrouter.ai/api/v1` and
  `openai/gpt-4o-mini`. The page has no control for the model, and the header it prints says only
  "MODEL  live endpoint".
- **Evidence:** `docs/app.js:219` (the message sent); `docs/py/bridge.py:526-534` (the
  fallbacks); `docs/index.html:126-143` (the options offered, none of them a model);
  `docs/py/bridge.py:647` (the header line)
- **Effect:** Every public game runs on one model chosen by a fallback rather than by a decision
  recorded anywhere, and neither the player nor the operator can see which. Changing it means
  editing a default in the bridge and rebuilding the bundle. This also decides whether the
  prompt-ordering work in `llm/context_builder.py` pays off at all, since automatic prefix
  caching is a per-model-family property.
- **Raised by:** engine LLM review 2026-08-05

## ER-029 — The diplomatic outcome parser has the same bare-label defect

- **Status:** open
- **Severity:** high
- **Area:** parsing
- **Observed:** `assess_diplomatic_outcome` reads its three fields with the same bare
  `startswith` tests as the two parsers in ER-015 and ER-016, and falls back to `NEUTRAL`, a delta
  of 0 and the string "The conversation concluded." when none matches. This is the third of the
  three call families that set metric changes, named as such in ER-017, and the sweep that
  produced ER-015 and ER-016 missed it.
- **Evidence:** `engine/diplomacy.py:325`, `:327`, `:336` (the bare-label tests);
  `engine/diplomacy.py:318-320` (the fallback values);
  `engine/diplomacy.py:340-342` (what is returned and displayed)
- **Effect:** Demonstrated by running the function on one answer in two forms, with a stub
  standing in for the model. Bare labels: outcome `FAILURE`, alliance delta -12, and the summary
  "Washington refused." shown to the player. The same text with the labels emphasised: outcome
  `NEUTRAL`, delta 0, and the placeholder "The conversation concluded." A call in which the United
  States refused the United Kingdom is recorded as neither good nor bad and costs nothing. As in
  ER-015 and ER-016 the call succeeded, so nothing is logged and no fallback counter moves. No
  frequency is claimed; a live provider was not called from this environment.
- **Raised by:** independent review of pull request 40, 2026-08-05

## ER-030 — A plainly worded refusal is read as conditional support

- **Status:** open
- **Severity:** high
- **Area:** parsing
- **Observed:** The `WILL_SUPPORT:` branch of the actor parser tests
  `"no" in content and "not" not in content`. The second clause was added to stop a phrase such as
  "not conditional" registering as a refusal, but it also rejects every refusal that contains the
  word "not". Anything that fails all three tests keeps the default, `"conditional"`, which
  contributes a positive alliance-cohesion term.
- **Evidence:** `engine/actor_simulation.py:177-185` (the branch, with the guard at `:181`);
  `engine/actor_simulation.py:152` (the default);
  `engine/actor_simulation.py:318-320` (`conditional` adds `int(2 * weight)` to cohesion);
  `engine/narrative_adjudication.py:871-877` (the sixty-forty blend that scales it)
- **Effect:** Demonstrated on four replies that follow the requested format exactly, with no
  markdown anywhere. "no" is read correctly as a refusal. "absolutely not", "not at this time" and
  "no, we will not assist" are all read as conditional support, so a refusal by the United States
  becomes a small alliance gain instead of a substantial loss. This is the same sign flip as
  ER-016 but reachable on well-formed output, which makes it the wider exposure of the two.
- **Raised by:** independent review of pull request 40, 2026-08-05

## ER-031 — An explicit multiplier of 1.0 is indistinguishable from silence

- **Status:** open
- **Severity:** low
- **Area:** parsing
- **Observed:** `multiplier` is initialised to 1.0 and, after parsing, any value still equal to
  1.0 is replaced from a quality-to-multiplier table. A model that answers `QUALITY: poor` and
  `QUALITY MULTIPLIER: 1.0` has its explicit answer overwritten with 0.5, because 1.0 is being
  used both as a default and as a legal value.
- **Evidence:** `engine/narrative_adjudication.py:361` (the initial value),
  `engine/narrative_adjudication.py:383-388` (the parse),
  `engine/narrative_adjudication.py:391-399` (the override)
- **Effect:** Demonstrated: that exact answer yields a multiplier of 0.5. The only value the model
  cannot express is the neutral one, and a model that deliberately says "this decision is poor but
  its effects are ordinary" gets its effects halved instead. Low severity because the substituted
  value is at least in the right direction for every quality band.
- **Raised by:** independent review of pull request 40, 2026-08-05
