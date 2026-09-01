# fogOfWar Kanban
<!-- kanbanger:board-id: 94a0b76877f44e7e8990e61054f91639 -->

## BACKLOG

*   [ ] Show-Safe: verify/fix browser adjudication after PR #57 (decision #73 gates urgency) - Pyodide reported can't start new thread; verify the fallback reads the player's decision and never silently substitutes canned adjudication. Record a real browser-path check.
*   [ ] Delivery: concurrent CLI adjudication pipeline (#64)
*   [ ] Delivery: extend shared cache prefix to the 7 uncached call families (#64)
*   [ ] Delivery: rewrite the delivery plan in mechanical language (#80) - https://github.com/earlyprototype/false-flag/issues/80 — branch docs/80-delivery-plan — depends #79.
*   [ ] Delivery: restore or replace missing DATA_LAYERS.md - models/layers.py and api/server.py cite DATA_LAYERS.md paragraphs, but the file is absent. Recover the intended document from prior session artifacts or replace stale references with a durable current source after understanding the fence.
*   [ ] Show-Safe: fix CLI EOF/Ctrl-C turn loss (#18) - Route cli/main.py prompts through interruption-safe handling and verify an interrupted turn does not disappear behind bare Aborted.
*   [ ] Show-Safe: extend PR #61 block-deletion to the 5 remaining decision-abandon paths + retire cli/main_dashboard.py - #22-class, owner-ruled bugs 27 Aug; include tests. cli/main_dashboard.py is the dead pre-#61 copy.
*   [ ] Advisors: apply the no-defaults ruling (#17) to actor_simulation + quality_assessment - Owner ruling 27 Aug: parse failure -> bounded retry -> visible failure; defaulted fields contribute zero.
*   [ ] Delivery: reconcile public Claude session into durable handover (#79) - Cloud session session_015NPEdfpJtAXR7sqKXHxQAQ is not present in local Claude JSONL files and unauthenticated retrieval is blocked. Obtain/export the public thread without copying credential text, store a sanitised durable handover under Research/System, then reconcile it against PR #67/#69 outputs. https://github.com/earlyprototype/false-flag/issues/79 — branch docs/79-session-reconciliation.
*   [ ] Show-Safe: close 3 information leaks - trust ints, threshold flags, save spoilers
*   [ ] Delivery: fix episodes README Turn 6+ TBD line - contradicts existing turn_006.yaml
*   [ ] Show-Safe: build_play_bundle.py must write index.html with LF on Windows - currently CRLF
*   [ ] Advisors: add state-actor memory for Mystery coherence - Outstanding from the prior DTDL/dashboard handover: designed during 23–27 Aug, not implemented. Recover the existing design before scoping; do not reinvent it.
*   [ ] Delivery: ruff lint — config, cleanup, then CI gate - ruff --select E9,F = 200 findings (56× F821 undefined-name — triage for latent bugs first). Add pyproject config, fix or ignore deliberately, then add the lint step to ci.yml checks job. Deferred from #102.
*   [ ] Show-Safe: Windows test suite — 12 environment/encoding/EOL failures - Reported by Sol 31 Aug: full suite green on Linux CI (721 passed, 3 skipped) but 12 unrelated environment/encoding/line-ending failures on Windows. Likely residue of the .gitattributes/EOL work — triage and fix or mark expected-skip on win32.
*   [ ] Show-Safe: dashboard remaining half — a11y, reset contract, traceability (#92) - https://github.com/earlyprototype/false-flag/issues/92 — supersedes #84/#85/#86; cheap half shipped in PR #98. Remaining per issue body: accessibility pass to WCAG 2.2, full demo-reset contract across control surfaces, data-flow traceability.
*   [ ] XR: WebXR COBRA room - five advisors driven by speak-tags
*   [ ] XR: station-based layer selection via raycast focus
*   [ ] XR: diplomat-call scene switch on same embodiment pipeline
*   [ ] Prompts: default situation summary must preserve turn-specific continuity (#111) - https://github.com/earlyprototype/false-flag/issues/111 — audit finding
*   [ ] Prompts: align inject-generation instructions with the Mystery context boundary (#112) - https://github.com/earlyprototype/false-flag/issues/112 — audit finding
*   [ ] Prompts: return parsed decision-interpretation fields to API clients (#113) - https://github.com/earlyprototype/false-flag/issues/113 — audit finding
*   [ ] Prompts: remove raw markdown from deterministic inject descriptions (#114) - https://github.com/earlyprototype/false-flag/issues/114 — audit finding
*   [ ] Prompts: keep campaign memory on Pro in the Recommended Hybrid preset (#115) - https://github.com/earlyprototype/false-flag/issues/115 — audit finding
*   [ ] Prompts: add advisor fanout to prompt byte-parity coverage (#116) - https://github.com/earlyprototype/false-flag/issues/116 — audit finding
*   [ ] Prompts: make call-log analysis verify every structured family it claims (#117) - https://github.com/earlyprototype/false-flag/issues/117 — audit finding
*   [ ] Prompts: keep deterministic decision interpretation faithful to submitted forces (#119) - https://github.com/earlyprototype/false-flag/issues/119 — audit finding
*   [ ] Prompts: preserve concrete asks and commitments across diplomacy calls (#120) - https://github.com/earlyprototype/false-flag/issues/120 — audit finding
*   [ ] Prompts: enforce the inject output-shape and channel contract (#121) - https://github.com/earlyprototype/false-flag/issues/121 — audit finding
*   [ ] Prompts: make narrator bridges connect to the player decision (#122) - https://github.com/earlyprototype/false-flag/issues/122 — audit finding
*   [ ] Delivery: scope development to one game type plus Mystery mode (#89) - https://github.com/earlyprototype/false-flag/issues/89 — full work order in the issue; own branch; crosses ~29 files; solo dispatch
*   [ ] Advisors: give advisors the hidden-state model foreign actors have (#90) - https://github.com/earlyprototype/false-flag/issues/90 — item 3 overlaps #88; agree the boundary before dispatch
*   [ ] Advisors: /private advisor channel (#15) - https://github.com/earlyprototype/false-flag/issues/15 — distinct from #88 private memory; neither delivers the other
*   [ ] Advisors: bilateral relations rendering + newspaper front page (#11) - https://github.com/earlyprototype/false-flag/issues/11 — relations already render in intel panel; front page unbuilt
*   [ ] Delivery: role packs design (#24) - https://github.com/earlyprototype/false-flag/issues/24 — long-horizon design; depends on #89 mode decision
*   [ ] Show-Safe: real-channel email inject artifact (#76) - https://github.com/earlyprototype/false-flag/issues/76 — owner-confirmed MVP-worthy demo artifact
*   [ ] XR: live-hybrid mode (#77) - https://github.com/earlyprototype/false-flag/issues/77 — owner-confirmed design record; per-layer real/simulated seam
*   [ ] Prompts: voice production bible (#78) - https://github.com/earlyprototype/false-flag/issues/78 — body is mojibake at source, re-paste needed
*   [ ] Globe: Manus research queue (#70) - https://github.com/earlyprototype/false-flag/issues/70 — P1a landed via PR #99; P1b/P1c/P2a/P2b/P3 unfired; owner fires
*   [ ] XR: decide the VR room delivery route (#127) - https://github.com/earlyprototype/false-flag/issues/127 — OPEN, owner rules; Unity-native room vs the owner's WebXR walk-in proposal (advisors in seats, screens load data layers). No default.

## TODO

*   [ ] Advisor private continuity and per-agent state (#88) - https://github.com/earlyprototype/false-flag/issues/88 — depends #87 — supersedes #82. Carry-overs from #82 close: preserve objector-only override charge (engine/game_manager.py:447-470, no double-charge); DTDL extend-only; private-memory isolation tests (Mystery off+on). Sentiment doc is design input, not spec.

## DOING


## REVIEW
*   [ ] Fan out advisor pushback to one LLM call per advisor (#87) - https://github.com/earlyprototype/false-flag/issues/87 — branch feat/87-advisor-pushback-fanout — supersedes #81. Remaining after #96: per-advisor fan-out via generate_group; /ask keyword router PM-voice bug; carry-overs from #81 close: Mystery-leak tests + DTDL extend-only + browser/preview parity.
*   [ ] PH-0 Prune ~17 stale/merged branches (29 Aug: 7 local + 22 remote deleted; active branches remain)
*   [ ] Audit recent Claude threads and enforce onboarding - Verify the last few Claude sessions against PLAN/docs, correct source attribution, and make AGENTS/CLAUDE point future sessions to the recent-session index.

## DONE

*   [x] Delivery: tech element briefs for future agents (#128) - https://github.com/earlyprototype/false-flag/issues/128 — docs/tech/ fact-files: WEBXR, CESIUM, CONVAI, QUEST3, SERVER_STREAMING + index; agent-executed, PR through the gate.
*   [x] Audit runtime prompt quality and regression evidence (#83) - https://github.com/earlyprototype/false-flag/issues/83 — branch audit/83-prompt-quality-regression.
*   [x] Reconcile Situation Globe status docs (#109) - https://github.com/earlyprototype/false-flag/issues/109 — rescued uncommitted doc edits from the PR #99 session live on branch docs/rescue-pr99-session-edits; rebase their intent onto current truth (Stage 1 DONE, #99 merged, #72/#74 ruled) and land through the gate.
*   [x] Globe manual zoom controls: +/− buttons and slider (#107) - https://github.com/earlyprototype/false-flag/issues/107 — branch feat/107-globe-zoom-controls — owner-requested input redundancy (trackpad pinch unreliable; projector rigs). PM-built small bounded fix.
*   [x] Issue #100: keep Situation Globe URL on last successful session - https://github.com/earlyprototype/false-flag/issues/100 — requiring TDD, isolated branch, PR, review.
*   [x] PR #99: resolve review findings and restore canonical docs - https://github.com/earlyprototype/false-flag/pull/99 — align fallback semantics to the normative degradation ladder; set St Fergus confidence to medium; preserve the already-correct Stage 1 BUILT status; tests/review; report PR.
*   [x] PR #97: remove advisor turn leak and rebase onto main - https://github.com/earlyprototype/false-flag/pull/97 — requiring focused regression test, conflict resolution/regeneration, review.
*   [x] Add three-stage CI pipeline (#102) - https://github.com/earlyprototype/false-flag/issues/102 — branch ci/102-three-stage-pipeline — port LCCL checks + Claude review gate + dormant auto-merge; lint gate deferred (200 E9/F findings).
*   [x] Capture Claude handover and reconcile current state - Recover the linked Claude session, reconcile it with current main/GitHub, correct stale handovers, and capture actionable work without duplicating PLAN.md.
*   [x] DTDL dataflow build (PR #65): merged 28 Aug - owner browser review positive (/dataflow DTDL)
*   [x] Dashboard twin-model panel (PR #66): merged 28 Aug - Session;1 telemetry, game-type selector, review fixes
*   [x] SEDL alignment doc - False Flag scenario model mapped to SEDL (Nuwa pilot-partner artifact)
*   [x] After #57 merges: align or document 3 browser/terminal parity deviations (/decide with text, extra openers, bare intel)
*   [x] PH-0 Rewrite or retire GEMINI.md and fix GAME_DESCRIPTION.md stale claims
*   [x] PH-0 Annotate frozen UX/UI/WebApp trackers and link audits/ from README
*   [x] PH-0 Retire or repair scripts/gate_runner.py and status_board.py
*   [x] PH-0 Add .gitattributes (eol=lf, game.zip binary) - bundle-hash tests break on Windows checkouts
*   [x] PH-0 Fix channel vocabulary drift - episodes README declares wrong channel set vs real turn YAML, and sim_loop.py colouring uses a third vocabulary
*   [x] PH-0 Fix #16 second confirm discards enhanced decision (cli/main.py:1866)
*   [x] PH-0 Fix #22 double decision transcript on apply-recommendations branch
*   [x] PH-0 Update episodes README turn summaries if PR 59 merges (left stale by re-pace)
*   [x] PH-1 Layer enum + layer-tagged push_event extension in api/server.py
*   [x] PH-1 call_log to live SSE relay
*   [x] PH-1 Dashboard MVP page - T+ ledger, metric traces, per-call cards
*   [x] PH-1 Seed dashboard from play_campaign.py batch runs (conditions axis)
*   [x] PH-2 Reroute matrix UI - 12 LLMContexts x provider/tier live switch
*   [x] PH-2 Prompt hot-edit - externalise templates with reload
*   [x] PH-2 Inject console - dashboard visual component; manual content authoring + trigger control (approved)
*   [x] Republish strategy artifact with 22 Aug scoping ruling folded in
*   [x] Operable data-flow view: live schema + game-type selector + click-to-reroute/prompt-edit (owner req 1+2)
*   [x] Mystery context segregation: player-facing calls never see the secret, scrubber deleted (PR #63)
*   [x] Run official DTDLParser on interop models once .NET SDK available (structural-only today)
*   [ ] Delivery: raise review max-turns to 50 (PR #129) - https://github.com/earlyprototype/false-flag/pull/129 — merged by owner (review self-skips its own machinery). Recorded post-merge; guardrail follow-up to the #126 turn-limit incident.
