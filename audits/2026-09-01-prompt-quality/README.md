# Runtime prompt quality audit — 2026-09-01

The active runtime has twelve routed LLM families and thirteen prompt shapes. Seven newly confirmed findings need new remediation; pushback also reproduced the incompleteness already owned by #87. Every other shape passed the captured case. No production prompt text changes in this audit.

`main` was refreshed through `609cdd0b253a352ba4d74fea26d20b666c2e9366`; both final captures ran at branch merge commit `39ca53fa1f4db0f203cbec84c9a41b74f9087278`.

## Evidence set

| Setting | Value |
|---|---|
| Game type | `war_game_2025` |
| Variant / difficulty / play mode | `standard` / `standard` / `immersive` |
| Mystery cases | off; on with `CHINA_PROXY_WAR` |
| Seed | `0` |
| Effective provider | `mock` (`MockDeterministicDriver`) |
| Effective model | driver default (`null`); configured tier is still logged per call |
| Main capture | [`evaluation-main.json`](evaluation-main.json): 50 calls, 25 per case, no fallback |
| Pushback capture | [`evaluation-pushback.json`](evaluation-pushback.json): 2 calls, captured last at `39ca53fa1f4db0f203cbec84c9a41b74f9087278` |
| Reproducer | [`capture.py`](capture.py) |

The capture stores the effective prompt, raw reply, configured tier, provider, model, batch position and parsed/consumed value for every call. The mock route is the product's deterministic first-run route, so its output quality is production-relevant. It also makes the run free and repeatable. This evidence does **not** claim that Gemini or an OpenAI-compatible model will produce the same prose.

Reproduce:

```powershell
python audits/2026-09-01-prompt-quality/capture.py main --output audits/2026-09-01-prompt-quality/evaluation-main.json
python audits/2026-09-01-prompt-quality/capture.py pushback --output audits/2026-09-01-prompt-quality/evaluation-pushback.json
```

The second command is deliberately separate so advisor pushback can be refreshed and audited after all other families.

## Active inventory

All calls route through `llm/router.py`. Every routed context can be overridden through `/routing` by provider, tier or exact model; provider and model can also be selected by environment/config. No production caller supplies the router's explicit `model_override` argument.

Only four prompt shapes are hot-editable: advisor Q&A single, advisor Q&A fanout, decision interpretation and advisor pushback. Their committed files live under `data/prompts/`, load through `llm/prompt_templates.py`, and are exposed by `api/control.py`. The other nine shapes are inline and have no prompt-text override.

| Prompt shape | Builder / runtime template | Production dispatch | Default tier | Prompt override | Reply handling |
|---|---|---|---|---|---|
| Advisor Q&A — single | `llm.prompts.build_advisor_context`; `data/prompts/advisor_qa.txt` | `agents.conversation.handle_player_question` | Pro | Hot-edit | Free prose; empty/error becomes an in-fiction deferral |
| Advisor Q&A — fanout | same builder with `fanout=True`; `advisor_qa_fanout.txt` | `handle_player_question_all`, five-call batch | Pro | Hot-edit | Free prose per advisor; isolated fallbacks |
| Decision interpretation | `build_decision_interpretation_prompt`; `decision_interpretation.txt` | `interpret_player_action` | Flash | Hot-edit | Five labelled fields requested; raw string returned |
| Critical omissions | `build_critical_omissions_prompt`, inline | `check_critical_omissions`, five-call batch | Pro | None | `CONCERN` + `RECOMMENDATION` or `NO_CONCERN`; tolerant parser |
| Inject generation | `build_inject_generation_prompt`, inline | `llm.inject_generator.generate_inject` | Pro | None | YAML mapping; title/description required; quiet-turn fallback |
| Diplomacy conversation | `DiplomaticEncounter.build_prompt`, inline plus `data/diplomatic_profiles.yaml` | `DiplomaticEncounter.process_turn` | Pro | None | Free prose; in-fiction fallback |
| Diplomacy outcome | `assess_diplomatic_outcome`, inline | encounter close | Pro | None | `OUTCOME`, cohesion delta and summary; tolerant/clamped parser |
| Character response | prompt in `generate_character_responses` | adjudication batch | Flash | None | Free prose, quote/whitespace normalisation and fallback |
| Quality assessment | prompt in `assess_action_quality` | decision adjudication | Pro | None | Quality, reasoning, effects and multiplier; tolerant/clamped parser |
| Actor simulation | `build_actor_prompt`, inline | `simulate_actor_responses`, up-to-three batch | Pro | None | Six labelled fields; tolerant parser and field defaults |
| Situation summary | prompt in `compute_situation_summary` | end-of-turn adjudication | Pro | None | Free prose; state-aware deterministic fallback |
| Narrator | `build_narrator_intro_prompt`, inline | `generate_narrator_bridge` | Flash | None | Free prose; in-fiction fallback |
| Advisor pushback | `build_pushback_prompt`; `advisor_pushback.txt` | decision preview | Flash | Hot-edit | `NO PUSHBACK` or role-labelled objections |

Provider-specific tier resolution is: Gemini tier names from `MODEL_NAMES`; OpenAI-compatible `OPENAI_COMPAT_MODEL_FLASH` / `_PRO`, falling back to `OPENAI_COMPAT_MODEL`; mock has no model name. In-process CLI presets mutate `ModelConfig`; facilitator `/routing` overrides take precedence over that tier table.

## Family results

Dimensions assessed: role fidelity, specificity, continuity, repetition, context segregation, output format, parser compatibility and player usefulness.

| Prompt shape | Result | Evidence-backed verdict |
|---|---|---|
| Advisor Q&A — single | **PASS** | NSA answer was role-specific, concise and useful. Prompt and reply were byte-identical across Mystery off/on; no secret truth entered the player-facing call. |
| Advisor Q&A — fanout | **FINDING F6** | Runtime quality passed: five distinct, role-correct answers with no repeated voice. Its editable prompt lacks the byte-golden regression guard applied to the other editable families. |
| Decision interpretation | **FINDING F3** | Reply was specific and format-correct, but downstream API consumers discard the structured forces/resources/timeline data. |
| Critical omissions | **PASS** | All five advisors returned standalone `NO_CONCERN` for a deliberately comprehensive order. The parser kept empty/error distinct from the all-clear sentinel. |
| Actor simulation | **PASS** | Three country-specific structured replies parsed cleanly. Mystery truth appeared only in each simulated capital's private role context; the ON case produced an observable China-related tell. |
| Quality assessment | **PASS** | The measured order received a plausible `adequate` result, reasoning, effects and multiplier. No direct Mystery truth reached this player-facing adjudicator. |
| Character response | **PASS** | Four distinct cabinet voices produced plain, role-appropriate follow-through with no repeated line. |
| Situation summary | **FINDINGS F1, F5** | The captured mock reply ignored the decision and changed actor outcomes, repeated generic stock prose in both cases, and returned three sentences against a 4–6 sentence contract. The recommended routing preset also downgrades this memory-bearing family from Pro to Flash. |
| Narrator | **PASS** | Two concise atmospheric sentences, plain text, no leaked mechanics or secret truth. |
| Diplomacy conversation | **PASS** | Ireland stayed in role and answered the request. Only the Mystery-ON prompt received Ireland's private motive; its output added a subtle Beijing tell. |
| Diplomacy outcome | **PASS** | Structured neutral outcome parsed and matched a call that kept the channel open without winning a firm commitment. |
| Inject generation | **FINDINGS F2, F4** | YAML parsed and produced a specific event, but the prompt requests hidden-truth alignment without receiving that truth, and the default mock output violates the prompt's no-markdown rule. |
| Advisor pushback | **FINDING F8 — existing #87** | Format, role fidelity and Mystery segregation passed, but one order containing nuclear and carrier-readiness triggers produced only the legal/diplomatic nuclear objections. Existing fanout work remains owned by #87. |

## Context segregation

The Mystery-ON raw prompts contain the `CHINA_PROXY_WAR` description or a country `secret_motive` only in `actor_simulation` and `diplomacy_conversation`. The other ten routed contexts contain no direct hidden truth. This is the intended fence: those two calls roleplay actors who know their own motives; player-facing adjudicators and advisors do not.

Observable consequences can still flow forward. In the ON case, actor and Irish outputs differ, which can alter later public transcript/state. That is not a secret-context leak. The inject problem in F2 is the opposite: its own instructions still claim that authoritative truth may be present when the context builder deliberately withholds it.

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
- **Context:** story summary, last-turn slice, event ledger and visible world state. `get_stochastic_inject_context` deliberately excludes the hidden truth because the inject is player-facing.
- **Route:** `inject_generation`, configured Pro, effective mock/driver-default.
- **Observed output:** Mystery ON selected `CHINA_PROXY_WAR`, but the generated cable-cut event contains no authoritative China thread and instead attributes the incident towards Russia.
- **Failure mode:** a live model must ignore the instruction, infer truth from indirect clues, or invent attribution. This is not leakage; it is an impossible instruction at the segregation boundary.
- **Remediation:** [#112 — align inject instructions with the Mystery boundary](https://github.com/earlyprototype/false-flag/issues/112).

### F3 — interpretation structure is discarded after a correct reply — Medium

- **Effective prompt:** requires `INTERPRETATION`, `FORCES INVOLVED`, `RESOURCES CONSUMED`, `TIMELINE` and `FEASIBILITY`.
- **Context:** full shared dossier and the PM's order.
- **Route:** `decision_interpretation`, configured Flash, effective mock/driver-default.
- **Observed output:** all five fields were present and specific.
- **Failure mode:** `interpret_player_action` returns raw text; the terminal-only parser ignores resources; `GameManager.preview_decision` exposes literal `forces_involved=[]` and `timeline="Immediate"`. API clients therefore receive placeholders rather than model output.
- **Remediation:** [#113 — return parsed interpretation fields to API clients](https://github.com/earlyprototype/false-flag/issues/113).

### F4 — mock injects breach their own plain-text contract — Medium

- **Effective prompt:** requires British-English plain prose with no markdown headings, `**bold**` or bullet markers.
- **Context / route:** same captured inject cases as F2; Pro tier, effective mock/driver-default.
- **Observed output:** both cases contain markdown labels such as `**Home Secretary:**` or `**GCHQ Bude Assessment:**` inside the YAML description.
- **Failure mode:** terminal CLIs compensate with `markdown_to_rich`; raw API and browser briefing paths receive the description unchanged. This regresses the raw-markdown fix recorded in closed issue #5.
- **Remediation:** [#114 — remove raw markdown from deterministic injects](https://github.com/earlyprototype/false-flag/issues/114).

### F5 — “Recommended Hybrid” silently downgrades the campaign memory — Medium

- **Effective route:** the default table assigns `situation_summary` to Pro because errors propagate into later prompts. Choosing CLI preset 2 changes it to Flash.
- **Observed configuration:** `llm/model_config.py` documents and sets Pro; `cli/model_settings_menu.py` sets Flash. The preset copy also says “Flash: ... Outcomes” while `diplomacy_outcome` is set to Pro and omits several actual Flash families.
- **Failure mode:** the normal-play recommendation contradicts the runtime's own quality rationale and its displayed summary, making the route inventory unreliable.
- **Remediation:** [#115 — keep campaign memory on Pro in Recommended Hybrid](https://github.com/earlyprototype/false-flag/issues/115).

### F6 — editable fanout prompt is outside the byte-regression golden — Medium

- **Effective prompt:** `advisor_qa_fanout.txt` is independently hot-editable and used for five production calls.
- **Observed regression evidence:** `prompt_templates.FAMILIES` has four templates, but `GOLDEN_FAMILIES` and `prompt_parity_golden.json` pin only advisor single, interpretation and pushback. Comments still call these “the three hot-editable families”; the control-surface guide says any family can be edited.
- **Failure mode:** fanout instruction drift can pass the byte-parity gate, while operators are given an inaccurate inventory.
- **Remediation:** [#116 — add advisor fanout to byte-parity coverage](https://github.com/earlyprototype/false-flag/issues/116).

### F7 — call-log analyser overstates structured-output verification — Medium

- **Evidence claim:** `dev-scripts/analyse_call_log.py` says it compares raw and parsed output across calls.
- **Observed implementation/output:** it reparses only `actor_simulation`; interpretation, omissions, inject, quality and diplomacy outcome are not reparsed. It exits successfully on a multi-family capture without checking those replies.
- **Failure mode:** prompt regressions can appear parser-verified when most structured families were never checked.
- **Remediation:** [#117 — verify every claimed structured family in call-log analysis](https://github.com/earlyprototype/false-flag/issues/117).

### F8 — current pushback drops a second valid trigger — Medium, already tracked

- **Effective prompt:** includes the full cabinet roster and its trigger lists; the test order both surges HMS Prince of Wales at reduced readiness and prepares nuclear first use.
- **Context:** shared player-safe dossier, the specific order and its interpretation; Mystery off/on prompts were byte-identical.
- **Route:** `advisor_pushback`, configured Flash, effective mock/driver-default, captured last at `39ca53fa1f4db0f203cbec84c9a41b74f9087278` after refreshing `origin/main` to `609cdd0b253a352ba4d74fea26d20b666c2e9366`.
- **Observed output:** Attorney General and Foreign Secretary objected to nuclear first use; no CDS carrier-readiness objection appeared.
- **Failure mode:** the current single shared call stops at one trigger class, so a second concrete constraint is absent from player pushback.
- **Remediation:** existing [#87 — fan out advisor pushback](https://github.com/earlyprototype/false-flag/issues/87); no duplicate issue filed.

## Recorded limitations and settled ground

- PR #97's four advisor contradictions and #91's “no historical prompt regression” conclusion were treated as settled and were not re-filed.
- Advisor pushback fanout remains in flight under #87. This audit records its current main commit and output but creates no competing fanout issue.
- Cache and concurrency remain under #64; they were inventoried as routing context, not re-audited.
- Open #17 owns the actor `PUBLIC_RESPONSE` fallback problem. The captured actor replies parsed cleanly, so this audit does not duplicate it.
- No live-provider call was made. The audit proves effective prompt assembly, context boundaries, default mock behaviour, routes and current parser/consumer compatibility.

## Documentation drift found during the audit

The following text is not reliable against current runtime:

- `docs/CONTROL_SURFACE_GUIDE.md`: says any AI family can be hot-edited; only four prompt shapes can.
- `llm/prompt_templates.py` and prompt parity test comments: say three hot-editable families; there are four.
- `api/dataflow.html`: says interpretation is parsed into forces/timeline/intent; the API returns raw text plus placeholders.
- `llm/prompts.py` and `llm/context_builder.py` inject comments: say narrative secrets are included; runtime excludes them.
- `cli/model_settings_menu.py`: Recommended Hybrid copy does not match the tiers it applies.
- `dev-scripts/analyse_call_log.py`: claims broader structured re-parsing than it performs.
- `llm/router.py`: batch-call documentation still cites a 150-token character-response cap; runtime uses 300.
- #89's four-country stance count is stale; both current narratives define eight stances.

## Verification

```text
capture.py main self-check: 50 calls; all 11 non-pushback families; Mystery off/on; mock only; no fallback
prompt/routing/parser focused suite: 169 passed, 1 skipped
parser adversarial suite: 84 passed, 1 skipped
```

The audit modifies only this dated audit directory and the Kanban board state. It changes no production prompt or runtime file.
