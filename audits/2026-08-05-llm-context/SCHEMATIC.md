# FALSE FLAG — LLM call schematic

Every prompt the game issues: what enters it, where that data comes from, how it is
bounded, why the call exists, and what its output changes. Traced against the source at
`d197c44`; measurements against `saves/parked_campaign4_borrowed_faces.json`.

Each input row is marked `IN` (reaches the prompt) or `OUT` (available to the call site
and not sent). `OUT` rows are the interesting ones.

## Briefing

### Games Master: generate the next crisis event ("inject") for this turn

`inject_generation`

- **Prompt built at** — llm/prompts.py:334 build_inject_generation_prompt (prompt f-string at llm/prompts.py:426-457); story-context half assembled by llm/context_builder.py:391 get_stochastic_inject_context
- **Dispatched at** — llm/inject_generator.py:71 generate_text(prompt, rng, context=LLMContext.INJECT_GENERATION) -> llm/router.py:203 generate_text -> llm/router.py:264 driver.generate_text
- **LLM context** — LLMContext.INJECT_GENERATION (llm/model_config.py:16), passed at llm/inject_generator.py:71
- **Model tier** — PRO -> "gemini-2.5-pro" (llm/model_config.py:34 DEFAULT_MODEL_CONFIG[INJECT_GENERATION]=ModelTier.PRO, name at llm/model_config.py:44); resolved at llm/router.py:232. No model_override, system_instruction, temperature or max_tokens is passed (llm/inject_generator.py:71 passes only prompt, rng, context), so the GeminiDriver defaults apply: temperature 0.7, max_output_tokens 2048, 60s timeout (llm/gemini_driver.py:92-104, 129). Model name also picks the rate limit: non-"flash" => 2 RPM (llm/router.py:134-140).
- **Calls per turn** — 0 or 1. Fires only when there is no scripted inject file for the turn AND stochastic mode is on (engine/sim_loop.py:316 `if inject is None and stochastic_injects`). The CLI gates stochastic mode on `world.turn >= stochastic_from_turn`, default 7 (cli/main.py:790, 837); GameManager the same (engine/game_manager.py:139-140).
- **Concurrency** — Alone. One sequential blocking call — not part of llm/fanout.py or batch_generate_text (neither references inject generation). show_spinner defaults to True (llm/router.py:206), so on a live provider it runs under the "AWAITING SECURE TRAFFIC" spinner (llm/router.py:290). On gemini/openai_compat it first claims a rate-limit slot (llm/router.py:241-244), which for a non-flash model means 2 RPM (llm/router.py:134-140).
- **On failure** — Layered, and the player never sees an error. (1) llm/router.py:269-279: any driver exception is retried once after a 2s sleep, then falls back to MockDeterministicDriver, which has a dedicated inject branch (llm/mock_driver.py:1230-1234) returning fenced YAML from a fixed pool — so a provider outage usually yields a valid mock inject rather than a failure. (2) If an exception still escapes, llm/inject_generator.py:72-74 logs a warning and returns None. (3) Empty/whitespace response -> None (llm/inject_generator.py:76-78). (4) YAML that is not a mapping, or YAMLError/ValueError/IndexError -> None (llm/inject_generator.py:98-101, 109-113); the raw response is only logged at DEBUG (llm/inject_generator.py:100, 112). (5) engine/sim_loop.py:325-329 turns None into _quiet_turn_inject (engine/sim_loop.py:36-53): id turn_NNN_quiet, title "Overnight Assessment", channel briefing, effects [] — a diegetic quiet turn with zero metric impact.

**Why this call exists.** Once the scripted turn files run out, this is the single call that invents the event the player wakes up to — the headline, the two-to-three-paragraph brief, and the metric hit it carries — so the campaign can keep going past the authored content.

**What it must return.** Free text expected to contain a fenced YAML mapping: `id`, `title` (string), `description` (2-3 paragraph block scalar), `channel` (one of briefing/intelligence/media/military), `effects` (list of {metric, delta} where delta is an int or a "min..max" string). Template at llm/prompts.py:446-455. The model's `id` is discarded and overwritten with f"turn_{world.turn:03d}_inject" at llm/inject_generator.py:105.

**Parsed at** llm/inject_generator.py:82-107 — fence extraction (`"```yaml"` -> +7 to next "```", llm/inject_generator.py:83-86; generic "```" -> +3 to next, 87-91; otherwise whole response, 92-94), then yaml.safe_load at llm/inject_generator.py:96, mapping-type check at llm/inject_generator.py:98, id stamp at llm/inject_generator.py:105. The returned dict is consumed by engine/sim_loop.py:331-426.

#### Data in — 17 reach the prompt

- `IN ` **Turn number in the instruction header and in the YAML `id:` template**
    - source: WorldState.turn — engine/sim_loop.py:322 passes `world.turn` as the `turn_number` positional; llm/inject_generator.py:65 forwards it
    - bound: unbounded (integer)
    - evidence: llm/prompts.py:426 ("...for turn {turn_number}") and llm/prompts.py:447 ("id: turn_{turn_number:03d}_inject")
- `IN ` **Context-block turn headers: "DYNAMIC INJECT GENERATION - TURN N" and "LAST TURN (TURN N-1) - FOR CONTINUITY"**
    - source: WorldState.turn (models/world.py:22), read directly by the context builder
    - bound: unbounded (integer)
    - evidence: llm/context_builder.py:407 and llm/context_builder.py:435
- `IN ` **Escalation Risk, as "Escalation Risk: N/100"**
    - source: WorldState.metrics.escalation_risk (models/world.py:7, 35)
    - bound: unbounded (0-100 int)
    - evidence: llm/context_builder.py:409
- `IN ` **Domestic Stability, as "Domestic Stability: N/100"**
    - source: WorldState.metrics.domestic_stability (models/world.py:8)
    - bound: unbounded (0-100 int)
    - evidence: llm/context_builder.py:410
- `IN ` **Alliance Cohesion, as "Alliance Cohesion: N/100"**
    - source: WorldState.metrics.alliance_cohesion (models/world.py:9)
    - bound: unbounded (0-100 int)
    - evidence: llm/context_builder.py:411
- `IN ` **SECRET NARRATIVE CONTEXT — global truth only: description, protagonist, antagonist, patsy, plus the four standing "act on your secret motive / never reveal" instructions**
    - source: WorldState.narrative: NarrativeConfig (models/world.py:26), set at campaign start from the scenario's narrative draw (cli/main.py:755, cli/main_dashboard.py:779, engine/game_manager.py:105)
    - bound: unbounded (free text from narratives.yaml)
    - evidence: llm/context_builder.py:415-417 calls `world_state.narrative.to_llm_context()`; body at models/narrative.py:31-43 and 69-79
- `IN ` **STORY SO FAR (HIGH-LEVEL SUMMARY) — a mechanically derived digest: number of distinct turns played, latest turn number, transcript line count, and the last 3 event-ish lines**
    - source: the full game transcript (cli/main.py:851 passes `transcript`), digested by llm/context_builder.py:562 generate_summary — which is NOT an LLM call (llm/context_builder.py:570 discards its summary_prompt argument)
    - bound: WINDOWED+TRUNCATED: only the last 3 collected event lines (`event_lines[-3:]`, llm/context_builder.py:595) and each is cut to 100 chars (`event[:100]`, llm/context_builder.py:596). Used only when `len(transcript) > 10` (llm/prompts.py:388); otherwise the literal string "The campaign has just begun; the full history appears below." (llm/prompts.py:395).
    - evidence: built at llm/prompts.py:393, injected at llm/context_builder.py:424; digest construction at llm/context_builder.py:587-600
- `IN ` **EVENTS ALREADY PLAYED block — one line per past inject: `Turn N | <title padded> | OPEN/ADVANCED/RESOLVED[ - <note>]`**
    - source: NarrativeState.event_ledger: List[PlayedEvent] (models/narrative_state.py:88). Written at briefing time by record_played_event (models/narrative_state.py:301-312) from engine/sim_loop.py:336-337 with (world.turn, inject['title']); disposition+note set later by close_event (models/narrative_state.py:314-328) from engine/narrative_adjudication.py:157-158. Read whole at engine/sim_loop.py:320 `narrative_state.recent_played_events()` (no n => `list(self.event_ledger)`, models/narrative_state.py:352-353), passed engine/sim_loop.py:324 -> llm/inject_generator.py:66 -> llm/prompts.py:405.
    - bound: Entry COUNT is UNBOUNDED — recent_played_events() deliberately returns every entry (models/narrative_state.py:330-356). Each TITLE is TRUNCATED at _LEDGER_TITLE_MAX = 60 (llm/context_builder.py:64) to text[:57]+"..." (llm/context_builder.py:87-88). Each NOTE was truncated upstream to 90 chars on a word boundary by _truncate_decision(action, 90) (engine/narrative_adjudication.py:158; engine/endings.py:190-196).
    - evidence: llm/context_builder.py:428-431 (transcript branch) renders it between the story digest and the LAST TURN window; llm/prompts.py:411-413 appends it on the no-transcript branch. Renderer at llm/context_builder.py:74-107.
- `IN ` **LAST TURN transcript window — the verbatim lines of the previous turn (its inject text, advisor Q&A, the decision, the adjudication and effect boxes)**
    - source: the full game transcript list; engine/sim_loop.py:323 passes `full_transcript`, which the CLI extends with each turn's briefing_lines at cli/main.py:953 (so at generation time the newest TURN header is the PREVIOUS turn's)
    - bound: WINDOWED twice. Lines: sliced backwards from the last `^TURN \d+$` header including its ruler (llm/context_builder.py:139-146), capped at MAX_INJECT_CONTINUITY_LINES = 400 (llm/context_builder.py:61, passed llm/prompts.py:401); an over-long turn keeps head 2/3 and tail 1/3 of budget-1 around "[... mid-turn discussion elided for length ...]" (llm/context_builder.py:156-163). Chars: the real bound is max_chars = MAX_ADVISOR_TRANSCRIPT_CHARS = 320_000 (llm/context_builder.py:27, default arg llm/context_builder.py:114), trimmed from the HEAD with a "[... earlier lines elided for length ...]" marker (llm/context_builder.py:166-189). No turn header at all => plain `transcript[-400:]` tail (llm/context_builder.py:145).
    - evidence: sliced at llm/prompts.py:400-401, injected at llm/context_builder.py:437 (`context_parts.extend(last_turn_transcript)`)
- `IN ` **UK objectives — the whole `objectives.uk` mapping (primary + secondary list), interpolated as a Python dict repr**
    - source: initial_conditions['objectives']['uk'], loaded from data/scenarios/<scenario_id>/initial_conditions.yaml:325 by engine/initial_conditions.py:26-40, called at engine/sim_loop.py:317
    - bound: unbounded — whole sub-tree stringified
    - evidence: read at llm/prompts.py:362, interpolated at llm/prompts.py:431 ("{objectives.get('uk', {})}")
- `IN ` **Russian objectives (hidden from player) — the whole `red_objectives` mapping: strategic, pretext, preparation, assessment**
    - source: initial_conditions['red_objectives'] (data/scenarios/war_game_2025/initial_conditions.yaml:298)
    - bound: unbounded — whole sub-tree stringified
    - evidence: read at llm/prompts.py:363, interpolated at llm/prompts.py:434
- `IN ` **Russian strategy pattern — escalation_patterns.russian_strategy (primary/secondary objective + 6 tactics), as a dict repr**
    - source: scenario_library YAML loaded by llm/inject_generator.py:21-33 _load_scenario_library, passed at llm/inject_generator.py:65
    - bound: unbounded. NOTE the path is HARDCODED to data/scenarios/war_game_2025/scenario_library.yaml (llm/inject_generator.py:27) regardless of the scenario_id used for initial_conditions; missing file => {} and the whole library_context block is omitted (llm/prompts.py:367).
    - evidence: llm/prompts.py:376
- `IN ` **UK constraints pattern — escalation_patterns.uk_constraints (military + political bullet lists), as a dict repr**
    - source: same scenario_library YAML
    - bound: unbounded
    - evidence: llm/prompts.py:377
- `IN ` **Potential scenario menu — naval_scenarios + infrastructure_scenarios + diplomatic_scenarios concatenated and printed as a Python list-of-dicts repr (ids, descriptions, locations, effects, variations, composition numbers, allied positions...)**
    - source: scenario_library['naval_scenarios'|'infrastructure_scenarios'|'diplomatic_scenarios'] (data/scenarios/war_game_2025/scenario_library.yaml:47, 81, 199)
    - bound: No length cap. FILTERED by _drop_used_scenarios (llm/prompts.py:305-331): any entry sharing a >3-char non-stopword with a ledger title is dropped. Because the YAML entries are dicts, `words(s)` stringifies the ENTIRE dict (llm/prompts.py:320 `str(text).lower()`), so a ledger title word matching any nested location/effect/variation kills the whole entry. If the filter empties the pool it is restored intact (`remaining or scenarios`, llm/prompts.py:331).
    - evidence: assembled llm/prompts.py:368-370, filtered llm/prompts.py:373, interpolated llm/prompts.py:378
- `IN ` **Rule 7 "CONTINUITY IS MANDATORY" (points at the LAST TURN block)**
    - source: presence of a non-empty transcript
    - bound: conditional — omitted entirely when transcript is falsy
    - evidence: llm/prompts.py:419-421, spliced into the numbered list at llm/prompts.py:443 via {continuity_rule}
- `IN ` **Rule 8 "DO NOT RESTAGE RESOLVED EVENTS" (points at the EVENTS ALREADY PLAYED block)**
    - source: truthiness of the event_ledger argument
    - bound: conditional — an empty list [] is falsy, so a fresh campaign gets no rule 8 and no ledger block
    - evidence: llm/prompts.py:422-424
- `IN ` **Static Games Master framing + the six fixed generation rules + the YAML output template (id/title/description/channel/effects)**
    - source: literal text in the builder
    - bound: fixed
    - evidence: llm/prompts.py:426, 437-443, 445-457

#### Available but not sent — 10

- `OUT` **Per-country FactionStance detail — secret_motive, public_posture, economic_leverage, intel_sharing_level for each nation**
    - source: NarrativeConfig.stances (models/narrative.py:19)
    - evidence: llm/context_builder.py:416 calls `to_llm_context()` with NO target_country_code; models/narrative.py:46 gates the whole stance block on `if target_country_code:`. Only the diplomacy path passes one (llm/context_builder.py:502). So the inject generator never sees any country's secret motive.
- `OUT` **The shared briefing dossier prefix (campaign framing header, FULL windowed game history, Turn/Phase, all five metrics, build_world_state_summary narrative gloss) that every advisor/decision/pushback/omissions prompt opens with**
    - source: llm/context_builder.py:285 build_shared_context_prefix
    - evidence: get_stochastic_inject_context (llm/context_builder.py:391-439) never calls build_shared_context_prefix or render_transcript_block; llm/prompts.py:404-405 is the only path in. The inject prompt therefore shares NO cacheable prefix with the rest of the turn's calls and never sees the full campaign transcript — only the last-turn slice plus the digest.
- `OUT` **Casualty counts (casualties_mil / casualties_civ)**
    - source: WorldState.metrics.casualties_mil / casualties_civ (models/world.py:10-11)
    - evidence: llm/context_builder.py:409-411 lists only the three 0-100 gauges. Casualties appear only via build_world_state_summary (llm/prompts.py:64), which this builder uses ONLY on the no-transcript branch (llm/prompts.py:410) — a branch the CLI and GameManager never take because they always pass full_transcript (cli/main.py:851, engine/game_manager.py:149). Only the legacy engine/sim_loop.py:676 run_full_turn path omits the transcript.
- `OUT` **world.flags (KEY INTELLIGENCE FLAGS)**
    - source: WorldState.flags (models/world.py:36), maintained by engine.flags.update_world_flags
    - evidence: rendered only by build_world_state_summary (llm/prompts.py:67-71), used only on the no-transcript branch at llm/prompts.py:410; get_stochastic_inject_context never touches world_state.flags
- `OUT` **world.recent_injects (titles of the last 5 applied injects)**
    - source: WorldState.recent_injects (models/world.py:52), appended at engine/sim_loop.py:391-392
    - evidence: no reference to recent_injects anywhere in llm/prompts.py or llm/context_builder.py; it feeds the critical-omissions prompt instead
- `OUT` **world.phase, world.difficulty, world.posture, world.spatial_state, world.diplomatic_relationships, world.actor_system, world.discussion_transcript**
    - source: models/world.py:23, 32, 37, 40, 58, 64, 46
    - evidence: none of these identifiers appear in llm/prompts.py:334-459 or llm/context_builder.py:391-439. (world.difficulty does silently rescale the inject's own effects afterwards — engine/sim_loop.py:196 — but the generator is never told which difficulty it is writing for.)
- `OUT` **NarrativeState's other fields: situation_summary, recent_events, active_crises, characters/CharacterAttitude trust, hidden_metrics — i.e. everything NarrativeState.to_llm_context() would render**
    - source: models/narrative_state.py:80-98, to_llm_context at models/narrative_state.py:240-266
    - evidence: engine/sim_loop.py:320-324 extracts ONLY `narrative_state.recent_played_events()` and passes it as event_ledger; the narrative_state object itself is never handed to generate_inject. NarrativeState.to_llm_context is a different method from NarrativeConfig.to_llm_context (models/narrative.py:21) — only the latter is called, at llm/context_builder.py:416.
- `OUT` **initial_conditions sections other than objectives.uk and red_objectives — characters, constraints, uk_forces, red_forces, stockpiles, intelligence, critical_infrastructure, locations, diplomatic_contacts, timeline, environment, initial_flags**
    - source: data/scenarios/war_game_2025/initial_conditions.yaml:27,35,48,69,84,122,268,305,358,383,441,533
    - evidence: llm/prompts.py:362-363 reads only 'objectives' and 'red_objectives' from the dict; nothing else is indexed in the builder
- `OUT` **scenario_library sections other than the three merged lists and the two escalation patterns — cyber_scenarios, military_target_scenarios, civilian_target_scenarios, covert_operation_scenarios, uk_response_scenarios, public_reaction_scenarios, crisis_timeline, themes, llm_guidance, metadata**
    - source: data/scenarios/war_game_2025/scenario_library.yaml:110,120,158,180,240,287,314,331,365,8
    - evidence: llm/prompts.py:368-370 concatenates only naval/infrastructure/diplomatic; llm/prompts.py:376-377 reads only escalation_patterns.russian_strategy and .uk_constraints. Notably `llm_guidance`, the section written to steer this exact call, is never sent.
- `OUT` **rng (Random)**
    - source: engine/sim_loop.py:322 passes the campaign rng
    - evidence: llm/inject_generator.py:71 passes it to generate_text as the driver seed only; llm/gemini_driver.py:122 draws a seed from it (and then does not use it — Gemini takes no seed). Never interpolated into the prompt text.

#### What the output changes

- world.metrics.<metric> is mutated in place by engine/sim_loop.py:385 -> apply_inject_effects (engine/sim_loop.py:172-259): a "a..b" delta becomes the integer midpoint (engine/sim_loop.py:215-222); non-casualty deltas are scaled by the difficulty multiplier standard 0.5 / challenging 0.7 / brutal 1.0 with a magnitude floor of 1 (engine/sim_loop.py:191-196, 228-232); casualties are added uncapped and floored at 0 (engine/sim_loop.py:240-241); everything else is clamped (engine/sim_loop.py:243). Unknown metric names are skipped with a "Skipped: unknown metric" transcript line (engine/sim_loop.py:253).
- world.flags is refreshed by update_world_flags after the effects land (engine/sim_loop.py:256-257), so a generated escalation delta can flip intelligence flags.
- narrative_state.hidden_metrics and previous_metrics are re-synced from the post-inject world.metrics (cli/main.py:869-875, engine/game_manager.py:163-169) — this is what gives immersive-mode vibe arrows their trend baseline.
- narrative_state.event_ledger gains a new PlayedEvent(turn=world.turn, title=inject['title'], disposition='open') at engine/sim_loop.py:336-337 -> models/narrative_state.py:301-312 — i.e. this call's own title becomes an input to every LATER inject-generation prompt, and to the _drop_used_scenarios filter.
- The title is handed to a second LLM call, the narrator bridge, at engine/sim_loop.py:349 generate_narrator_bridge(world, full_transcript, inject.get('title'), rng).
- world.recent_injects gets the title appended and is trimmed to the last 5 (engine/sim_loop.py:391-392), which feeds the critical-omissions prompt.
- Player-facing screen text: title (upper-cased panel header), description paragraphs and channel-derived border colour via display_inject (engine/sim_loop.py:79-123). Channel mismatch: the prompt offers briefing/intelligence/media/military (llm/prompts.py:452) but the colour map only knows briefing/intel/breaking (engine/sim_loop.py:85-89), so three of the four legal values silently fall through to the default accent colour (engine/sim_loop.py:90).
- The description lines and the effect boxes are appended to the turn transcript (engine/sim_loop.py:381, 386, and the box construction at engine/sim_loop.py:248-251), which the caller merges into the campaign transcript (cli/main.py:953) — so this output becomes the LAST TURN continuity window for the next turn's inject and the history block for every advisor call.
- If the parsed dict happens to carry a `diplomatic_encounter` mapping with required+country, a mandatory diplomatic encounter runs immediately (engine/sim_loop.py:395-418) — but the prompt template never asks for that key, so a generated inject in practice never triggers it. Likewise `image` (engine/sim_loop.py:152-167) is never requested.
- The dict is returned to the caller as the turn's inject (engine/sim_loop.py:433) and to GameManager.get_turn_briefing (engine/game_manager.py:171).

#### Observed gaps

- The prompt tells the model to write for "the current world state" (rule 4, llm/prompts.py:441) but never shows casualties or intelligence flags in real play: llm/context_builder.py:409-411 emits only the three 0-100 gauges, and the build_world_state_summary block that carries casualties (llm/prompts.py:64) and flags (llm/prompts.py:67-71) is on the branch taken only when transcript is falsy (llm/prompts.py:410) — which the CLI and GameManager never take (cli/main.py:851, engine/game_manager.py:149).
- The inject prompt does not use build_shared_context_prefix (llm/context_builder.py:285) at all — get_stochastic_inject_context (llm/context_builder.py:391-439) builds its own header from scratch. So the generator never sees the full campaign history (only the last-turn slice plus a mechanical 3-line digest), and this call shares no cacheable prefix with the advisor/decision/pushback/omissions calls that all open with the shared dossier.
- Rule 2 says the inject must align with "the narrative truth (if provided above)", but on the no-transcript branch (llm/prompts.py:410) the story context is build_world_state_summary, which contains no narrative block at all — the secret truth is silently absent from the very first generated inject on that path.
- Per-country secret motives are never sent: llm/context_builder.py:416 calls to_llm_context() with no country code, so the entire FactionStance section (models/narrative.py:46-67) is skipped even though rule 6 asks the model to "subtly advance the hidden narrative".
- The scenario library path is hardcoded to data/scenarios/war_game_2025/scenario_library.yaml (llm/inject_generator.py:27) while initial_conditions come from the live scenario_id (engine/sim_loop.py:317) — any other scenario gets war_game_2025's scenario menu, or none if the file is absent.
- scenario_library's `llm_guidance` section (data/scenarios/war_game_2025/scenario_library.yaml:365) — the part of the library explicitly written to steer generation — is never read; llm/prompts.py:368-377 pulls only five keys.
- _drop_used_scenarios matches ledger-title words against str(dict) of a whole scenario entry (llm/prompts.py:320, 330), not just its id or description, because the YAML entries are mappings (data/scenarios/war_game_2025/scenario_library.yaml:49-79). One ledger title containing e.g. "orkney" or "cable" removes an entire scenario family from the menu.
- The ledger block and rule 8 are gated on truthiness (llm/prompts.py:422, llm/context_builder.py:428-429), so an empty ledger is indistinguishable from no ledger — correct here, but it also means a caller that omits the transcript while passing a ledger gets the block via the fallback path at llm/prompts.py:411-413 with no LAST TURN section, which is exactly the mismatch the comment at llm/prompts.py:407-409 warns about.
- engine/sim_loop.py:676 (run_full_turn, the legacy/test path) calls run_turn_briefing with neither full_transcript nor narrative_state, so on that path the generator gets no transcript, no ledger, no rule 7 and no rule 8.

### Narrator bridge between turns

`narrator_bridge`

- **Prompt built at** — llm/prompts.py:558 build_narrator_intro_prompt; the f-string is llm/prompts.py:589-615
- **Dispatched at** — engine/narrator.py:36-42 generate_text(...) -> llm/router.py:264 driver.generate_text(prompt, rng, **kwargs). Entered from engine/sim_loop.py:346-351.
- **LLM context** — none - engine/narrator.py:36-42 passes no `context=` argument, so llm/router.py:231-234 falls through to model_name = None
- **Model tier** — None selected. Because context is omitted, llm.model_config is bypassed entirely and the driver default is used: llm/gemini_driver.py:66-71 -> config.GEMINI_MODEL, defaulting to "gemini-2.5-flash". The /llm model-settings menu therefore cannot influence this call.
- **Calls per turn** — At most 1 per turn, and 0 on turn 1. Gated three times: engine/sim_loop.py:331 (an inject exists), engine/sim_loop.py:344 (`world.turn > 1 and full_transcript`), engine/narrator.py:29 (`len(transcript) >= 5`). engine/sim_loop.py:676 (run_full_turn) passes no full_transcript, so that entry point never fires it.
- **Concurrency** — Alone. Single blocking call at engine/narrator.py:36, before the inject is displayed (engine/sim_loop.py:380) and followed by a hard 2.5s sleep (engine/sim_loop.py:374).
- **On failure** — Four layers. (1) llm/router.py:269-279 retries once after 2s then substitutes a MockDeterministicDriver response. (2) engine/narrator.py:44-46 catches anything else and returns the literal fallback "Time passes. The situation develops..." - which is then written into the transcript as a real [Narrator] line and will be picked up as a story-digest "event" by llm/context_builder.py:583. (3) engine/sim_loop.py:375-377 wraps the whole block in `except Exception: pass`, so a failure there yields no bridge at all and no log line. (4) The Rich import for display is isolated in its own try (engine/sim_loop.py:363-367) so a headless caller still gets the transcript line.

**Why this call exists.** Prints 2-3 sentences of atmosphere at the top of a turn so the jump from last turn's decision to the new inject reads as elapsed time and rising tension rather than a hard cut.

**What it must return.** Free prose, 2-3 sentences, no structure. Only transformation is .strip() at engine/narrator.py:43.

**Parsed at** engine/sim_loop.py:353 (truthiness check) then engine/sim_loop.py:355, which wraps it as f"\n[Narrator] {bridge_text}\n" - a single transcript element containing embedded newlines. No parsing beyond that.

#### Data in — 11 reach the prompt

- `IN ` **Static narrator framing ("You are the Narrator of a high-stakes political thriller wargame (like 'The West Wing' meets 'Hunt for Red October')")**
    - source: Hard-coded literal
    - bound: unbounded (fixed)
    - evidence: llm/prompts.py:589
- `IN ` **Turn number and phase, as "=== CURRENT SITUATION (Turn N, BRIEFING phase) ===" (phase is "briefing" here, set at engine/sim_loop.py:301)**
    - source: world.turn / world.phase (models/world.py:22-23)
    - bound: unbounded
    - evidence: llm/prompts.py:584 calls build_world_state_summary, which emits it at llm/prompts.py:58; interpolated into the prompt at llm/prompts.py:592
- `IN ` **Escalation risk as a prose band only (low/moderate/high/critical)**
    - source: world.metrics.escalation_risk (models/world.py:7)
    - bound: unbounded
    - evidence: banded at llm/prompts.py:34-39, emitted at llm/prompts.py:60
- `IN ` **Domestic stability as a prose band only (stable/uncertain/fragile/in crisis)**
    - source: world.metrics.domestic_stability (models/world.py:8)
    - bound: unbounded
    - evidence: banded at llm/prompts.py:41-46, emitted at llm/prompts.py:61
- `IN ` **Alliance cohesion as a prose band only (strong and unified/uncertain/fragile/fractured)**
    - source: world.metrics.alliance_cohesion (models/world.py:9)
    - bound: unbounded
    - evidence: banded at llm/prompts.py:48-53, emitted at llm/prompts.py:62
- `IN ` **Casualty counts (military and civilian, raw integers)**
    - source: world.metrics.casualties_mil / casualties_civ (models/world.py:10-11)
    - bound: unbounded
    - evidence: llm/prompts.py:64, inside the summary interpolated at llm/prompts.py:592
- `IN ` **Active intelligence flags, title-cased**
    - source: world.flags (models/world.py:36)
    - bound: unbounded
    - evidence: llm/prompts.py:67-71
- `IN ` **The anti-meta instruction block ("You are a real advisor in COBRA...", "Do NOT reference 'metrics'...") - carried in even though the speaker here is a narrator, not an advisor**
    - source: Hard-coded literal inside build_world_state_summary
    - bound: unbounded (fixed)
    - evidence: llm/prompts.py:74-77, pulled in wholesale by llm/prompts.py:584
- `IN ` **Recent transcript tail, under "Recent Events (Transcript):"**
    - source: The FULL campaign transcript. engine/narrator.py:32 passes `transcript` (the whole game history from cli/main.py:786) into the parameter named `last_turn_transcript` - despite the name and the docstring at llm/prompts.py:571 claiming "Transcript lines from the previous turn", no slicing to a turn boundary happens anywhere on this path.
    - bound: WINDOWED to the last 20 list elements. The `20` is a bare literal at llm/prompts.py:587 - not a named constant, and unrelated to MAX_ADVISOR_TRANSCRIPT_CHARS (320_000) or MAX_INJECT_CONTINUITY_LINES (400). There is NO character bound, so 20 unwrapped paragraph lines can be arbitrarily large.
    - evidence: engine/sim_loop.py:346-350 passes full_transcript -> engine/narrator.py:32 -> llm/prompts.py:587 `"\n".join(last_turn_transcript[-20:])`, interpolated at llm/prompts.py:595
- `IN ` **Title of the inject about to be shown**
    - source: inject.get("title", "Unknown Event") at engine/sim_loop.py:349, where `inject` comes from load_inject_for_turn (sim_loop.py:311) or generate_inject (sim_loop.py:322)
    - bound: unbounded
    - evidence: engine/narrator.py:32 -> llm/prompts.py:598 `"{next_inject_title}"`
- `IN ` **Task instructions (set the scene, connect the previous choice, build tension, DO NOT reveal the inject content) plus two hard-coded few-shot example bridges**
    - source: Hard-coded literal
    - bound: unbounded (fixed)
    - evidence: llm/prompts.py:600-614

#### Available but not sent — 4

- `OUT` **Raw metric values 0-100 for escalation / stability / cohesion**
    - source: world.metrics.*
    - evidence: The narrator prompt is built only from build_world_state_summary (llm/prompts.py:584), which never prints the numeric metric values - only the bands at llm/prompts.py:60-62. It does NOT call llm/context_builder.py:build_shared_context_prefix, which is the only place the raw numbers are emitted (context_builder.py:337-339).
- `OUT` **System instruction "You are a master storyteller for a political thriller. Be concise, atmospheric, and serious."**
    - source: engine/narrator.py:39
    - evidence: CONDITIONAL, and false on the default and Gemini providers. llm/router.py:255-263 inspects the driver signature and only forwards system_instruction if the driver declares it. GeminiDriver.generate_text is `(self, prompt, rng)` (llm/gemini_driver.py:106), MockDeterministicDriver.generate_text is `(self, prompt, rng)` (llm/mock_driver.py:1140), OfflineDriver likewise (llm/offline_driver.py:15) - so the system instruction is silently dropped for all three. Only OpenAICompatDriver declares it (llm/openai_compat_driver.py:150-157).
- `OUT` **temperature = 0.7**
    - source: engine/narrator.py:40
    - evidence: Same signature filter at llm/router.py:259-260. Dropped for Gemini (llm/gemini_driver.py:106); Gemini instead uses the driver-wide config temperature from llm/gemini_driver.py:90,98 (default 0.7, coincidentally the same). Honoured only on openai_compat (llm/openai_compat_driver.py:155).
- `OUT` **max_tokens = 150 (the intended length cap on the bridge)**
    - source: engine/narrator.py:41
    - evidence: Dropped by the same filter at llm/router.py:261-262 because GeminiDriver.generate_text (llm/gemini_driver.py:106) does not accept max_tokens; Gemini uses GEMINI_MAX_TOKENS, default 2048 (llm/gemini_driver.py:91,101). Honoured only on openai_compat (llm/openai_compat_driver.py:156).

#### What the output changes

- Appends one `[Narrator] ...` element to the turn's transcript (engine/sim_loop.py:355), which the caller merges into the campaign transcript (cli/main.py:953, engine/game_manager.py:156) - so it becomes permanent GAME HISTORY for every later prompt via llm/context_builder.py:326.
- Feeds the inject generator's STORY DIGEST: context_builder.generate_summary treats any line starting with "[Narrator]" as a notable event (llm/context_builder.py:583 - the leading "\n" is removed by the .strip() at context_builder.py:576), keeps the last three (context_builder.py:595) truncated to 100 chars each (context_builder.py:596), and that digest is interpolated into the inject-generation prompt (llm/prompts.py:393 -> 405 -> get_stochastic_inject_context, context_builder.py:424).
- Printed to screen in italic secondary colour and followed by a hard 2.5-second sleep (engine/sim_loop.py:369-374). Suppressed when suppress_display is set (engine/sim_loop.py:362), which is how GameManager runs it (engine/game_manager.py:151).
- Mutates no metric, no flag, and no narrative state. Purely narrative text.

#### Observed gaps

- The secret narrative truth NEVER reaches the narrator. This prompt does not call llm/context_builder.py:build_shared_context_prefix; it is assembled only from build_world_state_summary (llm/prompts.py:584), which contains no reference to world.narrative. So the one component whose explicit job is foreshadowing (llm/prompts.py:604 "Build tension before the next inject is revealed") is blind to the hidden protagonist/patsy that the inject generator does see (llm/context_builder.py:415-418).
- The player's last decision is not passed. llm/prompts.py:576-581 is dead code: `last_decision = "Unknown decision"` is assigned, the loop over the reversed transcript has a body of `pass`, and `last_decision` is never interpolated into the f-string at llm/prompts.py:589-615. The instruction at llm/prompts.py:603 ("Connect the player's previous choice") relies entirely on the decision happening to fall inside the 20-line tail.
- No prompt-cache sharing with the rest of the turn. Every other transcript-carrying prompt opens with the identical dossier from llm/context_builder.py:285-355 (see the rationale at context_builder.py:288-307); the narrator opens with its own framing line (llm/prompts.py:589), so it shares a zero-length prefix with the advisor, decision, pushback and omissions calls - and it is also the first call of the turn, so it warms nothing.
- History beyond 20 lines is invisible here even though the advisor calls get 320,000 characters (llm/context_builder.py:27). On a real transcript, 20 lines is roughly the tail of one adjudication.
- world.recent_injects (models/world.py:52) is not passed, so the narrator has no list of what recently happened other than the raw 20-line tail.
- No event ledger / narrative_state reaches the narrator: engine/sim_loop.py:346-351 passes only (world, full_transcript, title, rng), while the inject generator two lines earlier is given event_ledger (sim_loop.py:320-324).

#### Corrections against this block — 4

_A correction supersedes the row it concerns._

- **REFUTED** — narrator_bridge / notable_gaps: "...and it is also the first call of the turn, so it warms nothing."
    - correction: On any turn where the inject is dynamically generated the narrator is the SECOND LLM call of the turn, not the first. run_turn_briefing calls generate_inject at engine/sim_loop.py:322-324, and generate_inject issues a real provider call at llm/inject_generator.py:71 (`generate_text(prompt, rng, context=LLMContext.INJECT_GENERATION)`), which is 24 lines before the narrator bridge at engine/sim_loop.py:346. Stochastic generation is on from turn 7 by default (cli/main.py:790 / engine/game_manager.py:139-140 `stochastic_from` default 7), which is exactly the turn range where the narrator's own gate (`world.turn > 1`, engine/sim_loop.py:344) is satisfied. The downstream conclusion (the narrator shares no cacheable prefix with anything) still holds, because the inject prompt opens with "You are the Games Master..." at llm/prompts.py:426 — but the stated ordering fact is wrong.
    - evidence: engine/sim_loop.py:322 -> llm/inject_generator.py:71
- **CORRECTED** — narrator_bridge inputs: temperature "Gemini instead uses the driver-wide config temperature from llm/gemini_driver.py:90,98"; max_tokens "Gemini uses GEMINI_MAX_TOKENS, default 2048 (llm/gemini_driver.py:91,101)"; and the same 91,101 citation repeated in advisor_qa notable_gaps.
    - correction: All four line numbers are off. The config reads are at llm/gemini_driver.py:92 (`temperature = getattr(config, "GEMINI_TEMPERATURE", 0.7)`) and :93 (`max_tokens = getattr(config, "GEMINI_MAX_TOKENS", 2048)`); the GenerationConfig fields are at :100 (`temperature=temperature`) and :103 (`max_output_tokens=max_tokens`). Line 90 is a bare `try:`, line 91 is `import config`, line 98 is a comment, line 101 is `top_p=0.9`. The 0.7/2048 values and the substance are correct.
    - evidence: llm/gemini_driver.py:92-93, 100, 103
- **CORRECTED** — narrator_bridge / affects: story digest — "the leading '\n' is removed by the .strip() at context_builder.py:576"
    - correction: The strip is at llm/context_builder.py:575 (`line = raw_line.strip()`); line 576 is `if not line:`. The mechanism is real — the transcript element written at engine/sim_loop.py:355 is `f"\n[Narrator] {bridge_text}\n"`, and only the strip at 575 lets the `startswith("[Narrator]")` test at 583 fire.
    - evidence: llm/context_builder.py:575
- **CORRECTED** — narrator_bridge / concurrency: "Single blocking call at engine/narrator.py:36 ... and followed by a hard 2.5s sleep (engine/sim_loop.py:374)."
    - correction: The sleep is not unconditional, so "followed by a hard 2.5s sleep" is wrong as stated in the concurrency field (the map's own `affects` field states it correctly). engine/sim_loop.py:374 `time.sleep(2.5)` sits inside three nested conditions: `if not suppress_display:` (362), the `else:` of the Rich import try (364-368), and `if RICH_ENABLED:` (369). GameManager sets suppress_display=True (engine/game_manager.py:151), so the headless/dashboard/API path takes the LLM latency with no pause at all.
    - evidence: engine/sim_loop.py:362,364-369,374

## Discussion

### Advisor answers the PM's question (COBRA Q&A)

`advisor_qa`

- **Prompt built at** — llm/prompts.py:82 build_advisor_context; the actual f-string is llm/prompts.py:147-169
- **Dispatched at** — agents/conversation.py:211 (llm_generate_fn(prompt, rng, context=LLMContext.ADVISOR_QA)); llm_generate_fn is llm.router.generate_text, bound at engine/sim_loop.py:479 (imported sim_loop.py:29). Provider call is llm/router.py:264 driver.generate_text(prompt, rng, **kwargs).
- **LLM context** — LLMContext.ADVISOR_QA (llm/model_config.py:12)
- **Model tier** — PRO -> "gemini-2.5-pro" (llm/model_config.py:30 maps ADVISOR_QA->ModelTier.PRO; llm/model_config.py:44 maps PRO->gemini-2.5-pro; resolved at llm/router.py:232). On the openai_compat provider the gemini-* name is discarded and OPENAI_COMPAT_MODEL is used instead (llm/openai_compat_driver.py:125-126), so tier selection is a no-op there.
- **Calls per turn** — One LLM call per *matched advisor* per question, not one per question. agents/conversation.py:192-196 appends every advisor whose keyword list hits, so a question containing e.g. both "defence" and "legal" fires 2 calls; no match falls back to a single NSA call (conversation.py:199-200). The /advise panel in cli/main.py:1251-1271 issues 5 separate run_turn_discussion calls (one per advisor), each of which fires at least one LLM call. A question that addresses an absent official short-circuits to a canned Cabinet Secretary line and burns NO call (conversation.py:168-174).
- **Concurrency** — Alone, strictly sequential. agents/conversation.py:208-215 is a plain for-loop calling llm_generate_fn once per advisor. llm.fanout.generate_group IS imported at agents/conversation.py:18 but is used only by check_critical_omissions (conversation.py:382); the Q&A path never batches, so two matched advisors mean two serial round-trips.
- **On failure** — Three layers. (1) llm/router.py:269-279: one retry after a 2s sleep, then a MockDeterministicDriver response is substituted and a [WARNING] is printed - the game never sees the exception. (2) If the driver could not even be constructed, llm/router.py:165-168 already fell back to mock at driver-build time. (3) agents/conversation.py:216-217 catches anything remaining and returns the tuple ("System", f"Error generating response: {e}"), which is then written into the transcript as a literal line and shown to the player. Note the failure text becomes permanent prompt history.

**Why this call exists.** Lets the player interrogate a named cabinet advisor during the discussion phase and get an in-character, domain-specific answer before committing to a decision.

**What it must return.** Free-form markdown prose in character. No structured fields, no sentinel, no parsing at all - the string is used whole.

**Parsed at** agents/conversation.py:213-215 (packed into a (role, response) tuple with role taken from uk_advisors[char_id]["role"], NOT from anything the model said); the tuples are consumed at engine/sim_loop.py:484-485.

#### Data in — 21 reach the prompt

- `IN ` **Static shared-dossier framing header ("UK CRISIS WARGAME - SHARED BRIEFING DOSSIER" + "The material below is the same for every member of the COBRA cell.")**
    - source: Hard-coded literal, no state object
    - bound: unbounded (fixed ~6 lines)
    - evidence: llm/context_builder.py:310-317, reached via llm/prompts.py:113 -> context_builder.py:358-365 get_advisor_context -> build_shared_context_prefix
- `IN ` **Secret narrative truth: description / protagonist / antagonist / patsy, plus the "DO NOT REVEAL" instruction block**
    - source: world.narrative (models/world.py:26, a NarrativeConfig) rendered by NarrativeConfig.to_llm_context (models/narrative.py:21-81)
    - bound: unbounded
    - evidence: llm/context_builder.py:322-324 (`if world_state.narrative: parts.append(world_state.narrative.to_llm_context())`). Only populated in Mystery Mode: engine/game_manager.py:92-99 leaves selected_narrative=None otherwise, so in Original Story Mode this block is absent entirely.
- `IN ` **Full game transcript (every prior turn's injects, narrator bridges, advisor answers, decisions, adjudications), under the GAME HISTORY header**
    - source: the `transcript` argument threaded cli/main.py:786 (list) -> cli/main.py:1271/1621 -> engine/sim_loop.py:481 -> agents/conversation.py:210 -> llm/prompts.py:113 -> context_builder.py:326
    - bound: WINDOWED by characters, not lines. MAX_ADVISOR_TRANSCRIPT_CHARS = 320_000 (llm/context_builder.py:27), the default max_chars of render_transcript_block (context_builder.py:207) and not overridden at the call site (context_builder.py:326). Over budget, _TRANSCRIPT_HEAD_SHARE = 0.2 (context_builder.py:54) reserves 64,000 chars for the campaign opening, the rest is spent from the end, and the middle is replaced with "[... N lines of mid-campaign history elided for length ...]" cut on TURN headers (context_builder.py:230-282).
    - evidence: llm/context_builder.py:326 `parts.append(render_transcript_block(transcript))`; rendered at context_builder.py:206-282. Header text at context_builder.py:35-38.
- `IN ` **Turn number (raw)**
    - source: world.turn (models/world.py:22)
    - bound: unbounded
    - evidence: llm/context_builder.py:335 `f"Turn: {world_state.turn}"`; also a second time inside the narrative summary at llm/prompts.py:58
- `IN ` **Phase string ("discussion")**
    - source: world.phase (models/world.py:23), set at engine/sim_loop.py:460
    - bound: unbounded
    - evidence: llm/context_builder.py:336 `f"Phase: {world_state.phase}"`; again at llm/prompts.py:58
- `IN ` **Escalation Risk (raw 0-100 integer)**
    - source: world.metrics.escalation_risk (models/world.py:7)
    - bound: unbounded
    - evidence: llm/context_builder.py:337
- `IN ` **Domestic Stability (raw 0-100 integer)**
    - source: world.metrics.domestic_stability (models/world.py:8)
    - bound: unbounded
    - evidence: llm/context_builder.py:338
- `IN ` **Alliance Cohesion (raw 0-100 integer)**
    - source: world.metrics.alliance_cohesion (models/world.py:9)
    - bound: unbounded
    - evidence: llm/context_builder.py:339
- `IN ` **Military casualties (raw integer)**
    - source: world.metrics.casualties_mil (models/world.py:11)
    - bound: unbounded
    - evidence: llm/context_builder.py:340; repeated in narrative form at llm/prompts.py:64
- `IN ` **Civilian casualties (raw integer)**
    - source: world.metrics.casualties_civ (models/world.py:10)
    - bound: unbounded
    - evidence: llm/context_builder.py:341; repeated at llm/prompts.py:64
- `IN ` **Narrative re-rendering of the SAME three metrics as prose bands (low/moderate/high/critical; stable/uncertain/fragile/in crisis; strong and unified/uncertain/fragile/fractured) - so every advisor prompt states the metrics twice, once numerically and once as bands**
    - source: world.metrics.* via build_world_state_summary
    - bound: unbounded
    - evidence: llm/context_builder.py:351-352 imports and appends build_world_state_summary(world_state); banding at llm/prompts.py:34-53, emitted at llm/prompts.py:60-62
- `IN ` **Active intelligence flags, title-cased and comma-joined ("KEY INTELLIGENCE FLAGS: ...")**
    - source: world.flags (models/world.py:36), populated by engine.flags.update_world_flags
    - bound: unbounded - every truthy flag is listed, no cap
    - evidence: llm/prompts.py:67-71 (only truthy flags: `if v`), reached via llm/context_builder.py:352
- `IN ` **Standing anti-meta instruction ("Do NOT reference 'metrics', 'game mechanics', 'scores'...")**
    - source: Hard-coded literal
    - bound: unbounded (4 fixed lines)
    - evidence: llm/prompts.py:74-77 via llm/context_builder.py:352
- `IN ` **The advisor's role title (e.g. "Military Commander", "Intelligence Coordinator" - the raw YAML `role`, NOT the cabinet title shown on screen)**
    - source: initial_conditions["characters"][character_id]["role"] (data/scenarios/war_game_2025/initial_conditions.yaml:444,454,464,474,484,494)
    - bound: unbounded
    - evidence: llm/prompts.py:106 reads it; interpolated at llm/prompts.py:149 and again at 159
- `IN ` **Advisor knowledge domains list**
    - source: initial_conditions["characters"][id]["knowledge_domains"] (initial_conditions.yaml:446 etc.)
    - bound: unbounded
    - evidence: llm/prompts.py:107 -> interpolated at llm/prompts.py:151
- `IN ` **Advisor key concerns list**
    - source: initial_conditions["characters"][id]["key_concerns"] (initial_conditions.yaml:451 etc.)
    - bound: unbounded
    - evidence: llm/prompts.py:108 -> interpolated at llm/prompts.py:152
- `IN ` **All scenario constraints (capability / political / legal / time), rendered as headed bullet lists**
    - source: initial_conditions["constraints"] (initial_conditions.yaml:358-380)
    - bound: unbounded - every category and every item
    - evidence: llm/prompts.py:119-125 build context_sections; joined at llm/prompts.py:141 and interpolated at llm/prompts.py:155
- `IN ` **UK order of battle (naval/air units, locations, readiness, armament) as a raw `str(dict)` dump**
    - source: initial_conditions["uk_forces"] (initial_conditions.yaml:122-267)
    - bound: unbounded - str() of the whole dict, no truncation
    - evidence: llm/prompts.py:128-132 - CONDITIONAL: only if the advisor's knowledge_domains intersect {military_operations, force_readiness, threat_assessment}. On the shipped scenario that is chief_defence_staff ONLY (yaml:456); the NSA, Foreign Secretary, Home Secretary and Attorney General never see UK forces.
- `IN ` **Ammunition stockpiles (Sea Viper, Sky Sabre, ASRAAM, Tomahawk, Harpoon counts) as a raw `str(dict)` dump**
    - source: initial_conditions["stockpiles"] (initial_conditions.yaml:84-121)
    - bound: unbounded - str() of the whole dict
    - evidence: llm/prompts.py:135-139 - CONDITIONAL on knowledge_domains intersecting {military_operations, force_readiness}; chief_defence_staff only on the shipped scenario
- `IN ` **The player's question verbatim (including the CLI-appended brevity instruction, e.g. "[Please be concise - 3-4 sentences maximum]", which is part of the question string sent to the model)**
    - source: `question` param, from cli/main.py:1621 user_input or the canned /advise strings at cli/main.py:1252-1256 with brevity_note from cli/main.py:1227-1229
    - bound: unbounded - no length cap on player input anywhere on this path
    - evidence: llm/prompts.py:157 `The Prime Minister asks: "{question}"`
- `IN ` **Response-style instructions ("Respond in character", "Reference past decisions...", "If the question is outside your knowledge domain...") and the markdown FORMATTING INSTRUCTIONS block**
    - source: Hard-coded literal
    - bound: unbounded (fixed)
    - evidence: llm/prompts.py:159-168

#### Available but not sent — 1

- `OUT` **Per-country FactionStance secrets (secret_motive, public_posture, economic_leverage, intel_sharing_level)**
    - source: world.narrative.stances (models/narrative.py:19)
    - evidence: llm/context_builder.py:323 calls to_llm_context() with NO target_country_code, so the stance branch at models/narrative.py:46-67 never executes for this prompt. The parameter exists (models/narrative.py:21) but no caller in this group passes it.

#### What the output changes

- Appends one line `"{role}: {response}"` to the discussion transcript (engine/sim_loop.py:485), which the caller then splices into the campaign-wide `transcript` (cli/main.py:1296 / 1651, engine/game_manager.py:186) - so every answer permanently widens the GAME HISTORY block of every subsequent prompt in the game (llm/context_builder.py:326).
- Extends world.discussion_transcript (engine/sim_loop.py:488). This field is written but never read by any prompt builder - it is only cleared again at engine/sim_loop.py:694, engine/game_manager.py:341, cli/main.py:1977, cli/main_dashboard.py:1742.
- Rendered to screen: role mapped through display_role (cli/display_utils.py:36-42) to the cabinet title, body through format_advisor_response (cli/main.py:1632-1647).
- Persisted into save files via the campaign transcript (cli/main.py:1041, 1980).
- Mutates NO metric, NO flag, and NO narrative state. There is no adjudication of advisor answers.

#### Observed gaps

- world.recent_injects - the titles of the last 5 injects - never reaches this prompt. It is read only by check_critical_omissions (agents/conversation.py:351-356) and interpolated only by build_critical_omissions_prompt (llm/prompts.py:494,506). Nothing in llm/prompts.py:147-169 or llm/context_builder.py:285-355 references it, so an advisor being asked "what just happened?" sees the event only if it happens to survive the transcript window.
- world.posture, world.spatial_state, world.diplomatic_relationships and world.actor_system (models/world.py:37,40,58,64) reach NO part of this prompt - grep of llm/prompts.py and llm/context_builder.py shows no reference to any of them.
- The advisor's own `pushback_triggers` and `influence` (initial_conditions.yaml:447-450, 445) are not in this prompt; pushback_triggers is used only by build_pushback_prompt (llm/prompts.py:270).
- Whole scenario sections that exist in initial_conditions.yaml and never reach an advisor: `intelligence` (yaml:48), `timeline` (yaml:35), `red_forces` (yaml:268), `red_objectives` (yaml:298), `objectives` (yaml:325), `intelligence_summary` (yaml:342), `diplomatic_contacts` (yaml:383), `critical_infrastructure` (yaml:69). build_advisor_context reads only characters/constraints/uk_forces/stockpiles (llm/prompts.py:103,119,129,136).
- engine/sim_loop.py:681 (run_full_turn) calls run_turn_discussion WITHOUT full_transcript, so on that entry point `transcript` is None and llm/prompts.py:113 renders `get_advisor_context([], world)` - the advisor gets an EMPTY game history. cli/main.py:1271/1621, cli/main_dashboard.py:1298/1407 and engine/game_manager.py:183 all do pass it.
- No narrative_state / event ledger reaches this call: run_turn_discussion (engine/sim_loop.py:436-443) has no narrative_state parameter at all, unlike run_turn_briefing (engine/sim_loop.py:320-324).
- No max_tokens is set on this call - agents/conversation.py:211 passes only (prompt, rng, context), so llm/router.py:261-262 never adds max_tokens and the Gemini driver's config-level default of 2048 applies (llm/gemini_driver.py:91,101). The brevity instruction is prose inside the question, not an API cap.

#### Corrections against this block — 5

_A correction supersedes the row it concerns._

- **CORRECTED** — advisor_qa input "Active intelligence flags" and narrator input "Active intelligence flags": bounded_by "unbounded - every truthy flag is listed, no cap"; source described as world.flags "populated by engine.flags.update_world_flags" as if it were an independent input.
    - correction: This input is hard-bounded at FIVE entries and carries zero information beyond metrics already in the prompt. `update_world_flags` (engine/flags.py:38-40) does not augment the dict — it REPLACES it wholesale: `world.flags = compute_risk_flags(world.metrics)`. compute_risk_flags (engine/flags.py:15-35) returns exactly five keys, every one a threshold over the same metrics already printed twice: risk_escalation (escalation_risk >= 60), risk_unrest (domestic_stability <= 40), risk_alliance_fragile (alliance_cohesion <= 40), risk_civilian_harm (casualties_civ > 0), risk_military_losses (casualties_mil > 0). Every WorldState is constructed with flags={} (cli/main.py:763, cli/main_dashboard.py:787, engine/game_manager.py:113, engine/sim_loop.py:713) and update_world_flags is the only writer anywhere (called at engine/sim_loop.py:257 and 426). So the scenario's `initial_flags` block (data/scenarios/war_game_2025/initial_conditions.yaml:27-32: us_commitment, russian_families_departed, severomorsk_attack_false_flag, public_awareness) NEVER reaches any prompt, and "KEY INTELLIGENCE FLAGS" at llm/prompts.py:67-71 is a third rendering of the metrics, not intelligence.
    - evidence: engine/flags.py:15-40
- **CORRECTED** — advisor_qa / calls_per_turn: "The /advise panel in cli/main.py:1251-1271 issues 5 separate run_turn_discussion calls (one per advisor), each of which fires at least one LLM call."
    - correction: Five run_turn_discussion calls, but SIX LLM calls. The Home Secretary's canned question at cli/main.py:1255 is "Home Secretary, what are the domestic security concerns? {brevity_note}". The routing loop at agents/conversation.py:192-196 appends every advisor whose keyword list hits: home_secretary matches on "home" and "domestic" (conversation.py:187) AND national_security_advisor matches on "security" (conversation.py:185) — `_question_matches_keyword` is a \b-anchored regex (conversation.py:92) and \bsecurity\b matches "domestic security". The other four questions each match exactly one advisor ("assess" does not match "assessment" under \b, so the NSA question stays at one). Cost/latency estimates built on "5" are 20% low.
    - evidence: cli/main.py:1255 + agents/conversation.py:185,187,192-196
- **CORRECTED** — advisor_qa / model_tier: "On the openai_compat provider the gemini-* name is discarded and OPENAI_COMPAT_MODEL is used instead (llm/openai_compat_driver.py:125-126)"
    - correction: The cited lines are the wrong branch. Line 125 is the test `if model_name and not model_name.lower().startswith("gemini"):` and line 126 is `self.model_name = model_name` — i.e. the branch that KEEPS the caller's model name. The discard the claim describes happens at lines 127-128 (`else: self.model_name = _config_value("OPENAI_COMPAT_MODEL", "OPENAI_COMPAT_MODEL")`). The behavioural claim is right; the citation points at its opposite.
    - evidence: llm/openai_compat_driver.py:125-128
- **CORRECTED** — narrator_bridge inputs: temperature "Gemini instead uses the driver-wide config temperature from llm/gemini_driver.py:90,98"; max_tokens "Gemini uses GEMINI_MAX_TOKENS, default 2048 (llm/gemini_driver.py:91,101)"; and the same 91,101 citation repeated in advisor_qa notable_gaps.
    - correction: All four line numbers are off. The config reads are at llm/gemini_driver.py:92 (`temperature = getattr(config, "GEMINI_TEMPERATURE", 0.7)`) and :93 (`max_tokens = getattr(config, "GEMINI_MAX_TOKENS", 2048)`); the GenerationConfig fields are at :100 (`temperature=temperature`) and :103 (`max_output_tokens=max_tokens`). Line 90 is a bare `try:`, line 91 is `import config`, line 98 is a comment, line 101 is `top_p=0.9`. The 0.7/2048 values and the substance are correct.
    - evidence: llm/gemini_driver.py:92-93, 100, 103
- **CORRECTED** — advisor_qa input "Secret narrative truth": evidence given only as "Only populated in Mystery Mode: engine/game_manager.py:92-99 leaves selected_narrative=None otherwise".
    - correction: The cited path is not the one the CLI (the primary entry point for this call) uses. engine/game_manager.py drives cli/main_dashboard.py, api/server.py and docs/py/bridge.py. In cli/main.py the narrative is drawn by select_narrative() at cli/main.py:454-515 — returning None on menu choice 1 (:497) or on an empty narrative list (:515), and `random.choice(narratives)` on choice 2 (:504) — called at cli/main.py:637 and set into WorldState at cli/main.py:755 (`narrative=selected_narrative`). The conclusion (block absent in Original Story Mode) holds on both paths; the evidence covers only one of them.
    - evidence: cli/main.py:454-515, 637, 755

## Decision

### Decision interpretation — turning the PM's typed order into a structured operational summary

`decision_interpretation`

- **Prompt built at** — llm/prompts.py:174 build_decision_interpretation_prompt; the actual f-string is llm/prompts.py:202-239. Shared prefix built by llm/context_builder.py:285 build_shared_context_prefix (invoked at llm/prompts.py:202).
- **Dispatched at** — agents/conversation.py:244 — llm_generate_fn(prompt, rng, context=LLMContext.DECISION_INTERPRETATION). llm_generate_fn is llm.router.generate_text, injected at engine/sim_loop.py:536 (imported sim_loop.py:29, defined llm/router.py:203).
- **LLM context** — LLMContext.DECISION_INTERPRETATION
- **Model tier** — FLASH -> "gemini-2.5-flash" (llm/model_config.py:31 maps DECISION_INTERPRETATION to ModelTier.FLASH; llm/model_config.py:43 maps FLASH to the model name). Globally overridable: cli/main.py:573 use_flash_for_all under --flash-only, cli/model_settings_menu.py:78-81 per-context override, api/server.py:562-564.
- **Calls per turn** — 1 per decision submission. A second full pass fires if the player applies critical-omission recommendations (cli/main.py:1765) or amends after pushback (cli/main.py:1798 'A' -> continue -> loop re-runs cli/main.py:1701). The API path calls it twice per turn by design: once dry_run (engine/game_manager.py:193) and once committed (engine/game_manager.py:270).
- **Concurrency** — Alone. First of three strictly sequential dispatches inside run_turn_decision (engine/sim_loop.py:532 interpretation, :546 pushback, :566 omissions); pushback consumes this call's output so they cannot be overlapped.
- **On failure** — agents/conversation.py:243-245 has no try/except, so any exception propagates into run_turn_decision and up to cli/main.py:1701, which is also unguarded. In practice the router absorbs it: llm/router.py:269-279 retries once after a 2s sleep, then returns MockDeterministicDriver().generate_text(prompt, rng), which for this prompt shape echoes the player's decision back as the INTERPRETATION line (llm/mock_driver.py:1183-1195). A 60s per-request timeout is set at llm/gemini_driver.py:126. There is no schema check: an empty string or an apology would flow straight into the transcript, the pushback prompt and the adjudication prompt.

**Why this call exists.** Turn whatever the player typed at the 'Decision>' prompt into a clear order the game can show back to them and hand to the adjudicator — what they intend, which forces move, what gets consumed, how fast, and whether it is even possible.

**What it must return.** Free text. The prompt asks for five labelled lines: INTERPRETATION / FORCES INVOLVED / RESOURCES CONSUMED / TIMELINE / FEASIBILITY (llm/prompts.py:230-235). Nothing in the codebase parses or validates this — the string is returned verbatim.

**Parsed at** No parser exists. agents/conversation.py:245 returns the raw string. It is then used verbatim at: engine/sim_loop.py:541-542 (transcript lines 'Interpretation:' + text); cli/main.py:1702 display_decision_summary; engine/narrative_adjudication.py:228 where it is interpolated as `INTERPRETATION: {interpretation}` into the action-quality prompt; llm/prompts.py:284 where it is interpolated into the pushback prompt.

#### Data in — 19 reach the prompt

- `IN ` **Fixed dossier framing header — the ruler, 'UK CRISIS WARGAME - SHARED BRIEFING DOSSIER', and two lines saying the material is shared across the COBRA cell**
    - source: Hard-coded literal, no state object
    - bound: static, ~200 chars
    - evidence: llm/context_builder.py:309-317, emitted at the top of build_shared_context_prefix which is interpolated at llm/prompts.py:202
- `IN ` **Secret narrative truth — GLOBAL TRUTH description, Crisis Protagonist, Primary Target, Being Used as Pawn, plus four standing 'act on your secret motive / never reveal' instructions**
    - source: world.narrative (models/world.py:26, an Optional[NarrativeConfig]); fields models/narrative.py:14-19. Set only in Mystery Mode at cli/main.py:755 from select_narrative (cli/main.py:637, random.choice at cli/main.py:504); None in Original Story Mode (cli/main.py:496)
    - bound: not truncated; absent entirely when world.narrative is None (guarded at llm/context_builder.py:322)
    - evidence: llm/context_builder.py:322-324 calls world_state.narrative.to_llm_context(); the block is built at models/narrative.py:31-44 and 69-79
- `IN ` **Game history header text ('GAME HISTORY - everything that has happened, in order...')**
    - source: Hard-coded constant _HISTORY_HEADER
    - bound: static; deliberately carries no line/char counts so the prefix does not move as the transcript grows (llm/context_builder.py:30-34)
    - evidence: llm/context_builder.py:35-38, emitted at llm/context_builder.py:228 / :277
- `IN ` **Full campaign transcript — every briefing/inject line, narrator bridge, discussion Q&A, prior turns' decisions, interpretations, pushback, critical advisories and adjudication results accumulated since turn 1**
    - source: The caller's `transcript` list: cli/main.py:1701 passes it positionally as full_transcript -> engine/sim_loop.py:499 -> :538 -> agents/conversation.py:228/243 -> llm/prompts.py:202. Loaded from the save file on resume (engine/persistence.py:124).
    - bound: WINDOWED by characters, not lines. MAX_ADVISOR_TRANSCRIPT_CHARS = 320_000 (llm/context_builder.py:27), applied as the default max_chars at llm/context_builder.py:207 — no caller ever overrides it. Under budget: emitted whole (llm/context_builder.py:227-228). Over budget: _TRANSCRIPT_HEAD_SHARE = 0.2 (llm/context_builder.py:54) reserves 64,000 chars for the campaign opening, grown a whole turn at a time on TURN N boundaries (llm/context_builder.py:230-247); the remaining ~256,000 chars are taken from the tail, also on turn boundaries (llm/context_builder.py:250-260); the middle is replaced by a single '[... N lines of mid-campaign history elided for length ...]' marker (llm/context_builder.py:280). Fallback plain character tail when no turn boundary fits (llm/context_builder.py:265-272).
    - evidence: llm/context_builder.py:326 parts.append(render_transcript_block(transcript)); renderer at llm/context_builder.py:206-282
- `IN ` **Current turn number**
    - source: world.turn (models/world.py:22)
    - bound: scalar
    - evidence: llm/context_builder.py:335 f"Turn: {world_state.turn}"; also restated at llm/prompts.py:58
- `IN ` **Current phase string**
    - source: world.phase (models/world.py:23)
    - bound: scalar
    - evidence: llm/context_builder.py:336. Value is 'decision' on the CLI path because engine/sim_loop.py:521 sets it before the call; it stays 'discussion' on the API preview path because game_manager.py:198 passes dry_run=True and sim_loop.py:520 skips the assignment.
- `IN ` **Escalation Risk, raw 0-100**
    - source: world.metrics.escalation_risk (models/world.py:7, models/world.py:35)
    - bound: scalar
    - evidence: llm/context_builder.py:337
- `IN ` **Domestic Stability, raw 0-100**
    - source: world.metrics.domestic_stability
    - bound: scalar
    - evidence: llm/context_builder.py:338
- `IN ` **Alliance Cohesion, raw 0-100**
    - source: world.metrics.alliance_cohesion
    - bound: scalar
    - evidence: llm/context_builder.py:339
- `IN ` **Military casualties count**
    - source: world.metrics.casualties_mil
    - bound: scalar
    - evidence: llm/context_builder.py:340, and again as prose at llm/prompts.py:64
- `IN ` **Civilian casualties count**
    - source: world.metrics.casualties_civ
    - bound: scalar
    - evidence: llm/context_builder.py:341, and again as prose at llm/prompts.py:64
- `IN ` **Narrative restatement of the SAME three metrics as band words — THREAT ASSESSMENT low/moderate/high/critical, DOMESTIC SITUATION stable/uncertain/fragile/in crisis, ALLIANCE STATUS strong and unified/uncertain/fragile/fractured. The numbers therefore appear twice, once raw and once banded.**
    - source: world.metrics, re-read by build_world_state_summary
    - bound: static thresholds at llm/prompts.py:35-53
    - evidence: llm/prompts.py:34-62, appended at llm/context_builder.py:351-352
- `IN ` **KEY INTELLIGENCE FLAGS line — title-cased names of the truthy entries of world.flags**
    - source: world.flags (models/world.py:36), recomputed from metrics alone by engine/flags.py:15-35 via update_world_flags (engine/flags.py:38-40, called at engine/sim_loop.py:256 and :639). Possible keys: risk_escalation, risk_unrest, risk_alliance_fragile, risk_civilian_harm, risk_military_losses.
    - bound: at most 5 flags; note these are pure metric restatements, NOT the scenario's initial_flags (data/scenarios/war_game_2025/initial_conditions.yaml:29-34), which never reach any prompt
    - evidence: llm/prompts.py:67-71 — only truthy flags are listed, and the whole block is omitted when none are set
- `IN ` **Standing anti-meta instruction ('You are a real advisor in COBRA... Do NOT reference metrics, game mechanics, scores or values')**
    - source: Hard-coded
    - bound: static
    - evidence: llm/prompts.py:74-77
- `IN ` **UK order of battle — full naval and air force list with ids, types, locations, readiness statuses, armaments and notes, rendered as a raw Python dict repr**
    - source: initial_conditions['uk_forces'], loaded from data/scenarios/<id>/initial_conditions.yaml:132+ by engine/initial_conditions.py:13-45, called at engine/sim_loop.py:525
    - bound: NOT truncated — the whole section goes in as `{uk_forces}`. Measured at ~4,700 chars for the shipped war_game_2025 scenario.
    - evidence: read at llm/prompts.py:194, interpolated at llm/prompts.py:207 under 'Available forces:'
- `IN ` **Ammunition stockpiles — every munition category with counts and notes (Sea Viper 96, Tomahawk 30, Storm Shadow 50, etc.), raw dict repr**
    - source: initial_conditions['stockpiles'] (initial_conditions.yaml:96-131)
    - bound: NOT truncated (~900 chars in the shipped scenario)
    - evidence: read at llm/prompts.py:195, interpolated at llm/prompts.py:210
- `IN ` **Constraints — capability / political / legal / time lists, raw dict repr**
    - source: initial_conditions['constraints']
    - bound: NOT truncated (~1,100 chars)
    - evidence: read at llm/prompts.py:193, interpolated at llm/prompts.py:213
- `IN ` **The player's raw free-form decision text, verbatim in quotes**
    - source: typer.prompt('Decision>') at cli/main.py:1688 -> `action` -> engine/sim_loop.py:534 -> agents/conversation.py:243. On the re-interpretation pass it is the recommendation-enhanced string built at cli/main.py:1745 append_recommendations_to_decision.
    - bound: NOT truncated and NOT escaped — an embedded double-quote or newline lands raw inside the quoted field
    - evidence: llm/prompts.py:215 f'The Prime Minister has decided: "{action}"'
- `IN ` **Static task framing and output-format instructions — 'interpret this as a DECISION/DIRECTIVE not a question', the five numbered asks, the five output labels, and the markdown formatting note**
    - source: Hard-coded
    - bound: static
    - evidence: llm/prompts.py:217-239

#### Available but not sent — 2

- `OUT` **Per-country FactionStance detail — secret_motive, public_posture, economic_leverage list, intel_sharing_level for RUS/USA/CHN/etc.**
    - source: world.narrative.stances (models/narrative.py:19)
    - evidence: llm/context_builder.py:323 calls to_llm_context() with NO argument; the stance block at models/narrative.py:46-67 is gated on `if target_country_code:` which is None here. Only engine/diplomacy's path passes one (llm/context_builder.py:502). Confirmed by building the real prompt: the rendered dossier contains GLOBAL TRUTH/protagonist/antagonist/patsy and nothing about stances.
- `OUT` **THIS turn's decision text as a transcript line ('Prime Minister's Decision: ...')**
    - source: engine/sim_loop.py:528 appends it to the LOCAL transcript list
    - evidence: engine/sim_loop.py:528 writes to the local `transcript` that is only returned at :584; the caller extends its own list afterwards (cli/main.py:1702). At dispatch time (sim_loop.py:532) the history block therefore ends with the discussion phase. The decision reaches the prompt only through the explicit 'The Prime Minister has decided:' field.

#### What the output changes

- Transcript lines 'Interpretation:' + the raw text (engine/sim_loop.py:541-542), which the caller appends to the campaign transcript (cli/main.py:1702) — so this text becomes part of the GAME HISTORY block of every later prompt in the campaign
- The OPERATIONAL ORDER panel the player reads before confirming (cli/main.py:1702 display_decision_summary, and again with show_details=True at cli/main.py:1712)
- The advisor pushback prompt in the same turn (llm/prompts.py:284)
- Metric deltas, indirectly: engine/narrative_adjudication.py:228 puts it in the action-quality prompt whose parsed EFFECTS become escalation_risk / domestic_stability / alliance_cohesion / casualties changes (engine/narrative_adjudication.py:404, applied then synced to world.metrics at cli/main.py:1875-1879)
- The saved game file, via the transcript (cli/main.py:1979 save_game)
- Nothing else — no flag, posture, ledger or world-state field is written from this output

#### Observed gaps

- The advisor roster is invisible to this call. build_decision_interpretation_prompt never reads initial_conditions['characters'] — llm/prompts.py:193-195 reads only constraints/uk_forces/stockpiles. The model interpreting a directive addressed to specific ministers does not know who they are.
- world.recent_injects — the titles of the last five injects, i.e. what is actually happening — does not reach this prompt. It is read only by check_critical_omissions (agents/conversation.py:352-353). The interpreter sees the event only if it happens to be inside the transcript window.
- The NarrativeState object is never passed to run_turn_decision at all (engine/sim_loop.py:493-501 has no narrative_state parameter), so event_ledger / PlayedEvent dispositions (models/narrative_state.py:88), active_crises (:94), situation_summary (:80) and per-advisor trust (models/narrative_state.py:91, CharacterAttitude.trust) reach neither this call nor the other two in this group.
- world.posture, world.spatial_state, world.diplomatic_relationships, world.difficulty and world.actor_system are never referenced anywhere in llm/prompts.py or llm/context_builder.py — grep over both files returns no hits. Named-location unit tracking (models/world.py:40) therefore cannot inform a feasibility judgement.
- The scenario's intelligence assessment, pre-game timeline, critical_infrastructure and environment sections (initial_conditions.yaml:52-95, :532-537) are loaded into the dict but no prompt in this group reads those keys — llm/prompts.py touches only constraints, uk_forces, stockpiles, characters, objectives, red_objectives.
- llm/context_builder.py:367 get_decision_interpreter_context — a purpose-built 'only the current turn's discussion' context for exactly this call — is DEAD CODE. Grep across the repo finds only its definition; no caller, not even a test.

#### Corrections against this block — 5

_A correction supersedes the row it concerns._

- **REFUTED** — decision_interpretation output_shape/consumed_by: "Nothing in the codebase parses or validates this — the string is returned verbatim" / "No parser exists."
    - correction: A parser exists and runs on every CLI decision. cli/display_utils.py:157 parse_interpretation_simple splits the interpretation on the exact labels the prompt asks for — 'INTERPRETATION:' (:179), 'FORCES INVOLVED:' (:181), 'TIMELINE:' (:188), 'FEASIBILITY:' (:193) — into a {summary, forces, timeline, concerns} dict, and display_decision_summary calls it at :229 to build the OPERATIONAL ORDER panel (:269). It is imported into the CLI at cli/main.py:52. The map also therefore misses two truncations on this output: the forces list is capped at 5 entries (cli/display_utils.py:186 and :200), and when no label parses the raw text is trimmed to 400 chars (cli/display_utils.py:259-261). Note FEASIBILITY is only surfaced when the line contains 'impossible' or 'requires clarification' (:194).
    - evidence: cli/display_utils.py:157-205, cli/display_utils.py:229
- **REFUTED** — decision_interpretation affects: parsed EFFECTS of the action-quality prompt become "escalation_risk / domestic_stability / alliance_cohesion / casualties changes".
    - correction: Casualties are not reachable from this call. The prompt requests exactly three deltas (narrative_adjudication.py:261-263: escalation_risk, alliance_cohesion, domestic_stability). The parser only accepts a metric line if it contains 'escalation', 'alliance' or 'stability' (narrative_adjudication.py:375), so a casualties line is silently discarded. determine_base_effects (:411-446) never emits a casualties key either, and apply_quality_scaling (:449-497) only scales/merges those keys. cli/main.py:1880-1881 does copy casualties from narrative_state.hidden_metrics, but nothing in this adjudication path writes them.
    - evidence: engine/narrative_adjudication.py:260-264, engine/narrative_adjudication.py:375, engine/narrative_adjudication.py:411-446
- **CORRECTED** — decision_interpretation affects/consumed_by: "the OPERATIONAL ORDER panel the player reads before confirming (cli/main.py:1702 display_decision_summary, and again with show_details=True at cli/main.py:1712)".
    - correction: cli/main.py:1702 is `transcript.extend(decision_lines)` — the transcript append, not the display call. display_decision_summary(action, interpretation, show_details=False) is at :1705 (and again at :1769 after re-interpretation); the show_details=True call is at :1713, while :1712 is the `if see_details == "details":` test.
    - evidence: cli/main.py:1702, cli/main.py:1705, cli/main.py:1713
- **CORRECTED** — decision_interpretation affects: "Metric deltas ... applied then synced to world.metrics at cli/main.py:1875-1879"; "the text handed to adjudication (cli/main.py:1845/1858)"; "The saved game file, via the transcript (cli/main.py:1979 save_game)".
    - correction: The metric sync is cli/main.py:1877-1881 (1875 is blank, 1876 a comment; the map's range also omits the two casualties lines at 1880-1881). `action` is passed to adjudication at :1846 (actor path) and :1857 (narrative path) — 1845 is `world.actor_system,` and 1858 is `interpretation,`. save_game is called at :1980, not :1979.
    - evidence: cli/main.py:1846, cli/main.py:1857, cli/main.py:1877-1881, cli/main.py:1980
- **CORRECTED** — decision_interpretation affects (via narrative adjudication): "engine/narrative_adjudication.py:404" is where the parsed EFFECTS live.
    - correction: Line 404 is `"reasoning": _scrub_reasoning(reasoning, world_narrative) or "Action assessed.",`. The effects key is line 405, `"suggested_effects": effects`; the parser that fills it is _parse_quality_response at :347-406.
    - evidence: engine/narrative_adjudication.py:404-405

### Advisor pushback — cabinet ministers objecting to the order before it is committed

`advisor_pushback`

- **Prompt built at** — llm/prompts.py:244 build_pushback_prompt; f-string at llm/prompts.py:277-300. Shared prefix from llm/context_builder.py:285, invoked at llm/prompts.py:277.
- **Dispatched at** — agents/conversation.py:272 — llm_generate_fn(prompt, rng, context=LLMContext.ADVISOR_PUSHBACK). Concrete function is llm.router.generate_text (llm/router.py:203), injected at engine/sim_loop.py:551.
- **LLM context** — LLMContext.ADVISOR_PUSHBACK
- **Model tier** — FLASH -> "gemini-2.5-flash" (llm/model_config.py:32, :43). Same global overrides as the interpretation call.
- **Calls per turn** — 1 per decision submission, always immediately after the interpretation call (engine/sim_loop.py:546). Re-runs on every amend/enhance loop (cli/main.py:1765, :1798).
- **Concurrency** — Alone. Sequentially after the interpretation call — it interpolates that call's output (llm/prompts.py:284) — and before the five-way omissions fan-out.
- **On failure** — No try/except around the call (agents/conversation.py:271-272); the router's retry-then-MockDeterministicDriver fallback (llm/router.py:269-279) is the only guard. Parser degradation is silent and one-directional: (a) any line anywhere containing only 'NO PUSHBACK' discards every concern in the response (agents/conversation.py:278-279); (b) lines appearing before the first recognised role are dropped outright, with the code comment saying so (agents/conversation.py:305); (c) a line whose ':' prefix is not a known role is appended to the PREVIOUS advisor's message (agents/conversation.py:302-304), so a mislabelled speaker's text is attributed to whoever spoke last; (d) if no line carries a recognised role prefix at all, the result is [] and the UI reports 'No advisor concerns raised.' — indistinguishable from a genuine all-clear.

**Why this call exists.** Give the player a last in-fiction warning — the Foreign Secretary or the Attorney General speaking up — before the decision goes to adjudication, and a chance to amend it.

**What it must return.** Free text. Expected: one or more lines of '[ADVISOR ROLE]: [concern]', or the bare sentinel 'NO PUSHBACK' (llm/prompts.py:291-296).

**Parsed at** agents/conversation.py:277-307 — hand-rolled line parser. agents/conversation.py:278 aborts to [] if ANY line is the NO PUSHBACK sentinel (_is_no_pushback_line, agents/conversation.py:130-133, which strips markdown/punctuation decoration). Otherwise each line is split on the first ':' (agents/conversation.py:293-298); the prefix is decoration-stripped by _normalize_role_prefix (:111-113) and accepted only if it is in _known_pushback_roles (:95-108).

#### Data in — 15 reach the prompt

- `IN ` **Fixed dossier framing header**
    - source: Hard-coded
    - bound: static
    - evidence: llm/context_builder.py:309-317 via llm/prompts.py:277
- `IN ` **Secret narrative truth (global only: description, protagonist, antagonist, patsy + the four standing instructions)**
    - source: world.narrative (models/world.py:26); set at cli/main.py:755 in Mystery Mode only
    - bound: not truncated; block absent when world.narrative is None
    - evidence: llm/context_builder.py:322-323 -> models/narrative.py:31-44, 69-79
- `IN ` **Game history header text**
    - source: _HISTORY_HEADER constant
    - bound: static
    - evidence: llm/context_builder.py:35-38 emitted at :228/:277
- `IN ` **Full campaign transcript (all prior turns' injects, Q&A, decisions, interpretations, pushback, adjudications)**
    - source: cli/main.py:1701 `transcript` -> sim_loop.py:499 full_transcript -> :553 -> agents/conversation.py:255/271 -> llm/prompts.py:277
    - bound: WINDOWED: MAX_ADVISOR_TRANSCRIPT_CHARS = 320_000 chars (llm/context_builder.py:27, default at :207, never overridden). Over budget, _TRANSCRIPT_HEAD_SHARE = 0.2 (llm/context_builder.py:54) keeps 64,000 chars of the campaign opening on turn boundaries, spends the rest from the tail, and replaces the middle with one elision marker line (llm/context_builder.py:230-282).
    - evidence: llm/context_builder.py:326 render_transcript_block(transcript)
- `IN ` **Turn number**
    - source: world.turn
    - bound: scalar
    - evidence: llm/context_builder.py:335; restated at llm/prompts.py:58
- `IN ` **Phase string**
    - source: world.phase
    - bound: scalar
    - evidence: llm/context_builder.py:336 (set to 'decision' at engine/sim_loop.py:521 unless dry_run)
- `IN ` **Escalation Risk / Domestic Stability / Alliance Cohesion, raw 0-100**
    - source: world.metrics (models/world.py:6-11, :35)
    - bound: scalars
    - evidence: llm/context_builder.py:337-339
- `IN ` **Military and civilian casualty counts**
    - source: world.metrics.casualties_mil / casualties_civ
    - bound: scalars
    - evidence: llm/context_builder.py:340-341 and llm/prompts.py:64
- `IN ` **Banded prose restatement of the same three metrics (THREAT ASSESSMENT / DOMESTIC SITUATION / ALLIANCE STATUS)**
    - source: world.metrics re-read by build_world_state_summary
    - bound: static thresholds
    - evidence: llm/prompts.py:34-62, appended via llm/context_builder.py:351-352
- `IN ` **KEY INTELLIGENCE FLAGS — truthy entries of world.flags, title-cased**
    - source: world.flags, derived purely from metrics by engine/flags.py:15-35
    - bound: at most 5 flags; whole line omitted when none truthy
    - evidence: llm/prompts.py:67-71
- `IN ` **Standing anti-meta instruction block**
    - source: Hard-coded
    - bound: static
    - evidence: llm/prompts.py:74-77
- `IN ` **The player's raw decision text, verbatim in quotes**
    - source: cli/main.py:1688 typer.prompt -> engine/sim_loop.py:548 -> agents/conversation.py:271
    - bound: not truncated, not escaped
    - evidence: llm/prompts.py:281 f'The PM has decided: "{action}"'
- `IN ` **The interpretation produced by the previous LLM call, verbatim**
    - source: Return of interpret_player_action (agents/conversation.py:245) -> engine/sim_loop.py:532 -> :549
    - bound: NOT truncated — whatever the FLASH model emitted, including a mock-fallback string or an error apology, is pasted in whole
    - evidence: llm/prompts.py:284 under 'Interpretation of this action:'
- `IN ` **Advisor roster with pushback triggers — one '- {role}: {trigger1}, {trigger2}, {trigger3}' line per character, e.g. '- Diplomatic Lead: Actions that violate international law, Military responses without diplomatic cover, Decisions that isolate UK from allies'**
    - source: initial_conditions['characters'] (initial_conditions.yaml:441-501), each entry's 'role' and 'pushback_triggers' keys; loaded at engine/sim_loop.py:525
    - bound: no cap; the 'note' filter excludes the four Russian characters (initial_conditions.yaml:509, :516, :523, :530) but NOT prime_minister — the player's own persona is offered to the model as an advisor who may push back on the player's decision
    - evidence: llm/prompts.py:263 reads characters, :267-271 builds the lines filtering on `isinstance(char_data, dict) and "note" not in char_data`, :273 joins, :287 interpolates. Verified by building the real prompt: six lines, Government Leader / Military Commander / Intelligence Coordinator / Domestic Security / Diplomatic Lead / Legal Advisor.
- `IN ` **Static task framing and output format — the 2-3 sentence brief, 'reference past warnings', the '[ADVISOR ROLE]: [their concern]' template, the NO PUSHBACK sentinel and the bold-formatting note**
    - source: Hard-coded
    - bound: static
    - evidence: llm/prompts.py:289-300

#### Available but not sent — 1

- `OUT` **Per-country FactionStance detail (secret_motive, public_posture, economic_leverage, intel_sharing_level)**
    - source: world.narrative.stances (models/narrative.py:19)
    - evidence: llm/context_builder.py:323 calls to_llm_context() with no target_country_code, so the branch at models/narrative.py:46-67 never executes

#### What the output changes

- Transcript lines 'Advisor Concerns:' + '{role}: {concern}' per advisor, or 'No advisor concerns raised.' (engine/sim_loop.py:556-563) — appended to the campaign transcript at cli/main.py:1702, so it becomes GAME HISTORY for every later prompt
- The ADVISOR CONCERNS panel and the P/A/C gate that decides whether the turn proceeds, the player re-types the decision, or the turn falls back to discussion (cli/main.py:1782-1808). A non-empty list is what makes the decision non-auto-confirming (cli/main.py:1808 else-branch decision_confirmed = True)
- The API's concerns_list, where each pushback entry is given the canned recommendation 'Consider revising your approach.' (engine/game_manager.py:213-219), and the resolve_decision response payload (engine/game_manager.py:349)
- The saved game file, via the transcript
- NOTHING mechanical: no metric, flag, trust value or ledger entry is written from pushback anywhere in the codebase

#### Observed gaps

- uk_forces, stockpiles and constraints do NOT reach this prompt, although they reach the interpretation prompt three lines earlier. llm/prompts.py:263 reads only 'characters'. The Chief of the Defence Staff is asked to fire the trigger 'Militarily implausible actions (e.g., deploying unavailable assets)' and 'Actions that waste limited munitions' (initial_conditions.yaml:458-460) without being shown the order of battle or the munition counts that would make either judgement possible.
- The advisors' knowledge_domains and key_concerns (initial_conditions.yaml:446, :451 etc.) are not included — build_pushback_prompt reads only 'role' and 'pushback_triggers' (llm/prompts.py:269-270), whereas build_advisor_context does read them (llm/prompts.py:107-108).
- No 'personality' or character-voice field reaches the prompt, so all six advisors are simulated in one call with no differentiation beyond a role name and three trigger phrases.
- world.recent_injects (the last five inject titles) is not included — only check_critical_omissions reads it (agents/conversation.py:352-353).
- The NarrativeState — per-advisor trust and relationship (models/narrative_state.py:91, CharacterAttitude.trust), active_crises, situation_summary, event_ledger — is never passed to run_turn_decision (engine/sim_loop.py:493-501 has no such parameter), so an advisor whose trust has collapsed pushes back exactly as one who is loyal.
- The prompt asks the model to label speakers with the scenario's abstract 'role' values ('Government Leader', 'Diplomatic Lead'). The parser accepts those plus a hard-coded alias table of natural titles (agents/conversation.py:24-31) — verified set: attorney general, cds, chief defence staff, chief of the defence staff, diplomatic lead, domestic security, foreign secretary, government leader, home secretary, intelligence coordinator, legal advisor, military commander, national security adviser, national security advisor, nsa, pm, prime minister. Anything outside that set — e.g. 'Defence Secretary:' or 'Chancellor:' — is silently merged into the previous advisor's message (agents/conversation.py:302-304) or dropped (:305).

#### Corrections against this block — 1

_A correction supersedes the row it concerns._

- **CORRECTED** — advisor_pushback affects: "The ADVISOR CONCERNS panel and the P/A/C gate ... A non-empty list is what makes the decision non-auto-confirming (cli/main.py:1808 else-branch decision_confirmed = True)", cited as cli/main.py:1782-1808.
    - correction: Three errors. (a) The pushback block is an `elif` (cli/main.py:1790) hanging off `if critical_concerns:` (:1717) — whenever any critical omission survived parsing, the ADVISOR CONCERNS panel and the P/A/C gate are never reached at all and pushback affects nothing in the CLI beyond the transcript. (b) Line 1808 is `amend_pending = True`, not an else-branch; the `decision_confirmed = True` assignments are at :1817 (choice not A/C) and :1819 (no pushback). (c) The block spans 1789-1819, not 1782-1808 — 1782-1787 is the critical-advisory 'I' (Ignore) branch.
    - evidence: cli/main.py:1790, cli/main.py:1808, cli/main.py:1817-1819

### Critical omissions scan — five advisors independently check what the PM forgot to do (one identical-shaped call per advisor, fired as one parallel group)

`critical_omissions.advisor_scan`

- **Prompt built at** — llm/prompts.py:462 build_critical_omissions_prompt (f-string starts llm/prompts.py:501, ends llm/prompts.py:553); shared prefix built by llm/context_builder.py:285 build_shared_context_prefix
- **Dispatched at** — agents/conversation.py:382 generate_group(...) -> llm/fanout.py:67 (batch path, llm_batch_fn supplied) or llm/fanout.py:81 (sequential path); batch fn is llm/router.py:297 batch_generate_text, single fn is llm/router.py:203 generate_text. Wired at engine/sim_loop.py:566-575.
- **LLM context** — LLMContext.CRITICAL_OMISSIONS (passed at agents/conversation.py:384)
- **Model tier** — ModelTier.PRO -> "gemini-2.5-pro" by default (llm/model_config.py:33 maps LLMContext.CRITICAL_OMISSIONS -> PRO; llm/model_config.py:42-45 maps PRO -> "gemini-2.5-pro"). Resolved at llm/router.py:333 via get_model_config().get_model_for_context(context). Player-overridable in cli/model_settings_menu.py:120. NOTE: the model name is only advisory for the openai_compat provider, which takes OPENAI_COMPAT_MODEL.
- **Calls per turn** — 5 per run_turn_decision call — one per id in advisors_to_check (agents/conversation.py:359-365) that survives the filter at agents/conversation.py:374. run_turn_decision itself can run twice in a turn: the CLI re-runs it after the player applies recommendations (cli/main.py:1701 then cli/main.py:1765; cli/main_dashboard.py:1472 then :1536), and GameManager runs it once dry (engine/game_manager.py:193) and once committed (engine/game_manager.py:270) — so up to 10 calls per turn.
- **Concurrency** — All five go out together as one group. engine/sim_loop.py:574 passes llm_batch_fn=batch_generate_text, so llm/fanout.py:66-76 takes the batch path; the driver fans them across a thread pool (max_workers=min(len,10) at llm/gemini_driver.py:197, min(len,8) at llm/openai_compat_driver.py:273). Rate limiting claims one slot per prompt BEFORE dispatch (llm/router.py:373-378). They run strictly after the single decision-interpretation call (engine/sim_loop.py:532) and the single pushback call (engine/sim_loop.py:546), which share the same cacheable prefix. Without llm_batch_fn (tests, engine/sim_loop.py:685 run_turn path) they run sequentially (llm/fanout.py:78-84). No max_tokens is passed (agents/conversation.py:382-385), so there is no output cap.
- **On failure** — Per-prompt driver failure on the batch path: the driver catches inside its thread pool and returns "[ERROR: ...]" in that slot (llm/gemini_driver.py:211; llm/openai_compat_driver.py:265, :284). That string is truthy and contains no "NO_CONCERN", so agents/conversation.py:390 lets it through, but _extract_labeled_text finds no CONCERN:/RECOMMENDATION: label (agents/conversation.py:404-405, regex at :123) and last_field stays None, so concern remains "" and the guard at agents/conversation.py:419 drops it silently. The error marker therefore CANNOT leak into player-visible text here (unlike the case the fanout docstring warns about at llm/fanout.py:52-55). Whole-batch failure: llm/router.py:382-396 retries once after a 2s sleep (re-claiming rate-limit slots at :391) and then falls back to MockDeterministicDriver().batch_generate_text, printing a WARNING. Short/long result list: llm/fanout.py:72-75 prints "[WARN] batch returned N responses for M prompts" and pads with empty strings so the zip at agents/conversation.py:387 cannot silently drop advisors. Sequential path failure: llm/fanout.py:82-84 prints "[WARN] LLM call failed" and substitutes "", which agents/conversation.py:390 skips. Parse-time exception for one advisor: caught at agents/conversation.py:424-427, prints "[WARN] Critical omissions check failed for {char_id}" and continues with the rest. No advisors loaded: returns [] at agents/conversation.py:347-348. Missing advisor ids are filtered out at agents/conversation.py:374 (and get_all_uk_advisors excludes any character carrying a "note" key, engine/initial_conditions.py:74-77), so a scenario lacking e.g. attorney_general simply fires fewer than five calls. Sentinel over-matching: agents/conversation.py:390 tests `"NO_CONCERN" in response` as a plain substring, so a genuine concern whose prose anywhere contains NO_CONCERN or "NO CONCERN" (e.g. echoing the format block) is discarded whole.

**Why this call exists.** After the player commits a decision, the Foreign Secretary, Chief of the Defence Staff, Attorney General, Home Secretary and National Security Advisor each scan the decision for a CATASTROPHIC gap (no NATO coordination, no legal authority, no public statement, no ally consultation, no logistics) and either raise one concern + one recommendation, or say nothing.

**What it must return.** Free text. Either the sentinel NO_CONCERN, or two labelled lines: "CONCERN: <2-3 sentences>" and "RECOMMENDATION: <1 action>" (format specified llm/prompts.py:540-553). Parser tolerates markdown decoration and case via the regex at agents/conversation.py:123 (_extract_labeled_text) and folds unlabelled continuation lines into whichever label was seen last (agents/conversation.py:412-417).

**Parsed at** agents/conversation.py:387-422 (loop over zip(checking, responses)); sentinel test at agents/conversation.py:390; label extraction at agents/conversation.py:404-417; tuple built at agents/conversation.py:419-422 using initial_conditions characters[char_id]["role"], defaulting to "Advisor".

#### Data in — 16 reach the prompt

- `IN ` **Shared dossier framing header ("UK CRISIS WARGAME - SHARED BRIEFING DOSSIER", "The material below is the same for every member of the COBRA cell.")**
    - source: static literal in build_shared_context_prefix
    - bound: static, 6 lines — not bounded by any constant
    - evidence: llm/context_builder.py:309-317, interpolated at llm/prompts.py:501
- `IN ` **SECRET NARRATIVE CONTEXT — the campaign's hidden truth: description (GLOBAL TRUTH), protagonist, antagonist, patsy (omitted when "NONE"), plus the "never reveal / plausible deniability" instruction block. Per-country FactionStance data (secret_motive, public_posture, intel_sharing_level, economic_leverage) is NOT included because to_llm_context is called with no target_country_code.**
    - source: world.narrative (models/world.py:26, an Optional[NarrativeConfig]) -> NarrativeConfig.to_llm_context()
    - bound: unbounded — whole scenario-authored strings interpolated verbatim (models/narrative.py:36-43)
    - evidence: llm/context_builder.py:322-324 calls world_state.narrative.to_llm_context() with no argument; body at models/narrative.py:21-81; the country-specific branch is models/narrative.py:46-67 and is skipped. Block omitted entirely when world.narrative is None.
- `IN ` **The FULL campaign transcript — every turn's inject text, narrator bridges, advisor Q&A, past decisions, past interpretations, past CRITICAL ADVISORY blocks — under the header "GAME HISTORY - everything that has happened, in order."**
    - source: caller-supplied full_transcript list: cli/main.py:786 `transcript = []` accumulated across the whole campaign (extended at cli/main.py:953, 1296, 1651, 1702); GameManager.self.transcript (engine/game_manager.py:198, 276). Passed engine/sim_loop.py:573 -> agents/conversation.py:317 -> agents/conversation.py:378 -> llm/prompts.py:468 -> llm/prompts.py:501 as `transcript or []`.
    - bound: WINDOWED by MAX_ADVISOR_TRANSCRIPT_CHARS = 320_000 characters (llm/context_builder.py:27), the default of render_transcript_block's max_chars (llm/context_builder.py:207). Under budget: verbatim and complete (llm/context_builder.py:227-228). Over budget: head keeps the campaign opening up to _TRANSCRIPT_HEAD_SHARE = 0.2 -> 64,000 chars (llm/context_builder.py:54, 230), cut on TURN N boundaries (llm/context_builder.py:242-247); tail spends the remainder backwards, also on turn boundaries (llm/context_builder.py:253-260); the middle is replaced by "[... N lines of mid-campaign history elided for length ...]" (llm/context_builder.py:280). NOTE: this is a WIDENING relative to the comment at llm/prompts.py:496-500 — the old 100-line window is gone.
    - evidence: llm/context_builder.py:326 parts.append(render_transcript_block(transcript)); renderer at llm/context_builder.py:206-282; interpolated into the prompt at llm/prompts.py:501
- `IN ` **Current turn number and phase string ("CURRENT SITUATION / Turn: N / Phase: decision")**
    - source: world.turn (models/world.py:22), world.phase (models/world.py:23). Phase is set to "decision" at engine/sim_loop.py:521 unless dry_run=True (engine/game_manager.py:193-199 leaves it at "discussion").
    - bound: scalar
    - evidence: llm/context_builder.py:335-336
- `IN ` **Raw numeric metrics block: Escalation Risk /100, Domestic Stability /100, Alliance Cohesion /100, Military Casualties, Civilian Casualties**
    - source: world.metrics (models/world.py:34) — Metrics fields at models/world.py:7-11
    - bound: scalars
    - evidence: llm/context_builder.py:337-341
- `IN ` **Narrative re-rendering of the SAME metrics as adjectives: THREAT ASSESSMENT (low/moderate/high/critical), DOMESTIC SITUATION (stable/uncertain/fragile/in crisis), ALLIANCE STATUS (strong and unified/uncertain/fragile/fractured), plus turn+phase and casualties a second time**
    - source: world.metrics via build_world_state_summary
    - bound: static shape; the metrics themselves are scalars. Note this duplicates the numeric block above in every prompt.
    - evidence: llm/context_builder.py:351-352 imports and appends build_world_state_summary(world_state); thresholds at llm/prompts.py:33-51; header line llm/prompts.py:58; casualties llm/prompts.py:64
- `IN ` **KEY INTELLIGENCE FLAGS — the truthy world flags, underscores stripped and title-cased**
    - source: world.flags (models/world.py:35, Dict[str,bool]); mutated by update_world_flags (engine/sim_loop.py:257, :625)
    - bound: UNBOUNDED — no cap on the number of flags rendered
    - evidence: llm/prompts.py:67-71 — only flags whose value is truthy are listed (`for k, v in world.flags.items() if v`)
- `IN ` **Standing anti-meta instruction ("You are a real advisor in COBRA... Do NOT reference 'metrics', 'game mechanics', 'scores', or 'values'")**
    - source: static literals in build_world_state_summary
    - bound: static
    - evidence: llm/prompts.py:73-77
- `IN ` **The advisor's role title, used twice: "You are the UK {role}" and "YOUR ROLE AS {role.upper()}"**
    - source: initial_conditions["characters"][character_id]["role"], defaulting to the raw character_id. initial_conditions loaded at engine/sim_loop.py:525 load_initial_conditions(scenario_id, root_path)
    - bound: unbounded scenario string
    - evidence: llm/prompts.py:489-490 (lookup), llm/prompts.py:503 and llm/prompts.py:531 (interpolation)
- `IN ` **Which of the five advisors is speaking (character_id), which selects exactly one domain line: foreign affairs / military readiness / domestic security / legal authority / strategic coordination. The other four conditional expressions render as empty strings, leaving four blank lines in every prompt.**
    - source: agents/conversation.py:359-365 advisors_to_check, filtered to ids actually present in get_all_uk_advisors at agents/conversation.py:374
    - bound: one of five fixed strings
    - evidence: llm/prompts.py:532-536 — five separate `{"..." if character_id == "x" else ""}` expressions; ids supplied at agents/conversation.py:377
- `IN ` **RECENT EVENTS block — the recent_events argument. It contains ONLY inject TITLES, never inject descriptions.**
    - source: world.recent_injects (models/world.py:52, List[str]). The only writer in the whole repo is engine/sim_loop.py:391 `world.recent_injects.append(str(title))` where title = inject.get("title") (engine/sim_loop.py:390). Read at agents/conversation.py:352-353, passed as the 5th positional arg at agents/conversation.py:378, joined at llm/prompts.py:494, interpolated at llm/prompts.py:506.
    - bound: DOUBLY TRUNCATED to 5 entries: engine/sim_loop.py:392 `del world.recent_injects[:-5]` hard-caps the stored list at 5 immediately after each append, and agents/conversation.py:353 takes `[-5:]` again (redundant). Each entry is a bare title with no length cap. The docstring at llm/prompts.py:481 ("Last 2-3 inject descriptions") is WRONG on both count and content. Also note engine/sim_loop.py:387 skips the append entirely when replay=True (post-load), so a reloaded save can under-report.
    - evidence: agents/conversation.py:352-353 -> agents/conversation.py:377-378 -> llm/prompts.py:494 `recent_context = "\n".join(recent_events)` -> llm/prompts.py:505-506. Writer: engine/sim_loop.py:389-392.
- `IN ` **Fallback RECENT EVENTS when world.recent_injects is empty: "Active situation: {flag_key}" for the first three flag KEYS in insertion order — including flags whose value is False.**
    - source: world.flags keys (models/world.py:35)
    - bound: TRUNCATED to 3 by the literal slice [:3] at agents/conversation.py:356. Raw snake_case keys, not prettified.
    - evidence: agents/conversation.py:354-356 `recent_events = [f"Active situation: {flag}" for flag in list(world.flags.keys())[:3]]` — no truthiness filter, unlike llm/prompts.py:68
- `IN ` **Literal "No recent major events" when both recent_injects and flags are empty**
    - source: llm/prompts.py:494 else-branch
    - bound: static
    - evidence: llm/prompts.py:494
- `IN ` **THE PRIME MINISTER'S DECISION — the player's raw decision text, quoted verbatim**
    - source: player_decision = the `action` string typed by the player (cli/main.py:1688 typer.prompt), passed engine/sim_loop.py:568 -> agents/conversation.py:312 -> agents/conversation.py:377 -> llm/prompts.py:466
    - bound: UNBOUNDED — no truncation anywhere. On the CLI re-run path this is the ENHANCED decision, i.e. the original text plus "Additionally:" and the previously-accepted RECOMMENDATION bullets (cli/main.py:201-224 append_recommendations_to_decision, assigned at cli/main.py:1755, re-fed at cli/main.py:1765).
    - evidence: llm/prompts.py:508-509 `"{player_decision}"`
- `IN ` **Static task definition: the five catastrophic outcome classes (alliance loss, international law, nuclear escalation, domestic collapse, military disaster), the HIGH threshold instruction, and five worked examples of critical omissions**
    - source: literals in the f-string
    - bound: static
    - evidence: llm/prompts.py:515-529
- `IN ` **Static response-format contract: CONCERN/RECOMMENDATION labels or the NO_CONCERN sentinel, plus the trailing "Your response (CONCERN + RECOMMENDATION or NO_CONCERN):" cue**
    - source: literals in the f-string
    - bound: static
    - evidence: llm/prompts.py:538-553

#### Available but not sent — 8

- `OUT` **Absence of transcript on one code path: engine/sim_loop.py:685 calls run_turn_decision(world, scenario_id, action, rng, root_path) with no full_transcript, so transcript is None and the history block renders as just the header with zero lines.**
    - source: engine/sim_loop.py:685 (run_turn legacy path)
    - evidence: engine/sim_loop.py:685 — only 5 positional args; full_transcript defaults to None (engine/sim_loop.py:499); `transcript or []` at llm/prompts.py:501 turns it into an empty history block
- `OUT` **`interpretation` — the decision-interpretation LLM output produced moments earlier at engine/sim_loop.py:532**
    - source: engine/sim_loop.py:569 passes it into check_critical_omissions as the 3rd positional arg (agents/conversation.py:313)
    - evidence: DEAD PARAMETER. `grep -n interpretation agents/conversation.py` returns only lines 13, 241, 243-245, 251, 262, 271, 313, 322, 333, 372 — inside check_critical_omissions (agents/conversation.py:310-429) the name appears ONLY in the docstring (line 333) and a comment (line 372). It is never read in the body and is never forwarded: the builder call at agents/conversation.py:376-379 passes (world, initial_conditions, char_id, player_decision, recent_events, transcript) and build_critical_omissions_prompt has no interpretation parameter at all (llm/prompts.py:462-468). The advisors judge the player's raw words, not the interpreted action.
- `OUT` **`personality` — the advisor's characterisation string from initial_conditions**
    - source: llm/prompts.py:491 reads character.get("personality", "Professional and direct")
    - evidence: DEAD LOCAL. `grep -n personality llm/prompts.py` returns exactly one line: 491. The name never appears inside the f-string at llm/prompts.py:501-553. Unlike the advisor Q&A prompt, these five advisors are given no personality at all.
- `OUT` **This turn's decision-phase working transcript — "Prime Minister's Decision: ...", "Interpretation: ...", and the advisor pushback lines generated seconds earlier**
    - source: the LOCAL `transcript` list in run_turn_decision (engine/sim_loop.py:523, appended at :528, :541-542, :557-559)
    - evidence: That local list is a different object from `full_transcript` and is only merged into the campaign transcript by the CALLER, after run_turn_decision returns (engine/sim_loop.py:584 return, then cli/main.py:1702 / engine/game_manager.py:275 transcript.extend). At agents/conversation.py:378 the prompt is built from `full_transcript`, which does not yet contain any of it. (Exception: on the CLI amend re-run at cli/main.py:1765 the FIRST pass's lines — including its CRITICAL ADVISORY block — have already been extended in at cli/main.py:1702, so the second pass does see them.)
- `OUT` **Advisor pushback tuples from generate_advisor_pushback (engine/sim_loop.py:546)**
    - source: engine/sim_loop.py:546-554
    - evidence: Never passed to check_critical_omissions — the call at engine/sim_loop.py:566-575 takes (world, action, interpretation, initial_conditions, generate_text, rng, full_transcript, llm_batch_fn) and pushback is not among them. It is only appended to the local transcript at engine/sim_loop.py:557-559.
- `OUT` **Everything in initial_conditions other than characters[character_id]["role"] — constraints, uk_forces, objectives, the other advisors' entries**
    - source: initial_conditions dict loaded at engine/sim_loop.py:525
    - evidence: llm/prompts.py:489-491 is the only use of initial_conditions in the builder, and only "role" survives to the f-string (llm/prompts.py:503, :531). get_constraints / get_uk_forces (engine/initial_conditions.py:82, :94) are never called from this path.
- `OUT` **world.posture, world.spatial_state, world.diplomatic_relationships, world.actor_system, world.discussion_transcript, world.difficulty, world.scene**
    - source: models/world.py:36, :39, :57, :63, :46, :32, :29
    - evidence: build_shared_context_prefix (llm/context_builder.py:285-355) touches only world_state.narrative, .turn, .phase and .metrics; build_world_state_summary (llm/prompts.py:21-79) adds only .flags. None of these fields is referenced in either function or in build_critical_omissions_prompt.
- `OUT` **The event ledger / NarrativeState played-event dispositions**
    - source: narrative_state.recent_played_events() (engine/sim_loop.py:320-321)
    - evidence: render_event_ledger (llm/context_builder.py:74) is called only from get_stochastic_inject_context (llm/context_builder.py:428) and llm/prompts.py:410 — the inject generator path. build_shared_context_prefix never calls it, and check_critical_omissions has no narrative_state parameter (agents/conversation.py:310-319).

#### What the output changes

- Returns List[(role, concern, recommendation)] (agents/conversation.py:429). Nothing in the parse loop (agents/conversation.py:387-422) mutates WorldState — no metric, flag or posture is touched by this call directly.
- engine/sim_loop.py:577-582: when non-empty, writes a "CRITICAL ADVISORY:" block plus one "{role}: {concern}" and "RECOMMENDATION: {recommendation}" pair per concern into the turn's transcript lines, which cli/main.py:1702 (and cli/main_dashboard.py:1473, engine/game_manager.py:275) extends into the campaign transcript — so these lines become permanent GAME HISTORY and re-enter every later prompt through render_transcript_block.
- cli/main.py:1717-1718 -> display_critical_concerns_with_selection (cli/main.py:137-198): renders a numbered panel of concerns and blocks the turn until the player chooses. 'D' returns to discussion (cli/main.py:1720-1725), 'M' cancels for a manual rewrite (cli/main.py:1727-1732), 'A'/'S' applies selected recommendations.
- cli/main.py:1742 -> append_recommendations_to_decision (cli/main.py:201-224): REWRITES THE PLAYER'S ACTION TEXT, appending "\n\nAdditionally:" and one "- {recommendation}" bullet per selected concern; cli/main.py:1755 assigns it to `action`, so the LLM's own recommendation text becomes the player's decision of record and flows into re-interpretation (cli/main.py:1765) and then into adjudication — including the keyword heuristics at engine/sim_loop.py:601-625 that move escalation_risk/alliance_cohesion/domestic_stability on words like "nato", "public", "strike". This is the only route by which this call changes metrics.
- cli/main_dashboard.py:172-256 and :1488-1543 mirror the same display/apply/re-run behaviour.
- engine/game_manager.py:205-212 flattens the tuples into concerns_list dicts (role/concern/recommendation) returned as "critical_concerns" from interpret_decision (engine/game_manager.py:225), surfaced by the API at api/server.py:714-718 InterpretationResponse; engine/game_manager.py:350-353 emits the same shape from resolve_decision, consumed by docs/py/bridge.py:978.
- Advisors returning NO_CONCERN produce nothing at all (agents/conversation.py:390-391 `continue`) — no transcript line, no UI element.

#### Observed gaps

- The LLM's own interpretation of the decision — computed at engine/sim_loop.py:532 and passed to check_critical_omissions at engine/sim_loop.py:569 — never reaches any of the five prompts (dead parameter, agents/conversation.py:313 vs the builder signature at llm/prompts.py:462-468). The advisors are asked to spot gaps in the PM's plan while seeing only the raw typed sentence.
- The advisor pushback generated seconds earlier (engine/sim_loop.py:546) is invisible to the omissions scan, so the same objection can be raised twice in one turn from two different calls.
- This turn's decision, interpretation and pushback are all in a LOCAL transcript list (engine/sim_loop.py:523-560) that is not merged into full_transcript until after the call returns, so the shared history block stops at the end of the discussion phase.
- recent_events is titles only. The inject's actual description text never reaches the RECENT EVENTS block — only via the far larger transcript block, where it is unlabelled. llm/prompts.py:481 claims "Last 2-3 inject descriptions"; the code delivers up to 5 titles (engine/sim_loop.py:391, agents/conversation.py:353).
- The flags fallback at agents/conversation.py:356 lists flag keys without checking their boolean value, so a flag explicitly set to False can be presented as an "Active situation" — inconsistent with llm/prompts.py:68, which filters on truthiness.
- recent_injects is not appended when replay=True (engine/sim_loop.py:387), so after a save/load the RECENT EVENTS block can be empty or stale and silently falls through to the flags fallback.
- No advisor personality reaches the prompt (llm/prompts.py:491 is a dead local), so all five voices differ only by a role title and one domain bullet — the personality that shapes the advisor Q&A calls is absent here.
- No scenario constraints, UK force posture, ROE or objectives reach the prompt, although the Attorney General is asked about legal authority and the CDS about operational feasibility (llm/prompts.py:489-491 is the only read of initial_conditions).
- The metrics appear twice in every prompt — once as raw numbers (llm/context_builder.py:337-341) and once as adjectives (llm/prompts.py:58-64) — immediately above an instruction never to speak in numbers (llm/prompts.py:76).
- No max_tokens cap is set for this group (agents/conversation.py:382-385 omits it), even though the format asks for only 2-3 sentences plus one action, and the group runs on the PRO tier (llm/model_config.py:33).
- world.flags renders with no cap (llm/prompts.py:67-71) — the one unbounded element of the shared prefix.

## Adjudication

### Action quality assessment (the "ACTION ASSESSMENT" verdict)

`ADJ-1`

- **Prompt built at** — engine/narrative_adjudication.py:223-266 (inline f-string inside assess_action_quality; there is no separate builder in llm/prompts.py)
- **Dispatched at** — engine/narrative_adjudication.py:269 — llm_generate_fn(prompt, rng, max_tokens=400)
- **LLM context** — none — no `context=` kwarg is passed at engine/narrative_adjudication.py:269, so llm/router.py:231-234 leaves model_name=None and the driver default model is used. LLMContext.CHARACTER_RESPONSE and every other enum member in llm/model_config.py:10-20 are unused by this call.
- **Model tier** — Driver default, NOT a configured tier. llm/router.py:229-234: model_override=None and context=None → model_name=None → llm/router.py:183-200 caches a driver built with model_name=None → llm/gemini_driver.py:66-71 falls back to config.GEMINI_MODEL or "gemini-2.5-flash". get_model_config().get_model_for_context() (llm/model_config.py:61-71) is never reached.
- **Calls per turn** — Exactly 1 per adjudicated turn, on both pipelines: engine/narrative_adjudication.py:762-764 (narrative path) and engine/narrative_adjudication.py:859 (actor-simulation path).
- **Concurrency** — Alone, sequential, blocking. It is the first LLM call of adjudication on the narrative path; on the actor path it runs after the actor-response group (engine/narrative_adjudication.py:847-850). Its output must land before ADJ-2 because ADJ-2's prompt interpolates quality_assessment["quality"] (engine/narrative_adjudication.py:541).
- **On failure** — Bare `except Exception` at engine/narrative_adjudication.py:272-273 falls back to _heuristic_quality_assessment (:276-344), a pure keyword scanner. The same fallback fires without any LLM call when llm_generate_fn or rng is None (:211-213). Beneath that, llm/router.py:269-279 already retries once after a 2s sleep and then substitutes MockDeterministicDriver output, so a genuine API failure usually surfaces as the mock's canned "QUALITY: adequate" block (llm/mock_driver.py:1157-1168) rather than reaching the heuristic.

**Why this call exists.** Grades the Prime Minister's committed decision on a five-point scale and proposes the metric deltas plus a multiplier, producing the paragraph of critique the player reads in the ACTION ASSESSMENT panel.

**What it must return.** Plain text in a line-oriented template: `QUALITY: <word>`, `REASONING: <paragraph>`, an `EFFECTS:` header followed by `escalation_risk: <int>` / `alliance_cohesion: <int>` / `domestic_stability: <int>`, and `QUALITY MULTIPLIER: <float>`. Requested cap max_tokens=400 (engine/narrative_adjudication.py:269).

**Parsed at** engine/narrative_adjudication.py:347-406 _parse_quality_response (called at :270)

#### Data in — 10 reach the prompt

- `IN ` **Hidden metric block: escalation risk, alliance cohesion, domestic stability, each as "N/100" plus a CRITICAL/HIGH/MODERATE-style qualitative label computed inline**
    - source: NarrativeState.hidden_metrics (models/narrative_state.py:72), a models/world.py:6-11 Metrics object
    - bound: unbounded (three integers). Values are PRE-effect on both paths: assess runs at :762 before the apply loop at :772-776, and at :859 before the apply loop at :879-883.
    - evidence: models/narrative_state.py:250-252 builds the lines; engine/narrative_adjudication.py:216 calls to_llm_context(); engine/narrative_adjudication.py:224 interpolates it as {context}
- `IN ` **Casualty counts (military, civilian)**
    - source: NarrativeState.hidden_metrics.casualties_mil / .casualties_civ (models/world.py:10-11)
    - bound: unbounded (two integers)
    - evidence: models/narrative_state.py:253, via engine/narrative_adjudication.py:216 → :224
- `IN ` **"Recent Events" list — dramatic-event prose lines**
    - source: NarrativeState.recent_events (models/narrative_state.py:83)
    - bound: WINDOWED to the last 3 entries (slice [-3:] at models/narrative_state.py:256); the field itself is capped at 10 by models/narrative_state.py:298-299. In practice near-static: the only writers anywhere in non-test code are the 3 seed strings at models/narrative_state.py:459-463 and the three crisis strings at engine/narrative_adjudication.py:953, :958, :963 — no inject, decision or adjudication result is ever appended.
    - evidence: models/narrative_state.py:255-256 `self.recent_events[-3:]`, via engine/narrative_adjudication.py:216 → :224
- `IN ` **"Active Crises" list**
    - source: NarrativeState.active_crises (models/narrative_state.py:94)
    - bound: unbounded (no slice), but bounded in practice: 3 seeds at models/narrative_state.py:449-453 plus at most 3 more from engine/narrative_adjudication.py:952, :957, :962
    - evidence: models/narrative_state.py:258-259, via engine/narrative_adjudication.py:216 → :224
- `IN ` **Character relationship roster: each advisor's display name, relationship word (ALLIED/NEUTRAL/HOSTILE/UNKNOWN) and trust/100**
    - source: NarrativeState.characters — Dict[str, CharacterAttitude] (models/narrative_state.py:91, model at :36-43)
    - bound: unbounded (full dict, no slice); fixed at 5 entries by models/narrative_state.py:403-439. Note stance_summary is NOT part of this block — only name/relationship/trust.
    - evidence: models/narrative_state.py:261-262 iterates self.characters.values(), via engine/narrative_adjudication.py:216 → :224
- `IN ` **Game time string and turn number**
    - source: NarrativeState.game_time (models/narrative_state.py:98) and NarrativeState.turn (:97)
    - bound: unbounded. game_time is written once at construction (engine/game_manager.py:131, cli/main.py:783, cli/main_dashboard.py:807) and never updated, so it is a frozen date string for the whole campaign. turn is stale by one from turn 2 onward: it is only synced after adjudication (engine/game_manager.py:329, cli/main.py:1933), which is the same staleness the docstring at engine/narrative_adjudication.py:140-144 relies on.
    - evidence: models/narrative_state.py:264, via engine/narrative_adjudication.py:216 → :224
- `IN ` **Secret narrative truth: GLOBAL TRUTH description, Crisis Protagonist, Primary Target, and Being Used as Pawn (patsy), wrapped in the "SECRET NARRATIVE CONTEXT (DO NOT REVEAL DIRECTLY)" banner and the four standing INSTRUCTIONS lines**
    - source: WorldState.narrative — a models/narrative.py:12 NarrativeConfig, passed in as world_narrative from engine/game_manager.py:300 and cli/main.py:1850/:1861
    - bound: unbounded/untruncated. Only the GLOBAL half: to_llm_context() is called with no target_country_code (engine/narrative_adjudication.py:221), so the per-country stance block at models/narrative.py:45-67 — secret_motive, public_posture, intel_sharing_level, economic_leverage — is skipped entirely. Absent altogether when world.narrative is None (guard at engine/narrative_adjudication.py:220).
    - evidence: engine/narrative_adjudication.py:219-221 builds narrative_context; :225 interpolates it. Body from models/narrative.py:31-40 (banner, description, protagonist, antagonist), :42-43 (patsy), :69-79 (instructions).
- `IN ` **PLAYER ACTION — the raw free-text decision the player typed**
    - source: action argument, threaded from cli/main.py:1846 / engine/game_manager.py:295 (action_text)
    - bound: unbounded — no truncation anywhere on this path
    - evidence: engine/narrative_adjudication.py:226 `PLAYER ACTION: {action}`
- `IN ` **INTERPRETATION — the full raw text of the decision-interpretation LLM call (INTERPRETATION / FORCES INVOLVED / RESOURCES CONSUMED / TIMELINE / FEASIBILITY)**
    - source: return value of agents/conversation.py:244 interpret_player_action, surfaced by engine/sim_loop.py:532 and handed on at engine/game_manager.py:296 / cli/main.py:1847
    - bound: unbounded — the raw string is passed through with no parsing or truncation (agents/conversation.py:244-245 returns it verbatim)
    - evidence: engine/narrative_adjudication.py:228 `INTERPRETATION: {interpretation}`
- `IN ` **Static rubric: six numbered judgement criteria (including the "judge under uncertainty" clause), the "secret context is background for YOU" instruction, the four anti-leak prohibitions, and the required QUALITY/REASONING/EFFECTS/QUALITY MULTIPLIER output template**
    - source: literal text in the f-string
    - bound: fixed literal
    - evidence: engine/narrative_adjudication.py:230-265

#### Available but not sent — 7

- `OUT` **Shared briefing dossier prefix (framing header + transcript block + CURRENT SITUATION metrics + build_world_state_summary)**
    - source: llm/context_builder.py:285 build_shared_context_prefix
    - evidence: assess_action_quality (engine/narrative_adjudication.py:186-193) has no transcript or world_state parameter at all, and llm/context_builder.py is not imported by engine/narrative_adjudication.py (imports at :16-28). Nothing in this file calls build_shared_context_prefix or get_advisor_context.
- `OUT` **Full game transcript / game history**
    - source: transcript list built in cli/main.py and engine/game_manager.py:279
    - evidence: No transcript parameter exists on assess_action_quality (engine/narrative_adjudication.py:186-193) and none is passed at either call site (:762-764, :859). The MAX_ADVISOR_TRANSCRIPT_CHARS=320,000 budget at llm/context_builder.py:27 is irrelevant to this call.
- `OUT` **Purpose-built adjudicator context (decision + summary + world state + metric-impact instructions)**
    - source: llm/context_builder.py:514 get_adjudicator_context
    - evidence: get_adjudicator_context has zero callers in code — a repo-wide grep finds it only at its definition (llm/context_builder.py:514) and in docs/PHASE_3_COMPLETE.md:23 and docs/DYNAMIC_NARRATIVE_SYSTEM.md:57. It is dead code.
- `OUT` **Rolling player-facing situation summary**
    - source: NarrativeState.situation_summary (models/narrative_state.py:80)
    - evidence: models/narrative_state.py:240-266 to_llm_context() never references self.situation_summary. It appears only in display paths (models/narrative_state.py:233-234, cli/main.py:1110 and :1962, cli/main_dashboard.py:1158 and :1733).
- `OUT` **Event ledger (which injects have played and their open/advanced/resolved disposition)**
    - source: NarrativeState.event_ledger (models/narrative_state.py:88)
    - evidence: to_llm_context() at models/narrative_state.py:240-266 omits it; render_event_ledger (llm/context_builder.py:74) is only wired into the inject prompt via llm/context_builder.py:428. The adjudicator writes to the ledger (engine/narrative_adjudication.py:155-158) but never reads it into a prompt.
- `OUT` **World flags, posture, spatial_state, recent_injects, diplomatic_relationships, difficulty, phase, actor_system trust levels**
    - source: models/world.py:32-67 WorldState fields
    - evidence: assess_action_quality receives no WorldState at all (engine/narrative_adjudication.py:186-193); only NarrativeState and NarrativeConfig cross the boundary.
- `OUT` **play_mode (classic/immersive/emergent)**
    - source: NarrativeState.play_mode (models/narrative_state.py:101)
    - evidence: to_llm_context() (models/narrative_state.py:240-266) does not mention play_mode; it is consumed only by display_for_mode (:199-236) and cli/display_utils.py:324.

#### What the output changes

- quality string — validated against the five-word whitelist at engine/narrative_adjudication.py:366-369, else defaults to "adequate"
- multiplier — parsed at :383-388 and clamped to [0.5, 2.5]; if it parses to exactly 1.0 (or is missing) the quality→multiplier table at :391-399 overrides it (catastrophic maps to 2.0, deliberately amplifying rather than inverting harm)
- suggested_effects dict — built by the loose `elif` at :374-381 that fires on ANY line containing a colon and the substring escalation/alliance/stability, so continuation lines of the REASONING paragraph can be mis-parsed as metrics; int() failures are silently swallowed at :380-381
- reasoning — scrubbed at :404 by _scrub_reasoning (:78-112), which drops whole sentences matching the _LEAK_MARKERS regex (:38-43), containing narrative_id, or sharing an 8-token window with the narrative description (_DESCRIPTION_WINDOW=8, :48, :60-75); if nothing survives it becomes _NEUTRAL_REASONING ("Your advisors take stock of the response.", :50)
- hidden_metrics mutation, narrative path: suggested_effects is passed as BOTH base_effects and inside quality_assessment at engine/narrative_adjudication.py:767-769, so apply_quality_scaling (:471-482) computes final = (clamp±20(int(delta*multiplier)) + delta) // 2 — the LLM's delta is counted twice — then :772-776 applies it with clamp(0,100)
- hidden_metrics mutation, actor path: base_effects come from the keyword heuristic determine_base_effects (:865, defined :411-446), scaled and merged with suggested_effects at :866, then weighted 40% against 60% actor effects at :876 before being applied at :879-883
- context modifiers applied after merge: alliance gains halved when alliance_cohesion>70, domestic gains halved when escalation_risk>80 (:489-496)
- advisor trust — narrative path only: _update_character_attitudes (:788, defined :928-943) shifts uk_nsa/uk_foreign_sec/uk_home_sec/uk_cds by +5/+2/0/-3/-8 on the quality word. This is NEVER called on the actor-simulation path (no call anywhere in :799-900), so advisor trust is frozen in actor-enabled campaigns
- quality word is interpolated into every ADJ-2 advisor prompt as ACTION QUALITY and selects the tone adjective (:541, :608-615)
- reasoning is displayed in the ACTION ASSESSMENT panel (cli/display_utils.py:330/:336, softened by narrative_assessment for non-classic modes at :324-325), appended to the save transcript (cli/main.py:1884-1886), and returned as "reasoning" to the API (engine/game_manager.py:345)
- actor path only: reasoning and quality are re-wrapped into the actor summary string by _generate_actor_summary (:892, defined :903-925), which is what that path returns as `reasoning`

#### Observed gaps

- The transcript is absent entirely. The adjudicator grades the decision without seeing the discussion that produced it, the inject it responds to, or any prior turn — llm/context_builder.py's 320,000-char history budget (:27) is never spent here.
- The event ledger is absent, so the adjudicator cannot tell whether the action closes a thread — yet its own return value drives record_event_disposition (:155-158, :779, :864), which infers closure from keyword overlap instead (_CLOSURE_VERBS, :118-123).
- situation_summary is absent, despite update_situation_summary's docstring at :669-671 claiming it "feeds to_llm_context() for every downstream prompt". It does not — models/narrative_state.py:240-266 never reads it.
- recent_events is effectively frozen at the three seed strings (models/narrative_state.py:459-463): nothing in the game appends injects or decisions to it, so the "Recent Events" block is stale from turn 1.
- Per-country stances (secret_motive, public_posture, intel_sharing_level, economic_leverage) are withheld because no target_country_code is passed (:221 vs models/narrative.py:45-67), so the adjudicator judges "how other actors will really respond" — its own instruction at :233-234 — without their motives.
- max_tokens=400 is silently discarded on Gemini: llm/router.py:255-262 only forwards it when the driver signature declares it, and llm/gemini_driver.py:106 is `generate_text(self, prompt, rng)`. The effective cap becomes the driver-wide max_output_tokens=2048 (llm/gemini_driver.py:93, :103). Only llm/openai_compat_driver.py:150-157 honours it.
- The advisor's own stance_summary strings are visible to ADJ-2 but not here; conversely this call sees casualties and game_time, which ADJ-2 also sees. Neither sees final_effects.

#### Corrections against this block — 5

_A correction supersedes the row it concerns._

- **REFUTED** — ADJ-1 notable_gaps: "The event ledger is absent... yet its own return value drives record_event_disposition (:155-158, :779, :864)" — i.e. the quality-assessment output feeds event-disposition recording.
    - correction: record_event_disposition's signature is `def record_event_disposition(narrative_state, action) -> None` (:137). Neither call site passes the assessment: :779 is `record_event_disposition(narrative_state, action)` and :864 is identical. ADJ-1's return value plays no part whatsoever — the disposition is inferred purely from `infer_event_disposition(current.title, action)` (:155) over the raw player text. The map's own following clause ("which infers closure from keyword overlap instead") contradicts the claim it just made. Nothing from the LLM assessment reaches the ledger.
    - evidence: engine/narrative_adjudication.py:137, :779, :864
- **CORRECTED** — ADJ-2 dispatch_site: "Both call sites supply one: engine/game_manager.py:301/:314 and cli/main.py:1851/:1862 pass llm_batch_fn=batch_generate_text". Same two-call-site framing is used in ADJ-1's inputs ("passed in as world_narrative from engine/game_manager.py:300 and cli/main.py:1850/:1861").
    - correction: There is a THIRD live call-site pair the map never mentions: cli/main_dashboard.py:1614 `adjudicate_with_actor_simulation(...)` and :1626 `adjudicate_with_narrative(...)`, both passing `world_narrative=world.narrative` and `llm_batch_fn=batch_generate_text` (:1621/:1622 and :1633/:1634). It is non-test, runnable code (`python -m cli.main_dashboard`), imported at cli/main_dashboard.py:57. The behavioural conclusions are unchanged because the arguments are identical, but "both call sites" is factually wrong — there are three.
    - evidence: cli/main_dashboard.py:1614-1622, :1626-1634
- **CORRECTED** — ADJ-1 (and ADJ-3) input "Game time string and turn number": "game_time is written once at construction (engine/game_manager.py:131, cli/main.py:783, cli/main_dashboard.py:807) and never updated, so it is a frozen date string for the whole campaign."
    - correction: The enumeration of writers is incomplete and the characterisation is wrong on one branch. Two further construction sites exist for legacy saves that carry no narrative state: cli/main.py:739 and cli/main_dashboard.py:763 both build the NarrativeState with `game_time=f"Turn {world.turn}"`. On that path the string interpolated at models/narrative_state.py:264 is "Turn 7", not a date at all, so "frozen date string" does not hold. ("Never updated after construction" does hold — no assignment to `.game_time` exists anywhere outside these five constructor calls.)
    - evidence: cli/main.py:736-739, cli/main_dashboard.py:760-763
- **CORRECTED** — ADJ-1 failure_behaviour: "Bare `except Exception` at engine/narrative_adjudication.py:272-273 falls back to _heuristic_quality_assessment".
    - correction: The `except Exception:` clause is at :271. Line 272 is the comment `# Fallback to heuristic on error` and :273 is the `return _heuristic_quality_assessment(action, narrative_state)`. The cited range excludes the except statement itself.
    - evidence: engine/narrative_adjudication.py:271-273
- **CORRECTED** — ADJ-1 input 'Purpose-built adjudicator context': "get_adjudicator_context has zero callers in code — a repo-wide grep finds it only at its definition (llm/context_builder.py:514) and in docs/PHASE_3_COMPLETE.md:23 and docs/DYNAMIC_NARRATIVE_SYSTEM.md:57."
    - correction: The grep result is under-reported: the name also appears in docs/handover/PHASE_3_COMPLETE.md:23 and docs/handover/DYNAMIC_NARRATIVE_SYSTEM.md:57 (and in a stale copy at .claude/worktrees/agent-a80faf2d48cc5fbe8/llm/context_builder.py:239). The load-bearing conclusion is confirmed: there is no Python caller anywhere outside the definition, so the function is dead and reaches no prompt.
    - evidence: docs/handover/DYNAMIC_NARRATIVE_SYSTEM.md:57, docs/handover/PHASE_3_COMPLETE.md:23

### Advisor reactions to the adjudicated decision (the ADVISOR REACTIONS lines)

`ADJ-2`

- **Prompt built at** — engine/narrative_adjudication.py:597-633 build_character_response_prompt (one prompt per responding advisor, built in the list comprehension at :536-544)
- **Dispatched at** — engine/narrative_adjudication.py:545-546 generate_group(...) → llm/fanout.py:67 `llm_batch_fn(prompts, rng, **kwargs)` when a batch fn is supplied, else the sequential loop at llm/fanout.py:78-85. Both call sites supply one: engine/game_manager.py:301/:314 and cli/main.py:1851/:1862 pass llm_batch_fn=batch_generate_text, so the live path is llm/router.py:297 batch_generate_text → llm/router.py:383 driver.batch_generate_text.
- **LLM context** — none — generate_group is called positionally at engine/narrative_adjudication.py:545 as (prompts, llm_generate_fn, rng, llm_batch_fn, max_tokens=...), so `context` keeps its None default (llm/fanout.py:25) and is never added to kwargs (llm/fanout.py:61-62). LLMContext.CHARACTER_RESPONSE — defined at llm/model_config.py:19 and mapped to ModelTier.FLASH at :37 — is dead for this call.
- **Model tier** — Driver default. llm/router.py:331-335: context=None and model_override=None → model_name=None → llm/router.py:337 builds the default driver. The FLASH mapping intended for character responses (llm/model_config.py:37) is never consulted.
- **Calls per turn** — 1 to 4 prompts per adjudicated turn, one LLM completion each, issued as a single group. Selection is _select_responding_characters (engine/narrative_adjudication.py:564-587): uk_nsa unconditionally (:572); +uk_foreign_sec if abs(alliance_cohesion delta) > 5 (:575-576); +uk_home_sec if abs(domestic_stability delta) > 5 (:579-580); +uk_cds if escalation_risk delta > 5 (:583-584); truncated to the first 4 (:587); then filtered to ids actually present in narrative_state.characters (:530-531).
- **Concurrency** — The group. All selected advisor prompts go out together through llm/fanout.py:67 → llm/router.py:383 driver.batch_generate_text (a thread pool). No advisor sees another's reply — engine/narrative_adjudication.py:532-533 states this and the prompts are built independently at :536-544. Runs after ADJ-1 (whose quality word it needs) and before ADJ-3.
- **On failure** — Two distinct failure shapes, both handled. Sequential path: llm/fanout.py:82-85 catches per-prompt exceptions, prints a warning and inserts "" — which then becomes the "Understood, Prime Minister." fallback at engine/narrative_adjudication.py:560. Batch path: the live drivers catch inside their thread pools and return "[ERROR: ...]" strings (llm/openai_compat_driver.py:240-242), which never raise and so never reach the router's retry — the guard at engine/narrative_adjudication.py:557-558 exists precisely to stop a cabinet minister reading out an HTTP status. A short batch result is padded to length with a [WARN] at llm/fanout.py:72-75. A whole-batch failure retries once after 2s then falls back to MockDeterministicDriver.batch_generate_text (llm/router.py:382-396). With llm_generate_fn or rng None, no call is made at all and _generate_templated_responses (:636-655) returns a single canned NSA line.

**Why this call exists.** Gives the player two or three sentences from each relevant cabinet advisor, spoken in COBRA and pitched to how well the decision was judged.

**What it must return.** Free prose, 2-3 sentences of in-character dialogue, no structure or delimiters. Requested cap max_tokens=150 via CHARACTER_RESPONSE_MAX_TOKENS (engine/narrative_adjudication.py:594, passed at :546 → llm/fanout.py:63-64 → llm/router.py:303).

**Parsed at** engine/narrative_adjudication.py:548-561 — inline zip loop: strips whitespace and wrapping double quotes (:550), blanks any string beginning "[ERROR:" (:557-558), and substitutes f"[{char.name}] Understood, Prime Minister." for anything empty (:560). There is no field parser.

#### Data in — 13 reach the prompt

- `IN ` **Hidden metric block: escalation risk, alliance cohesion, domestic stability with qualitative labels**
    - source: NarrativeState.hidden_metrics (models/narrative_state.py:72)
    - bound: unbounded (three integers). POST-effect here: generate_character_responses runs at :782 after the apply loop at :772-776 (narrative path) and at :886 after :879-883 (actor path), so advisors react to already-moved metrics.
    - evidence: models/narrative_state.py:250-252 via engine/narrative_adjudication.py:605 (context = narrative_state.to_llm_context()) → :618
- `IN ` **Casualty counts (military, civilian)**
    - source: NarrativeState.hidden_metrics.casualties_mil / .casualties_civ (models/world.py:10-11)
    - bound: unbounded (two integers)
    - evidence: models/narrative_state.py:253 via engine/narrative_adjudication.py:605 → :618
- `IN ` **"Recent Events" list**
    - source: NarrativeState.recent_events (models/narrative_state.py:83)
    - bound: WINDOWED to last 3 (models/narrative_state.py:256); field capped at 10 (:298-299); in practice the 3 seeds from :459-463 plus any crisis strings from engine/narrative_adjudication.py:953/:958/:963
    - evidence: models/narrative_state.py:255-256 via engine/narrative_adjudication.py:605 → :618
- `IN ` **"Active Crises" list**
    - source: NarrativeState.active_crises (models/narrative_state.py:94)
    - bound: unbounded (no slice). Note this snapshot is taken BEFORE _check_and_trigger_crises runs (:791 narrative path / :895 actor path), so a crisis tripped by this turn's effects is not yet listed.
    - evidence: models/narrative_state.py:258-259 via engine/narrative_adjudication.py:605 → :618
- `IN ` **Character relationship roster for ALL five characters (name, relationship, trust) — including the four advisors not speaking and the US NSA**
    - source: NarrativeState.characters (models/narrative_state.py:91)
    - bound: unbounded (full dict); 5 entries (models/narrative_state.py:403-439). Trust values are PRE-update on the narrative path (_update_character_attitudes runs later, at :788), and permanently un-updated on the actor path (never called in :799-900).
    - evidence: models/narrative_state.py:261-262 via engine/narrative_adjudication.py:605 → :618
- `IN ` **Game time string and turn number**
    - source: NarrativeState.game_time / .turn (models/narrative_state.py:97-98)
    - bound: unbounded; game_time frozen at construction (engine/game_manager.py:131), turn one behind from turn 2 on (synced only at engine/game_manager.py:329 / cli/main.py:1933)
    - evidence: models/narrative_state.py:264 via engine/narrative_adjudication.py:605 → :618
- `IN ` **PLAYER ACTION — raw decision text**
    - source: action argument (engine/narrative_adjudication.py:783 / :887 → :539)
    - bound: unbounded
    - evidence: engine/narrative_adjudication.py:620 `PLAYER ACTION: {action}`
- `IN ` **ACTION QUALITY — the one-word grade from ADJ-1**
    - source: quality_assessment["quality"] (engine/narrative_adjudication.py:541), produced at :366-369/:401
    - bound: single whitelisted word
    - evidence: engine/narrative_adjudication.py:621 `ACTION QUALITY: {quality}`
- `IN ` **Speaking advisor's display name ("You are {name}.")**
    - source: CharacterAttitude.name (models/narrative_state.py:39), seeded at models/narrative_state.py:406/:413/:420/:427/:434
    - bound: unbounded; fixed strings
    - evidence: engine/narrative_adjudication.py:623
- `IN ` **Speaking advisor's relationship word and trust score toward the PM**
    - source: CharacterAttitude.relationship / .trust (models/narrative_state.py:40-41)
    - bound: unbounded; trust clamped 0-100 by models/narrative_state.py:278. Pre-update on the narrative path (:788 runs after :782).
    - evidence: engine/narrative_adjudication.py:624 `Your relationship with the PM: {character.relationship.upper()} (trust: {character.trust}/100)`
- `IN ` **Speaking advisor's stance_summary one-liner**
    - source: CharacterAttitude.stance_summary (models/narrative_state.py:43)
    - bound: unbounded, but STATIC for the whole campaign: the only values ever written are the five literals at models/narrative_state.py:409/:416/:423/:430/:437. update_character_attitude accepts a stance_summary argument (models/narrative_state.py:272, applied at :283-284) but no caller anywhere passes it — the sole non-test call site is engine/narrative_adjudication.py:943, which passes trust_delta only.
    - evidence: engine/narrative_adjudication.py:625 `Your current stance: {character.stance_summary}`
- `IN ` **Tone adjective derived from the quality word ("impressed and supportive" … "alarmed and strongly opposed")**
    - source: literal tone_guidance dict
    - bound: fixed literal; defaults to "neutral" for an unrecognised quality (:615)
    - evidence: engine/narrative_adjudication.py:608-615 builds it, :627 interpolates `a tone that is {tone}`
- `IN ` **Length and staging instruction ("2-3 sentences, in character, as if speaking directly to the Prime Minister in a COBRA briefing")**
    - source: literal text
    - bound: fixed literal
    - evidence: engine/narrative_adjudication.py:629-631

#### Available but not sent — 7

- `OUT` **Secret narrative truth (NarrativeConfig)**
    - source: WorldState.narrative (models/world.py:26)
    - evidence: world_narrative is not a parameter of generate_character_responses (engine/narrative_adjudication.py:503-511) nor of build_character_response_prompt (:597-602), and neither call site passes it (:782-785, :886-889). Advisors react with no knowledge of the hidden narrative — unlike ADJ-1 and unlike the actor-simulation prompts, which get it at :843-844.
- `OUT` **final_effects — the metric deltas about to be / just applied**
    - source: computed at engine/narrative_adjudication.py:767 / :869-876
    - evidence: PARAMETER EXISTS BUT IS NOT INTERPOLATED. final_effects is passed into generate_character_responses at :784 / :888 and declared at :506, but its only use in the body is _select_responding_characters(narrative_state, final_effects) at :530 — it is never handed to build_character_response_prompt (:536-544 passes only character, action, quality, narrative_state) and appears nowhere in the f-string at :617-631. The advisor is told the grade, never the consequences.
- `OUT` **quality_assessment["reasoning"] — the adjudicator's written critique**
    - source: engine/narrative_adjudication.py:404
    - evidence: The whole quality_assessment dict reaches generate_character_responses (:506, :783/:887) but only ["quality"] is read (:541). "reasoning" and "suggested_effects" never enter the prompt.
- `OUT` **INTERPRETATION of the decision**
    - source: agents/conversation.py:244 via engine/sim_loop.py:532
    - evidence: interpretation is not a parameter of generate_character_responses (engine/narrative_adjudication.py:503-511); the call sites at :782-785 and :886-889 do not pass it.
- `OUT` **Other advisors' reactions this turn**
    - source: the sibling prompts in the same group
    - evidence: Prompts are built independently at engine/narrative_adjudication.py:536-544 and fanned out in one shot at llm/fanout.py:67; the comment at :532-533 states the intent explicitly.
- `OUT` **Actor (international) responses generated earlier this turn on the actor path**
    - source: actor_responses from engine/narrative_adjudication.py:847-850
    - evidence: generate_character_responses is called at :886-889 without actor_responses; nothing in :597-633 references them.
- `OUT` **Shared briefing dossier prefix, full transcript, world state summary, event ledger, situation_summary, WorldState flags/posture/recent_injects**
    - source: llm/context_builder.py:285, :74; models/narrative_state.py:80, :88; models/world.py:32-67
    - evidence: build_character_response_prompt (engine/narrative_adjudication.py:597-602) takes only character, action, quality and narrative_state; its entire context is to_llm_context() at :605, which omits situation_summary and event_ledger (models/narrative_state.py:240-266). engine/narrative_adjudication.py never imports llm.context_builder (imports at :16-28).

#### What the output changes

- Returned as a List[Tuple[name, text)] from adjudicate_with_narrative (:796) / adjudicate_with_actor_simulation (:900)
- Rendered in the ADVISOR REACTIONS block (cli/display_utils.py:366 onward, invoked from cli/main.py:1866-1874)
- Written verbatim into the save transcript as `{char_name}: "{response}"` (cli/main.py:1894-1898)
- Returned to the API/browser as "advisor_reactions" (engine/game_manager.py:347)
- Mutates NOTHING in NarrativeState — no metric, trust value, stance_summary, crisis or ledger entry is touched by this output. It is pure flavour text.

#### Observed gaps

- The advisor does not see what the decision actually did — final_effects is passed to the function and used only for casting, never shown (engine/narrative_adjudication.py:506, :530 vs :536-544).
- The advisor does not see the adjudicator's reasoning, so the spoken reaction and the ACTION ASSESSMENT paragraph beside it are generated from disjoint information.
- No secret narrative truth reaches advisors, so they cannot foreshadow the hidden plot the way ADJ-1 and the actor simulation can.
- stance_summary is dead state: seeded once at models/narrative_state.py:409-437 and never written again, so "Your current stance" says the same thing on turn 1 and turn 18 regardless of what happened.
- Trust in the prompt is one adjudication stale on the narrative path (:788 runs after :782) and permanently stale on the actor path (_update_character_attitudes is never called from :799-900), so an advisor whose trust should have collapsed still introduces itself as ALLIED.
- max_tokens=150 is silently dropped on Gemini: llm/router.py:353-361 only forwards it when the driver signature declares it, and llm/gemini_driver.py:151 is `batch_generate_text(self, prompts, rng)`. The comment at engine/narrative_adjudication.py:590-593 warns that a dropped cap yields an empty advisor line; on Gemini it is dropped, leaving only the driver-wide 2048 (llm/gemini_driver.py:93, :103).
- The prompt has no shared cacheable prefix: it opens with the per-turn metrics block, the exact anti-pattern llm/context_builder.py:288-307 was written to fix — but this call site never adopted build_shared_context_prefix.

#### Corrections against this block — 3

_A correction supersedes the row it concerns._

- **CORRECTED** — ADJ-2 dispatch_site: "Both call sites supply one: engine/game_manager.py:301/:314 and cli/main.py:1851/:1862 pass llm_batch_fn=batch_generate_text". Same two-call-site framing is used in ADJ-1's inputs ("passed in as world_narrative from engine/game_manager.py:300 and cli/main.py:1850/:1861").
    - correction: There is a THIRD live call-site pair the map never mentions: cli/main_dashboard.py:1614 `adjudicate_with_actor_simulation(...)` and :1626 `adjudicate_with_narrative(...)`, both passing `world_narrative=world.narrative` and `llm_batch_fn=batch_generate_text` (:1621/:1622 and :1633/:1634). It is non-test, runnable code (`python -m cli.main_dashboard`), imported at cli/main_dashboard.py:57. The behavioural conclusions are unchanged because the arguments are identical, but "both call sites" is factually wrong — there are three.
    - evidence: cli/main_dashboard.py:1614-1622, :1626-1634
- **CORRECTED** — ADJ-2 failure_behaviour: "the live drivers catch inside their thread pools and return \"[ERROR: ...]\" strings (llm/openai_compat_driver.py:240-242)".
    - correction: Lines 240-242 are the *docstring* of batch_generate_text ("Mirrors GeminiDriver.batch_generate_text: individual failures are returned as \"[ERROR: ...]\" strings..."), not the code. The behaviour is real but lives at :260-265 (`generate_single`'s `except Exception as e: return f"[ERROR: {_truncate(str(e), 200)}]"`) and :283-284, and at llm/gemini_driver.py:192-193 and :210-211. Citing a docstring as evidence for runtime behaviour is precisely the error this audit is meant to exclude; the substance survives, the evidence does not.
    - evidence: llm/openai_compat_driver.py:240-242 vs :260-265, :283-284; llm/gemini_driver.py:192-193, :210-211
- **CORRECTED** — ADJ-2 concurrency and inputs: "No advisor sees another's reply — engine/narrative_adjudication.py:532-533 states this" (cited twice, also under 'Other advisors' reactions this turn').
    - correction: Line 532 is blank. The comment is at :533-534 ("Each advisor reacts to the same decision and the same assessment; none / of them reads another's line. Asked together rather than in sequence."). The independence claim itself is confirmed by the prompt construction at :536-544 and the fan-out at llm/fanout.py:67, but the cited lines are off by one.
    - evidence: engine/narrative_adjudication.py:532-534

### Situation summary refresh (the PM's daily brief paragraph)

`ADJ-3`

- **Prompt built at** — engine/narrative_adjudication.py:675-685 (inline f-string inside update_situation_summary)
- **Dispatched at** — engine/narrative_adjudication.py:687 — llm_generate_fn(prompt, rng, max_tokens=150).strip().strip('"')
- **LLM context** — none — no `context=` kwarg at engine/narrative_adjudication.py:687, so llm/router.py:231-234 leaves model_name=None.
- **Model tier** — Driver default (llm/router.py:229-236 → llm/gemini_driver.py:66-71 config.GEMINI_MODEL / "gemini-2.5-flash"). No LLMContext member covers situation summaries at all (llm/model_config.py:10-20).
- **Calls per turn** — Exactly 1 per adjudicated turn, on both pipelines: engine/narrative_adjudication.py:794 and :898. It is the last LLM call of the adjudication step.
- **Concurrency** — Alone, sequential, last. Fires after effects are applied (:772-776 / :879-883), after event disposition is recorded (:779 / :864), after advisor reactions (:782 / :886), after trust updates (:788, narrative path only) and after crisis triggers (:791 / :895).
- **On failure** — try/except at engine/narrative_adjudication.py:686-695 logs at debug level and drops through to a deterministic fallback built from the current hidden metrics (:697-729): a risk sentence keyed on escalation_risk thresholds 85/70/50 (:699-706), an alliance sentence on alliance_cohesion 70/50/30 (:708-715), a domestic sentence on domestic_stability 70/50/30 (:717-724), plus "Active crises: ..." from active_crises[-3:] (:727-728). The same fallback is reached when the LLM returns an empty/whitespace string, because the assignment is gated on `if summary:` (:688) and control falls out of the try block. It also runs with no LLM call at all when llm_generate_fn or rng is None (:673). Underneath, llm/router.py:269-279 retries once then substitutes the mock's canned brief (llm/mock_driver.py:1171-1174), so a true API failure normally yields mock prose rather than the deterministic fallback.

**Why this call exists.** Rewrites the two-or-three-sentence standing brief the player reads at the end of the turn, so the crisis, the alliance and the home front are described as they now stand after the decision.

**What it must return.** Free prose, 2-3 sentences, no structure. Requested cap max_tokens=150 (engine/narrative_adjudication.py:687).

**Parsed at** engine/narrative_adjudication.py:687-690 — no parser: .strip().strip('"') then a truthiness test; a non-empty string is assigned straight to state and the function returns early (:689-690).

#### Data in — 8 reach the prompt

- `IN ` **Hidden metric block with qualitative labels**
    - source: NarrativeState.hidden_metrics (models/narrative_state.py:72)
    - bound: unbounded (three integers). POST-effect — this is the last call in the pipeline.
    - evidence: models/narrative_state.py:250-252 via engine/narrative_adjudication.py:674 → :676
- `IN ` **Casualty counts (military, civilian)**
    - source: NarrativeState.hidden_metrics.casualties_mil / .casualties_civ (models/world.py:10-11)
    - bound: unbounded (two integers)
    - evidence: models/narrative_state.py:253 via engine/narrative_adjudication.py:674 → :676
- `IN ` **"Recent Events" list**
    - source: NarrativeState.recent_events (models/narrative_state.py:83)
    - bound: WINDOWED to last 3 (models/narrative_state.py:256); field capped at 10 (:298-299). Any crisis line added this turn at engine/narrative_adjudication.py:953/:958/:963 IS visible here, because :791/:895 run before :794/:898.
    - evidence: models/narrative_state.py:255-256 via engine/narrative_adjudication.py:674 → :676
- `IN ` **"Active Crises" list**
    - source: NarrativeState.active_crises (models/narrative_state.py:94)
    - bound: unbounded (no slice). Includes crises triggered this turn (:791/:895 precede :794/:898) — unlike the snapshot ADJ-2 sees.
    - evidence: models/narrative_state.py:258-259 via engine/narrative_adjudication.py:674 → :676
- `IN ` **Character relationship roster (name, relationship, trust) for all five characters**
    - source: NarrativeState.characters (models/narrative_state.py:91)
    - bound: unbounded; 5 entries. Trust is POST-update on the narrative path (:788 precedes :794); on the actor path it is unchanged since campaign start because _update_character_attitudes is never called in :799-900.
    - evidence: models/narrative_state.py:261-262 via engine/narrative_adjudication.py:674 → :676
- `IN ` **Game time string and turn number**
    - source: NarrativeState.game_time / .turn (models/narrative_state.py:97-98)
    - bound: unbounded; game_time frozen at construction (engine/game_manager.py:131, cli/main.py:783), turn one behind from turn 2 on (synced at engine/game_manager.py:329 / cli/main.py:1933, i.e. AFTER this call)
    - evidence: models/narrative_state.py:264 via engine/narrative_adjudication.py:674 → :676
- `IN ` **THE PRIME MINISTER'S LATEST DECISION — raw action text**
    - source: action argument, from engine/narrative_adjudication.py:794 / :898
    - bound: unbounded — no truncation (contrast the ledger note at :158, which does truncate the same string to 90 chars)
    - evidence: engine/narrative_adjudication.py:678
- `IN ` **Instruction block: "2-3 sentences for the Prime Minister's daily brief", cover crisis / alliance / mood at home, plain serious prose, no headings, numbers or bullets**
    - source: literal text
    - bound: fixed literal
    - evidence: engine/narrative_adjudication.py:680-685

#### Available but not sent — 6

- `OUT` **The PREVIOUS situation_summary being replaced**
    - source: NarrativeState.situation_summary (models/narrative_state.py:80)
    - evidence: The prompt at engine/narrative_adjudication.py:675-685 interpolates only {context} and {action}, and to_llm_context() (models/narrative_state.py:240-266) never reads situation_summary. The "refresh" is a from-scratch rewrite off the metric block, not a rolling update — nothing carries forward from the prior summary.
- `OUT` **Action quality, the adjudicator's reasoning, and the applied metric deltas**
    - source: quality_assessment and final_effects computed earlier in the same function
    - evidence: update_situation_summary's signature (engine/narrative_adjudication.py:660-665) takes only narrative_state, action, llm_generate_fn and rng; the call sites at :794 and :898 pass nothing else. The summariser cannot know whether the decision was graded catastrophic.
- `OUT` **Advisor reactions and (actor path) international actor responses generated moments earlier**
    - source: character_responses (:782/:886), actor_responses (:847-850)
    - evidence: Neither is a parameter of update_situation_summary (:660-665) nor passed at :794/:898.
- `OUT` **Secret narrative truth (NarrativeConfig)**
    - source: WorldState.narrative (models/world.py:26)
    - evidence: world_narrative is not a parameter of update_situation_summary (engine/narrative_adjudication.py:660-665) and is not passed at :794 or :898 — even though both callers hold it. Note this also means the output is never run through _scrub_reasoning (:78-112), so unlike ADJ-1's reasoning it has no leak guard; it is safe only because the model was never shown the secret.
- `OUT` **INTERPRETATION of the decision**
    - source: agents/conversation.py:244
    - evidence: Not a parameter of update_situation_summary (engine/narrative_adjudication.py:660-665).
- `OUT` **Shared briefing dossier prefix, full transcript, world state summary, event ledger**
    - source: llm/context_builder.py:285, :74; models/narrative_state.py:88
    - evidence: The only context is to_llm_context() at engine/narrative_adjudication.py:674, which omits event_ledger entirely (models/narrative_state.py:240-266); llm.context_builder is not imported by this module (imports at :16-28).

#### What the output changes

- Overwrites NarrativeState.situation_summary in place (engine/narrative_adjudication.py:689)
- That field is DISPLAY-ONLY. It is read at models/narrative_state.py:233-234 (emergent-mode display_for_mode), cli/main.py:1110 and :1962, and cli/main_dashboard.py:1158 and :1733. A repo-wide grep finds no other non-test reader.
- It reaches NO LLM prompt anywhere in the game. models/narrative_state.py:240-266 to_llm_context() does not include it, and the inject prompt's "STORY SO FAR" block uses a different string — the deterministic digest from llm/context_builder.py:562-600 generate_summary, wired in at llm/prompts.py:393 and :404. The docstring at engine/narrative_adjudication.py:669-671 ("feeds to_llm_context() for every downstream prompt") is FALSE.
- Nothing else is mutated: no metric, trust, crisis, ledger entry or transcript line. The summary is not appended to the save transcript by cli/main.py:1884-1906 either.

#### Observed gaps

- The summariser is asked "how the crisis stands after this decision" but is shown neither the decision's assessed quality, its reasoning, nor the deltas that were applied — only the post-effect absolute metric values and the raw action text.
- It cannot see the summary it is replacing, so there is no continuity between consecutive briefs beyond what the metric block happens to encode; the ledger and transcript that would supply that continuity are both absent.
- Because the output is stored to state and shown verbatim without _scrub_reasoning, it is the one adjudication output with no leak guard — mitigated only by the secret narrative not being in its prompt.
- recent_events, one of only two narrative signals it does receive, is effectively frozen at three seed strings (models/narrative_state.py:459-463) since nothing appends injects or decisions to it.
- max_tokens=150 is silently dropped on Gemini (llm/router.py:255-262 vs llm/gemini_driver.py:106); the 2-3 sentence limit rests entirely on the instruction text at engine/narrative_adjudication.py:680-681.

#### Corrections against this block — 1

_A correction supersedes the row it concerns._

- **CORRECTED** — ADJ-1 (and ADJ-3) input "Game time string and turn number": "game_time is written once at construction (engine/game_manager.py:131, cli/main.py:783, cli/main_dashboard.py:807) and never updated, so it is a frozen date string for the whole campaign."
    - correction: The enumeration of writers is incomplete and the characterisation is wrong on one branch. Two further construction sites exist for legacy saves that carry no narrative state: cli/main.py:739 and cli/main_dashboard.py:763 both build the NarrativeState with `game_time=f"Turn {world.turn}"`. On that path the string interpolated at models/narrative_state.py:264 is "Turn 7", not a date at all, so "frozen date string" does not hold. ("Never updated after construction" does hold — no assignment to `.game_time` exists anywhere outside these five constructor calls.)
    - evidence: cli/main.py:736-739, cli/main_dashboard.py:760-763

## External

### Foreign capital's reaction to the UK decision ("International Response")

`state_actor_response`

- **Prompt built at** — engine/actor_simulation.py:24 build_actor_prompt (single f-string, engine/actor_simulation.py:32-85)
- **Dispatched at** — engine/actor_simulation.py:131 generate_group(...) -> llm/fanout.py:67 (batch path, llm_batch_fn = llm.router.batch_generate_text) or llm/fanout.py:81 (sequential path, llm.router.generate_text)
- **LLM context** — none
- **Model tier** — Driver default (no tier). engine/actor_simulation.py:131 calls generate_group with four POSITIONAL args, so fanout's context param stays None (llm/fanout.py:24-25, 60-64) and no `context` kwarg is forwarded; llm/router.py:231-234 / 331-335 then leave model_name=None and the driver picks its own default. There is no STATE_ACTOR member in LLMContext at all (llm/model_config.py:10-19), so this group is the only major call family with no per-context model selection and no entry in DEFAULT_MODEL_CONFIG (llm/model_config.py:29-38).
- **Calls per turn** — 0 when world.actor_system is unset (engine/game_manager.py:289 chooses adjudicate_with_narrative instead); otherwise len(relevant_actor_ids), hard-capped at 3 by max_actors=3 at engine/narrative_adjudication.py:838 and the sort/slice at engine/actor_simulation.py:273-274.
- **Concurrency** — Dispatched as one group of up to 3 prompts. All prompts are built first (engine/actor_simulation.py:129-130) and then handed to generate_group together, so no actor can see another actor's reply. Concurrent when llm_batch_fn is supplied (game_manager.py:301, cli/main.py:1851 both pass batch_generate_text); sequential loop otherwise (llm/fanout.py:78-85).
- **On failure** — Batch path: the live driver traps per-prompt exceptions and returns '[ERROR: ...]' in that slot, so engine/actor_simulation.py:135-136 detects the prefix and substitutes _heuristic_actor_response (:214-224). Sequential path: llm/fanout.py:82-84 catches and yields '', which the same falsy test at :135 catches. Parse exceptions -> heuristic (:140-141). A short batch result is padded with '' by llm/fanout.py:72-75 so zip cannot silently drop actors. Underneath, llm/router.py:269-279 / 382-396 already retries once and then falls back to MockDeterministicDriver. The heuristic is a fixed 'We are reviewing this development.' with trust_change 0 and will_support 'conditional', i.e. a failed call still moves alliance_cohesion by +2*weight via the conditional branch (engine/actor_simulation.py:318-320).

**Why this call exists.** After the player commits a decision, each of up to three relevant foreign governments answers it in character - a public line, a hidden private view, and whether they will back the UK.

**What it must return.** Six labelled plain-text lines: PUBLIC_RESPONSE, PRIVATE_ASSESSMENT, TRUST_CHANGE (-20..+20), WILL_SUPPORT (yes/no/conditional), CONDITIONS, INTEL_SHARED (engine/actor_simulation.py:68-80)

**Parsed at** engine/actor_simulation.py:145 _parse_actor_response; per-line startswith scan at :159-202, TRUST_CHANGE via regex r"TRUST_CHANGE:\s*([+-]?\d+)" (:157, :169-175). Only the FIRST line of each field survives - the loop is line-by-line, so a multi-line PUBLIC_RESPONSE is silently truncated to its first line (:162-163).

#### Data in — 22 reach the prompt

- `IN ` **Actor's formal country name**
    - source: StateActor.full_name (models/state_actors.py:11), loaded from data/state_actors.yaml via load_actors_from_yaml (models/state_actors.py:103-117)
    - bound: unbounded
    - evidence: engine/actor_simulation.py:33 ("You are simulating {actor.full_name}'s response"), :36, :61
- `IN ` **ISO country code**
    - source: StateActor.country_code (models/state_actors.py:10)
    - bound: unbounded
    - evidence: engine/actor_simulation.py:36
- `IN ` **Public diplomatic stance**
    - source: StateActor.official_position (models/state_actors.py:14)
    - bound: unbounded
    - evidence: engine/actor_simulation.py:37
- `IN ` **Current bilateral relationship score with the UK (0-100)**
    - source: StateActor.relationship_uk (models/state_actors.py:15); mutated every turn by StateActor.update_relationship (models/state_actors.py:55-65)
    - bound: clamped 0-100 at models/state_actors.py:58
    - evidence: engine/actor_simulation.py:38
- `IN ` **Hidden true motivations (comma-joined list)**
    - source: StateActor.true_motivations (models/state_actors.py:19-22)
    - bound: unbounded - whole list joined
    - evidence: engine/actor_simulation.py:41
- `IN ` **Hidden agendas (comma-joined list, or 'None')**
    - source: StateActor.hidden_agendas (models/state_actors.py:23-26)
    - bound: unbounded - whole list joined
    - evidence: engine/actor_simulation.py:42
- `IN ` **Threat perception 0-100**
    - source: StateActor.threat_perception (models/state_actors.py:27-30)
    - bound: pydantic ge=0 le=100
    - evidence: engine/actor_simulation.py:43
- `IN ` **Domestic political pressure 0-100**
    - source: StateActor.domestic_pressure (models/state_actors.py:31-34)
    - bound: pydantic ge=0 le=100
    - evidence: engine/actor_simulation.py:44
- `IN ` **Strategic dependencies (raw Python dict repr, e.g. {'RUS': 'natural_gas_supply'})**
    - source: StateActor.dependencies (models/state_actors.py:35-38)
    - bound: unbounded
    - evidence: engine/actor_simulation.py:45 - interpolated as the dict itself, not formatted
- `IN ` **Redlines (comma-joined list, or 'None')**
    - source: StateActor.redlines (models/state_actors.py:39-42)
    - bound: unbounded - whole list joined
    - evidence: engine/actor_simulation.py:46
- `IN ` **Military capability 0-100**
    - source: StateActor.military_capability (models/state_actors.py:45)
    - bound: pydantic ge=0 le=100
    - evidence: engine/actor_simulation.py:49
- `IN ` **Economic leverage 0-100**
    - source: StateActor.economic_leverage (models/state_actors.py:46)
    - bound: pydantic ge=0 le=100
    - evidence: engine/actor_simulation.py:50
- `IN ` **Diplomatic influence 0-100**
    - source: StateActor.diplomatic_influence (models/state_actors.py:47)
    - bound: pydantic ge=0 le=100
    - evidence: engine/actor_simulation.py:51
- `IN ` **Intelligence-sharing posture (full/selective/limited/none)**
    - source: StateActor.intelligence_sharing (models/state_actors.py:48)
    - bound: unbounded string
    - evidence: engine/actor_simulation.py:52
- `IN ` **WORLD CONTEXT block, part 1: hidden metric values with band labels (Escalation Risk + CRITICAL/HIGH/MODERATE, Alliance Cohesion + STRONG/MODERATE/WEAK, Domestic Stability + STABLE/WAVERING/FRAGILE)**
    - source: NarrativeState.hidden_metrics (models/narrative_state.py:71) rendered by NarrativeState.to_llm_context (models/narrative_state.py:240-266), assembled into world_context at engine/narrative_adjudication.py:841
    - bound: unbounded (three integers)
    - evidence: models/narrative_state.py:250-252 -> engine/narrative_adjudication.py:841 -> engine/actor_simulation.py:55 ({world_context})
- `IN ` **WORLD CONTEXT block, part 2: military and civilian casualty counts**
    - source: NarrativeState.hidden_metrics.casualties_mil / casualties_civ (models/world.py:10-11)
    - bound: unbounded
    - evidence: models/narrative_state.py:253 -> engine/actor_simulation.py:55
- `IN ` **WORLD CONTEXT block, part 3: recent dramatic events**
    - source: NarrativeState.recent_events (models/narrative_state.py:83)
    - bound: WINDOWED to the last 3 entries (models/narrative_state.py:256). The list itself is separately capped at 10 by NarrativeState.add_event (models/narrative_state.py:297-299).
    - evidence: models/narrative_state.py:256 uses self.recent_events[-3:]
- `IN ` **WORLD CONTEXT block, part 4: active crisis names**
    - source: NarrativeState.active_crises (models/narrative_state.py:94), appended by _check_and_trigger_crises (engine/narrative_adjudication.py:946-963)
    - bound: unbounded - whole list rendered
    - evidence: models/narrative_state.py:259 -> engine/actor_simulation.py:55
- `IN ` **WORLD CONTEXT block, part 5: every UK advisor's name, relationship label and trust score**
    - source: NarrativeState.characters dict of CharacterAttitude (models/narrative_state.py:36-43, 91)
    - bound: unbounded - all characters. Note this leaks internal UK advisor trust levels into a foreign government's prompt.
    - evidence: models/narrative_state.py:262 iterates self.characters.values()
- `IN ` **WORLD CONTEXT block, part 6: in-fiction clock and turn number**
    - source: NarrativeState.game_time, NarrativeState.turn (models/narrative_state.py:96-97)
    - bound: unbounded
    - evidence: models/narrative_state.py:264 -> engine/actor_simulation.py:55
- `IN ` **SECRET NARRATIVE TRUTH - global only: description, protagonist, antagonist, patsy, plus the 'never reveal / plausible deniability' instruction block**
    - source: WorldState.narrative -> NarrativeConfig.to_llm_context() (models/narrative.py:21-81), passed as world_narrative from engine/game_manager.py:300 / cli/main.py:1850
    - bound: unbounded
    - evidence: engine/narrative_adjudication.py:843-844 appends '\n\nSECRET NARRATIVE TRUTH:\n' + world_narrative.to_llm_context() to world_context, which lands at engine/actor_simulation.py:55
- `IN ` **The UK action the actor is reacting to - the player's raw decision text**
    - source: player action string; engine/game_manager.py:267 action_text -> :293 / cli/main.py:1688 action -> :1846
    - bound: UNBOUNDED - no truncation anywhere on this path
    - evidence: engine/narrative_adjudication.py:847 passes `action` as player_action -> engine/actor_simulation.py:129 -> :58 (=== UK ACTION ===) and :99/:103 fallback path

#### Available but not sent — 8

- `OUT` **Per-country FactionStance: SECRET MOTIVE, PUBLIC POSTURE, INTELLIGENCE SHARING WITH UK, ECONOMIC LEVERAGE TOOLS**
    - source: NarrativeConfig.stances[] (models/narrative.py:4-10, data/scenarios/war_game_2025/narratives.yaml:8-31)
    - evidence: engine/narrative_adjudication.py:844 calls world_narrative.to_llm_context() with NO argument, so target_country_code is None and the per-country branch at models/narrative.py:46-67 never executes. Structurally it could not work anyway: one world_context string is built once (narrative_adjudication.py:841-844) and shared by every actor prompt (actor_simulation.py:129-130).
- `OUT` **The LLM interpretation of the player's decision**
    - source: run_turn_decision output; engine/game_manager.py:270 interpretation -> :296
    - evidence: engine/narrative_adjudication.py:803 accepts `interpretation` but only forwards it to assess_action_quality at :859; the simulate_actor_responses call at :847-850 passes only (actors, action, world_context, llm_generate_fn, rng, llm_batch_fn)
- `OUT` **Full game transcript / game history**
    - source: GameManager.transcript (engine/game_manager.py:260, 501) / cli/main.py transcript
    - evidence: build_actor_prompt (engine/actor_simulation.py:24-25) takes only (actor, player_action, world_context); adjudicate_with_actor_simulation (engine/narrative_adjudication.py:799-807) has no transcript parameter. llm.context_builder.build_shared_context_prefix is never called on this path (no import of context_builder in engine/actor_simulation.py or in the actor branch of engine/narrative_adjudication.py). This is the group's biggest divergence from the advisor calls.
- `OUT` **WorldState metrics, flags, phase and the narrative world-state summary**
    - source: models/world.py:35-36; llm/prompts.py:21 build_world_state_summary
    - evidence: adjudicate_with_actor_simulation receives narrative_state, not WorldState (engine/narrative_adjudication.py:800); build_world_state_summary is never called on the actor path. The hidden-metric numbers do arrive, but via NarrativeState.to_llm_context, not via the world summary.
- `OUT` **Actor's stated public commitments**
    - source: StateActor.public_commitments (models/state_actors.py:16)
    - evidence: no occurrence of public_commitments anywhere in engine/actor_simulation.py:32-85
- `OUT` **Actor's last 3 recent actions, trust trajectory, and last-contacted turn**
    - source: StateActor.recent_actions / trust_trajectory / last_contacted_turn (models/state_actors.py:51-53)
    - evidence: none of these three names appear in build_actor_prompt (engine/actor_simulation.py:32-85). trust_trajectory is written by update_relationship (models/state_actors.py:60-65) and never read into any prompt; StateActor.add_action (models/state_actors.py:67-70) has no callers.
- `OUT` **Player-facing situation summary and the played-event ledger**
    - source: NarrativeState.situation_summary (models/narrative_state.py:80), NarrativeState.event_ledger (models/narrative_state.py:88)
    - evidence: NarrativeState.to_llm_context (models/narrative_state.py:248-265) renders neither field, and nothing else is appended to world_context (engine/narrative_adjudication.py:841-844)
- `OUT` **Other actors' replies this turn**
    - source: the sibling ActorResponse objects
    - evidence: engine/actor_simulation.py:129-130 builds all prompts before engine/actor_simulation.py:131 issues any call

#### What the output changes

- TRUST_CHANGE -> clamped to [-20,+20] (engine/actor_simulation.py:173) -> StateActorSystem.update_actor_relationship (engine/narrative_adjudication.py:851-853) -> StateActor.relationship_uk clamped 0-100 and StateActor.trust_trajectory set to improving/stable/declining (models/state_actors.py:55-65)
- TRUST_CHANGE also shifts domestic_stability +2 when >5 and -3 when <-5 (engine/actor_simulation.py:323-326)
- WILL_SUPPORT weighted by StateActor.diplomatic_influence/50 -> alliance_cohesion / escalation_risk deltas (engine/actor_simulation.py:309-320) plus a consensus bonus/penalty (:328-337)
- those actor_effects merged 60/40 with quality_effects (engine/narrative_adjudication.py:869-876) -> written into NarrativeState.hidden_metrics with clamp (engine/narrative_adjudication.py:879-883) -> copied into world.metrics (engine/game_manager.py:317-321, cli/main.py:1877-1881)
- new hidden_metrics can trip _check_and_trigger_crises, adding 'War Threshold Reached' / 'Domestic Crisis' / 'Alliance Fracturing' to active_crises and recent_events (engine/narrative_adjudication.py:895, 946-963)
- PUBLIC_RESPONSE -> word-boundary truncated to 90 chars (engine/narrative_adjudication.py:922, engine/endings.py:190-196) into the 'International Response' reasoning block (:910-925), which is displayed and written to the save transcript (cli/main.py:1886, 1903)
- PUBLIC_RESPONSE (untruncated) -> on-screen INTERNATIONAL REACTIONS panel (cli/display_utils.py:416/422); trust_change shown numerically only in classic play_mode (:411-413, :418-421)
- full ActorResponse dicts -> API field 'international_reactions' (engine/game_manager.py:348) -> api/server.py:795 and docs/py/bridge.py:1012
- DEAD OUTPUTS: private_assessment, conditions and intel_shared are parsed into ActorResponse (engine/actor_simulation.py:204-212) and read by nothing outside the model - a repo-wide grep finds no consumer, so the model's 'intelligence you choose to share' never reaches the player or any metric

#### Observed gaps

- The entire game transcript is absent. Advisors get build_shared_context_prefix with up to MAX_ADVISOR_TRANSCRIPT_CHARS = 320,000 chars of history (llm/context_builder.py:27, 285-355); foreign capitals get only NarrativeState.recent_events[-3:] (models/narrative_state.py:256). A capital reacting to turn 12 sees three event strings.
- Per-country secret motives never reach the actor prompts. narratives.yaml defines stances keyed RUS/USA/CHN/IRL (data/scenarios/war_game_2025/narratives.yaml:8,13,18,23) which exactly match StateActor.country_code values in data/state_actors.yaml (USA/FRA/DEU/POL/RUS), yet engine/narrative_adjudication.py:844 calls to_llm_context() with no country, so every actor receives only the global truth and none of its own SECRET MOTIVE.
- No LLMContext, so no model-tier control. Every other significant call family selects a model (llm/model_config.py:29-38); this one silently uses the driver default because generate_group is called positionally at engine/actor_simulation.py:131.
- The player's action is inserted raw with no interpretation and no truncation (engine/actor_simulation.py:58), while the quality assessor on the same turn does get the interpretation (engine/narrative_adjudication.py:859).
- Actor history is stateless across turns: recent_actions/trust_trajectory/last_contacted_turn exist on the model (models/state_actors.py:51-53) but are never shown, so an actor cannot recall what it said last turn - only its drifted relationship_uk number carries forward.
- identify_relevant_actors (engine/actor_simulation.py:226-276) selects by keyword match on the raw action string and can return codes not present in actor_system.actors; engine/narrative_adjudication.py:846 filters those out, so a NATO-keyword action naming USA/FRA/DEU/POL is silently reduced to whichever exist.

#### Corrections against this block — 6

_A correction supersedes the row it concerns._

- **REFUTED** — state_actor_response / affects: "DEAD OUTPUTS: private_assessment, conditions and intel_shared are parsed into ActorResponse (engine/actor_simulation.py:204-212) and read by nothing outside the model - a repo-wide grep finds no consumer"
    - correction: `conditions` HAS a consumer and is shown to the player. docs/py/bridge.py:1002 reads `result.get("international_reactions")` (the dicts produced at engine/game_manager.py:348) and lines 1014-1015 render each one: `for cond in (r.get("conditions") or []): pen.wrap(f"· {cond}", ...)` inside the INTERNATIONAL RESPONSE section. `will_support` is also consumed there (bridge.py:1008-1011, drives the ✓/○/✗ mark). Only `private_assessment` and `intel_shared` are genuinely dead — they ride along in `r.dict()` but no renderer reads them (api/server.py:795 pushes `r['public_response']` only). The map's own "affects" bullet citing docs/py/bridge.py:1012 contradicts its DEAD OUTPUTS bullet.
    - evidence: docs/py/bridge.py:1002,1014-1015
- **CORRECTED** — state_actor_response input "SECRET NARRATIVE TRUTH ... reaches_prompt: true" and diplomacy_conversation input "SECURE CONTEXT part 5: global secret narrative truth ... reaches_prompt: true", both stated unconditionally
    - correction: Both are gated on `world.narrative` being non-None, and it is None in the default game type. engine/game_manager.py:91-92: `selected_narrative = None` / `if self.mystery_mode:` — Original Story Mode leaves it None. cli/main.py:490-493: `choice = typer.prompt(..., default=1)`; choice 1 (the DEFAULT) `return None`. Downstream, engine/narrative_adjudication.py:843 `if world_narrative:` and llm/context_builder.py:501 `if world_state.narrative:` both skip the block. So in a default (non-Mystery) campaign no SECRET NARRATIVE TRUTH reaches either prompt — the actor prompt's `{world_context}` (actor_simulation.py:55) carries only NarrativeState.to_llm_context(), and the diplomat's `{secure_context}` carries only metrics + filtered transcript. The entries should read "reaches_prompt: only in Mystery Mode".
    - evidence: engine/game_manager.py:90-92; cli/main.py:493; engine/narrative_adjudication.py:843; llm/context_builder.py:501
- **CORRECTED** — state_actor_response / notable_gaps: "narratives.yaml defines stances keyed RUS/USA/CHN/IRL (data/scenarios/war_game_2025/narratives.yaml:8,13,18,23) which exactly match StateActor.country_code values in data/state_actors.yaml (USA/FRA/DEU/POL/RUS)"
    - correction: The two sets do NOT match. Stances are {RUS, USA, CHN, IRL}; state actors are {USA, FRA, DEU, POL, RUS}. Only USA and RUS intersect. CHN and IRL have stances but are not state actors at all, and FRA/DEU/POL are state actors with no stance. So even if engine/narrative_adjudication.py:844 were fixed to pass a country code, three of the five actors — including two of the three defaults chosen at engine/actor_simulation.py:264 (`["USA","FRA","POL"]`) — would still fall through the `next((s for s in self.stances if s.country_code == target_country_code), None)` lookup at models/narrative.py:47 and receive no SECRET MOTIVE. Only the format matches, not the values.
    - evidence: data/scenarios/war_game_2025/narratives.yaml:8,13,18,23 vs data/state_actors.yaml:5,36,69,99,124
- **CORRECTED** — state_actor_response / notable_gaps: identify_relevant_actors "can return codes not present in actor_system.actors; engine/narrative_adjudication.py:846 filters those out, so a NATO-keyword action naming USA/FRA/DEU/POL is silently reduced to whichever exist"
    - correction: Two errors. (a) With shipped data all four of USA/FRA/DEU/POL exist (data/state_actors.yaml:5,36,69,99), so the :846 filter removes nothing; the NATO branch's 4 codes are cut to 3 by the max_actors slice at actor_simulation.py:273-274, sorted by relationship_uk descending — a different mechanism with a different result than "whichever exist". (b) In the hypothetical the gap describes, the reduction would NOT be silent: line 274 is `sorted(relevant, key=lambda c: actor_system.actors[c].relationship_uk, ...)`, a bare dict index that raises KeyError for a missing code before narrative_adjudication.py:846 is ever reached. That exception escapes into the callers' broad try/except (engine/game_manager.py:323, cli/main.py:1907), which aborts the whole adjudication, not just that actor.
    - evidence: engine/actor_simulation.py:273-274; data/state_actors.yaml:5,36,69,99
- **CORRECTED** — state_actor_response / affects: "PUBLIC_RESPONSE -> word-boundary truncated to 90 chars ... into the 'International Response' reasoning block (:910-925), which is displayed and written to the save transcript (cli/main.py:1886, 1903)"
    - correction: cli/main.py:1903 does not write the truncated reasoning block. It is a separate, independent write of the FULL untruncated text: `adjudication_lines.append(f"{response.actor_id}: \"{response.public_response}\"")` under an "International Reactions:" header appended at :1901. Only :1886 (`reasoning`) carries the 90-char word-boundary version. The save transcript therefore contains each PUBLIC_RESPONSE twice — once truncated to 90 chars via reasoning, once in full — which the map does not state.
    - evidence: cli/main.py:1886 vs cli/main.py:1900-1903
- **CORRECTED** — state_actor_response input: "WORLD CONTEXT block, part 5: every UK advisor's name, relationship label and trust score"
    - correction: models/narrative_state.py:262 iterates `self.characters.values()` unconditionally, and the dict built by create_initial_narrative_state is not all-UK: models/narrative_state.py:404-410 seeds `usa_nsa` / "US National Security Advisor" (trust=50) alongside the four uk_* advisors. So a foreign capital's prompt is fed the US NSA's trust score as well as the UK cell's. (The related "leaks internal UK advisor trust levels" note stands and is if anything understated.)
    - evidence: models/narrative_state.py:262, 404-410

### Foreign leader/diplomat's reply on a live diplomatic call

`diplomacy_conversation_reply`

- **Prompt built at** — engine/diplomacy.py:181 build_diplomatic_conversation_prompt (f-string at engine/diplomacy.py:230-260)
- **Dispatched at** — engine/diplomacy.py:430 (DiplomaticEncounter.process_turn -> llm_generate(prompt, rng, context=LLMContext.DIPLOMACY_CONVERSATION)); llm_generate is llm.router.generate_text at engine/sim_loop.py:412, cli/main.py:1189, cli/main_dashboard.py:1211 and engine/game_manager.py:518
- **LLM context** — LLMContext.DIPLOMACY_CONVERSATION
- **Model tier** — PRO -> gemini-2.5-pro (llm/model_config.py:35, 43-44), selected via llm/router.py:231-232
- **Calls per turn** — One per player message inside an active call. CLI loop runs at most max_exchanges iterations (engine/diplomacy.py:526-528). The API/browser path (engine/game_manager.py:511-525) has NO exchange cap - DiplomaticEncounter.process_turn never counts exchanges, so a player can keep talking indefinitely.
- **Concurrency** — Alone. Strictly sequential and blocking - each reply depends on the accumulated call history.
- **On failure** — No try/except at engine/diplomacy.py:430. Protection is entirely inside llm/router.py:269-279: one retry after a 2s backoff, then MockDeterministicDriver produces a canned in-character line (llm/mock_driver.py:1241-1261 matches on 'you are roleplaying as the'). If the router itself raises, the exception propagates out of process_turn - crashing the CLI loop or surfacing as an HTTP 500 (api/server.py:454-456). Note also that engine/diplomacy.py:526 reads conversation_rules off the leader/diplomat profile dict, which never contains that key (it is top-level in data/diplomatic_profiles.yaml:319), so max_exchanges always falls back to the hardcoded 11 default.

**Why this call exists.** Lets the player hold a real back-and-forth phone call with the US President, the Kremlin, Beijing etc., with the counterpart staying in character and pushing toward a concrete ask.

**What it must return.** Free-form prose, in character. No structured fields and no length instruction.

**Parsed at** engine/diplomacy.py:431-434 - response.strip(), then appended verbatim to self.transcript as '{title}: {response}' and to self.history as (title, response). There is NO parser: whatever the model returns is shown to the player and fed back into the next prompt.

#### Data in — 15 reach the prompt

- `IN ` **Counterpart's title (e.g. 'President of the United States')**
    - source: diplomatic profile leader/diplomat dict -> counterpart_profile['title'] (engine/diplomacy.py:204), from data/diplomatic_profiles.yaml:9 etc., chosen by check_diplomatic_access (engine/diplomacy.py:137-178)
    - bound: unbounded
    - evidence: engine/diplomacy.py:230, 232, 248, 260
- `IN ` **Counterpart's personality paragraph**
    - source: counterpart_profile['personality'] (engine/diplomacy.py:205), data/diplomatic_profiles.yaml:10-14
    - bound: unbounded
    - evidence: engine/diplomacy.py:233
- `IN ` **Counterpart's tone descriptor**
    - source: counterpart_profile['tone'] (engine/diplomacy.py:206)
    - bound: unbounded
    - evidence: engine/diplomacy.py:234
- `IN ` **Counterpart's key concerns, as a bullet list**
    - source: counterpart_profile['key_concerns'] (engine/diplomacy.py:207), formatted at :225
    - bound: unbounded - all concerns rendered
    - evidence: engine/diplomacy.py:238 ({concerns_text})
- `IN ` **Country name (switchboard key: 'US', 'France', 'Russia', 'China', ...)**
    - source: DiplomaticEncounter.country (engine/diplomacy.py:352); from inject YAML at engine/sim_loop.py:398, from /call parsing at cli/main.py:1163-1178, or from normalize_country at engine/game_manager.py:490
    - bound: unbounded
    - evidence: engine/diplomacy.py:230
- `IN ` **SECURE CONTEXT part 1: current turn number**
    - source: WorldState.turn (models/world.py:22) via get_diplomatic_context
    - bound: unbounded
    - evidence: llm/context_builder.py:494 -> engine/diplomacy.py:212 -> :240 ({secure_context})
- `IN ` **SECURE CONTEXT part 2: raw UK Escalation Risk /100**
    - source: WorldState.metrics.escalation_risk (models/world.py:7)
    - bound: raw integer - note this bypasses build_world_state_summary's 'do not talk in numbers' framing
    - evidence: llm/context_builder.py:495
- `IN ` **SECURE CONTEXT part 3: raw UK Domestic Stability /100**
    - source: WorldState.metrics.domestic_stability (models/world.py:8)
    - bound: raw integer
    - evidence: llm/context_builder.py:496
- `IN ` **SECURE CONTEXT part 4: raw NATO Alliance Cohesion /100**
    - source: WorldState.metrics.alliance_cohesion (models/world.py:9)
    - bound: raw integer
    - evidence: llm/context_builder.py:497
- `IN ` **SECURE CONTEXT part 5: global secret narrative truth (GLOBAL TRUTH description, Crisis Protagonist, Primary Target, Being Used as Pawn, plus the 'never reveal / plausible deniability' instructions)**
    - source: WorldState.narrative -> NarrativeConfig.to_llm_context(target_country_code) (models/narrative.py:21-81)
    - bound: unbounded
    - evidence: llm/context_builder.py:501-503 -> engine/diplomacy.py:212 -> :240
- `IN ` **SECURE CONTEXT part 6: filtered game transcript - public events, turn headers, briefings, news, intel reports and lines matching the country, with UK COBRA deliberation lines stripped**
    - source: full_transcript passed from engine/sim_loop.py:415 / cli/main.py:1192 / cli/main_dashboard.py:1214 / engine/game_manager.py:501 -> DiplomaticEncounter.full_transcript (engine/diplomacy.py:362) -> build_diplomatic_conversation_prompt(full_transcript=...) (engine/diplomacy.py:428)
    - bound: UNBOUNDED. get_diplomatic_context applies NO character or line budget - it never calls render_transcript_block, _bound_chars or MAX_ADVISOR_TRANSCRIPT_CHARS (llm/context_builder.py:441-512 imports none of them). Filtering is the only size reduction, and the filter is loose: the '===' / 'turn ' markers at :458 latch in_public_event on for most structural lines, and the country test at :465 is a bare substring test, so country 'US' matches 'us' inside 'discuss', 'must', 'focus', 'trust' and turns on in_diplomatic_exchange for unrelated lines.
    - evidence: llm/context_builder.py:454-486 builds filtered_lines, :510 extends context_parts with all of them -> engine/diplomacy.py:212 -> :240
- `IN ` **Fallback context when no transcript is supplied: 'Turn: N' + 'Escalation: X/100'**
    - source: WorldState.turn and WorldState.metrics.escalation_risk
    - bound: n/a
    - evidence: engine/diplomacy.py:214-215 - only when full_transcript is falsy. All four production call sites pass it, so this branch fires only for direct API users and tests.
- `IN ` **This call's conversation so far - every (speaker, message) pair, including the rng-chosen opening line**
    - source: DiplomaticEncounter.history (engine/diplomacy.py:369), appended at :402 (opening), :414 (player), :434 (counterpart)
    - bound: CLI: bounded by the max_exchanges loop (engine/diplomacy.py:528), i.e. <= 1 opening + 11 player + 11 counterpart lines. API/browser: UNBOUNDED - engine/game_manager.py:511-525 calls process_turn with no counter and there is no end endpoint (api/server.py:445-456, docs/py/bridge.py:897).
    - evidence: engine/diplomacy.py:219-223 builds call_history -> :243
- `IN ` **The player's current message on the call**
    - source: typer.prompt at cli/main.py:1193 / _prompt at cli/main_dashboard.py:1214 / request.message at api/server.py:453
    - bound: UNBOUNDED - no truncation
    - evidence: engine/diplomacy.py:406 process_turn(player_message) -> :426-428 -> :245 (UK Prime Minister: {player_message})
- `IN ` **Exchange counter, rendered as 'This is exchange N of a maximum 11'**
    - source: len(conversation_history) + 1 (engine/diplomacy.py:228)
    - bound: The '11' is a hardcoded literal in the prompt string, not read from data/diplomatic_profiles.yaml:320. Because history holds two entries per exchange, the counter advances by 2 per round and reaches 11 after roughly five player turns.
    - evidence: engine/diplomacy.py:251

#### Available but not sent — 10

- `OUT` **Per-country FactionStance: SECRET MOTIVE, PUBLIC POSTURE, INTELLIGENCE SHARING WITH UK, ECONOMIC LEVERAGE TOOLS**
    - source: NarrativeConfig.stances[] (models/narrative.py:4-10), data/scenarios/war_game_2025/narratives.yaml:8-31
    - evidence: llm/context_builder.py:502 DOES request it - narrative.to_llm_context(target_country_code) - but target_country_code is the switchboard key ('US', 'France', 'Russia', 'Ukraine', 'Ireland', 'China'; engine/diplomacy.py:96-104, 111-121) while FactionStance.country_code is ISO-3 ('RUS', 'USA', 'CHN', 'IRL'; models/narrative.py:6, data/scenarios/war_game_2025/narratives.yaml:8,13,18,23). The exact-equality lookup at models/narrative.py:47 therefore never matches for any shipped country, and the branch at :49-67 never runs. Meanwhile engine/diplomacy.py:249 instructs the model to 'Act according to your SECRET MOTIVE (if provided above) at all times' - the motive is never above.
- `OUT` **The inject's diplomatic-encounter briefing text ('The US President is concerned about UK unilateral actions and wants assurances...')**
    - source: data/scenarios/war_game_2025/episodes/turn_006.yaml:32-33 -> engine/sim_loop.py:399 context -> run_diplomatic_encounter(context=...) (engine/diplomacy.py:411, :483) -> DiplomaticEncounter.__init__ context
    - evidence: engine/diplomacy.py:355 stores self.context and nothing ever reads it - grep of engine/diplomacy.py shows self.context appearing only on line 355. build_diplomatic_conversation_prompt has no context parameter (engine/diplomacy.py:181-188). The same is true of engine/game_manager.py:499's 'Player initiated call'. The one authored piece of scenario setup for the mandatory US call is dead.
- `OUT` **Profile-authored LLM instructions and per-country outcome guidance (including the Russia/Ireland/Poland/US/China special cases)**
    - source: data/diplomatic_profiles.yaml:322-337 conversation_rules.llm_instructions and :338-355 outcome_assessment
    - evidence: Neither key is read anywhere in engine/diplomacy.py - the only profiles lookups are countries (:154), leader/diplomat (:164, :171), title/personality/tone/key_concerns (:204-207), opening_lines (:394) and conversation_rules (:526, on the wrong dict - see below). The equivalent guidance is hardcoded at engine/diplomacy.py:251-258.
- `OUT` **Country full_name from the diplomatic profile ('United States of America')**
    - source: data/diplomatic_profiles.yaml:6
    - evidence: engine/diplomacy.py:204-207 reads only title/personality/tone/key_concerns from counterpart_profile, and full_name sits one level up on the country dict which build_diplomatic_conversation_prompt never receives
- `OUT` **Access level ('leader' vs 'diplomat')**
    - source: check_diplomatic_access return (engine/diplomacy.py:365)
    - evidence: self.access_level is set at engine/diplomacy.py:365 and never read again in the file; only the title implies it
- `OUT` **Casualty counts, world flags, posture, recent injects, spatial state**
    - source: WorldState.metrics.casualties_mil/civ (models/world.py:10-11), WorldState.flags (:36), posture (:37), spatial_state (:40), recent_injects (:52)
    - evidence: get_diplomatic_context renders only turn + three metrics (llm/context_builder.py:494-497); build_world_state_summary - which does render casualties and flags (llm/prompts.py:64-71) - is not called on the conversation path
- `OUT` **Bilateral relationship scores**
    - source: WorldState.diplomatic_relationships (models/world.py:58) and StateActor.relationship_uk (models/state_actors.py:15)
    - evidence: WorldState.diplomatic_relationships is declared at models/world.py:58 and is read or written NOWHERE in the codebase (repo-wide grep returns only the declaration). The actor system's relationship_uk lives in world.actor_system and is never consulted by engine/diplomacy.py - the two foreign-power systems are entirely disconnected: an actor whose trust the player has just wrecked in adjudication answers the phone with no memory of it.
- `OUT` **NarrativeState (hidden metrics, situation_summary, event_ledger, character attitudes)**
    - source: engine/game_manager.py:555 narrative_state
    - evidence: DiplomaticEncounter takes a WorldState only (engine/diplomacy.py:350); no narrative_state parameter exists on any function in engine/diplomacy.py
- `OUT` **The shared briefing dossier prefix used by advisor/decision prompts**
    - source: llm/context_builder.py:285 build_shared_context_prefix
    - evidence: engine/diplomacy.py:202 imports get_diplomatic_context only; build_shared_context_prefix has no diplomacy caller. So the prompt-cache-friendly stable prefix, the event ledger and the 320k-char history window all bypass diplomacy entirely.
- `OUT` **UK COBRA internal deliberations**
    - source: transcript lines beginning 'Prime Minister:', 'National Security Advisor:', etc.
    - evidence: DELIBERATELY excluded by the in_cobra_deliberation filter at llm/context_builder.py:470-484. Note the exclusion is imperfect in the other direction: the state latches, so a COBRA line only re-enables output when a later line re-matches a public-event or country marker.

#### What the output changes

- Appends the counterpart's line to DiplomaticEncounter.transcript (engine/diplomacy.py:433), which is returned to the CLI printer (engine/diplomacy.py:543-546) and to the API/browser as 'transcript' (engine/game_manager.py:522)
- Appends to DiplomaticEncounter.history (engine/diplomacy.py:434), which becomes the CONVERSATION SO FAR block of the next reply prompt (:219-223) and the whole input to the outcome-assessment call (:287-289)
- The encounter transcript is merged into the campaign transcript (engine/sim_loop.py:420, cli/main.py:1201, cli/main_dashboard.py:1220), so it later feeds get_diplomatic_context on subsequent calls and the advisor history window
- No metric is changed by this call - all metric movement comes from the separate outcome call

#### Observed gaps

- The prompt commands 'Act according to your SECRET MOTIVE (if provided above) at all times' (engine/diplomacy.py:249) but the country-code mismatch means no secret motive is ever provided - the counterpart only ever has the global narrative truth. This is the single most consequential gap in the group.
- The filtered transcript is the only unbounded transcript in the codebase. Advisors are windowed to 320,000 chars (llm/context_builder.py:27) and inject generation to 400 lines (:61); get_diplomatic_context has no cap at all (:441-512), so a late-campaign call ships an ever-growing block to a PRO model.
- The mandatory-encounter briefing authored in the scenario YAML is loaded, threaded through three function signatures, and dropped on the floor (engine/diplomacy.py:355).
- No casualty figures reach the counterpart, so a foreign leader cannot react to British or civilian dead.
- The counterpart has no memory of previous calls except whatever the loose transcript filter happens to keep, and no access to the actor system's relationship_uk trust score that the same countries carry in adjudication.

### End-of-call scoring: did the PM's phone call help or hurt?

`diplomacy_outcome_assessment`

- **Prompt built at** — engine/diplomacy.py:265 assess_diplomatic_outcome (f-string at engine/diplomacy.py:293-314)
- **Dispatched at** — engine/diplomacy.py:316 llm_generate(prompt, rng, context=LLMContext.DIPLOMACY_OUTCOME), reached from DiplomaticEncounter.end (engine/diplomacy.py:455)
- **LLM context** — LLMContext.DIPLOMACY_OUTCOME
- **Model tier** — PRO -> gemini-2.5-pro (llm/model_config.py:36, 43-44)
- **Calls per turn** — At most one per completed diplomatic call. Fires when the CLI exchange loop exits (engine/diplomacy.py:549-550) or when the player types an explicit closer - '/end', 'end', 'goodbye', 'thank you', 'that will be all', 'end call' (engine/diplomacy.py:419-423). In the API/browser path there is no end endpoint, so if the player never types a closer this call NEVER fires and the encounter's cohesion delta is never applied.
- **Concurrency** — Alone, blocking, once at hang-up.
- **On failure** — No try/except around the dispatch at engine/diplomacy.py:316 - llm/router.py:269-279 retries once then falls back to MockDeterministicDriver, which emits 'ALLIANCE_COHESION_DELTA: 0' (llm/mock_driver.py:1261). If the router still raises, the exception escapes end() and therefore escapes process_turn/run_diplomatic_encounter. Parse failure is silent and safe: OUTCOME stays 'NEUTRAL', delta 0, summary 'The conversation concluded.' (engine/diplomacy.py:319-321), so an unparseable reply produces a no-op call. Because end() sets self.active = False before the LLM call (:452), a raised exception still leaves the encounter closed but with self.outcome None and no delta applied.

**Why this call exists.** Judges the finished diplomatic call and converts it into an alliance-cohesion swing plus a two-or-three sentence verdict the player reads as the line goes dead.

**What it must return.** Three labelled lines: OUTCOME: [SUCCESS/NEUTRAL/FAILURE], ALLIANCE_COHESION_DELTA: [-15..+15], SUMMARY: [2-3 sentences] (engine/diplomacy.py:310-312)

**Parsed at** engine/diplomacy.py:323-338 - line-prefix scan with str.replace. Delta parsed by stripping '+' and spaces then int(), clamped to [-15,15] at :333; ValueError -> 0 (:334-335). SUMMARY is single-line only, so a multi-line summary is truncated to its first line (:336-337).

#### Data in — 10 reach the prompt

- `IN ` **Narrative world-state summary header: turn number and phase**
    - source: WorldState.turn, WorldState.phase (models/world.py:22-23) via build_world_state_summary
    - bound: unbounded
    - evidence: llm/prompts.py:58 -> engine/diplomacy.py:291 world_summary -> :296 ({world_summary})
- `IN ` **Escalation risk as a band word only (low/moderate/high/critical)**
    - source: WorldState.metrics.escalation_risk (models/world.py:7)
    - bound: BUCKETED to 4 bands at llm/prompts.py:34-39 (<30 / <60 / <80 / else) - the raw number does not reach this prompt, unlike the conversation prompt which sends it raw
    - evidence: llm/prompts.py:34-39 computes escalation_desc, :60 renders 'THREAT ASSESSMENT: {UPPER} risk of further Russian escalation' -> engine/diplomacy.py:296
- `IN ` **Domestic stability as a band word (stable/uncertain/fragile/in crisis)**
    - source: WorldState.metrics.domestic_stability (models/world.py:8)
    - bound: BUCKETED to 4 bands (>70 / >40 / >20 / else)
    - evidence: llm/prompts.py:41-46, :61 -> engine/diplomacy.py:296
- `IN ` **Alliance cohesion as a band phrase (strong and unified / uncertain / fragile / fractured)**
    - source: WorldState.metrics.alliance_cohesion (models/world.py:9)
    - bound: BUCKETED to 4 bands (>70 / >40 / >20 / else)
    - evidence: llm/prompts.py:48-53, :62 -> engine/diplomacy.py:296
- `IN ` **Military and civilian casualty counts**
    - source: WorldState.metrics.casualties_mil / casualties_civ (models/world.py:10-11)
    - bound: unbounded (raw integers)
    - evidence: llm/prompts.py:64 -> engine/diplomacy.py:296
- `IN ` **Active world flags, title-cased, as 'KEY INTELLIGENCE FLAGS'**
    - source: WorldState.flags (models/world.py:36), maintained by engine.flags.update_world_flags
    - bound: unbounded - all truthy flags
    - evidence: llm/prompts.py:67-71 -> engine/diplomacy.py:296
- `IN ` **Anti-metagaming instruction block ('You are a real advisor in COBRA... Do NOT reference metrics/game mechanics/scores')**
    - source: hardcoded in build_world_state_summary
    - bound: constant
    - evidence: llm/prompts.py:73-77 -> engine/diplomacy.py:296. Slightly incongruous here: the assessor is then explicitly asked for a numeric ALLIANCE_COHESION_DELTA at :311.
- `IN ` **Country name (switchboard key)**
    - source: DiplomaticEncounter.country (engine/diplomacy.py:352) passed at :456
    - bound: unbounded
    - evidence: engine/diplomacy.py:298 (=== DIPLOMATIC CONVERSATION WITH {country} ===)
- `IN ` **The complete call transcript - every (speaker, message) pair including the rng-chosen opening line, the PM's lines, and the counterpart's replies**
    - source: DiplomaticEncounter.history (engine/diplomacy.py:369), passed as conversation_history at :456-457
    - bound: NO explicit truncation. CLI: implicitly bounded by the 11-iteration loop (engine/diplomacy.py:528) to ~23 lines. API/browser: UNBOUNDED, since process_turn imposes no cap (engine/diplomacy.py:406-436).
    - evidence: engine/diplomacy.py:287-289 joins it into conversation_text -> :299
- `IN ` **The four assessment criteria and the OUTCOME/ALLIANCE_COHESION_DELTA/SUMMARY output contract**
    - source: hardcoded in engine/diplomacy.py:301-314
    - bound: constant
    - evidence: engine/diplomacy.py:301-313

#### Available but not sent — 4

- `OUT` **Secret narrative truth (global or per-country)**
    - source: WorldState.narrative -> NarrativeConfig.to_llm_context (models/narrative.py:21-81)
    - evidence: assess_diplomatic_outcome (engine/diplomacy.py:265-314) imports only build_world_state_summary (:284) and never touches world.narrative. So the assessor judges a Mystery-mode call with no idea what the counterpart was secretly trying to achieve - the one call in the game whose score depends most on hidden intent.
- `OUT` **Counterpart profile: title, personality, tone, key concerns; the profile's own per-country outcome guidance**
    - source: data/diplomatic_profiles.yaml:9-42 and :338-355 conversation_rules.outcome_assessment
    - evidence: engine/diplomacy.py:265-271 takes (world, country, conversation_history, llm_generate, rng) - no profile parameter. The YAML's explicit scoring rules ('Russia: conversations always tense; avoiding escalation is success', 'China: volunteering British intelligence to them is a loss') at data/diplomatic_profiles.yaml:348-355 are never read by anything.
- `OUT` **The wider game transcript**
    - source: DiplomaticEncounter.full_transcript (engine/diplomacy.py:362)
    - evidence: self.full_transcript is used only at engine/diplomacy.py:428 for the conversation prompt; the end() call at :455-457 passes only self.history. The assessor sees the phone call in isolation, with no knowledge of what the UK did that turn.
- `OUT` **Access level, the inject's encounter context, and whether the call was mandatory**
    - source: engine/diplomacy.py:365 access_level, :355 self.context, :482 required
    - evidence: None of the three is passed to assess_diplomatic_outcome (engine/diplomacy.py:455-457); `required` is never read anywhere in run_diplomatic_encounter's body

#### What the output changes

- ALLIANCE_COHESION_DELTA -> world.metrics.alliance_cohesion, clamped 0-100 (engine/diplomacy.py:474). This is the only place a diplomatic call moves world state.
- -> DiplomaticEncounter.outcome dict {'assessment', 'cohesion_delta'} (engine/diplomacy.py:459-462), returned to the API/browser as 'outcome' (engine/game_manager.py:524) and as the second return value of run_diplomatic_encounter (:558)
- -> closing transcript block (engine/diplomacy.py:466-471): classic mode appends 'Alliance Cohesion: {delta:+d}'; immersive/emergent instead get the number-free _relationship_reading(title, delta) line (engine/diplomacy.py:76-93, thresholds >=8 / >=3 / >0 / ==0 / >-5 / else). show_metrics is set from play_mode=='classic' at cli/main.py:1197 and engine/game_manager.py:502; engine/sim_loop.py:407-418 and cli/main_dashboard.py:1206-1217 do NOT pass show_metrics, so mandatory encounters and the dashboard CLI always print the raw number regardless of play mode (default True at engine/diplomacy.py:352, :491).
- OUTCOME and SUMMARY -> the assessment string (engine/diplomacy.py:340) which is printed and appended to the campaign transcript (engine/sim_loop.py:420, cli/main.py:1201). The OUTCOME token itself drives nothing mechanical - only the delta moves state.
- After the call, callers re-clamp and refresh flags without re-applying the delta (engine/sim_loop.py:425-426, cli/main.py:1208-1209, cli/main_dashboard.py:1227-1228), and the CLI paths resync narrative_state.hidden_metrics.alliance_cohesion from world.metrics (cli/main.py:1212, cli/main_dashboard.py:1231). engine/game_manager.py has no such resync, so in the API/browser path a diplomatic delta lands on world.metrics and is then overwritten at the next adjudication when narrative_state.hidden_metrics is copied back over world.metrics (engine/game_manager.py:317-321).

#### Observed gaps

- The assessor never sees the secret narrative truth, so it cannot tell a call where the counterpart was manipulating the PM from one where they were levelling.
- data/diplomatic_profiles.yaml:338-355 contains hand-authored per-country scoring rules that no code reads - the model reconstructs them from scratch, or does not.
- The call is judged with no knowledge of the UK decision that prompted it: full_transcript is deliberately withheld here even though the encounter object holds it.
- In the API/browser path the outcome call only fires on an explicit closer string (engine/diplomacy.py:419-423); abandoning a call means the cohesion delta is never assessed or applied.

## State reachability

34 of 41 audited state fields reach no prompt at all.

### Reaches no prompt — 34

- **WorldState (models/world.py:40) · spatial_state**
    - consequence: The game has no notion of where units physically are. Advisors cannot be asked 'where is HMS Montrose' and the inject generator cannot place an event at a location the player actually holds forces at.
    - evidence: models/world.py:40 is the ONLY occurrence of the identifier in the entire repo (grep across llm/, agents/, engine/, models/, cli/, api/ returns one hit, the declaration). Nothing writes it, nothing reads it.
- **WorldState (models/world.py:58) · diplomatic_relationships**
    - consequence: Dead duplicate of actor relationship state; harmless but it is persisted in every save (engine/persistence.py:64 world.model_dump()) and reads like live state to anyone editing the model.
    - evidence: models/world.py:58 is the only occurrence repo-wide. Bilateral relationship is tracked instead on StateActor.relationship_uk (models/state_actors.py:15), which is updated at engine/narrative_adjudication.py:853.
- **WorldState (models/world.py:37) · posture**
    - consequence: red_intent / tempo were clearly meant to steer the adversary. Nothing in any prompt tells the model how aggressive Russia currently is other than the escalation_risk number.
    - evidence: Set to {} at engine/game_manager.py:114, cli/main.py:764, cli/main_dashboard.py:788. The only non-empty assignment is the legacy demo engine/sim_loop.py:714 (run_single_scene, docstring marks it Deprecated). No read site anywhere; engine/intelligence.py mentions 'posture' only in prose/comments (lines 23, 47, 182-208), never world.posture.
- **WorldState (models/world.py:46) · discussion_transcript**
    - consequence: Field is pure write-and-clear bookkeeping. It is not the vehicle by which discussion reaches prompts, contrary to its docstring.
    - evidence: Written at engine/sim_loop.py:488 (world.discussion_transcript.extend(transcript)); cleared at engine/sim_loop.py:694, engine/game_manager.py:341, cli/main.py:1977, cli/main_dashboard.py:1742. No read site. The same lines separately reach prompts only because callers also append them to the full transcript list.
- **WorldState (models/world.py:32) · difficulty**
    - consequence: The inject generator writes the same events on 'standard' and 'brutal'; difficulty is a post-hoc multiplier on numbers, never a narrative instruction.
    - evidence: Only read at engine/sim_loop.py:196 (difficulty_multipliers.get(world.difficulty, 0.5)) to scale scripted inject deltas. Not interpolated anywhere in llm/prompts.py or llm/context_builder.py.
- **WorldState (models/world.py:29) · scene**
    - consequence: None beyond the legacy duplication the field's own comment admits.
    - evidence: Read only at engine/events.py:38 (scene_eq == world.scene) for scripted inject matching; kept in sync at engine/game_manager.py:340, cli/main.py:1976, cli/main_dashboard.py:1741. world.turn is what reaches prompts (llm/context_builder.py:336).
- **NarrativeState (models/narrative_state.py:80) · situation_summary**
    - consequence: The single most expensive orphan: the game spends one LLM call per turn writing a rolling narrative summary and then shows it only to the player. On the parked campaign it is a 400-char paragraph naming the mole investigation and the intelligence-sharing decision - exactly the continuity the inject generator lacks. What the generator gets instead is the digest, which on this save reads 'Turns played: 17', 'Transcript length: 1853 lines' and the SAME narrator line repeated three times ('The hours tick by with agonizing slowness...'), because generate_summary's event filter at line 583 matches '[Narrator]' lines.
    - evidence: Written at engine/narrative_adjudication.py:689 (LLM path) and :729 (deterministic fallback) every single turn via update_situation_summary, called from adjudicate_with_narrative:794 and adjudicate_with_actor_simulation:898. Every read is display: models/narrative_state.py:234, cli/main.py:1110 and :1962, cli/main_dashboard.py:1158 and :1733. It is NOT in NarrativeState.to_llm_context() (models/narrative_state.py:240-266). The 'STORY SO FAR (HIGH-LEVEL SUMMARY)' block in the inject prompt (llm/context_builder.py:422-424) is fed by llm/prompts.py:393 summary = generate_summary(transcript, ...), i.e. llm/context_builder.py:562-600, a mechanical digest that deletes its summary_prompt argument at line 570.
- **NarrativeState (models/narrative_state.py:75) · previous_metrics**
    - consequence: No prompt ever learns the DIRECTION of travel. An advisor is told 'Escalation Risk: 82/100' whether it just jumped from 45 or has been falling from 95 all game.
    - evidence: Only consumer is calculate_vibe at models/narrative_state.py:173-174, which produces the rising/falling/stable arrow for the immersive display. to_llm_context (lines 248-265) prints absolute metric values only.
- **NarrativeState (models/narrative_state.py:101) · play_mode**
    - consequence: Expected - it is a presentation setting.
    - evidence: Read at models/narrative_state.py:209 (display_for_mode) and throughout cli/ for display routing (e.g. cli/main.py:1090-1107, cli/display_utils.py:324/341). Absent from to_llm_context.
- **CharacterAttitude (models/narrative_state.py:42) · characters[*].last_interaction**
    - consequence: No prompt can say 'you have not spoken to the Home Secretary since turn 4'.
    - evidence: models/narrative_state.py:42 is the only occurrence repo-wide. Never assigned (update_character_attitude at :270-292 does not touch it), never read. Confirmed null for all five characters in saves/parked_campaign4_borrowed_faces.json after 17 turns.
- **CharacterAttitude (models/narrative_state.py:37) · characters[*].character_id**
    - consequence: None.
    - evidence: Used only as a dict key / selector (models/narrative_state.py:276, engine/narrative_adjudication.py:941-943). build_character_response_prompt interpolates character.name, .relationship, .trust, .stance_summary (engine/narrative_adjudication.py:623-625) and to_llm_context interpolates .name/.relationship/.trust (models/narrative_state.py:262).
- **StateActorSystem (models/state_actors.py:90) · turn**
    - consequence: Permanently 1 in every save; the actor subsystem has no clock of its own.
    - evidence: models/state_actors.py:90 is the only occurrence; grep for 'actor_system.turn' across llm/, agents/, engine/, models/, cli/, api/ returns nothing. Never incremented, never read.
- **StateActor (models/state_actors.py:16) · public_commitments**
    - consequence: An actor cannot be held to a promise it made. Nothing in the prompt says 'you publicly committed to Article 5 enforcement last turn'.
    - evidence: models/state_actors.py:16 is the only occurrence repo-wide. build_actor_prompt (engine/actor_simulation.py:32-85) interpolates official_position, relationship_uk, true_motivations, hidden_agendas, threat_perception, domestic_pressure, dependencies, redlines, military_capability, economic_leverage, diplomatic_influence, intelligence_sharing - not this.
- **StateActor (models/state_actors.py:51) · recent_actions**
    - consequence: Each actor answers every turn with no memory of its own previous answers; the 'BEHAVIORAL TRACKING' section of the model is inert.
    - evidence: Read only for the player-facing intel panel at engine/intelligence.py:316-319. Its writer, StateActor.add_action (models/state_actors.py:67-70), has ZERO callers anywhere in the repo - so it is always empty even for that panel.
- **StateActor (models/state_actors.py:52) · trust_trajectory**
    - consequence: France is told its relationship score is 44/100 but never that it has fallen 30 points in two turns, so it cannot react to the trend.
    - evidence: Written by update_relationship (models/state_actors.py:60-65), called from engine/narrative_adjudication.py:853. Read only at engine/intelligence.py:294 for the display panel. Not in build_actor_prompt.
- **StateActor (models/state_actors.py:53) · last_contacted_turn**
    - consequence: No prompt can express diplomatic neglect.
    - evidence: models/state_actors.py:53 is the only occurrence repo-wide. Never written by engine/diplomacy.py or anything else.
- **ActorResponse (models/state_actors.py:83) · action_taken**
    - consequence: Actors can say things but the model has no slot for what they DO, so nothing an ally does is ever fed back into the world.
    - evidence: _parse_actor_response (engine/actor_simulation.py:204-212) constructs ActorResponse without it, and build_actor_prompt's response format (engine/actor_simulation.py:70-80) never asks for it. _heuristic_actor_response (:216-224) likewise omits it.
- **parsed initial_conditions (data/scenarios/war_game_2025/initial_conditions.yaml) · initial_flags**
    - consequence: us_commitment: uncertain, f35_pilots_murdered: true, severomorsk_attack_false_flag: true, public_awareness - the scenario's entire opening factual state - never reaches a model. The only flags an advisor ever sees (llm/prompts.py:67-71) are the five derived-from-metrics booleans in engine/flags.py:15-35, which carry zero information the metric lines above them do not already carry.
    - evidence: grep for "initial_flags" across engine/, cli/, api/, llm/, agents/ returns nothing. WorldState is built with flags={} (engine/game_manager.py:114, cli/main.py:764, cli/main_dashboard.py:788) and world.flags is then wholly REPLACED by compute_risk_flags(metrics) at engine/flags.py:41.
- **parsed initial_conditions · intelligence**
    - consequence: severomorsk_attribution, pilot_murders, cyber_attacks and russian_naval_deployment - the scenario's assessed intelligence picture - are invisible to the NSA advisor whose knowledge domain is literally 'intelligence'.
    - evidence: grep for "intelligence" as a dict key ('intelligence' / "intelligence") across llm/, agents/, engine/, models/, cli/, api/ returns no read of initial_conditions['intelligence']. engine/initial_conditions.py only exposes characters, constraints, uk_forces, stockpiles (lines 58, 91, 103, 115).
- **parsed initial_conditions · intelligence_summary (uk_knows / russia_knows)**
    - consequence: The explicit information-asymmetry table - what each side knows - never reaches the actor prompts or the inject generator, so fog of war is not modelled at all.
    - evidence: Zero occurrences of 'intelligence_summary' anywhere in llm/, agents/, engine/, models/, cli/, api/.
- **parsed initial_conditions · red_forces**
    - consequence: The inject generator is told Russia's goals but not its order of battle, so generated events are unconstrained by what Russia actually has (active_operation, 7 naval entries).
    - evidence: Zero occurrences of 'red_forces' in llm/, agents/, engine/, models/, cli/, api/. Only red_objectives is read (llm/prompts.py:363 -> interpolated at :434).
- **parsed initial_conditions · locations**
    - consequence: Combined with the dead WorldState.spatial_state, geography exists nowhere in the prompt layer. The 8 UK sites, 3 operational areas and 1 Russian location are unused.
    - evidence: Zero occurrences of 'locations' as an initial_conditions key in llm/, agents/, engine/, models/, cli/, api/.
- **parsed initial_conditions · critical_infrastructure**
    - consequence: status, recent_attacks, attacks_count never reach the Home Secretary's prompt despite 'infrastructure' being one of her routing keywords (agents/conversation.py:187).
    - evidence: Zero occurrences in llm/, agents/, engine/, models/, cli/, api/.
- **parsed initial_conditions · environment**
    - consequence: public_mood, media_coverage, economic_impact, weather are unused - note build_narrator_intro_prompt (llm/prompts.py:602) explicitly asks the model to invent 'weather' while the scenario ships a weather field.
    - evidence: Zero occurrences in llm/, agents/, engine/, models/, cli/, api/.
- **parsed initial_conditions · timeline**
    - consequence: The 5-entry chronology that establishes how the crisis started is not in any prompt; models must reconstruct it from the transcript, which is exactly the part that gets elided.
    - evidence: The only 'timeline' hits are unrelated: engine/game_manager.py:228 (a hardcoded 'Immediate' placeholder in a response dict) and cli/display_utils.py:169-258 (parsing the word 'TIMELINE' out of an LLM interpretation).
- **parsed initial_conditions · objectives['russia']**
    - consequence: Duplicated-but-different content: red_objectives (a separate top-level key) does reach the inject prompt at llm/prompts.py:434, so the Russian goals that DO reach a prompt are the ones in red_objectives, and objectives.russia silently diverges.
    - evidence: llm/prompts.py:362 reads the whole objectives dict but line 431 interpolates only objectives.get('uk', {}). objectives['russia'] is never referenced.
- **parsed initial_conditions · metadata.title / .scenario / .description / .start_date**
    - consequence: The scenario's own 121-char description is never given to any model; every prompt hardcodes 'UK-Russia crisis wargame' framing instead (e.g. llm/prompts.py:426, llm/context_builder.py:311).
    - evidence: Only metadata.start_time is read: engine/game_manager.py:131, cli/main.py:783, cli/main_dashboard.py:807 -> NarrativeState.game_time -> models/narrative_state.py:264. The other four subkeys have no reader.
- **parsed initial_conditions · game_state (turn / phase)**
    - consequence: A scenario cannot start mid-crisis at turn 3.
    - evidence: No reader. WorldState is constructed with turn=1, phase='briefing' hardcoded (engine/game_manager.py:103, :115).
- **parsed initial_conditions · characters[*].influence**
    - consequence: All advisors carry equal weight in the prompt layer regardless of the scenario's stated influence ranking.
    - evidence: build_advisor_context reads role/knowledge_domains/key_concerns only (llm/prompts.py:106-108); build_pushback_prompt reads role/pushback_triggers (llm/prompts.py:269-271); build_critical_omissions_prompt reads role (llm/prompts.py:490). 'influence' has no reader anywhere.
- **parsed initial_conditions · characters.president_russia / chief_general_staff / head_military_intelligence / commander_northern_fleet (and their .objectives)**
    - consequence: Four fully-specified adversary personas with per-character objectives exist in the data and are shown to no model. Russia is roleplayed only as the generic StateActor 'RUS' - and only when identify_relevant_actors happens to pick it.
    - evidence: get_all_uk_advisors excludes any character carrying a 'note' key (engine/initial_conditions.py:76), and build_pushback_prompt applies the identical filter inline (llm/prompts.py:268 'if isinstance(char_data, dict) and "note" not in char_data'). No other prompt builder indexes characters by these ids.
- **llm/prompts.py:491, build_critical_omissions_prompt · personality (local variable)**
    - consequence: Dead read; the five omissions prompts differ from one another only by role name and the five conditional bullet lines at :532-536.
    - evidence: llm/prompts.py:491 personality = character.get("personality", "Professional and direct") is assigned and then never appears in the f-string at lines 501-553 (which interpolates build_shared_context_prefix, role, recent_context, player_decision, role.upper() and character_id). The key does not exist in the scenario data either - every character in data/scenarios/war_game_2025/initial_conditions.yaml has keys ['role','influence','knowledge_domains','pushback_triggers','key_concerns'].
- **data/scenarios/war_game_2025/scenario_library.yaml (loaded llm/inject_generator.py:21-33) · scenario_library: cyber_scenarios, military_target_scenarios, civilian_target_scenarios, covert_operation_scenarios, uk_response_scenarios, public_reaction_scenarios, crisis_timeline, themes, llm_guidance, metadata**
    - consequence: Two thirds of the mined scenario library is invisible to the generator, which is one reason the same naval set-piece keeps returning (the very bug issue #25 chased). Note llm_guidance - whose subkeys are literally adaptation_principles, maintain_tension and avoid - is guidance written FOR the LLM that no LLM ever sees.
    - evidence: llm/prompts.py:368-370 pools ONLY naval_scenarios + infrastructure_scenarios + diplomatic_scenarios (9 entries of 26), and llm/prompts.py:376-377 interpolates only escalation_patterns.russian_strategy and escalation_patterns.uk_constraints. The remaining 17 scenario entries and the four other top-level keys are never touched.
- **parsed initial_conditions · diplomatic_contacts**
    - consequence: Menu data only; acceptable.
    - evidence: Single reader at engine/game_manager.py:663 (contacts = self.initial_conditions.get('diplomatic_contacts', [])), which builds a menu list. Not in any prompt builder.
- **llm/model_config.py:19 · LLMContext.CHARACTER_RESPONSE**
    - consequence: Quality assessment, character reactions, situation summary and all actor roleplay silently run on the driver's default model rather than the configured tier; the per-context model table is half decorative.
    - evidence: Declared at llm/model_config.py:19 with a tier at :37. Every LLM call in the adjudication path omits context=: engine/narrative_adjudication.py:269 llm_generate_fn(prompt, rng, max_tokens=400), :687 llm_generate_fn(prompt, rng, max_tokens=150), :545 generate_group(..., max_tokens=CHARACTER_RESPONSE_MAX_TOKENS) with no context kwarg, engine/actor_simulation.py:99 llm_generate_fn(prompt, rng), :131 generate_group(prompts, llm_generate_fn, rng, llm_batch_fn) - no context. With context=None, llm/router.py:233-234 sets model_name=None and the driver default is used.

### Reaches at least one prompt — 7

- **NarrativeState (models/narrative_state.py:88) · event_ledger**
    - reaches: build_inject_generation_prompt ONLY (llm/prompts.py:334-459). See ledger_reach for the full trace.
    - note: See ledger_reach.consequence. Additionally: saves/parked_campaign4_borrowed_faces.json has NO event_ledger key at all (written before the field existed); engine/persistence.py:134 NarrativeState(**dict) therefore defaults it to [], so resuming that 17-turn campaign hands the generator an empty ledger.
- **NarrativeState (models/narrative_state.py:83) · recent_events**
    - reaches: assess_action_quality, build_character_response_prompt, update_situation_summary, build_actor_prompt - all via NarrativeState.to_llm_context()
    - note: Nothing that actually happens in the story is ever added. After 17 turns the parked save holds only the three seed strings from models/narrative_state.py:459-463 plus two crisis markers, so the last-3 window that every adjudication prompt reads is ['Russian families departing UK en masse', 'Crisis: Situation at war threshold', 'Crisis: Public order deteriorating'] - stale from turn 1, while the campaign has since sunk HMS Montrose.
- **CharacterAttitude (models/narrative_state.py:40-43) · characters[*].trust / .relationship / .stance_summary**
    - reaches: to_llm_context (models/narrative_state.py:262 - name/relationship/trust) and build_character_response_prompt (engine/narrative_adjudication.py:623-625 - name/relationship/trust/stance_summary)
    - note: In every real campaign these three fields are frozen at their setup values from models/narrative_state.py:404-438 and still interpolated into every adjudication prompt. Verified in the parked save after 17 turns: trust 50/75/70/80/85, relationship neutral/allied/allied/allied/allied, stance_summary verbatim from the constructor. The models are being told the Foreign Secretary is 'Loyal but concerned about alliance unity' at turn 18 of a shooting war.
- **StateActorSystem (models/state_actors.py:89) · actors**
    - reaches: build_actor_prompt only (engine/actor_simulation.py:32-85)
    - note: Russia (RUS is in data/state_actors.yaml - confirmed in the parked save's actor list) is only prompted when the keyword heuristic at engine/actor_simulation.py:242-264 happens to select it; the default fallback list at line 264 is ['USA','FRA','POL'], so the adversary usually never speaks.
- **WorldState (models/world.py:52) · WorldState.recent_injects**
    - reaches: build_critical_omissions_prompt ONLY
    - note: Inject titles reach exactly one of the ~15 calls in a turn. The advisor Q&A, decision-interpretation, pushback, narrator, diplomacy and inject prompts get no title list at all.
- **WorldState (models/world.py:36) · WorldState.flags**
    - reaches: every prompt that opens with build_shared_context_prefix (advisor Q&A, decision interpretation, pushback, critical omissions), plus narrator bridge and diplomacy-outcome assessment; and the inject prompt only on the empty-transcript path
    - note: Carries no independent information: engine/flags.py:41 update_world_flags REPLACES world.flags wholesale with compute_risk_flags(metrics), five booleans thresholded off the same numbers printed three lines above (llm/context_builder.py:337-341). The scenario's initial_flags are never merged in.
- **NarrativeConfig.stances (models/narrative.py:19) · WorldState.narrative (per-country FactionStance)**
    - reaches: the diplomatic conversation prompt ONLY
    - note: The actor-simulation prompt - the one place a country is actually roleplayed - gets only the GLOBAL truth (description/protagonist/antagonist/patsy) and never that country's own secret motive or intel-sharing level. The per-nation half of mystery mode is used only in one-to-one diplomatic calls.

## The event ledger, traced

### Receives it

- build_inject_generation_prompt (llm/prompts.py:334-459) - the ONLY prompt in the game. Full chain: engine/sim_loop.py:320-321 (event_ledger = narrative_state.recent_played_events(), full list, n=None) -> sim_loop.py:322-324 generate_inject(..., event_ledger=event_ledger) -> llm/inject_generator.py:43 (param) -> :64-66 build_inject_generation_prompt(..., event_ledger=event_ledger) -> llm/prompts.py:405 get_stochastic_inject_context(summary, last_turn_transcript, world, event_ledger=event_ledger) -> llm/context_builder.py:428 render_event_ledger(event_ledger) -> the f-string at llm/context_builder.py:103 'Turn {turn} | {title} | {DISPOSITION} - {note}'. Alternate no-transcript path: llm/prompts.py:411-413. It also (a) shrinks the scenario-library pool at llm/prompts.py:373 via _drop_used_scenarios and (b) switches on continuity rule 8 at llm/prompts.py:422-424.
- Reached in practice only when the ledger is populated, which requires a caller to pass narrative_state into run_turn_briefing. All three do: engine/game_manager.py:152, cli/main.py:859, cli/main_dashboard.py:874. Entries are written at engine/sim_loop.py:336 record_played_event and closed at engine/narrative_adjudication.py:157 close_event (called from :779 and :864, i.e. both adjudication paths).

### Does not receive it

- build_advisor_context - advisor Q&A (llm/prompts.py:82-171; caller agents/conversation.py:210). Signature has no event_ledger parameter at all.
- build_decision_interpretation_prompt (llm/prompts.py:174-241; caller agents/conversation.py:243). No parameter.
- build_pushback_prompt (llm/prompts.py:244-302; caller agents/conversation.py:271). No parameter.
- build_critical_omissions_prompt x5, one per advisor (llm/prompts.py:462-555; caller agents/conversation.py:376-381). No parameter.
- build_narrator_intro_prompt (llm/prompts.py:558-616; caller engine/narrator.py:32). No parameter.
- build_shared_context_prefix / get_advisor_context (llm/context_builder.py:285-365) - the block the four above all open with. render_event_ledger is never called from it.
- assess_action_quality (engine/narrative_adjudication.py:223-266) - builds from narrative_state.to_llm_context(), which does not include event_ledger (models/narrative_state.py:240-266).
- build_character_response_prompt (engine/narrative_adjudication.py:597-633) - same to_llm_context, same omission.
- update_situation_summary's prompt (engine/narrative_adjudication.py:675-685) - same.
- build_actor_prompt (engine/actor_simulation.py:32-85) - world_context comes from narrative_state.to_llm_context() at engine/narrative_adjudication.py:841, so no ledger.
- build_diplomatic_conversation_prompt (engine/diplomacy.py:181-262) and assess_diplomatic_outcome's prompt (engine/diplomacy.py:293-314) - neither takes or renders it.

### Consequence

The ledger is the game's only per-turn compression of the campaign - one ~94-character line stating what was staged and how it was left - and it is shown to exactly one of the roughly fifteen LLM calls a turn. The asymmetry is exactly backwards from what the two windowing schemes need.

(1) The transcript-carrying prompts (advisor Q&A, decision interpretation, pushback, five omissions checks) are the ones that lose history to elision. On saves/parked_campaign4_borrowed_faces.json render_transcript_block keeps turn 1 and turns 12-17 and deletes 1,099 lines covering turns 2-11 (llm/context_builder.py:274-282). Those prompts therefore contain no trace at all of ten turns - not the injects, not the PM's decisions, not the adjudications - and the one artefact designed to survive that cut is not in them. The whole 17-entry ledger would cost about 1,600 characters against a 320,000-character budget of which 13,351 were left unspent (306,649 rendered vs 320,000).

(2) The one prompt that DOES get the ledger never gets the history block. build_inject_generation_prompt does not call render_transcript_block; get_stochastic_inject_context (llm/context_builder.py:391-439) assembles metrics + narrative + the generate_summary digest + the ledger + the last-turn slice. Verified empirically: the string 'GAME HISTORY' does not appear in the generated inject prompt for this campaign (48,908 chars total). So no prompt anywhere in the game ever holds both the full-history block and the ledger, and the generator's only view of turns 1-16 is the ledger plus a digest that on this save reads 'Turns played: 17 / Transcript length: 1853 lines' followed by the same narrator sentence three times.

(3) Worst case is a resumed campaign. saves/parked_campaign4_borrowed_faces.json has no event_ledger key (it predates the field); engine/persistence.py:134 reconstructs NarrativeState with the default_factory=list from models/narrative_state.py:88, so the ledger comes back EMPTY. Turn 18's inject generator then sees: no history block, an empty ledger, a useless digest, and turn 17's 94 lines - which is precisely the state in which issue #25's repeated submarine was possible.

(4) Because rule 8 is emitted only 'if event_ledger' (llm/prompts.py:422), an empty ledger also silently removes the DO-NOT-RESTAGE instruction, so the failure mode is not degraded-but-guarded, it is unguarded.

## Windowing

### budget chars

MAX_ADVISOR_TRANSCRIPT_CHARS = 320,000 characters (llm/context_builder.py:27), the default max_chars of render_transcript_block (llm/context_builder.py:207) and applied unoverridden from build_shared_context_prefix (llm/context_builder.py:326). Split by _TRANSCRIPT_HEAD_SHARE = 0.2 (llm/context_builder.py:54) -> head budget int(320000*0.2) = 64,000 chars for the campaign opening, remainder to the recent tail. Other windows in the same pipeline: MAX_INJECT_CONTINUITY_LINES = 400 (llm/context_builder.py:61) for the inject prompt's last-turn slice, itself char-bounded by the same 320,000 via get_last_turn_slice's max_chars default (llm/context_builder.py:114); _LEDGER_TITLE_MAX = 60 chars per ledger title (llm/context_builder.py:64); the narrator gets a hard last-20-lines slice with NO character bound (llm/prompts.py:587); get_diplomatic_context (llm/context_builder.py:441-512) applies no bound of any kind to its filtered transcript; NarrativeState.recent_events is windowed to the last 3 (models/narrative_state.py:256); WorldState.recent_injects to 5 (engine/sim_loop.py:392 + agents/conversation.py:353); actors to 3 (engine/narrative_adjudication.py:838).

### real transcript size

saves/parked_campaign4_borrowed_faces.json: 1,853 transcript lines, 729,186 characters counted the way the code counts them (sum(len(line)+1)), i.e. 2.28x the 320,000 budget and roughly 182,000 tokens. 17 TURN headers at lines 2, 184, 352, 506, 618, 711, 808, 902, 994, 1087, 1183, 1283, 1378, 1474, 1569, 1664, 1760; world.turn is 18 (turn 18 not yet started). The rendered history block comes out at 306,649 characters, and a full advisor prompt built from it (build_advisor_context with the real initial_conditions) is 314,695 characters, about 78,700 tokens.

### turns elided

10 of the 17 completed turns - turns 2 through 11 inclusive - are deleted entirely, 1,099 transcript lines, replaced by the single line '[... 1099 lines of mid-campaign history elided for length ...]' (llm/context_builder.py:280). Computed by replaying llm/context_builder.py:240-274: head_end = 183 (turn 1 only, 33,517 chars - turn 2 alone spans 39,914 chars and 33,517+39,914 = 73,431 > the 64,000 head budget, so the loop breaks and the head stops after one turn); tail_start = 1282, giving turns 12-17 at 272,819 chars against a tail budget of 286,483. 13,351 characters of the budget go unspent because both loops must stop on whole-turn boundaries.

### what is lost

For every prompt that opens with build_shared_context_prefix - advisor Q&A, decision interpretation, advisor pushback, and the five critical-omissions checks, i.e. the majority of a turn's calls - the entire middle of the campaign is gone: turns 2-11's injects, the PM's decisions, the adjudication reasoning, all diplomatic call transcripts in that span, and every advisor warning issued there. The prompts still instruct the models to use it: llm/prompts.py:160 'Reference past decisions, warnings, or outcomes from the conversation history', :228 'Consider the conversation history - if this decision builds on or contradicts previous actions', :289 'Reference past warnings or decisions from the conversation history if relevant (e.g. "As I warned in Turn 2...")' - and turn 2 is one of the elided turns on this exact save. Nothing substitutes for the loss: NarrativeState.situation_summary (the rolling prose recap) reaches no prompt at all; NarrativeState.recent_events is frozen at seed values; WorldState.recent_injects reaches only the omissions prompt and holds 5 titles; and event_ledger, the one structure built to survive precisely this cut, goes only to the inject generator. Conversely the inject generator, which does receive the ledger, receives no history block whatsoever - so the two halves of the campaign's memory never appear in the same prompt. Note also that _HISTORY_HEADER (llm/context_builder.py:35-38) tells the model this is 'everything that has happened, in order', which is true only in the sense that the gap is marked; the model is given no turn numbers for what is missing, only a line count.
