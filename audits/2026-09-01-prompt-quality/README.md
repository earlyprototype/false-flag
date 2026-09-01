# Runtime prompt quality audit — 2026-09-01

The active runtime has twelve routed LLM families and thirteen prompt shapes. Eleven newly confirmed findings need remediation; pushback also reproduced the incompleteness already owned by #87. Every other shape passed the captured case. No production prompt text changes in this audit.

`main` was refreshed through `8e7b233ed9840207958d4e22ac3ca6344f11c9f7`; both final captures ran at merged audit commit `5817398d6ae502bb07c4489f8e0747c0dd049f80` (the harness itself last changed at `7cbb797412916d4f9bd3322fdfdcf17377a97393`).

## Evidence set

| Setting | Value |
|---|---|
| Game type | `war_game_2025` |
| Variant / difficulty / play mode | `standard` / `standard` / `immersive` |
| Mystery cases | off; on with `CHINA_PROXY_WAR` |
| Seed | `0` |
| Effective provider | `mock` (`MockDeterministicDriver`) |
| Effective model | driver default (`null`); configured tier is still logged per call |
| Main capture | [`evaluation-main.json`](evaluation-main.json): 46 calls, 23 per case, no fallback, clean parser health |
| Pushback capture | [`evaluation-pushback.json`](evaluation-pushback.json): 2 calls, captured last at `5817398d6ae502bb07c4489f8e0747c0dd049f80` |
| Reproducer | [`capture.py`](capture.py) |

The capture stores the effective user prompt and system instruction, raw reply, configured tier, provider, model, temperature, token cap, model override, batch position and parsed/consumed value for every call. The mock route is the product's deterministic first-run route, so its output quality is production-relevant. It also makes the run free and repeatable. This evidence does **not** claim that Gemini or an OpenAI-compatible model will produce the same prose.

Reproduce:

```powershell
python audits/2026-09-01-prompt-quality/capture.py main --output audits/2026-09-01-prompt-quality/evaluation-main.json
python audits/2026-09-01-prompt-quality/capture.py pushback --output audits/2026-09-01-prompt-quality/evaluation-pushback.json
```

The main run preserves the production decision pipeline's seven child-seed slots while suppressing only the pushback call. The second command is deliberately separate so advisor pushback can be refreshed and audited after all other families.

## Active inventory

All calls route through `llm/router.py`. Every routed context can be overridden through `/routing` by provider, tier or exact model; provider and model can also be selected by environment/config. No production caller supplies the router's explicit `model_override` argument.

Only four prompt shapes are hot-editable: advisor Q&A single, advisor Q&A fanout, decision interpretation and advisor pushback. Their committed files live under `data/prompts/`, load through `llm/prompt_templates.py`, and are exposed by `api/control.py`. The test-oriented `WARGAME_PROMPT_DIR` environment variable can redirect all four to another directory. The other nine shapes are inline and have no prompt-text override.

| Prompt shape | Builder / runtime template | Production dispatch | Default tier | Prompt override | Reply handling |
|---|---|---|---|---|---|
| Advisor Q&A — single | `llm.prompts.build_advisor_context`; `data/prompts/advisor_qa.txt` | `agents.conversation.handle_player_question` | Pro | Hot-edit | Free prose; empty/error becomes an in-fiction deferral |
| Advisor Q&A — fanout | same builder with `fanout=True`; `advisor_qa_fanout.txt` | `handle_player_question_all`, five-call batch | Pro | Hot-edit | Free prose per advisor; isolated fallbacks |
| Decision interpretation | `build_decision_interpretation_prompt`; `decision_interpretation.txt` | `interpret_player_action` | Flash | Hot-edit | Five labelled fields requested; raw string returned |
| Critical omissions | `build_critical_omissions_prompt`, inline | `check_critical_omissions`, five-call batch | Pro | None | `CONCERN` + `RECOMMENDATION` or `NO_CONCERN`; tolerant parser |
| Inject generation | `build_inject_generation_prompt`, inline | `llm.inject_generator.generate_inject` | Pro | None | YAML mapping; title/description required; quiet-turn fallback |
| Diplomacy conversation | `engine.diplomacy.build_diplomatic_conversation_prompt`, inline plus `data/diplomatic_profiles.yaml` | `DiplomaticEncounter.process_turn` | Pro | None | Free prose; in-fiction fallback |
| Diplomacy outcome | `assess_diplomatic_outcome`, inline | encounter close | Pro | None | `OUTCOME`, cohesion delta and summary; tolerant/clamped parser |
| Character response | prompt in `generate_character_responses` | adjudication batch | Flash | None | Free prose, quote/whitespace normalisation and fallback |
| Quality assessment | prompt in `assess_action_quality` | decision adjudication | Pro | None | Quality, reasoning, effects and multiplier; tolerant/clamped parser |
| Actor simulation | `build_actor_prompt`, inline | `simulate_actor_responses`, up-to-three batch | Pro | None | Six labelled fields; tolerant parser and field defaults |
| Situation summary | prompt in `compute_situation_summary` | end-of-turn adjudication | Pro | None | Free prose; state-aware deterministic fallback |
| Narrator | `build_narrator_intro_prompt`, inline | `generate_narrator_bridge` | Flash | None | Free prose; in-fiction fallback |
| Advisor pushback | `build_pushback_prompt`; `advisor_pushback.txt` | decision preview | Flash | Hot-edit | `NO PUSHBACK` or role-labelled objections |

The four active provider choices are Gemini, OpenAI-compatible, mock and offline. Gemini resolves tier names through `MODEL_NAMES`; OpenAI-compatible uses `OPENAI_COMPAT_MODEL_FLASH` / `_PRO`, falling back to `OPENAI_COMPAT_MODEL`; mock and offline have no model name. In-process CLI presets mutate `ModelConfig`; facilitator `/routing` overrides take precedence over that tier table.

## Family results

Dimensions assessed: role fidelity, specificity, continuity, repetition, context segregation, output format, parser compatibility and player usefulness.

| Prompt shape | Result | Evidence-backed verdict |
|---|---|---|
| Advisor Q&A — single | **PASS** | NSA answer was role-specific, concise and useful. Prompt and reply were byte-identical across Mystery off/on; no secret truth entered the player-facing call. |
| Advisor Q&A — fanout | **FINDING F6** | Runtime quality passed: five distinct, role-correct answers with no repeated voice. Its editable prompt lacks the byte-golden regression guard applied to the other editable families. |
| Decision interpretation | **FINDINGS F3, F9** | The reply used all five labels, but API consumers discard the structure and the deterministic answer substituted unrequested forces. |
| Critical omissions | **PASS** | All five advisors returned standalone `NO_CONCERN` for a deliberately comprehensive order. The parser kept empty/error distinct from the all-clear sentinel. |
| Actor simulation | **PASS** | Three country-specific structured replies parsed cleanly. Mystery truth appeared only in each simulated capital's private role context; the ON case produced an observable China-related tell. |
| Quality assessment | **PASS** | The measured order received a plausible `adequate` result, reasoning, effects and multiplier. No direct Mystery truth reached this player-facing adjudicator. |
| Character response | **PASS** | The two advisors selected by the actual effects produced distinct, plain, role-appropriate follow-through with no repeated line. |
| Situation summary | **FINDINGS F1, F5** | The captured mock reply ignored the decision and changed actor outcomes, repeated generic stock prose in both cases, and returned three sentences against a 4–6 sentence contract. The recommended routing preset also downgrades this memory-bearing family from Pro to Flash. |
| Narrator | **FINDING F10** | Format and atmosphere passed, but the reply ignored the specific decision present in its prompt and repeated the same stock bridge in both cases. |
| Diplomacy conversation | **FINDING F11** | Ireland stayed in role and the Mystery-ON answer carried its private motive, but neither answer addressed the concrete maritime-observation request. |
| Diplomacy outcome | **FINDING F11** | The structure parsed, but “no commitments” contradicted the refugee, medical and quiet-diplomacy support just offered. |
| Inject generation | **FINDINGS F2, F4, F12** | YAML parsed and produced a specific event, but selected Mystery truth was absent, descriptions contained forbidden markdown, and both captured channels breached the documented enum. |
| Advisor pushback | **FINDING F8 — existing #87** | Format, role fidelity and Mystery segregation passed, but one order containing nuclear and carrier-readiness triggers produced only the legal/diplomatic nuclear objections. Existing fanout work remains owned by #87. |

## Context segregation

The Mystery-ON raw prompts contain the selected `CHINA_PROXY_WAR` description or a country `secret_motive` only in `actor_simulation` and `diplomacy_conversation`. The other ten routed contexts contain no direct selected-Mystery truth. This is the intended fence: those two calls roleplay actors who know their own motives; player-facing adjudicators and advisors do not.

Observable consequences can still flow forward. In the ON case, actor and Irish outputs differ, which can alter later public transcript/state. That is not a secret-context leak. The inject problem in F2 is the opposite: its own instructions still claim that authoritative truth may be present when the context builder deliberately withholds it.

The inject prompt does receive base-scenario Russian objectives explicitly labelled hidden from the player. It does **not** receive the selected Mystery narrative or actor secret motives. F2 is about that ambiguous boundary: base hidden material is present, but the selected truth the prompt tells the model to advance is not.

## Confirmed findings

### F1 — default situation summary loses campaign continuity — High

- **Effective prompt:** asks for 4–6 complete sentences covering the event, the PM's action, consequences, posture and unresolved threads.
- **Context:** the PM's specific NATO, patrol, cyber, public-reassurance and legal-approval order plus parsed adjudication and actor effects.
- **Route:** `situation_summary`, configured Pro, effective mock/driver-default.
- **Observed output:** the same three generic sentences in both cases: Russian posture continues; consultations continue; the decision is being watched.
- **Failure mode:** it names neither the order nor its effects, misses the sentence-count contract, and erases the only Mystery-dependent actor differences before this rolling memory feeds later prompts.
- **Remediation:** [#111 — preserve turn-specific situation-summary continuity](https://github.com/earlyprototype/false-flag/issues/111).

### F2 — inject prompt cannot obey its hidden-narrative instructions — High

- **Effective prompt:** says to align with “the narrative truth (if provided above)” and to subtly advance the hidden narrative, including a China-manipulation example.
- **Context:** story summary, last-turn slice, event ledger, visible world state and base-scenario hidden Russian objectives. `get_stochastic_inject_context` deliberately excludes the selected Mystery narrative and actor secret motives.
- **Route:** `inject_generation`, configured Pro, effective mock/driver-default.
- **Observed output:** Mystery ON selected `CHINA_PROXY_WAR`, but the generated Berlin sanctions split contains no authoritative China thread. Mystery OFF generated a Moscow ultimatum.
- **Failure mode:** a live model can mistake the base hidden objectives for the selected Mystery truth, ignore the instruction, infer from indirect clues, or invent attribution. The captured output did not leak selected truth; the instruction is ambiguous and impossible at that boundary.
- **Remediation:** [#112 — align inject instructions with the Mystery boundary](https://github.com/earlyprototype/false-flag/issues/112).

### F3 — interpretation structure is discarded after a format-valid reply — Medium

- **Effective prompt:** requires `INTERPRETATION`, `FORCES INVOLVED`, `RESOURCES CONSUMED`, `TIMELINE` and `FEASIBILITY`.
- **Context:** full shared dossier and the PM's order.
- **Route:** `decision_interpretation`, configured Flash, effective mock/driver-default.
- **Observed output:** all five fields were present; semantic fidelity is assessed separately in F9.
- **Failure mode:** `interpret_player_action` returns raw text; the terminal-only parser ignores resources; `GameManager.interpret_decision` exposes literal `forces_involved=[]` and `timeline="Immediate"`. API clients therefore receive placeholders rather than model output.
- **Remediation:** [#113 — return parsed interpretation fields to API clients](https://github.com/earlyprototype/false-flag/issues/113).

### F4 — mock injects breach their own plain-text contract — Medium

- **Effective prompt:** requires British-English plain prose with no markdown headings, `**bold**` or bullet markers.
- **Context / route:** same captured inject cases as F2; Pro tier, effective mock/driver-default.
- **Observed output:** both cases contain markdown labels such as `**Foreign Secretary:**`, `**NSA:**` and `**CDS:**` inside the YAML description.
- **Failure mode:** terminal CLIs compensate with `markdown_to_rich`; raw API and browser briefing paths receive the description unchanged. This regresses the raw-markdown fix recorded in closed issue #5.
- **Remediation:** [#114 — remove raw markdown from deterministic injects](https://github.com/earlyprototype/false-flag/issues/114).

### F5 — “Recommended Hybrid” silently downgrades the campaign memory — Medium

- **Effective prompt / context:** the same specific summary fold captured in F1: prior summary, current order, quality and applied effects.
- **Route:** the default table assigns `situation_summary` to Pro because errors propagate into later prompts. Choosing CLI preset 2 changes it to Flash.
- **Observed output:** the default mock output is recorded in F1. Mock ignores tier, so this audit makes no claim about a live Flash/Pro prose difference.
- **Observed configuration:** `llm/model_config.py` documents and sets Pro; `cli/model_settings_menu.py` sets Flash. The preset copy also says “Flash: ... Outcomes” while `diplomacy_outcome` is set to Pro and omits several actual Flash families.
- **Failure mode:** the normal-play recommendation contradicts the runtime's own quality rationale and its displayed summary, making the route inventory unreliable.
- **Remediation:** [#115 — keep campaign memory on Pro in Recommended Hybrid](https://github.com/earlyprototype/false-flag/issues/115).

### F6 — editable fanout prompt is outside the byte-regression golden — Medium

- **Effective prompt:** `advisor_qa_fanout.txt` is independently hot-editable and used for five production calls.
- **Context:** the shared player-safe dossier, one room-wide risk question and each advisor's own role context.
- **Route:** `advisor_qa`, configured Pro, effective mock/driver-default, five-call batch.
- **Observed output:** five distinct, role-correct answers; each call's consumed transcript line is recorded separately.
- **Observed regression evidence:** `prompt_templates.FAMILIES` has four templates, but `GOLDEN_FAMILIES` and `prompt_parity_golden.json` pin only advisor single, interpretation and pushback. Comments still call these “the three hot-editable families”; the control-surface guide says any family can be edited.
- **Failure mode:** fanout instruction drift can pass the byte-parity gate, while operators are given an inaccurate inventory.
- **Remediation:** [#116 — add advisor fanout to byte-parity coverage](https://github.com/earlyprototype/false-flag/issues/116).

### F7 — call-log analyser overstates structured-output verification — Medium

- **Effective prompt / context / route:** all captured structured families are in scope; the analyser is offline tooling and makes no LLM call of its own.
- **Evidence claim:** `dev-scripts/analyse_call_log.py` says it compares raw and parsed output across calls.
- **Observed output:** it reparses only `actor_simulation`; interpretation, omissions, inject, quality and diplomacy outcome are not reparsed. It exits successfully on a multi-family capture without checking those replies.
- **Failure mode:** prompt regressions can appear parser-verified when most structured families were never checked.
- **Remediation:** [#117 — verify every claimed structured family in call-log analysis](https://github.com/earlyprototype/false-flag/issues/117).

### F8 — current pushback drops a second valid trigger — Medium, already tracked

- **Effective prompt:** includes the full cabinet roster and its trigger lists; the test order both surges HMS Prince of Wales at reduced readiness and prepares nuclear first use.
- **Context:** shared player-safe dossier, the specific order and its interpretation; Mystery off/on prompts were byte-identical.
- **Route:** `advisor_pushback`, configured Flash, effective mock/driver-default, captured last at `5817398d6ae502bb07c4489f8e0747c0dd049f80` after refreshing `origin/main` to `8e7b233ed9840207958d4e22ac3ca6344f11c9f7`.
- **Observed output:** Attorney General and Foreign Secretary objected to nuclear first use; no CDS carrier-readiness objection appeared.
- **Failure mode:** the current single shared call stops at one trigger class, so a second concrete constraint is absent from player pushback.
- **Remediation:** existing [#87 — fan out advisor pushback](https://github.com/earlyprototype/false-flag/issues/87); no duplicate issue filed.

### F9 — deterministic interpretation substitutes unrequested forces — High

- **Effective prompt:** requires a structured reading of the actual directive, including the forces/assets being deployed.
- **Context:** the exact NATO/P-8/Type 23/cyber/public/legal order, current UK force inventory, constraints and the two preceding cabinet questions.
- **Route:** `decision_interpretation`, configured Flash, effective mock/driver-default.
- **Observed output:** the interpretation sentence preserved the order, but `FORCES INVOLVED` replaced the ordered Type 23 frigates with Type-45 destroyers and combat air patrols; only the P-8 remained faithful.
- **Failure mode:** a format-valid answer becomes the engine's canonical reading while inventing deployments and omitting an ordered asset. Label/parser checks cannot catch this semantic substitution.
- **Remediation:** [#119 — keep deterministic interpretation faithful to submitted forces](https://github.com/earlyprototype/false-flag/issues/119).

### F10 — narrator bridge ignores the recorded decision — Medium

- **Effective prompt:** asks for a concise atmospheric bridge grounded in recent transcript and current situation.
- **Context:** includes the full P-8/Type 23 deployment, allied consultation, cyber defence, public reassurance and legal restraint decision.
- **Route:** `narrator`, configured Flash, effective mock/driver-default, with its thriller system instruction, temperature `0.7` and 300-token cap.
- **Observed output:** both cases returned the same generic two-sentence passage about hours passing and an aide entering with a folder.
- **Failure mode:** format and tone pass, but no concrete decision, consequence or unresolved thread crosses the turn boundary, so the bridge provides no continuity or player feedback.
- **Remediation:** [#122 — connect narrator bridges to the player decision](https://github.com/earlyprototype/false-flag/issues/122).

### F11 — diplomacy loses concrete asks and offered commitments — Medium

- **Effective prompts:** the conversation asks the Taoiseach to answer the PM in role; the outcome assessor receives the completed call and must classify its result.
- **Context:** the PM asks Ireland to share maritime observations and keep a quiet channel open. Ireland's private motive enters only the Mystery-ON conversation; the outcome call receives the visible transcript, not that secret context.
- **Routes:** `diplomacy_conversation` and `diplomacy_outcome`, both configured Pro and effective mock/driver-default.
- **Observed output:** Ireland refused troops and ports, offered refugee, medical and quiet-diplomacy support, but never answered maritime observation sharing. The outcome then said no commitments were secured beyond continued consultation.
- **Failure mode:** the conversation is role-faithful but does not resolve the concrete ask, and its structured outcome contradicts commitments visible in the source transcript.
- **Remediation:** [#120 — preserve concrete asks and commitments across diplomacy calls](https://github.com/earlyprototype/false-flag/issues/120).

### F12 — inject output breaches its declared shape without parser resistance — Medium

- **Effective prompt:** requires a 2–3 paragraph YAML description and `channel` restricted to `briefing`, `intelligence`, `media` or `military`.
- **Context:** the captured stochastic-inject snapshots described in F2 and F4.
- **Route:** `inject_generation`, configured Pro, effective mock/driver-default.
- **Observed output:** the Mystery-OFF Moscow ultimatum used `channel: flash_alert`; the Mystery-ON Berlin sanctions split used `channel: diplomatic`. Both are outside the prompt enum, exceed three substantive text blocks and parsed successfully.
- **Additional source evidence:** the deterministic pool also emits `emergency` and `domestic`. `models.layers.CHANNEL_LAYER_MAP` recognises the other observed extensions but silently defaults `domestic` to SITREP despite claiming to cover the observed vocabulary.
- **Failure mode:** generator and parser accept an undocumented channel and overlong shape, so downstream consumers cannot rely on the declared contract and parser-health evidence remains falsely clean.
- **Remediation:** [#121 — enforce the inject output-shape and channel contract](https://github.com/earlyprototype/false-flag/issues/121).

## Recorded limitations and settled ground

- PR #97's four advisor contradictions and #91's “no historical prompt regression” conclusion were treated as settled and were not re-filed.
- Advisor pushback fanout remains in flight under #87. This audit records its current main commit and output but creates no competing fanout issue.
- Cache and concurrency remain under #64; they were inventoried as routing context, not re-audited.
- Open #17 owns the actor `PUBLIC_RESPONSE` fallback problem. The captured actor replies parsed cleanly, so this audit does not duplicate it.
- The stochastic-inject sample stages the authored turn-6 briefing through the production helper after one fully audited decision. It does not replay turns 2–5 or the required US call, so it supports prompt, route, segregation, format and parser findings but makes no full-campaign continuity claim.
- No live-provider call was made. The audit proves effective prompt assembly, context boundaries, default mock behaviour, routes and current parser/consumer compatibility.

## Documentation drift found during the audit

The following text is not reliable against current runtime:

- `docs/CONTROL_SURFACE_GUIDE.md`: says any AI family can be hot-edited; only four prompt shapes can.
- `llm/prompt_templates.py` and prompt parity test comments: say three hot-editable families; there are four.
- `api/dataflow.html`: says interpretation is parsed into forces/timeline/intent; the API returns raw text plus placeholders.
- `llm/prompts.py` and `llm/context_builder.py` inject comments: imply selected narrative secrets are included; runtime supplies base hidden objectives but excludes the selected Mystery narrative.
- `cli/model_settings_menu.py`: Recommended Hybrid copy does not match the tiers it applies.
- `dev-scripts/analyse_call_log.py`: claims broader structured re-parsing than it performs.
- `llm/router.py`: batch-call documentation still cites a 150-token character-response cap; runtime uses 300.
- `models/layers.py`: says its channel map covers every observed value, but deterministic injects emit unmapped `domestic`.
- #89's four-country stance count is stale; both current narratives define eight stances.

## Verification

```text
capture.py -O main self-check: 46 calls (23/case), exact path counts; all 11 non-pushback families; Mystery off/on; mock only; no fallback; parser health clean
capture.py -O pushback self-check: 2 calls (1/case), captured last; mock only; no fallback; parser health clean
Ruff audit harness check: passed
prompt/routing/parser/inject/diplomacy focused suite: 201 passed, 1 skipped
```

The audit modifies only this dated audit directory and the Kanban board state. It changes no production prompt or runtime file.
