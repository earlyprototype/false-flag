# FALSE FLAG — LLM-reply parser audit

Branch: claude/game-audit-pr-review-u6ujyq. Read-only audit; all paths absolute under /home/user/false-flag.
Failure shapes: (1) decorated labels, (2) worded/annotated values, (3) label-on-own-line + continuations,
(4) empty-after-label, (5) sentinel mishandling, (6) refusal/negation inversion.
Status values: HANDLED / PARTIAL / NOT-HANDLED / N-A. "Miss-recorded?" = parse_health.record_miss/record_fallback on fallback paths.

**Headline findings**
- `record_truncation` and `record_residue` (llm/parse_health.py:41, 56) have ZERO production callers — only tests/test_call_log.py:113-114 call them. The record_truncation docstring ("Drivers call this the moment the provider's finish reason says 'length'", llm/parse_health.py:46-48) describes behaviour that does not exist: neither llm/openai_compat_driver.py::generate_text (returns `text.strip()` at 230 without inspecting finish_reason except on EMPTY replies, 225-229) nor llm/gemini_driver.py::generate_text (183-188) records a "length" finish with partial text. Silent truncation reaches every parser.
- No parser does residue accounting; attach points are listed per parser below.
- Sentinel handling in `_parse_actor_response` still uses exact `== "none"` string compares instead of `is_sentinel_line` (engine/actor_simulation.py:226, 235).
- `_parse_quality_response` re-implements a weaker enum match instead of `match_enum` (engine/narrative_adjudication.py:390-391).

---

## P1. engine/actor_simulation.py::_parse_actor_response (engine/actor_simulation.py:160) — the ER-049 reference parser

| Shape | Status | Evidence |
|---|---|---|
| 1 decorated labels | HANDLED | extract_label at 181, 188, 195, 206, 222, 231 |
| 2 worded/annotated | HANDLED (annotated numbers: find_signed_int at 199, clamp 201; enum via match_enum 214). Fully worded "minus five" not recovered but miss-recorded (203) |
| 3 label-on-own-line | PARTIAL | HANDLED for PUBLIC_RESPONSE / PRIVATE_ASSESSMENT (last_text_field set 185, 192; accumulator 241-245). NOT-HANDLED for CONDITIONS and INTEL_SHARED: label line sets last_text_field=None (224, 233), so a value on the following line is silently dropped |
| 4 empty-after-label | HANDLED | empty public_response miss 252-253; empty TRUST_CHANGE → miss 203; empty WILL_SUPPORT → miss 219; empty CONDITIONS/INTEL legitimately mean none (prompt line 90) → N-A |
| 5 sentinel | NOT-HANDLED | 226, 235: exact `value.lower() != "none"` instead of is_sentinel_line |
| 6 refusal inversion | HANDLED | match_enum(..., refusal_value="no") 214-215 |

- Miss-recorded: yes — 203, 219, 248-249 (no labels at all), 250-251 (WILL_SUPPORT absent), 252-253. Default will_support="conditional" at 254-255.
- Residue attach point: after engine/actor_simulation.py:245 (lines reaching the loop end with last_text_field None).

NOT-HANDLED repros:
- Shape 3 (CONDITIONS):
  ```
  WILL_SUPPORT: conditional
  CONDITIONS:
  NATO consultation first; parliamentary approval
  ```
  → conditions == [] (222-229 read the empty value; the next line is dropped at 241-245 because last_text_field is None). A "conditional" ally with no stated conditions; no miss recorded.
- Shape 5 (INTEL_SHARED): `INTEL_SHARED: "none"` → extract_label strips ``*_` `` but not quotes (llm/parsing.py:60), so value `'"none"'` fails the compare at 235 → intel_shared='"none"' and the game reports intel was shared. Same for `CONDITIONS: None.` at 226 → conditions == ["None."]. (The prompt itself, engine/actor_simulation.py:92, shows the sentinel QUOTED — `or "none"` — so the quoted form is invited.)

## P2. engine/narrative_adjudication.py::_parse_quality_response (engine/narrative_adjudication.py:352)

| Shape | Status | Evidence |
|---|---|---|
| 1 decorated labels | HANDLED | extract_label 378, 388, 398, 404; strip_decoration on metric prefix 414 |
| 2 worded/annotated | PARTIAL | multiplier find_float 380-382 HANDLED; metric deltas find_signed_int 416 HANDLED; QUALITY NOT-HANDLED: 390-391 strip_decoration + exact membership, so "poor (borderline)" / "Poor — hasty" fails → miss (394) + default "adequate" (428-430) and multiplier drops from 0.5 to 1.0 (437-445) |
| 3 label-on-own-line | PARTIAL | REASONING continuations HANDLED (401, 424-426). QUALITY / QUALITY MULTIPLIER / metric value on the following line NOT-HANDLED (last_field=None at 385, 395, 421) |
| 4 empty-after-label | HANDLED | misses 384, 394, 420; end-of-parse misses 428-434 |
| 5 sentinel | N-A |
| 6 refusal inversion | N-A ("not good" fails membership → adequate, safe direction) |

- Silent value drop: 404 treats ANY `EFFECTS:` line as a bare header and discards its value; a single-line `EFFECTS: escalation_risk: -5` loses the delta (the metric branch 412-421 never sees it), no per-value miss. Repro: reply whose only delta is on the `EFFECTS:` line → effects == {} (miss only the generic 434 one).
- Shape 3 repro:
  ```
  QUALITY:
  poor
  REASONING: Overreach.
  ```
  → quality defaults "adequate", multiplier 1.0 instead of 0.5; the bare "poor" line vanishes (miss at 394 is recorded, but the value was recoverable one line down).
- Shape 2 repro: `QUALITY: **Poor** — hasty and escalatory` → "poor — hasty and escalatory" ∉ list → adequate. match_enum (llm/parsing.py:89-114) would recover it. **Duplication**: 390-391 re-implements a weaker match_enum.
- Miss-recorded: yes (384, 394, 420, 430, 432, 434).
- Residue attach point: after narrative_adjudication.py:426.

## P3. engine/narrative_adjudication.py::compute_situation_summary reply handling (narrative_adjudication.py:795-806)

Prose reply (`.strip().strip('"')` at 796-798); shapes 1-6 N-A. Gaps:
- Empty reply → None (806) → caller silently substitutes fallback_situation_summary (836-837, 986-988, 1105-1107); NO record_fallback. Attach at 799-806 (empty path and except path).
- max_tokens=400 (796): truncated fold ends mid-sentence and IS the player-facing synopsis; no truncation record exists anywhere (see headline).

## P4. engine/narrative_adjudication.py::generate_character_responses reply handling (narrative_adjudication.py:596-608)

Prose; shapes 1-6 N-A. `[ERROR:` batch-slot guard 604-605; empty → canned "Understood, Prime Minister." 607. Gap: neither path records — attach record_fallback("character_response", char.name) inside 604-607. (Cap CHARACTER_RESPONSE_MAX_TOKENS=150 at 641; truncation unrecorded, see headline.)

## P5. engine/diplomacy.py::assess_diplomatic_outcome (engine/diplomacy.py:281; parse loop 359-409)

| Shape | Status | Evidence |
|---|---|---|
| 1 decorated labels | HANDLED | extract_label 369, 380, 391 |
| 2 worded/annotated | HANDLED | match_enum 371; find_signed_int + clamp 382-384 |
| 3 label-on-own-line | PARTIAL | SUMMARY continuations HANDLED (394, 397-399). OUTCOME / ALLIANCE_COHESION_DELTA value on next line NOT-HANDLED: empty value defaults with a miss (375-376, 386-387) and the bare value line is discarded (398 only appends when last_field=="summary") |
| 4 empty-after-label | HANDLED | 375-376, 386-387; end-of-parse 401-409 |
| 5 sentinel | N-A |
| 6 refusal inversion | PARTIAL | match_enum negation lookback is exactly one word (llm/parsing.py:81-86): `OUTCOME: Not a failure` → token "failure" preceded by "a" → FAILURE (inverted). `not failure` is caught |

- Shape 3 repro:
  ```
  OUTCOME:
  SUCCESS
  ALLIANCE_COHESION_DELTA: +8
  ```
  → outcome=="NEUTRAL" (375-376); "Diplomatic Outcome: NEUTRAL" (412) shown/persisted despite the model's SUCCESS.
- Shape 6 repro: `OUTCOME: Not a failure, all told` → FAILURE via llm/parsing.py:111-113 (delta unaffected, but the displayed verdict inverts).
- Miss-recorded: yes (375, 386, 403, 406, 409).
- Residue attach point: after diplomacy.py:399.

## P6. engine/diplomacy.py::DiplomaticEncounter.process_turn conversation reply (diplomacy.py:524-528)

Prose; shapes 1-6 N-A. Gaps:
- No empty-reply guard: 524-527 append `f"{self.title}: {response}"` even when response=="" — a silent counterpart line, no fallback text, no record. (Contrast narrative_adjudication.py:604-607.)
- No `[ERROR:` guard (single-call router usually degrades to mock — llm/router.py:317-330 — but injected generate fns aren't covered).

## P7. agents/conversation.py::handle_player_question advisor QA reply (conversation.py:197-207)

Prose; shapes 1-6 N-A. Gaps: response appended verbatim (201-205) — no empty guard, no `[ERROR:` guard; exception path shows out-of-fiction "System: Error generating response: {e}" (206-207) with no record_fallback.

## P8. agents/conversation.py::interpret_player_action (conversation.py:212-238)

Pure passthrough (237-238); no guards; empty interpretation flows into downstream prompts and P11. No record anywhere. (Parsing shapes are exercised downstream.)

## P9. agents/conversation.py::generate_advisor_pushback (conversation.py:241-307)

| Shape | Status | Evidence |
|---|---|---|
| 1 decorated labels | HANDLED | role prefix via _normalize_role_prefix→strip_decoration (291, 113-120); sentinel decoration via is_sentinel_line (274) |
| 2 worded/annotated | N-A |
| 3 label-on-own-line | HANDLED | continuation branch 298-300 |
| 4 empty-after-label | NOT-HANDLED | `Home Secretary:` with empty remainder and no continuation yields ("Home Secretary", "") at 296-297; advisor rendered saying nothing, no miss |
| 5 sentinel | HANDLED (standalone-line test 274) — caveat below |
| 6 refusal inversion | N-A |

- Sentinel caveat (mixed reply): 274 scans ALL lines; a reply carrying real pushback plus a trailing standalone `NO PUSHBACK` returns [] and drops everything. Repro:
  ```
  Home Secretary: The public will panic without a statement.
  NO PUSHBACK
  ```
  → returns [] (274-275); objection vanishes, nothing recorded.
- Miss-recorded: orphan pre-role lines 302-305 (yes). Empty-message case records nothing.
- Residue attach point: after conversation.py:307 (orphan-miss at 305 already covers pre-role residue).

## P10. agents/conversation.py::check_critical_omissions (conversation.py:310; per-reply parse 395-452)

| Shape | Status | Evidence |
|---|---|---|
| 1 decorated labels | HANDLED | extract_label 425-426; is_sentinel_line 408-411 |
| 2 worded/annotated | N-A |
| 3 label-on-own-line | HANDLED | last_field continuations 427-438 |
| 4 empty-after-label | PARTIAL | recommendation-missing → miss + placeholder 440-444; concern-missing → miss + skip 445-447. NOT-HANDLED: an entirely EMPTY reply is treated as all-clear — `if not response or any(is_sentinel_line...)` (408-411) conflates "" with NO_CONCERN, no record |
| 5 sentinel | HANDLED (standalone-line 408-411) |
| 6 refusal inversion | N-A |

- Empty-reply repro: sequential fanout path returns "" for a failed call (llm/fanout.py:82-84) → silently counted as "advisor found nothing wrong". Should record at 408.
- Fallback-recorded: `[ERROR:` slots at 400-403 (record_fallback) — yes.
- Residue attach point: after conversation.py:438.

## P11. cli/display_utils.py::parse_interpretation_simple (cli/display_utils.py:159-211)

| Shape | Status | Evidence |
|---|---|---|
| 1 decorated labels | HANDLED | extract_label 181-184 |
| 2 worded/annotated | N-A |
| 3 label-on-own-line | PARTIAL | FORCES bullets 202-207 and TIMELINE next-line 208-209 HANDLED. INTERPRETATION NOT-HANDLED: 186-187 store the (possibly empty) value and set no current_section, so the summary paragraph below the bare label is dropped |
| 4 empty-after-label | PARTIAL | no per-field misses; only the all-fields-empty case records, in the caller (display_decision_summary, 264-269) |
| 5 sentinel | N-A |
| 6 refusal inversion | N-A |

- Shape 3 repro:
  ```
  INTERPRETATION:
  Deploy two Type-45s to the North Sea under NATO command.
  FORCES INVOLVED: Type-45 destroyers
  ```
  → summary=="" and the sentence is dropped (no branch consumes it, 178-209). Because forces parsed, the record_miss at 265 does NOT fire — the OPERATIONAL ORDER panel silently lacks its summary.
- FEASIBILITY: concern only captured when "impossible"/"requires clarification" is on the SAME line (198-200); a wrapped clause on the next line is dropped (current_section=None at 201).
- Prompt contract at llm/prompts.py:266-270 (INTERPRETATION / FORCES INVOLVED / TIMELINE / FEASIBILITY).
- Residue attach point: end of loop (after cli/display_utils.py:209).

## P12. cli/display_utils.py::narrative_assessment (cli/display_utils.py:60-79)

Parses engine-composed reasoning ("Action Quality:"/"Reasoning:" written by _generate_actor_summary, narrative_adjudication.py:1116-1117) — shapes 1-6 effectively N-A. Caveat: 71, 75 use bare `lower.startswith(...)` (not decoration-tolerant); safe today only because the input is engine text. Unknown quality words degrade safely (73-74).

## P13. engine/sim_loop.py::apply_inject_effects delta coercion (engine/sim_loop.py:173; coercion 205-252)

Shapes 1, 3-6 N-A (structured dict from YAML). Shape 2 HANDLED: int 216-217, float 218-219, quoted/annotated strings 220-235 (strip quotes/+, find_signed_int, find_float), "a..b" ranges 222-229; unreadable delta → visible skip line + record_miss (240-241). Gap: unknown METRIC NAME (model-authored) at 272-273 emits a transcript line but NO record_miss — attach record_miss("inject_effects", metric_name, "unknown metric") at 273.

## P14. llm/inject_generator.py::generate_inject YAML parsing (llm/inject_generator.py:84-116)

Shapes 1-6 N-A (YAML). Gaps:
- NO parse-health records on any failure path: empty reply 79-81, non-mapping 101-104, YAMLError 112-116, and the caller's quiet-turn fallback (engine/sim_loop.py:377-381) are logger-only. A campaign of quiet turns reports perfect parse health. Attach record_fallback("inject_generation", ...) at each.
- Unclosed code fence: `find("```", yaml_start)` == -1 (88, 93) makes the slice `[start:-1]` drop the final character instead of taking the rest of the reply.
- Schema check is only isinstance(dict) (101): a mapping missing title/description passes and renders an empty briefing (engine/sim_loop.py:80-82 default "").

## P15. engine/narrator.py::generate_narrator_bridge reply handling (engine/narrator.py:35-48)

Prose; shapes 1-6 N-A. Empty reply returns "" (45) → caller drops the bridge silently (engine/sim_loop.py:406); exception path returns canned line (46-48). Neither records a fallback. max_tokens=150 (43): truncation unrecorded (headline finding).

## P16. engine/opening.py::split_briefing (engine/opening.py:165-189)

From turn 2 the briefing description is LLM-written (engine/sim_loop.py commentary at 355-376), so the handover match at 184-188 (`"National Security Advisor" in line` + verb substrings "clears"/"begins", constants 42-44) parses model prose. Substring tests tolerate decoration (shape 1 HANDLED de facto); miss → no split, whole text as scene_setting (189) — benign degradation, no record needed. Shapes 2-6 N-A.

## P17. api/server.py::post_discussion role-tag heuristic (api/server.py:708-727)

Parses `"role: response"` transcript lines (engine prefix around LLM text). Bugs:
- Roster mismatch: 718 matches only ["NSA", "CDS", "Foreign Secretary", "Home Secretary", "Attorney General", "Prime Minister"], but handle_player_question emits the initial_conditions role names — "Military Commander", "Intelligence Coordinator", "Government Leader" etc. (data/scenarios/war_game_2025/initial_conditions.yaml:444, 454; agents/conversation.py:203-205) — so most advisor lines stream as type "narrator" with role=None. Compare cli/display_utils.py:28-35 which maps exactly these names.
- Shape 1: no strip_decoration on the candidate role (716); a decorated prefix never matches.
- No record of the misclassification (misses here are invisible).

## P18. docs/py/bridge.py — browser front-end parsers

- `_reflow` (docs/py/bridge.py:99-145): display re-wrapper over LLM prose; label detection _LABEL_RE at 96, block starts at 91. Formatting only — a misread merges lines, loses nothing. Shapes N-A for data loss.
- `_render_call` (docs/py/bridge.py:930-959): re-parses the diplomacy transcript with `":" in stripped and len(prefix)<48` (951-953); an LLM counterpart line whose reply contains an early colon after a line break inside one entry (938) can be dressed as a new speaker — display-only misattribution. isupper() guard 953 distinguishes closing labels.
- Fault probe `_watch_calls` (docs/py/bridge.py:285-303): scans batch results for `[ERROR:` prefix (296-299) — a reply-shape detector, HANDLED, feeds the on-page fault banner; note it only wraps openai_compat (324-325).
- split_briefing reuse at 779 — see P16.

## P19. llm drivers + router + fanout (transport-level reply handling)

- llm/openai_compat_driver.py::generate_text: empty completion raises with finish_reason in the MESSAGE only (225-229); a "length" finish WITH text returns silently (230) — no record_truncation call exists anywhere in production code (grep: only tests/test_call_log.py:113). The driver does not accept `meta_out` (signature 153-160), so even the router's call-log finish_reason slot (llm/router.py:309-310, 346) stays None for this driver.
- llm/gemini_driver.py::generate_text: same pattern — 183-184 return text; finish_reason consulted only in the no-text error (187-188). batch slot errors as `[ERROR: {finish_reason}]` at 238-239.
- Batch `[ERROR: ...]` slots: openai_compat_driver.py:268, 287; consumed by guards at narrative_adjudication.py:604, conversation.py:400, actor_simulation.py:150 — but NOT in diplomacy.py (P6) or handle_player_question (P7).
- llm/fanout.py::generate_group sequential path: failed call → "" with print-WARN only (82-84), no record_fallback; short batch padded with "" (72-76), print-WARN only. Empty strings then hit P10's empty==all-clear hole.
- llm/router.py: single-call double-failure records fallback (327-328) and batch whole-failure too (474-475) — HANDLED.
- llm/mock_driver.py parses PROMPTS (its input), not model replies — out of scope (e.g. 1189).

## P20. llm/context_builder.py::get_diplomatic_context (llm/context_builder.py:512-563) — prefix classifier over mixed transcript

Classifies transcript entries (engine + embedded LLM text) by speaker-prefix regex (_SPEAKER_PREFIX_RE, 491) with fail-closed intent (ER-018). Shape-3 analog gap: an UNLABELED entry of UK-internal LLM text passes the no-prefix filter at 560-561 and is shown to a foreign counterpart — concretely, format_decision_transcript appends the raw multi-line interpretation as its own unprefixed entry (engine/decision_phase.py:196), which typically has no `Word:` first line, so the UK's internal reading of the PM's decision enters every foreign leader's context. Not a crash, but the classifier's "prefix == internal" assumption inverts on continuation-style entries. (generate_summary at 641-679 is a deterministic digest of structural lines; benign.)

## P21. cli/main.py / cli/main_dashboard.py advisor-line re-parsers

- cli/main.py:1300-1324 and 1655-1665: split engine-prefixed `role: response` lines; prefix is engine-composed, so shapes largely N-A; failure mode is display-only.
- cli/main_dashboard.py:1042-1055: any briefing line with a colon in the first 40 chars becomes a "speaker" (1046-1051) — LLM inject prose like `0300 hours: contacts multiply...` renders as speaker "0300 Hours". Display-only misattribution of free LLM text; no record.

## Checked, no LLM-reply parsing (for completeness)
- engine/intelligence.py (pure generator from metrics), engine/endings.py (parses engine-prefixed transcript lines only, 176-180), engine/game_manager.py (consumes structured returns; 294-301 matches parser-produced role strings by name), ingestion/extract_events.py (placeholder returning []), engine/events.py (scripted YAML from disk), llm/prompts.py (builders), engine/decision_phase.py (infrastructure; records fallbacks at 169).

---

## Summary matrix (shapes 1-6 per parser)

| Parser (file:line) | 1 | 2 | 3 | 4 | 5 | 6 | Miss-recorded | Residue attach |
|---|---|---|---|---|---|---|---|---|
| P1 _parse_actor_response (engine/actor_simulation.py:160) | H | H | PARTIAL (CONDITIONS/INTEL 224,233) | H | **NOT (226,235)** | H | yes | after :245 |
| P2 _parse_quality_response (engine/narrative_adjudication.py:352) | H | PARTIAL (QUALITY 390-391) | PARTIAL (385,395,421) | H | n/a | n/a | yes | after :426 |
| P3 compute_situation_summary (narrative_adjudication.py:795-806) | n/a | n/a | n/a | **NOT (no record, 806)** | n/a | n/a | **no** | n/a (prose) |
| P4 generate_character_responses (narrative_adjudication.py:596-608) | n/a | n/a | n/a | PARTIAL (canned line, no record 604-607) | n/a | n/a | **no** | n/a (prose) |
| P5 assess_diplomatic_outcome (engine/diplomacy.py:359-409) | H | H | PARTIAL (377,388) | H | n/a | PARTIAL (llm/parsing.py:83) | yes | after :399 |
| P6 process_turn reply (diplomacy.py:524-528) | n/a | n/a | n/a | **NOT (no guard)** | n/a | n/a | **no** | n/a (prose) |
| P7 handle_player_question (conversation.py:197-207) | n/a | n/a | n/a | **NOT** | n/a | n/a | **no** | n/a (prose) |
| P8 interpret_player_action (conversation.py:212-238) | n/a | n/a | n/a | **NOT** | n/a | n/a | **no** | n/a |
| P9 generate_advisor_pushback (conversation.py:241-307) | H | n/a | H | **NOT (296-297)** | H (caveat 274) | n/a | partial (305) | after :307 |
| P10 check_critical_omissions (conversation.py:395-452) | H | n/a | H | PARTIAL (empty==all-clear 408) | H | n/a | yes | after :438 |
| P11 parse_interpretation_simple (cli/display_utils.py:159-211) | H | n/a | PARTIAL (INTERPRETATION 186-187) | PARTIAL (caller-only 265) | n/a | n/a | caller only | after :209 |
| P12 narrative_assessment (display_utils.py:60-79) | n/a (engine text) | — | — | — | — | — | n/a | n/a |
| P13 apply_inject_effects (engine/sim_loop.py:205-252) | n/a | H | n/a | n/a | n/a | n/a | yes (241) / **no (273)** | n/a |
| P14 generate_inject YAML (llm/inject_generator.py:84-116) | n/a | n/a | n/a | **NOT (no record)** | n/a | n/a | **no** | n/a |
| P15 generate_narrator_bridge (engine/narrator.py:35-48) | n/a | n/a | n/a | NOT (silent drop) | n/a | n/a | **no** | n/a |
| P16 split_briefing (engine/opening.py:165-189) | H (substring) | n/a | n/a | n/a | n/a | n/a | n/a (benign) | n/a |
| P17 server role heuristic (api/server.py:708-727) | **NOT** | n/a | n/a | n/a | n/a | n/a | **no** | n/a |
| P18 bridge.py _render_call (docs/py/bridge.py:930-959) | display-only | — | — | — | — | — | n/a | n/a |
| P20 get_diplomatic_context (llm/context_builder.py:512-563) | classifier-inversion on unlabeled entries (see P20) | — | — | — | — | — | n/a | n/a |
| P21 dashboard speaker split (cli/main_dashboard.py:1042-1055) | **NOT** (display-only) | — | — | — | — | — | no | n/a |

## Duplication of llm/parsing.py

1. engine/narrative_adjudication.py:390-391 — hand-rolled enum membership where match_enum exists (weaker: no annotation tolerance).
2. engine/actor_simulation.py:226, 235 — hand-rolled "none" sentinel compare where is_sentinel_line exists (weaker: quotes/punctuation leak).
3. api/server.py:716-718 — hand-rolled role-prefix match with no strip_decoration and a stale roster (cli/display_utils.py:28-35 holds the correct mapping).
4. cli/display_utils.py:71, 75 (narrative_assessment) — bare startswith label matching; extract_label would be the tolerant form if this ever sees model text.
5. docs/py/bridge.py:96 _LABEL_RE — a third label-shape regex, display-only.

## Parse-health gap list (fallback paths with no record)

- narrative_adjudication.py:806 (summary → None), 604-607 (character response canned line)
- diplomacy.py:524-527 (empty counterpart line)
- conversation.py:201-207 (advisor QA), 237-238 (interpretation), 296-297 (empty pushback message), 408 (empty omissions reply == all-clear)
- llm/inject_generator.py:79-81, 101-104, 112-116 + engine/sim_loop.py:377-381 (quiet-turn fallback)
- engine/sim_loop.py:273 (unknown metric name)
- engine/narrator.py:45-48
- llm/fanout.py:72-76, 82-84 (empty-string failure slots)
- Truncation: NO production caller of record_truncation (llm/parse_health.py:41); attach in llm/openai_compat_driver.py:225-230 and llm/gemini_driver.py:182-188 on finish_reason "length"/MAX_TOKENS.
- Residue: NO production caller of record_residue (llm/parse_health.py:56); attach points listed per parser above (P1 :245, P2 :426, P5 :399, P9 :307, P10 :438, P11 :209).
