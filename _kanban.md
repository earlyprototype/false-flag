# fogOfWar Kanban
<!-- kanbanger:board-id: 94a0b76877f44e7e8990e61054f91639 -->

## BACKLOG

*   [ ] Future / unprioritised work
*   [ ] PH-3 WebXR COBRA room - five advisors driven by speak-tags
*   [ ] PH-3 Station-based layer selection via raycast focus
*   [ ] PH-3 Diplomat-call scene switch on same embodiment pipeline
*   [ ] PH-4 Route CLI adjudication through concurrent pipeline
*   [ ] PH-4 Extend shared cache prefix to the 7 uncached call families
*   [ ] Close 3 information leaks - trust ints, threshold flags, save spoilers
*   [ ] PH-3 Choose Convai route - (a) Unity V3 WebGL build vs (b) Web SDK per-turn re-target, rec (b)
*   [ ] Fix episodes README Turn 6+ TBD line - contradicts existing turn_006.yaml
*   [ ] build_play_bundle.py write index.html with newline=LF on Windows (currently CRLF)
*   [ ] Add state-actor memory for Mystery coherence - Outstanding from the prior DTDL/dashboard handover: designed during 23–27 Aug, not implemented. Recover the existing design before scoping; do not reinvent it.
*   [ ] Ruff lint: config, cleanup, then CI gate - ruff --select E9,F = 200 findings (56× F821 undefined-name — triage for latent bugs first). Add pyproject config, fix or ignore deliberately, then add the lint step to ci.yml checks job. Deferred from #102.

## TODO

*   [ ] Ready to start, prioritised
*   [x] PH-0 Prune ~17 stale/merged branches (29 Aug: 7 local + 22 remote deleted; active branches remain)
*   [ ] No-defaults ruling (#17, owner 27 Aug): parse failure -> bounded retry -> visible failure; defaulted fields contribute zero. Apply to actor_simulation + quality_assessment families
*   [ ] Extend PR #61 block-deletion to the 5 remaining decision-abandon paths (#22-class, owner-ruled bugs 27 Aug) + tests; retire dead pre-#61 copy cli/main_dashboard.py
*   [ ] Fix CLI EOF/Ctrl-C turn loss (#18) - Route cli/main.py prompts through interruption-safe handling and verify an interrupted turn does not disappear behind bare Aborted.
*   [ ] PH-0 Verify/fix browser adjudication after PR #57 - Pyodide reported can't start new thread; verify the fallback reads the player's decision and never silently substitutes canned adjudication. Record a real browser-path check.
*   [ ] Restore or replace missing DATA_LAYERS.md - models/layers.py and api/server.py cite DATA_LAYERS.md paragraphs, but the file is absent. Recover the intended document from prior session artifacts or replace stale references with a durable current source after understanding the fence.
*   [ ] Rewrite the delivery plan in professional, mechanical language (#80) - https://github.com/earlyprototype/false-flag/issues/80 — branch docs/80-delivery-plan — depends #79.
*   [ ] Generate decision pushback independently for each advisor (#81) - https://github.com/earlyprototype/false-flag/issues/81 — branch feat/81-independent-advisor-pushback.
*   [ ] Persist advisor-specific trust and private decision memory (#82) - https://github.com/earlyprototype/false-flag/issues/82 — branch feat/82-advisor-trust-memory — depends #81.
*   [ ] Audit runtime prompt quality and regression evidence (#83) - https://github.com/earlyprototype/false-flag/issues/83 — branch audit/83-prompt-quality-regression.
*   [ ] Add data-flow descriptions, traceability and zoom controls (#84) - https://github.com/earlyprototype/false-flag/issues/84 — branch feat/84-dataflow-traceability-controls.
*   [ ] Provide a reliable demo reset across control surfaces (#85) - https://github.com/earlyprototype/false-flag/issues/85 — branch fix/85-control-surface-demo-reset.
*   [ ] Audit control-surface visual information and accessibility (#86) - https://github.com/earlyprototype/false-flag/issues/86 — branch audit/86-control-surface-accessibility — depends #84/#85.
*   [ ] Issue #100: keep Situation Globe URL on last successful session - https://github.com/earlyprototype/false-flag/issues/100 — requiring TDD, isolated branch, PR, review.

## DOING

*   [ ] Reconcile public Claude session into sanitised durable handover (#79) - Cloud session session_015NPEdfpJtAXR7sqKXHxQAQ is not present in local Claude JSONL files and unauthenticated retrieval is blocked. Obtain/export the public thread without copying credential text, store a sanitised durable handover under Research/System, then reconcile it against PR #67/#69 outputs. https://github.com/earlyprototype/false-flag/issues/79 — branch docs/79-session-reconciliation.
*   [ ] PR #99: resolve review findings and restore canonical docs - https://github.com/earlyprototype/false-flag/pull/99 — align fallback semantics to the normative degradation ladder; set St Fergus confidence to medium; preserve the already-correct Stage 1 BUILT status; tests/review; report PR.
*   [ ] Situation Globe — await owner GO, then execute PLAN.md - PLAN.md is the sole implementation plan. Keep this as one pointer; move it to TODO only when the owner explicitly authorizes Stage 1 First Light.
*   [ ] In progress (keep to 1-3 items)

## REVIEW
*   [ ] PR #97: remove advisor turn leak and rebase onto main - https://github.com/earlyprototype/false-flag/pull/97 — requiring focused regression test, conflict resolution/regeneration, review.
*   [ ] Audit recent Claude threads and enforce onboarding - Verify the last few Claude sessions against PLAN/docs, correct source attribution, and make AGENTS/CLAUDE point future sessions to the recent-session index.
*   [ ] AI-completed work awaiting human approval

## DONE
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
*   [x] Completed, human-approved work
