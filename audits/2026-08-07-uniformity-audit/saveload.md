# FALSE FLAG — Save/Load Completeness Audit (post-ER-047)

Status: COMPLETE.
Repo: /home/user/false-flag @ claude/game-audit-pr-review-u6ujyq (read-only audit).
Trigger: ER-047 (live diplomatic call dropped by save). Question: is every piece of mutable state covered, and is every save-point resumable?

Legend:
- **FULLY-COVERED** — written by to_dict, restored by from_dict, asserted by a named round-trip test.
- **RESTORED-NOT-TESTED** — serialized and restored, but no test pins the specific field.
- **SAVED-NOT-RESTORED** — written but never read back. (None found.)
- **UNSAVED** — mutable state that never reaches the payload.
- **EPHEMERAL/DERIVED (OK)** — deliberately not saved; rebuilt or harmless to lose.

Headline: **2 real gaps (F1 `_pending_pushback` unsaved, F2 post-briefing saves not marked as replays — the browser's own round-trip test exercises the double-apply without detecting it), 1 format split (CLI format lacks ending/encounter), plus test-coverage holes (actor_system, narrative sub-fields).**

---

## 1. GameManager field matrix (engine/game_manager.py)

`to_dict`: engine/game_manager.py:624-663. `from_dict`: :699-770. `_encounter_state`: :665-678. `save_game`/`load_game` (file wrappers): :680-697, :772-780.

| Field (where set) | Saved | Restored | Round-trip test | Verdict |
|---|---|---|---|---|
| `scenario_id` (:56) | :643 | :709 (ctor) | tests/test_web_bridge.py:133 `test_session_round_trips_through_to_dict` | FULLY-COVERED |
| `variant` (:57) | :644 | :710 | test_web_bridge.py:145 | FULLY-COVERED |
| `difficulty` (:58) | :645 | :711 | none | RESTORED-NOT-TESTED (also rides `world.difficulty`, models/world.py:32) |
| `play_mode` (:59) | :646 | :712 | test_web_bridge.py:144 | FULLY-COVERED |
| `seed` (:60) | :647 | :713 | exercised via rng tests | FULLY-COVERED |
| `mystery_mode` (:61) | :647 | :714 | test_web_bridge.py:146 | FULLY-COVERED |
| `rng` position (:62) | :661 via `encode_rng_state` (engine/persistence.py:25-32) | :738-741 (`setstate` AFTER ctor so the Mystery draw can't corrupt it — comment :735-737) | tests/test_game_manager.py:179 `test_save_load_resumes_the_draw_sequence`; :216 `test_old_payload_without_rng_state_still_loads` | FULLY-COVERED |
| `endings_enabled` (:66) | :648 (`config.endings`) | :715 | test_web_bridge.py:147 | FULLY-COVERED |
| `ending` (:67) | :655 (`ending_id` only) | :732 via `get_ending` | test_web_bridge.py:156 `test_ended_campaign_round_trips_as_ended`; :187 `test_unknown_ending_id_loads_as_a_playable_session` | FULLY-COVERED |
| `root_path` (:70) | — | recomputed | n/a | EPHEMERAL/DERIVED (OK, machine-local) |
| `transcript` (:71) | :654 | :724 | only growth asserted (tests/test_diplomatic_features.py:434-437); no equality test | RESTORED-NOT-TESTED (weak) |
| `active_encounter` (:72) | :658 via `_encounter_state` (:665-678; live calls only, ended calls dropped by design :667-669) | :752-768 | tests/test_diplomatic_features.py:415 `test_live_encounter_survives_save_and_load`; :439 `test_ended_encounter_is_not_resurrected_by_a_round_trip` | FULLY-COVERED (subfields §2) |
| `_pending_pushback` (:77) | **NO** | **NO** | none | **UNSAVED — FINDING F1** |
| `_resume_replay` (:84) | not saved (derived) | derived :746-747 from `world.phase in ("discussion","decision","adjudication")` | tests/test_game_manager.py:231 `test_mid_turn_load_replays_briefing_without_reapplying` (:245 True, :255 one-shot) | DERIVED — derivation has a hole, **FINDING F2** |
| `initial_conditions` (:99) | — | reloaded from scenario files (:99 via ctor) | n/a | EPHEMERAL/DERIVED (OK, static data) |
| `world` (:113-128) | :651 `self.world.dict()` | :722 `WorldState.parse_obj` | test_web_bridge.py:143,148-150 (turn, narrative_id, metrics) | top-level FULLY-COVERED; per-field §3 |
| `narrative_state` (:140-144) | :652 `.dict()` | :723 `NarrativeState.parse_obj` | model-level only (§4) | RESTORED-NOT-TESTED per-field |
| `scenario_config` (:147) | — | reloaded in ctor from scenario_id+variant | n/a | EPHEMERAL/DERIVED (OK) |
| `initial_metrics_snapshot` (:91-95) | :654 (`state.initial_metrics`) | :725-726 | test_web_bridge.py:148 | FULLY-COVERED |

### FINDING F1 — `_pending_pushback` is dropped by save/load (same shape as ER-047)
- Set by `interpret_decision` (engine/game_manager.py:271-273); consumed by `resolve_decision` (:352-355) to charge the ER-013 trust cost for committing pushback-drawing text verbatim.
- `to_dict` (:624-663) never writes it; `from_dict` leaves the fresh `None` from :77.
- Repro: API `/game/decision/interpret` (api/server.py:777) → `/game/save` (:467) → `/game/load` (:486) → `/game/decision/commit` with identical text. The advisor trust penalty silently vanishes. Same class as ER-047: field lives on the live object, never serialized.
- Severity: low-moderate; the sequence is legal on both the API and the browser worker.

### FINDING F2 — a save taken after the briefing but before the first question is not marked as a replay (headless front ends)
- `from_dict` infers `_resume_replay` from `world.phase in ("discussion","decision","adjudication")` (engine/game_manager.py:746-747). But `run_turn_briefing` sets `world.phase = "briefing"` (engine/sim_loop.py:345) and nothing in GameManager advances it until the first `process_question` (phase→"discussion" at engine/sim_loop.py:538); `interpret_decision` runs `dry_run=True`, which skips the phase write (engine/sim_loop.py:606-607).
- So a save between `get_turn_briefing()` and the first question stores `phase == "briefing"`; on load `_resume_replay` is False, and the front end's next `get_turn_briefing()` **re-applies the inject's metric effects (engine/sim_loop.py:437-439), re-appends `recent_injects` (:443-445), and re-opens the mandatory call (:448-497 / game_manager.py:178-198)** — the exact double-apply ER-004 exists to prevent. (`record_played_event` dedups by turn, models/narrative_state.py:341-352, so the ledger alone survives.)
- The terminal CLIs dodge this **deliberately**: cli/main.py:1011 and cli/main_dashboard.py:977 force `world.phase = "discussion"` before the /save-capable loop ("A save from here on resumes as a replay"). GameManager has no equivalent.
- Exposure by front end:
  - **API**: window = between `/game/{id}/briefing` and `/game/{id}/briefing/ack` (the ack is the only thing that sets phase→"discussion" server-side, api/server.py:680). Narrow but real; nothing stops `/game/save` there.
  - **Browser**: window = the whole start of every turn. The bridge never acks phase; after a briefing the player sits at AWAIT_DECISION with `phase=="briefing"` until they ask a question. Saving at "start of turn" is the most natural save moment there is; the worker accepts `save` at any awaiting state (docs/py/bridge.py:1240-1243).
  - **Smoking gun**: the shipped test tests/test_web_bridge.py:557 `test_save_and_load_round_trip` performs decide → endTurn (briefing for the next turn runs) → save → load; the load path (`bridge.load` :1162 → `start_briefing` :1185 → `run_briefing` :735 → `get_turn_briefing`) **re-applies that turn's inject effects**, and the test doesn't notice because it only asserts `world.turn` equality (:570). The double-apply ships today, exercised but unasserted.
- Fix shape: advance `world.phase` to "discussion" at the end of `get_turn_briefing` (mirroring the CLIs), or persist an explicit `briefing_played_for_turn: int` and derive the replay from it.

### FINDING F3 — actor_system round-trips untested
StateActorSystem carries real mutable campaign state — `relationship_uk` (models/state_actors.py:15), `recent_actions`/`trust_trajectory`/`last_contacted_turn` (:51-53), `threat_perception` (:27) — and rides inside `world.dict()`, so it is saved+restored; but no test in tests/ asserts any actor field survives a round trip. A pydantic schema change would regress silently.

## 2. DiplomaticEncounter subfields (engine/diplomacy.py:419-577) vs `_encounter_state` (engine/game_manager.py:665-678)

| Attr | Saved | Restored | Verdict |
|---|---|---|---|
| `country` (:428) | :671 | :757 | FULLY-COVERED (test_diplomatic_features.py:428) |
| `context` (:429) | :672 | :758 | FULLY-COVERED |
| `show_metrics` (:431) | :673 | :761 | RESTORED-NOT-TESTED |
| `required` (:440) | :674 | :762 | FULLY-COVERED (:427) |
| `transcript` (:451) | :675 | :765 | FULLY-COVERED (:430) |
| `history` (:452) | :676 (lists) | :766 (tuples) | FULLY-COVERED (drivability :433-437) |
| `_player_exchanges` (:459) | :677 (key `player_exchanges`) | :767 | FULLY-COVERED (:429) |
| `world`/`narrative_state`/`full_transcript` refs (:427,:436,:445) | — | re-wired to restored objects :756,:760,:763 | DERIVED (OK) |
| `profiles`/`access_level`/`profile`/`title`/`max_exchanges` (:447-458) | — | re-derived in ctor from restored world | DERIVED (OK — same metrics ⇒ same access) |
| `active` (:453) | implicit (only live calls saved) | ctor True | OK by construction |
| `outcome` (:454) | — | fresh None | OK — ended calls deliberately unsaved; the cohesion delta already landed (comment engine/game_manager.py:656-657) |

## 3. WorldState (models/world.py:20-67) — all 13 fields are pydantic, so all ride `world.dict()`/`parse_obj`
`turn` :22, `phase` :23, `narrative` (Mystery secret truth — the "secret role/scenario") :26, `scene` :29, `difficulty` :32, `metrics` :35, `flags` :36, `posture` :37, `spatial_state` :40, `discussion_transcript` :46, `recent_injects` :52, `diplomatic_relationships` :58, `actor_system` :64.
- Tested: turn/metrics/narrative (test_web_bridge.py:143,148-150); world equality in the CLI format (tests/test_persistence.py:63-67).
- Untested through GameManager: flags, posture, spatial_state, recent_injects, diplomatic_relationships, actor_system (F3) → RESTORED-NOT-TESTED.
- `discussion_transcript` correctly saved mid-turn and cleared at end of turn (engine/game_manager.py:415; cli/main.py:2005).

## 4. NarrativeState (models/narrative_state.py:63-101) — all pydantic, all serialized
`hidden_metrics` :72, `previous_metrics` :75 (drives trend arrows :169-178 — saved, untested), `situation_summary` :80, `recent_events` :83, `event_ledger` :88, `characters` (CharacterAttitude trust/relationship/stance :36-43) :91, `active_crises` :94, `turn` :97, `game_time` :98, `play_mode` :101.
- Serialized at engine/game_manager.py:652, restored :723.
- Model-level ledger round trip: tests/test_event_ledger.py:107 `test_ledger_round_trips_and_old_saves_load_clean` (also pins old-save default :116-117). No GameManager-level test pins characters/trust, situation_summary, previous_metrics, game_time, active_crises → RESTORED-NOT-TESTED.
- Advisor trust changes go through `update_character_attitude` (:310-332) into `characters` — covered by serialization; the *pending* pushback that would change it is F1.

## 5. Deliberately ephemeral state (explicitly fine)
- **Parse-health counters**: llm/parse_health.py:18-21 module dicts `_misses/_fallbacks/_truncations/_residues`. Telemetry, not game state. EPHEMERAL (OK).
- **CLI loop locals**: cli/main.py:812 `endings_disabled` (toggled at :2049 — note: *this one is arguably state*: a player who disabled endings and resumes gets them back on; minor), :821 `last_vignette`, :825 `parse_health_seen`, :829 `generation_banner_shown`. Cosmetic/telemetry except `endings_disabled` (minor finding F9).
- **Bridge session locals**: docs/py/bridge.py:398-410 `width`, `awaiting`, `_call_seen`, `key_source`, `_parse_health_seen`, `_paused` beat queue. UI pacing; `load()` clears `_paused` deliberately (:1171, tested tests/test_web_bridge.py:314). EPHEMERAL (OK). `_call_seen` reset at :1168 so a restored call re-renders from the top — OK.
- **API session envelope**: api/server.py:43-56 `GameSession.event_queue` + module `sessions` dict. In-memory only: a server restart loses every session not explicitly saved; no autosave exists on the API path (only explicit `/game/save`). Accept or document.

## 6. Second format: engine/persistence.py (used by both terminal CLIs) — narrower than GameManager's

Writer `save_game`: engine/persistence.py:50-104 (format "2.3"; fields at :91-101: scenario_id, world, transcript, play_mode, narrative_state, variant, initial_metrics, rng_state). Loader `load_game`: :142-179 + field readers :107-139.
Call sites: cli/main.py:1067 (/save), :2008 (end-of-turn autosave); cli/main_dashboard.py:1100, :1776. Load: cli/main.py:721-744; cli/main_dashboard.py:745-768.
Tests: tests/test_persistence.py:38,70,90,103,115,141,154,173 cover initial_metrics, variant, rng position, old-save defaults — good coverage *of the fields it has*.

### FINDING F4 — CLI format has no `ending` field; the finished-campaign autosave resumes as playable
- GameManager persists `ending_id` (engine/game_manager.py:655) and restores it (:732). The CLI format has no such key (engine/persistence.py:91-101).
- cli/main.py computes the ending at :1997-1998, then advances the turn and writes the autosave at :2008 **before** the debrief. A graded classic campaign leaves an autosave that the startup resume-offer (cli/main.py:597-617) reloads as a live turn-N+1 game. Same at cli/main_dashboard.py:1776.

### FINDING F5 — cross-format asymmetry (a field saved in one format but not the other)
- `active_encounter`: GameManager-only (engine/game_manager.py:658). Acceptable-by-construction in the CLI — /save is only reachable inside the discussion loop (cli/main.py:1066-1069) and diplomatic calls run blocking with no save affordance — but the two formats have different resumable envelopes, and a GameManager save opened by... nothing: the formats are mutually unreadable (different top-level shape), so no cross-load corruption, just capability divergence.
- `seed`: GameManager saves it (:647); CLI format stores only the rng *position* (engine/persistence.py:99). A resumed CLI campaign cannot report its seed.
- `ending` (F4), `mystery_mode`/`endings` config flags: GameManager-only (the Mystery *secret* itself survives both via `world.narrative`).
- `difficulty`: survives both via `world.difficulty`; the CLI's load-path default at cli/main.py:640 is dead weight but harmless.

## 7. api/server.py — GameManager's format, no drift, but resume surfacing is thin
- Save: api/server.py:467-483 → `manager.save_game` (GameManager format). Load: :486-507 → `GameManager.load_game` into a new session. List: :510-522.
- **FINDING F7**: after `/game/load` the client gets only `{session_id, turn, phase, metrics}` (:498-503); no endpoint returns the session transcript or a restored live call's lines (`GET /game/{id}` returns turn/phase/metrics/advisors only, :331-344). A restored mandatory call is enforced (`_require_no_mandatory_call` :732-747 blocks briefing/decision) but the client has no way to *see* the call it must answer. Saved-and-restored but not surfaced.
- `/game/new` (:259-271) accepts no seed/mystery_mode/endings — every API campaign runs the default `seed=42` (engine/game_manager.py:36). Not a save bug; determinism footnote.
- api/test_save_api.py:4 `test_save_api` checks HTTP plumbing (save→list→load→state), not field fidelity.

## 8. docs/py/bridge.py — GameManager's format via to_dict/from_dict; best resume story of the three
- Save: bridge.py:1151-1160 (`gm.to_dict("browser")` → JSON string to the page; page owns localStorage). Load: :1162-1185 (`from_dict`, clears stale beats :1171, then `push_state` and either `_emit_ending` :1183 for a finished game or `start_briefing` :1185).
- Resume of a live mandatory call works end to end: after the (replayed) briefing, `_finish_briefing` :818-830 detects `_required_call_live()` (:843-847), re-renders the restored `encounter.transcript` from line 0 (`_call_seen` reset at :1168) and puts the player back on the line. `ask`/`decide` are gated meanwhile (:852-854, :967-969).
- **FINDING F8 (minor)**: an *optional* (player-initiated) live call also survives the round trip, but nothing re-surfaces it: `_finish_briefing` only checks required calls, so after a load the player is told "YOUR MOVE" (:833) while `gm.active_encounter` is still live — their next `call` message, whatever country they name, is routed into the old restored encounter (`live` check bridge.py:890-891 ignores the country argument when a call is live).
- Bridge tests: tests/test_web_bridge.py:557 round trip (weak — see F2), :314 stale beats, :379 split-briefing-after-load pause.

## 9. Phase boundaries — where can a save occur, and does it resume?

Phase machine: `Phase = Literal["briefing","discussion","decision","adjudication"]` (models/world.py:15). Writers: briefing engine/sim_loop.py:345; discussion :538; decision :607 (skipped on dry_run) and engine/decision_phase.py:308; adjudication engine/sim_loop.py:666; reset-to-briefing engine/game_manager.py:413 / cli/main.py:2006. API ack: api/server.py:680.
Replay consumption: `_resume_replay` set at engine/game_manager.py:746-747, consumed once at :156-157 (`replay = self._resume_replay; self._resume_replay = False`), passed to run_turn_briefing :169; CLI equivalents cli/main.py:744→:874-880 area (flag cleared after first briefing; dashboard :768→:899, cleared :915).

| Save point | Reachable via | Stored phase | Resume correct? |
|---|---|---|---|
| Start of turn, briefing not yet run | CLI autosave (cli/main.py:2008, written after turn++/phase="briefing" :2003-2006); GameManager save right after `resolve_decision` | briefing | **YES** — replay=False is right; next briefing is genuinely new. Tested: tests/test_game_manager.py:216 area, test_web_bridge.py:557 (turn only) |
| After briefing ran, before first question / before ack | API save pre-ack; browser save at AWAIT_DECISION or mid-briefing AWAIT_PAUSE; GameManager.save_game any time | briefing | **NO — F2 double-apply.** Not reachable in the CLIs (phase forced to "discussion" first, cli/main.py:1011 / main_dashboard.py:977) |
| Mid-discussion (≥1 question asked) | CLI /save (cli/main.py:1067); API post-ack; browser after an ask | discussion | **YES** — replay=True; effects/ledger/mandatory call skipped (engine/sim_loop.py:363, :387, :437, :449); replay banner :498-501. Tested: tests/test_game_manager.py:231 |
| Mid-required-encounter | GameManager/API/browser only (CLI blocks) | briefing or discussion | **Encounter itself: YES (ER-047 fix**, tested tests/test_diplomatic_features.py:415). But if no question was asked before the call (the normal mandatory-call flow — it opens with the briefing), phase is "briefing" → **F2 also re-opens/re-applies on load**; the restored encounter object is then overwritten by the freshly re-created one (engine/game_manager.py:182-193). Compound failure. |
| After decision preview, before commit | API interpret→save; browser has no preview path; CLI /save unreachable inside decision loop (no /save handler there — cli/main.py:1688-1848 loop has no save command) | discussion (dry_run leaves phase) | Replay: YES. **Pushback memory: NO — F1.** |
| Mid-adjudication (pipeline running) | No front end exposes a save mid-`resolve_decision` (synchronous); a crash there loses the turn back to the last save | adjudication | Phase "adjudication" can only be *stored* by a save taken in the tiny window... in practice never stored; from_dict still treats it as replay (:747) — safe default. |
| After commit, before reactions rendered | Browser: `save` at AWAIT_CONFIRM (post-decide, pre-endTurn) | briefing (already advanced, game_manager.py:412-413) | YES — resumes at next turn's briefing; rendered-but-unread reaction text is in the saved transcript. |
| Campaign ended | Browser save allowed when over (bridge.py:1243); API too | briefing | YES — `ending_id` round-trips (test_web_bridge.py:156); bridge re-emits ending on load (:1182-1183). **CLI: NO — F4** (its format has no ending). |

## 10. RNG determinism
- Master generator: `GameManager.rng` (engine/game_manager.py:62); position saved :661, restored **after** construction :738-741 (constructor burns the Mystery draw — ER-037, comment :733-737). CLI: saved via `rng=` at cli/main.py:1067/2008, restored cli/main.py:733-737 (`rng.setstate` :735); dashboard cli/main_dashboard.py:757-759. Encoding: engine/persistence.py:25-46. Tests: tests/test_persistence.py:115,141,154,173; tests/test_game_manager.py:179,216.
- Child generators are all **derived from the master at call time**, so they are automatically re-anchored after load: decision-round child seeds `rng.randint` engine/decision_phase.py:160, consumed at :165; batch-driver child seeds llm/openai_compat_driver.py:261, consumed :265. No consumer holds a private long-lived Random across a save.
- Non-anchored instantiations, all benign: engine/sim_loop.py:733 `Random(42)` default inside legacy `run_full_turn` (only caller: deprecated `run_single_scene` :786 — not on any front-end path); engine/sim_loop.py:767 fresh `Random(seed)` in the same legacy helper; docs/py/bridge.py:602-603 module `random.randrange` used solely to pick a *new campaign's* seed before any game exists.
- Residual nondeterminism after load is only what already exists without saving: live-LLM output. No RNG gap found.

## 11. Design sketch — completeness-by-construction test

Goal: the next `self.whatever = ...` added to GameManager (or a new field on an encounter) fails CI unless it is either serialized or explicitly declared ephemeral. Two layers:

```python
# tests/test_saveload_completeness.py (sketch)

# Attributes that are DELIBERATELY not serialized. Adding an attribute to
# GameManager without adding it here or to to_dict fails the test.
EPHEMERAL_MANAGER_FIELDS = {
    "root_path",           # machine-local; recomputed in __init__
    "initial_conditions",  # static scenario data, reloaded from disk
    "scenario_config",     # static scenario data, reloaded from disk
    "_resume_replay",      # derived by from_dict from world.phase
    # NOTE: "_pending_pushback" must NOT be whitelisted — fixing F1 means
    # serializing it; until then this test documents the bug as an xfail.
}
EPHEMERAL_ENCOUNTER_FIELDS = {
    "world", "narrative_state", "full_transcript",       # re-wired refs
    "root_path", "profiles", "profile", "access_level",  # re-derived
    "title", "max_exchanges", "active", "outcome",       # re-derived / by-construction
}

def played_manager():
    gm = GameManager(seed=7, play_mode="classic", mystery_mode=True)
    gm.world.turn = 6               # turn with a scripted mandatory call
    gm.get_turn_briefing()
    gm.process_question("CDS, options?")
    gm.interpret_decision("Blockade the strait.")   # populates _pending_pushback
    gm.process_diplomacy("We stand with NATO.")     # live encounter state
    return gm

def test_every_live_manager_attribute_is_serialized_or_whitelisted():
    gm = played_manager()
    payload = gm.to_dict()
    restored = GameManager.from_dict(json.loads(json.dumps(payload, default=str)))
    for name, value in vars(gm).items():            # introspect LIVE object
        if name in EPHEMERAL_MANAGER_FIELDS:
            continue
        restored_value = getattr(restored, name, _MISSING)
        assert _equivalent(value, restored_value), (
            f"GameManager.{name} does not survive to_dict/from_dict — "
            f"serialize it or add it to EPHEMERAL_MANAGER_FIELDS with a reason")

def _equivalent(a, b):
    # pydantic models compare via .dict(); Random via .getstate();
    # DiplomaticEncounter via its own vars() minus EPHEMERAL_ENCOUNTER_FIELDS;
    # everything else via ==.
```

Key properties:
1. **`vars(live_object)` is the source of truth**, not a hand-kept field list — a new `self.x` shows up automatically. Same introspection applied recursively to `active_encounter` (against `EPHEMERAL_ENCOUNTER_FIELDS`) and, via `model_fields`, to WorldState/NarrativeState so a pydantic field marked `exclude=True` or shadowed by a custom serializer is caught too.
2. **The fixture must exercise every phase**: briefing run, question asked, decision previewed, call live — otherwise optional fields sit at their defaults and a dropped field compares equal. `played_manager()` above deliberately populates `_pending_pushback`, `active_encounter`, ledger, `recent_injects`, and moves the rng off its seed position.
3. **The whitelist is the audit**: `root_path`, `initial_conditions`, `scenario_config`, `_resume_replay` for GameManager; the re-derived/re-wired encounter fields listed above; plus (module-level, out of scope for introspection but documented) parse-health counters and per-front-end UI locals (§5).
4. A companion test does the same `vars()` sweep against the **CLI format** (engine/persistence.save_game/load_game) with its own, larger whitelist — which would immediately surface F4/F5 as named, deliberate exclusions or force the formats to converge (best fix: make the CLIs write `GameManager.to_dict`'s envelope).
5. rng anchor check: after restore, `assert restored.rng.getstate() == gm.rng.getstate()` and one draw from each compares equal.

## Findings index
- **F1** `_pending_pushback` UNSAVED — engine/game_manager.py:77,271-273,352-355 vs to_dict :624-663.
- **F2** post-briefing/pre-question saves resume with replay=False → inject effects double-apply — engine/game_manager.py:746-747 vs engine/sim_loop.py:345; CLI-only mitigation cli/main.py:1011, cli/main_dashboard.py:977; exercised-unasserted by tests/test_web_bridge.py:557.
- **F3** actor_system (models/state_actors.py:15,27,51-53) round-trip untested.
- **F4** CLI format lacks `ending`; finished-campaign autosave resumes as playable — engine/persistence.py:91-101, cli/main.py:1997-2008.
- **F5** format asymmetry: active_encounter/seed/ending/mystery flags GameManager-only — engine/game_manager.py:647,655,658 vs engine/persistence.py:91-101.
- **F7** API load surfaces no transcript/live-call lines — api/server.py:486-507, :331-344.
- **F8** restored *optional* live call never re-surfaced in browser; next `call` silently routes into it — docs/py/bridge.py:818-847,886-891.
- **F9** (minor) CLI `endings_disabled` toggle (cli/main.py:812,2049) not persisted; resumed campaign re-enables endings.
- Deliberately ephemeral, confirmed OK: parse-health counters (llm/parse_health.py:18-21), CLI/bridge UI locals (§5), API event queues (§5).
