# UNIFIED LLM CALL MAP — `false-flag` @ `d197c44`

**Reviewer refutations have been applied throughout.** Where an original map's claim was overturned or its citation corrected, the reviewer's version is what appears below. Line numbers are the corrected ones.

---

## 0. THE TURN AT A GLANCE

A single turn issues roughly **15 LLM calls** across five phases. Ordered as the code actually runs them:

| # | Phase | Call | Count/turn | LLMContext | Model actually used |
|---|---|---|---|---|---|
| 1 | BRIEFING | Inject generation | 0 or 1 (see resume caveat) | `INJECT_GENERATION` | PRO `gemini-2.5-pro` (runtime-mutable) |
| 2 | BRIEFING | Narrator bridge | 0 or 1 | **none** | driver default `gemini-2.5-flash` |
| 3 | BRIEFING/any | Diplomatic conversation reply | 1 per player message | `DIPLOMACY_CONVERSATION` | PRO |
| 4 | BRIEFING/any | Diplomatic outcome assessment | 0 or 1 per call ended | `DIPLOMACY_OUTCOME` | PRO |
| 5 | DISCUSSION | Advisor Q&A | ≥1 per question (6 for `/advise`) | `ADVISOR_QA` | PRO |
| 6 | DECISION | Decision interpretation | 1 per submission (loop is unbounded) | `DECISION_INTERPRETATION` | FLASH |
| 7 | DECISION | Advisor pushback | 1 per submission | `ADVISOR_PUSHBACK` | FLASH |
| 8 | DECISION | Critical omissions | 5 per submission (parallel group) | `CRITICAL_OMISSIONS` | PRO |
| 9 | ADJUDICATION | State-actor responses | 0–3 (parallel group) | **none** | driver default |
| 10 | ADJUDICATION | Action quality assessment | 1 | **none** | driver default |
| 11 | ADJUDICATION | Advisor character reactions | 1–4 (parallel group) | **none** | driver default |
| 12 | ADJUDICATION | Situation summary refresh | 1 | **none** | driver default |

**Eight of the twelve call families run on no `LLMContext` at all.** `llm/router.py:231-234` and `:331-335` leave `model_name=None` when `context` is absent, so the driver default (`config.GEMINI_MODEL` → `gemini-2.5-flash`, `llm/gemini_driver.py:66-71`) is used and `get_model_config()` is never consulted. `LLMContext.CHARACTER_RESPONSE` (`llm/model_config.py:19`, tier FLASH at `:37`) has **zero call sites** — it is declarative only. There is no `STATE_ACTOR` member at all. The per-context model table and the `/llm` settings menu therefore govern only the discussion/decision/inject/diplomacy families; the entire adjudication half of the turn ignores them.

**Only eight of the ~15 calls share a cacheable prefix.** `build_shared_context_prefix` (`llm/context_builder.py:285-355`) is used by advisor Q&A, decision interpretation, pushback and the five omissions checks. The narrator, the inject generator, all three adjudication calls, the actor group and both diplomacy calls each build their own header from scratch — the exact anti-pattern the rationale comment at `llm/context_builder.py:288-307` was written to eliminate.

---

## 1. THE SHARED BRIEFING DOSSIER (used by 8 of 15 calls)

Assembled once per prompt by `build_shared_context_prefix` (`llm/context_builder.py:285-355`):

| Block | Source → f-string | Bound |
|---|---|---|
| Ruler + "UK CRISIS WARGAME - SHARED BRIEFING DOSSIER" | literal, `context_builder.py:309-317` | static ~200 chars |
| SECRET NARRATIVE CONTEXT — description, protagonist, antagonist, patsy + 4 "never reveal" instructions | `world.narrative` (`models/world.py:26`) → `NarrativeConfig.to_llm_context()` at `context_builder.py:322-324`; body `models/narrative.py:31-44, 69-79` | **unbounded**, and **absent entirely outside Mystery Mode** — `cli/main.py:497` returns `None` on the default menu choice; `engine/game_manager.py:91-92` likewise |
| GAME HISTORY header + full campaign transcript | caller's `transcript` list → `render_transcript_block` at `context_builder.py:326`; header `:35-38` | **WINDOWED at `MAX_ADVISOR_TRANSCRIPT_CHARS = 320_000` chars** (`:27`, default at `:207`, never overridden). Head share `_TRANSCRIPT_HEAD_SHARE = 0.2` → 64,000 chars (`:54`), cut on `TURN N` boundaries; middle replaced by one `[... N lines of mid-campaign history elided for length ...]` marker (`:280`) |
| CURRENT SITUATION: Turn, Phase, Escalation/100, Domestic/100, Alliance/100, mil casualties, civ casualties | `world.turn/.phase/.metrics` → `context_builder.py:335-341` | scalars |
| `build_world_state_summary`: turn+phase **again** (`prompts.py:58`), the same three metrics **again as prose bands** (`:60-62`), casualties **again** (`:64`), KEY INTELLIGENCE FLAGS (`:67-71`), anti-meta instruction (`:74-77`) | `world.metrics`, `world.flags` → appended at `context_builder.py:351-352` | static thresholds |

Two facts about this block matter more than the rest:

- **Every metric is stated twice and the flags are a third restatement of the same three numbers.** `update_world_flags` (`engine/flags.py:38-40`) does not augment `world.flags`, it **replaces** it: `world.flags = compute_risk_flags(world.metrics)`. `compute_risk_flags` (`engine/flags.py:15-35`) returns exactly five thresholded booleans — `risk_escalation` (≥60), `risk_unrest` (≤40), `risk_alliance_fragile` (≤40), `risk_civilian_harm` (>0), `risk_military_losses` (>0). "KEY INTELLIGENCE FLAGS" carries **zero information** the two metric renderings above it do not already carry. Callers: `sim_loop.py:257`, `:426`, `:639`, `game_manager.py:322`, `cli/main.py:1209`.
- **`FactionStance` never reaches this prefix.** `context_builder.py:323` calls `to_llm_context()` with no `target_country_code`, so the per-country block at `models/narrative.py:46-67` (secret_motive, public_posture, economic_leverage, intel_sharing_level) is skipped for all eight calls.

---

## 2. BRIEFING PHASE

### 2.1 Inject generation — "what the player wakes up to"

**Builder** `llm/prompts.py:334` (`build_inject_generation_prompt`, f-string `:426-457`), story half from `llm/context_builder.py:391` `get_stochastic_inject_context`.
**Dispatch** `llm/inject_generator.py:71` → `router.py:264`.
**Purpose** Once the authored episode files run out, this single call invents the headline, the 2–3 paragraph brief and the metric hit that opens the turn.

**WHAT GOES IN**

| Data | Source → evidence | Bound |
|---|---|---|
| Turn number (instruction header + YAML `id:` template) | `world.turn` → `prompts.py:426, :447`; context headers `context_builder.py:407, :435` | unbounded |
| Escalation / Domestic / Alliance, raw /100 | `world.metrics` → `context_builder.py:409-411` | scalars |
| SECRET NARRATIVE CONTEXT (global only) | `world.narrative.to_llm_context()` → `context_builder.py:415-417` | unbounded; **Mystery Mode only** (gated `if world_state.narrative:` at `:415`) |
| STORY SO FAR digest — turns played, latest turn, transcript line count, last 3 "event-ish" lines | `generate_summary` (`context_builder.py:562-600`, **not an LLM call** — it discards its `summary_prompt` arg at `:570`) → `prompts.py:393` → `context_builder.py:424` | **last 3 lines (`:595`), each cut to 100 chars (`:596`)**; only used when `len(transcript) > 10` (`prompts.py:388`) |
| EVENTS ALREADY PLAYED ledger — `Turn N \| title \| OPEN/ADVANCED/RESOLVED - note` | `narrative_state.event_ledger` → `sim_loop.py:320-324` → `inject_generator.py:66` → `prompts.py:405` → `context_builder.py:428-431`, renderer `:74-107` | **entry count UNBOUNDED**; each title truncated to `_LEDGER_TITLE_MAX = 60` (`:64`, `:87-88`); each note pre-truncated to 90 chars by `_truncate_decision` (`narrative_adjudication.py:158`) |
| LAST TURN transcript window | full transcript sliced backwards from the last `^TURN \d+$` header | **`MAX_INJECT_CONTINUITY_LINES = 400`** (`context_builder.py:61`, passed `prompts.py:401`); over-long turns keep head 2/3 + tail 1/3 around `[... mid-turn discussion elided ...]` (`:156-163`); char bound `320_000` trimmed from the head (`:114`, `:166-189`) |
| UK objectives (`objectives.uk`), Russian objectives (`red_objectives`) — raw dict reprs | `initial_conditions` → `prompts.py:362-363` → `:431, :434` | unbounded |
| Russian strategy pattern, UK constraints pattern, and the naval+infrastructure+diplomatic scenario menu | `scenario_library.yaml` via `inject_generator.py:21-33` → `prompts.py:376-378` | menu **filtered** by `_drop_used_scenarios` (`prompts.py:305-331`): any entry sharing a >3-char non-stopword with a ledger title is dropped. Because entries are dicts, `words(s)` stringifies the **entire mapping** (`:320`), so a ledger word matching a nested location kills that entry. Per-**entry**, not per-family; no stemming ("cable" ≠ "cables"). Pool restored intact if emptied (`:331`) |
| Casualty running totals | **not a state field here** — but they arrive **inside the LAST TURN window** as `Effect: casualties_civ +12 (→ 34)` lines written by `sim_loop.py:248`, appended at `:386`, merged unstripped at `cli/main.py:953` and re-emitted by `context_builder.py:437` | conditional on the previous turn's inject moving casualties |

**Does NOT reach it:** the shared dossier prefix and hence the full campaign history (`get_stochastic_inject_context` never calls `build_shared_context_prefix` or `render_transcript_block`); `world.flags`; `world.recent_injects`; per-country `FactionStance` (`:416` passes no country code, though rule 6 asks the model to "subtly advance the hidden narrative"); `world.difficulty` (which silently rescales the very effects this call proposes, `sim_loop.py:196`); `world.posture`, `spatial_state`, `diplomatic_relationships`, `actor_system`, `discussion_transcript`; every `initial_conditions` section other than `objectives` and `red_objectives`; and — pointedly — `scenario_library.llm_guidance`, the section written expressly to steer this call. `world.phase` reaches only on the no-transcript branch, via `build_world_state_summary` at `prompts.py:410` → `:58`.

**WHAT IT AFFECTS**
`world.metrics` mutated in place by `apply_inject_effects` (`sim_loop.py:172-259`): `"a..b"` deltas become the integer midpoint (`:215-222`), non-casualty deltas scaled by difficulty 0.5/0.7/1.0 with a magnitude floor of 1 (`:191-196, :228-232`), casualties added uncapped (`:240-241`), everything else clamped (`:243`), unknown metric names skipped with a transcript line (`:253`). Then `update_world_flags` (`:257`), then `narrative_state.hidden_metrics`/`previous_metrics` re-sync (`cli/main.py:869-875`). A `PlayedEvent(turn, title, 'open')` is written to the ledger (`:336-337`) — **this call's own title becomes an input to every later inject prompt and to the `_drop_used_scenarios` filter**. The title is handed to the narrator bridge (`:349`) and appended to `world.recent_injects`, trimmed to 5 (`:391-392`). Description lines and effect boxes enter the transcript (`:381, :386`).

**Notable:** on the primary CLI path the **title never reaches the screen or the transcript** — `cli/main.py:858` always passes `suppress_display=True`, so `console.print(panel)` at `sim_loop.py:119` is skipped, and the Rich branch (`:117-123`) returns description paragraphs only. It is shown by `cli/main_dashboard.py:872` for turns > 1, and enters the transcript only in the non-Rich fallback (`:127-128`). The channel vocabulary is also mismatched: the prompt offers `briefing/intelligence/media/military` (`prompts.py:452`) but the colour map knows only `briefing/intel/breaking` (`sim_loop.py:85-89`).

**Calls per turn is 0, 1, or 1-per-resume.** The generation branch at `sim_loop.py:316` has **no `replay` guard** (`replay` is consulted only at `:384` and `:396`). Loading a mid-turn save sets `resume_replay` (`cli/main.py:729`) and re-runs the briefing (`:859`), generating a **different** inject for a turn already played, which overwrites the existing ledger entry's title (`narrative_state.py:308-311`) while the original inject's effects remain applied.

**Failure** is fully absorbed: router retry → `MockDeterministicDriver` (which has a dedicated inject branch, `mock_driver.py:1230-1234`); then `None` on any exception/empty/non-mapping YAML (`inject_generator.py:72-113`); then `_quiet_turn_inject` (`sim_loop.py:36-53`) — "Overnight Assessment", zero effects. The player never sees an error.

**Also note** the scenario library path is **hardcoded** to `data/scenarios/war_game_2025/scenario_library.yaml` (`inject_generator.py:27`) while `initial_conditions` come from the live `scenario_id` (`sim_loop.py:317`).

### 2.2 Narrator bridge — 2–3 sentences of elapsed time

**Builder** `llm/prompts.py:558` (f-string `:589-615`). **Dispatch** `engine/narrator.py:36-42`, entered from `sim_loop.py:346-351`.
**Gates:** an inject exists (`:331`), `world.turn > 1 and full_transcript` (`:344`), `len(transcript) >= 5` (`narrator.py:29`).

**IN:** static thriller framing (`prompts.py:589`); `build_world_state_summary` only (`:584`) — turn+phase (`:58`), the three metrics **as prose bands only** (`:60-62`, the raw numbers do **not** reach this call), casualties (`:64`), flags (`:67-71`), the anti-meta block (`:74-77`) despite the speaker being a narrator; the **last 20 transcript lines** (`prompts.py:587` — a bare literal, no char bound, so 20 unwrapped paragraphs can be arbitrarily large; the parameter is named `last_turn_transcript` and the docstring at `:571` claims "previous turn", but `narrator.py:32` passes the whole campaign transcript unsliced); the title of the inject about to be shown (`:598`).

**Silently dropped:** `system_instruction` ("You are a master storyteller…", `narrator.py:39`), `temperature=0.7` (`:40`) and `max_tokens=150` (`:41`) are all filtered out by the driver-signature inspection at `router.py:255-263` — `GeminiDriver.generate_text` is `(self, prompt, rng)` (`gemini_driver.py:106`). Gemini instead uses `GEMINI_TEMPERATURE` 0.7 (`:92`, applied `:100`) and `GEMINI_MAX_TOKENS` **2048** (`:93`, applied `:103`). Only `OpenAICompatDriver` honours them (`:150-157`). **The intended 150-token cap on the bridge does not exist on the default provider.**

**AFFECTS:** one `[Narrator] …` transcript element (`sim_loop.py:355`), which becomes permanent GAME HISTORY. It also feeds the inject generator's STORY DIGEST — `generate_summary` treats any line starting `[Narrator]` as a notable event (`context_builder.py:583`, reachable because of the strip at `:575`), keeps the last three (`:595`) at 100 chars each (`:596`). On the parked save this means **the same narrator sentence repeated three times** is what the inject generator receives as its "story so far". Displayed in italic; the 2.5s sleep at `sim_loop.py:374` is **conditional** on `not suppress_display` + Rich (`:362, :364-369`), so headless/dashboard/API paths take the latency with no pause. Mutates nothing.

**Ordering correction:** on any turn where the inject is dynamically generated, the narrator is the **second** LLM call of the turn (inject at `sim_loop.py:322` precedes it by 24 lines), and stochastic mode defaults on from turn 7 — exactly the range where the narrator's own `turn > 1` gate is satisfied. It still shares a zero-length prefix with everything else (the inject prompt opens "You are the Games Master…" at `prompts.py:426`).

**Notable gaps:** the secret narrative truth **never reaches the narrator** — the one component whose stated job is foreshadowing (`prompts.py:604`) is blind to the hidden protagonist/patsy the inject generator does see. `prompts.py:576-581` is **dead code**: `last_decision` is assigned, the loop body is `pass`, and it is never interpolated; the instruction "connect the player's previous choice" (`:603`) relies entirely on the decision falling inside the 20-line tail. 20 lines is roughly the tail of one adjudication — against 320,000 chars for the advisor calls.

---

## 3. DIPLOMACY (mandatory encounters at briefing; `/call` at any time)

### 3.1 Diplomatic conversation reply

**Builder** `engine/diplomacy.py:181` (f-string `:230-260`). **Dispatch** `:430`, context `DIPLOMACY_CONVERSATION` → PRO.

**IN:** counterpart title (`:233`, also `:230, :248, :260`), personality (`:234`), tone (`:235`), key concerns bullet list (`:238`), country switchboard key (`:230`); **SECURE CONTEXT** from `get_diplomatic_context` (`context_builder.py:441-512`) = turn (`:494`) + **raw** escalation/domestic/alliance (`:495-497`, bypassing the "don't talk in numbers" framing entirely) + the global narrative truth (`:501-503`, Mystery Mode only) + a **filtered transcript**; the call's own history (`:219-223`); the player's current message (`:245`); and an exchange counter rendered as "exchange N of a maximum 11" where **11 is a hardcoded literal** in the prompt string, not read from `data/diplomatic_profiles.yaml:320`, and where history holds two entries per exchange so the counter advances by 2 per round.

**The filtered transcript is the only completely unbounded transcript in the codebase.** `get_diplomatic_context` never calls `render_transcript_block`, `_bound_chars` or `MAX_ADVISOR_TRANSCRIPT_CHARS`. Filtering is the only size reduction and it is loose: the `===`/`turn ` markers at `:458` latch `in_public_event` on for most structural lines, and the country test at `:465` is a bare substring test — country `'US'` matches inside "discuss", "must", "focus", "trust". COBRA deliberation lines are excluded by design (`:470-484`), but the state latches, so a COBRA line only re-enables output when a later line re-matches. **A late-campaign call ships an ever-growing, uncapped block to a PRO model.**

**Does NOT reach it — and this is the group's headline defect:** the prompt instructs "Act according to your SECRET MOTIVE (if provided above) at all times" (`:249`), and `context_builder.py:502` **does** request it via `to_llm_context(target_country_code)` — but `target_country_code` is the switchboard key (`'US'`, `'France'`, `'Russia'`, `'China'`; `diplomacy.py:96-104, 111-121`) while `FactionStance.country_code` is ISO-3 (`RUS/USA/CHN/IRL`; `narratives.yaml:8,13,18,23`). The exact-equality lookup at `models/narrative.py:47` **never matches for any shipped country**. The motive is never above.

Also absent: the inject's authored encounter briefing — `data/scenarios/.../turn_006.yaml:32-33` is threaded through three signatures into `self.context` at `diplomacy.py:355` and **read by nothing**; the profile's own `llm_instructions` and per-country `outcome_assessment` (`diplomatic_profiles.yaml:322-355`); the country `full_name`; the access level (`:365`, set and never read); casualties, flags, posture, recent injects; `NarrativeState` entirely; `StateActor.relationship_uk` — **the two foreign-power systems are completely disconnected, so a capital whose trust the player just wrecked in adjudication answers the phone with no memory of it**; and the shared dossier prefix.

**AFFECTS:** appends to `self.transcript` (`:433`) and `self.history` (`:434`); the history becomes the CONVERSATION SO FAR of the next reply and the entire input to the outcome call. The encounter transcript merges into the campaign transcript (`sim_loop.py:420`, `cli/main.py:1201`). **No metric moves here.**

**Unbounded on the API path.** The CLI loop caps at `max_exchanges` (`:526-528`) — and note `:526` reads `conversation_rules` off the leader/diplomat profile dict, which never contains that key (it is top-level at `diplomatic_profiles.yaml:319`), so it always falls back to the hardcoded 11. `engine/game_manager.py:511-525` imposes **no cap at all**, so a browser player can talk indefinitely, growing both the history block and the unbounded filtered transcript on every PRO-tier call.

### 3.2 Diplomatic outcome assessment

**Builder** `diplomacy.py:265` (f-string `:293-314`), dispatch `:316` from `end()` at `:455`. PRO tier.

**IN:** `build_world_state_summary` (`:291`) — turn+phase, the three metrics **bucketed into 4 bands each** (`prompts.py:34-53`, the raw numbers do *not* reach, unlike the conversation prompt), casualties raw (`:64`), all truthy flags (`:67-71`), the anti-meta block (`:73-77` — incongruous, since the prompt then demands a numeric `ALLIANCE_COHESION_DELTA` at `:311`); the country name (`:298`); and the **complete call history** (`:287-289` → `:299`) with no explicit truncation.

**Does NOT reach it:** the secret narrative truth in any form — `assess_diplomatic_outcome` imports only `build_world_state_summary` and never touches `world.narrative`, so **the one call whose score most depends on hidden intent cannot tell a manipulative counterpart from an honest one**; the counterpart's profile; the hand-authored per-country scoring rules at `diplomatic_profiles.yaml:338-355` ("Russia: conversations always tense; avoiding escalation is success"; "China: volunteering British intelligence to them is a loss") which **no code reads anywhere**; and `full_transcript` — deliberately withheld at `:455-457` even though the encounter object holds it, so **the call is judged with no knowledge of the UK decision that prompted it**.

**AFFECTS:** `ALLIANCE_COHESION_DELTA` clamped to [-15,15] (`:333`) → `world.metrics.alliance_cohesion`, clamped 0-100 (`:474`). **This is the only place a diplomatic call moves world state.** The OUTCOME token drives nothing mechanical. The closing block prints the raw number in classic mode or `_relationship_reading` otherwise (`:76-93`), but `sim_loop.py:407-418` and `cli/main_dashboard.py:1206-1217` **do not pass `show_metrics`**, so mandatory encounters and the dashboard always print the number regardless of play mode. On the API path there is **no end endpoint**: if the player never types a closer (`:419-423`), this call never fires and the delta is never applied — and even when it is, `game_manager` has no post-call resync, so the delta is overwritten at the next adjudication when `hidden_metrics` is copied back over `world.metrics` (`game_manager.py:317-321`).

---

## 4. DISCUSSION PHASE — advisor Q&A

**Builder** `llm/prompts.py:82` (`build_advisor_context`, f-string `:147-169`). **Dispatch** `agents/conversation.py:211`. Context `ADVISOR_QA` → PRO.

**Purpose** Lets the player interrogate a named cabinet advisor in character before committing.

**Calls:** one per **matched advisor**, not per question. `conversation.py:192-196` appends every advisor whose keyword list hits. The `/advise` panel (`cli/main.py:1251-1271`) issues 5 `run_turn_discussion` calls but **6 LLM calls** — the Home Secretary's canned question "…what are the domestic security concerns?" (`:1255`) matches `home_secretary` on "home"/"domestic" **and** `national_security_advisor` on `\bsecurity\b` (`conversation.py:185, :187`, `\b`-anchored regex at `:92`). Cost/latency estimates built on "5" are 20% low. A question addressing an absent official short-circuits to a canned Cabinet Secretary line and burns no call (`:168-174`). Strictly **sequential** — `generate_group` is imported at `conversation.py:18` but used only by `check_critical_omissions`.

**IN:** the full shared dossier (§1), plus:
- advisor `role` (`prompts.py:106` → `:149, :159`) — the raw YAML role, not the on-screen cabinet title
- `knowledge_domains` (`:107` → `:151`), `key_concerns` (`:108` → `:152`)
- **all** scenario constraints, headed bullet lists (`:119-125` → `:141` → `:155`) — 904 chars measured
- **UK order of battle** as a raw `str(dict)` (`:128-132` → `:207`) — 4,103 chars, **conditional** on `knowledge_domains ∩ {military_operations, force_readiness, threat_assessment}`, which on the shipped scenario is `chief_defence_staff` **only**
- **Ammunition stockpiles** as raw `str(dict)` (`:135-139`) — 814 chars, conditional on `∩ {military_operations, force_readiness}`, again CDS only
- the player's question verbatim, including the CLI-appended `[Please be concise - 3-4 sentences maximum]` (`:157`) — **no length cap on player input anywhere on this path**

**Does NOT reach it:** `world.recent_injects` (so an advisor asked "what just happened?" sees the event only if it survives the transcript window); `world.posture`, `spatial_state`, `diplomatic_relationships`, `actor_system`; the advisor's own `pushback_triggers` and `influence`; **`personality`** — `build_advisor_context` reads only role/knowledge_domains/key_concerns, so no personality shapes these calls either (the only prompt in the repo that interpolates `personality` is the diplomacy counterpart prompt, `diplomacy.py:205, :234`); and whole scenario sections `intelligence`, `timeline` (35-47), `red_forces`, `red_objectives`, `objectives`, `intelligence_summary`, `diplomatic_contacts`, `critical_infrastructure` (69-83). No `narrative_state` parameter exists on `run_turn_discussion` at all.

**No `max_tokens`** is set (`conversation.py:211` passes only prompt/rng/context), so the driver-wide 2048 applies; the brevity instruction is prose inside the question.

**Path defect:** `sim_loop.py:681` (`run_full_turn`) calls `run_turn_discussion` **without** `full_transcript`, so on that entry point the advisor gets an **empty game history**.

**AFFECTS:** one `"{role}: {response}"` line per answer into the turn transcript (`sim_loop.py:485`), spliced into the campaign transcript (`cli/main.py:1296/1651`) — **so every answer permanently widens the GAME HISTORY block of every subsequent prompt**. Also extends `world.discussion_transcript` (`:488`), which is **written and never read**. Mutates no metric, no flag, no narrative state. There is no adjudication of advisor answers.

**Failure text becomes permanent prompt history:** `conversation.py:216-217` returns `("System", f"Error generating response: {e}")`, written into the transcript as a literal line.

---

## 5. DECISION PHASE

All three calls run inside `run_turn_decision` (`sim_loop.py:493-584`), strictly sequential: interpretation (`:532`) → pushback (`:546`) → omissions fan-out (`:566`). **The loop is unbounded** — `cli/main.py:1665` is `while not decision_confirmed:` and several branches `continue` without confirming ('M' manual rewrite `:1728-1733`, declined enhanced decision `:1753-1757`, declined proceed-anyway `:1777-1779`, pushback amend `:1799`). A player who keeps amending drives an arbitrary number of 7-call rounds in one turn.

Critically, **this turn's decision-phase lines are in a LOCAL transcript list** (`sim_loop.py:523, :528, :541-542, :557-559`) merged into the campaign transcript only by the caller *after* the function returns (`cli/main.py:1702`, `game_manager.py:279`). So all three calls see a history block that stops at the end of the discussion phase.

### 5.1 Decision interpretation — FLASH

**Builder** `prompts.py:174` (f-string `:202-239`). **Dispatch** `conversation.py:244`.

**IN:** shared dossier (§1, phase = "decision" via `sim_loop.py:521`, still "discussion" on the API dry-run path since `game_manager.py:200` passes `dry_run=True`); constraints (904 chars, `prompts.py:193` → `:213`); UK forces (4,103 chars, `:194` → `:207`); stockpiles (814 chars, `:195` → `:210`) — **none truncated**; the player's raw decision **not truncated and not escaped** (`:215`, so an embedded quote or newline lands raw inside the quoted field); static task framing (`:217-239`).

**Does NOT reach it:** the advisor roster — `prompts.py:193-195` reads only constraints/uk_forces/stockpiles, so the model interpreting a directive addressed to specific ministers **does not know who they are**; `world.recent_injects`; `NarrativeState` in any form (no parameter on `run_turn_decision`); `posture`/`spatial_state`/`diplomatic_relationships`/`actor_system`; the scenario's `intelligence`, `timeline`, `critical_infrastructure`, `environment`. Note `llm/context_builder.py:367` `get_decision_interpreter_context` — a purpose-built context for exactly this call — is **dead code**, no caller anywhere.

**OUT and how it's parsed:** the prompt asks for five labelled lines. **A parser does exist and runs on every CLI decision** — `cli/display_utils.py:157` `parse_interpretation_simple` splits on `INTERPRETATION:` (`:179`), `FORCES INVOLVED:` (`:181`), `TIMELINE:` (`:188`), `FEASIBILITY:` (`:193`) into a `{summary, forces, timeline, concerns}` dict, called by `display_decision_summary` at `:229` to build the OPERATIONAL ORDER panel (`:269`). Two truncations live here: **forces capped at 5 entries** (`:186, :200`) and, when nothing parses, the **raw text trimmed to 400 chars** (`:259-261`). FEASIBILITY is surfaced only when the line contains "impossible" or "requires clarification" (`:194`).

**AFFECTS:** `Interpretation:` transcript lines (`sim_loop.py:541-542`); the OPERATIONAL ORDER panel (`cli/main.py:1705`, details at `:1713`); the pushback prompt (`prompts.py:284`); and the action-quality prompt (`narrative_adjudication.py:228`) whose parsed EFFECTS become metric deltas applied at `cli/main.py:1877-1881`. **Those effects cannot include casualties** — the prompt requests exactly three deltas (`narrative_adjudication.py:261-263`), the parser only accepts lines containing "escalation"/"alliance"/"stability" (`:375`), `determine_base_effects` never emits a casualties key (`:411-446`), and `apply_quality_scaling` only merges those keys (`:449-497`). `cli/main.py:1880-1881` copies casualties from `hidden_metrics`, but nothing in this path writes them.

### 5.2 Advisor pushback — FLASH

**Builder** `prompts.py:244` (f-string `:277-300`). **Dispatch** `conversation.py:272`.

**IN:** shared dossier; the player's raw decision (`:281`); **the interpretation verbatim, untruncated** (`:284`) — including a mock-fallback string or an error apology; and the **advisor roster with pushback triggers**, one `- {role}: {t1}, {t2}, {t3}` line per character (`:263, :267-273` → `:287`). The `"note" not in char_data` filter excludes the four Russian personas but **not `prime_minister`** — the player's own persona is offered to the model as an advisor who may push back on the player's decision.

**Does NOT reach it:** `uk_forces`, `stockpiles`, `constraints` — although all three reached the interpretation prompt three lines earlier. **The Chief of the Defence Staff is asked to fire the triggers "Militarily implausible actions (e.g., deploying unavailable assets)" and "Actions that waste limited munitions" without being shown the order of battle or the munition counts.** Also absent: `knowledge_domains`, `key_concerns`, any personality field, `recent_injects`, and `NarrativeState` trust — **an advisor whose trust has collapsed pushes back exactly as one who is loyal**.

**OUT:** hand-rolled line parser (`conversation.py:277-307`) with four one-directional degradations: (a) **any** line containing the `NO PUSHBACK` sentinel discards *every* concern in the response (`:278-279`); (b) lines before the first recognised role are dropped (`:305`); (c) an unrecognised `:` prefix is **appended to the previous advisor's message** (`:302-304`); (d) no recognised prefix anywhere → `[]`, reported as "No advisor concerns raised" — indistinguishable from a genuine all-clear. The accepted alias set is hardcoded at `conversation.py:24-31`; "Defence Secretary:" or "Chancellor:" fall through it.

**AFFECTS:** transcript lines (`sim_loop.py:556-563`); and — **the block is an `elif`** (`cli/main.py:1790`) hanging off `if critical_concerns:` (`:1717`). **Whenever any critical omission survived parsing, the ADVISOR CONCERNS panel and the P/A/C gate are never reached at all and pushback affects nothing in the CLI beyond the transcript.** When it is reached: 'A' → `amend_pending = True` (`:1803-1809`), 'C' → "Decision cancelled. Returning to discussion." (`:1810-1815`), otherwise `decision_confirmed = True` (`:1817`, and `:1819` when there was no pushback). **No metric, flag, trust value or ledger entry is ever written from pushback.**

### 5.3 Critical omissions — five parallel PRO calls

**Builder** `prompts.py:462` (f-string `:501-553`), one per advisor, built in the comprehension at `conversation.py:375-381`. **Dispatch** `conversation.py:382` → `fanout.py:67` → `router.py:297` `batch_generate_text` (thread pool, `max_workers=min(len,10)`), with one rate-limit slot claimed per prompt **before** dispatch (`router.py:373-378`).

**IN:** the **byte-identical** shared dossier; the advisor's `role` twice (`prompts.py:503, :531`); a one-line remit blurb selected by `character_id` (`:532-536` — the four non-matching branches emit empty strings, leaving four blank lines in every rendered prompt); the player's raw decision (`:508-509`); and a **RECENT EVENTS** block.

**RECENT EVENTS is double-windowed to 5 and is titles only.** `world.recent_injects` is written at `sim_loop.py:391` and immediately capped by `del world.recent_injects[:-5]` (`:392`); `conversation.py:353` slices `[-5:]` again. The docstring at `prompts.py:481` claiming "Last 2-3 inject descriptions" is wrong on both count and content. The fallback when empty emits `Active situation: {flag_key}` for the first three flag **keys** with **no truthiness filter** (`conversation.py:354-356`) — so a flag explicitly `False` can be presented as an active situation, inconsistent with `prompts.py:68`. And the append is skipped when `replay` (guard at `sim_loop.py:384`), so a reloaded save can under-report or fall through to the flags fallback.

**Two dead inputs — this is the group's core defect:**
- **`interpretation` is a dead parameter.** `sim_loop.py:569` passes it as the third positional argument, declared at `conversation.py:313`, and inside `check_critical_omissions` (`:310-429`) the name appears **only in the signature and the docstring**. `build_critical_omissions_prompt` has no `interpretation` parameter at all (`prompts.py:462-468`). **Five PRO-tier advisors judge the raw typed sentence with no access to the structured reading of it the game just paid FLASH to produce.**
- **`personality` is a dead local.** `prompts.py:491` reads it and it never appears in the f-string. The key does not exist in the scenario data either.

Also absent: the pushback those same advisors produced seconds earlier (not among the arguments at `sim_loop.py:566-575`) — **so the same objection can be raised twice in one turn by two different calls**; `uk_forces`/`stockpiles`/`constraints`, so the CDS is asked to flag "Committing forces WITHOUT securing logistics" with no force data and the Attorney General to judge legal authority with no constraints block; the event ledger, so an advisor can flag an omission about a thread the player already closed; and each other's answers, with nothing deduplicating before `cli/main.py:1717` renders the list. `prime_minister` is excluded here (`conversation.py:359-365`) though `build_pushback_prompt` includes it.

**Output cap:** the call site omits `max_tokens` (`conversation.py:382-385`), but the driver-level cap still applies — `GEMINI_MAX_TOKENS` default **2048** via `generation_config` reused by the batch path (`gemini_driver.py:92-103, :177, :184`); `OPENAI_COMPAT_MAX_TOKENS` default 2048 (`openai_compat_driver.py:140-142, :184`). On the Gemini batch path the call site **could not** set a cap: `batch_generate_text` is `(self, prompts, rng)` (`:151`) and `router.py:353-361` only forwards `max_tokens` to drivers whose signature declares it.

**Parsing** (`conversation.py:387-427`): discard on empty or on `NO_CONCERN`/`NO CONCERN` appearing **anywhere** as a plain substring (`:390`) — a genuine concern echoing the format block is discarded whole. `_extract_labeled_text` (`:116-127`) tolerates markdown; unlabelled lines fold into the last-seen field (`:412-417`); an entry survives only if **both** concern and recommendation are non-empty (`:419`). A batch-path `[ERROR: …]` slot is truthy but carries no labels, so it is dropped silently at `:419` — **net effect of any failure is a silent all-clear.**

**AFFECTS — this is the only decision-phase call that changes the game state:** transcript lines (`sim_loop.py:577-582`); the CRITICAL ADVISORY selection UI (`cli/main.py:1717-1780`, 'D' returns to discussion `:1720-1726`, 'M' cancels `:1728-1733`); and **it rewrites the player's decision** — 'A'/'S' calls `append_recommendations_to_decision` (`:1742`), `action = enhanced_decision` (`:1758`), which re-runs all three decision calls (`:1765`) and becomes the text handed to adjudication (`:1846`/`:1857`). The LLM's own recommendation text becomes the player's decision of record and therefore moves every metric — via the **LLM adjudicator**, not the keyword heuristics (`sim_loop.py:618-635` is imported as `run_turn_adjudication_fallback` at `cli/main.py:67` and reached only inside the `except` at `:1918`).

**API consumers cannot distinguish the two sources:** `game_manager.py:205-211` flattens the omissions tuples into `concerns_list`, then `:215-221` appends the **pushback** tuples to the same list with the synthetic recommendation `"Consider revising your approach."` (`:220`). The `critical_concerns` field returned at `:225` and surfaced by `api/server.py:716` and `docs/py/bridge.py:978` is a blend.

---

## 6. ADJUDICATION

Two pipelines. `world.actor_system` is **always truthy** in real play (`game_manager.py:122`, `cli/main.py:771`, `cli/main_dashboard.py:795` all call `load_actors_from_yaml`), so the **actor path is the live one**: `adjudicate_with_actor_simulation` (`narrative_adjudication.py:799-900`). Three live call-site pairs exist: `game_manager.py:301/:314`, `cli/main.py:1851/:1862`, and `cli/main_dashboard.py:1614/:1626` — all passing `world_narrative` and `llm_batch_fn=batch_generate_text`.

Actor path order: actors (`:847-850`) → quality (`:859`) → apply effects (`:879-883`) → advisor reactions (`:886`) → crises (`:895`) → summary (`:898`). **`_update_character_attitudes` is never called on this path**, so advisor trust is frozen in every real campaign.

### 6.1 State-actor responses — up to 3 parallel calls, **no LLMContext**

**Builder** `engine/actor_simulation.py:24` (f-string `:32-85`). **Dispatch** `:131` `generate_group(...)` with **four positional args**, so `context` stays `None` and no tier is selected.

**IN — the richest actor model in the game:** `full_name`, `country_code`, `official_position`, `relationship_uk` (live, clamped 0-100), `true_motivations`, `hidden_agendas`, `threat_perception`, `domestic_pressure`, `dependencies` (raw dict repr), `redlines`, `military_capability`, `economic_leverage`, `diplomatic_influence`, `intelligence_sharing` (`:33-52`); a `{world_context}` block (`:55`) = `NarrativeState.to_llm_context()` (hidden metrics + bands, casualties, `recent_events[-3:]`, all `active_crises`, **every character's name/relationship/trust**, game_time, turn) plus, **in Mystery Mode only**, the global narrative truth appended at `narrative_adjudication.py:843-844`; and the player's **raw, untruncated** action (`:58`).

The character roster is **not UK-only**: `models/narrative_state.py:404-410` seeds `usa_nsa` alongside the four `uk_*` advisors, so **a foreign capital's prompt is fed the internal trust scores of the UK cabinet *and* the US National Security Advisor.**

**Does NOT reach it:** the interpretation (`narrative_adjudication.py:803` accepts it but forwards it only to `assess_action_quality` at `:859`); **the entire game transcript** — advisors get up to 320,000 chars, a foreign capital reacting to turn 12 gets three `recent_events` strings; the shared dossier; `build_world_state_summary`; `public_commitments`; `recent_actions`/`trust_trajectory`/`last_contacted_turn`; `situation_summary`; `event_ledger`; each other's replies.

**Per-country secret motives never reach them,** and fixing the missing country-code argument at `:844` would not be enough: the world-context string is built **once** and shared by every actor prompt (`actor_simulation.py:129-130`), and the code sets do not match — stances are `{RUS, USA, CHN, IRL}` (`narratives.yaml:8,13,18,23`) while actors are `{USA, FRA, DEU, POL, RUS}` (`state_actors.yaml:5,36,69,99,124`). Only USA and RUS intersect; two of the three default actors (`["USA","FRA","POL"]`, `actor_simulation.py:264`) have no stance at all.

**Selection:** `identify_relevant_actors` (`:226-276`) keyword-matches the raw action, then sorts by `relationship_uk` descending and slices to `max_actors=3` (`:273-274`). With shipped data the NATO branch's four codes are cut to three by that slice. A code missing from `actor_system.actors` would raise `KeyError` at `:274` — a bare dict index — before the filter at `narrative_adjudication.py:846` runs, aborting the whole adjudication via the broad `except` at `cli/main.py:1907`.

**OUT:** six labelled lines; parsed line-by-line (`:145, :159-202`), so a **multi-line PUBLIC_RESPONSE is silently truncated to its first line** (`:162-163`).

**AFFECTS:** `TRUST_CHANGE` clamped [-20,+20] → `update_actor_relationship` → `relationship_uk` + `trust_trajectory` (`state_actors.py:55-65`); also `domestic_stability` ±2/-3 (`:323-326`). `WILL_SUPPORT` weighted by `diplomatic_influence/50` → alliance/escalation deltas (`:309-320`) plus consensus bonus (`:328-337`). Those merge **60/40** with quality effects (`narrative_adjudication.py:869-876`) → `hidden_metrics` (`:879-883`) → `world.metrics` (`cli/main.py:1877-1881`). PUBLIC_RESPONSE is word-truncated to 90 chars into the reasoning block (`:922`) **and separately written in full** to the save transcript under "International Reactions:" (`cli/main.py:1901-1903`) — it appears twice, once truncated, once whole.

**Dead outputs:** `private_assessment` and `intel_shared` are parsed into `ActorResponse` (`:204-212`) and read by no renderer. (`conditions` and `will_support` **are** consumed — `docs/py/bridge.py:1008-1015` renders both.) `ActorResponse.action_taken` (`state_actors.py:83`) is never constructed and never requested — **actors can say things but the model has no slot for what they do.**

**Failure still moves metrics:** `_heuristic_actor_response` returns `will_support='conditional'`, which adds `+2*weight` to alliance cohesion via `:318-320`.

### 6.2 Action quality assessment — 1 call, **no LLMContext**

**Builder/dispatch** inline at `narrative_adjudication.py:223-266`, dispatched `:269` with `max_tokens=400`.

**IN:** `narrative_state.to_llm_context()` (`:216` → `:224`) — hidden metrics with qualitative labels, casualties, `recent_events[-3:]`, all `active_crises`, the five characters' name/relationship/trust, `game_time` + `turn`; the **global** secret narrative truth (`:219-221`, Mystery Mode only, no country code so no stances); the player's raw action (`:226`); the **full interpretation, untruncated** (`:228`); the static rubric (`:230-265`).

**Metrics are PRE-effect on both paths** (assess at `:762`/`:859` runs before the apply loops at `:772-776`/`:879-883`). `narrative_state.turn` is **stale by one** from turn 2 onward (synced only at `game_manager.py:329`/`cli/main.py:1933`). `game_time` is written once at construction and never updated — and on the legacy-save path it is not even a date: `cli/main.py:739` and `cli/main_dashboard.py:763` build it as `f"Turn {world.turn}"`.

**Does NOT reach it:** the shared dossier or **any transcript at all** — `assess_action_quality` (`:186-193`) has no transcript or `WorldState` parameter and the module never imports `llm.context_builder`. **The adjudicator grades the decision without seeing the discussion that produced it, the inject it responds to, or any prior turn.** Also absent: `situation_summary`; `event_ledger`; all `WorldState` fields; `play_mode`; per-country stances. `llm/context_builder.py:514` `get_adjudicator_context` — built for exactly this — has **no Python caller anywhere**.

**`max_tokens=400` is silently discarded on Gemini** (`router.py:255-262` vs `gemini_driver.py:106`); effective cap 2048.

**AFFECTS:** `quality` validated against a five-word whitelist (`:366-369`, else "adequate"); `multiplier` clamped [0.5, 2.5] (`:383-388`), and if it parses to exactly 1.0 the quality→multiplier table (`:391-399`) overrides it — **`catastrophic` maps to 2.0, amplifying harm rather than inverting it**. `suggested_effects` is built by a loose `elif` (`:374-381`) firing on any line containing a colon and "escalation"/"alliance"/"stability", so REASONING continuation lines can be mis-parsed as metrics; `int()` failures are swallowed. `reasoning` is scrubbed by `_scrub_reasoning` (`:78-112`) against `_LEAK_MARKERS` and an 8-token overlap with the narrative description, falling back to `_NEUTRAL_REASONING` if nothing survives. On the narrative path `suggested_effects` is passed as **both** `base_effects` and inside `quality_assessment` (`:767-769`), so `apply_quality_scaling` computes `final = (clamp±20(int(delta*mult)) + delta) // 2` — **the LLM's delta is counted twice**. Context modifiers halve alliance gains above 70 cohesion and domestic gains above 80 escalation (`:489-496`).

**It does not drive the ledger.** `record_event_disposition`'s signature is `(narrative_state, action)` (`:137`) and both call sites (`:779`, `:864`) pass exactly that. Disposition is inferred purely from `infer_event_disposition(current.title, action)` (`:155`) over the raw player text — the assessment plays no part.

### 6.3 Advisor character reactions — 1–4 parallel calls, **no LLMContext**

**Builder** `narrative_adjudication.py:597-633`. **Dispatch** `:545-546` `generate_group(..., max_tokens=CHARACTER_RESPONSE_MAX_TOKENS)` — positional, so no `context`.

**Casting** (`_select_responding_characters`, `:564-587`): `uk_nsa` always; `+uk_foreign_sec` if |Δalliance| > 5; `+uk_home_sec` if |Δdomestic| > 5; `+uk_cds` if Δescalation > 5; truncated to 4.

**IN:** `to_llm_context()` (`:605` → `:618`) — **POST-effect** metrics here; the player's raw action (`:620`); the **one-word quality grade** (`:621`); the speaking advisor's `name` (`:623`), `relationship` + `trust` (`:624`), `stance_summary` (`:625`); and a tone adjective derived from the quality word (`:608-615`).

**Does NOT reach it — and the omissions are severe:**
- **`final_effects` is passed and never interpolated.** It is declared at `:506`, passed at `:784`/`:888`, and its **only** use in the body is `_select_responding_characters(narrative_state, final_effects)` at `:530`. `build_character_response_prompt` receives only `(character, action, quality, narrative_state)` at `:536-544`. **The advisor is told the grade and never the consequences.**
- `quality_assessment["reasoning"]` never enters the prompt — **the spoken reaction and the ACTION ASSESSMENT paragraph printed beside it are generated from disjoint information.**
- The secret narrative truth is absent (`world_narrative` is not a parameter), so advisors cannot foreshadow the plot ADJ-1 and the actor prompts can see.
- The interpretation, sibling replies, actor responses, the shared dossier, the transcript, `situation_summary` and `event_ledger` are all absent.

**`stance_summary` is dead state.** The only values ever written are the five literals at `narrative_state.py:409/416/423/430/437`. `update_character_attitude` accepts a `stance_summary` argument (`:272`, applied `:283-284`) and **no caller ever passes it** — `narrative_adjudication.py:943` passes `trust_delta` only. Trust is one adjudication stale on the narrative path and **permanently frozen on the actor path**. Verified in the parked save after 17 turns: trust 50/75/70/80/85, relationships neutral/allied×4, stance summaries verbatim from the constructor. **The model is told the Foreign Secretary is "Loyal but concerned about alliance unity" at turn 18 of a shooting war.**

**`max_tokens=150` is silently dropped on Gemini** (`router.py:353-361` vs `gemini_driver.py:151`), leaving 2048 — despite the comment at `:590-593` warning that a dropped cap yields an empty advisor line.

**AFFECTS:** display, save transcript (`cli/main.py:1894-1898`) and the API's `advisor_reactions`. **Mutates nothing** — pure flavour text. Guards: `[ERROR:` prefixes are blanked (`:557-558`) and empties become `"Understood, Prime Minister."` (`:560`), which exists precisely to stop a cabinet minister reading out an HTTP status.

### 6.4 Situation summary refresh — 1 call, **no LLMContext**

**Builder/dispatch** inline `narrative_adjudication.py:675-685`, dispatched `:687` with `max_tokens=150` (dropped on Gemini).

**IN:** `to_llm_context()` (`:674` → `:676`) — post-effect metrics, casualties, `recent_events[-3:]` **including crisis lines added this turn** (`:791`/`:895` precede it), all `active_crises` **including ones tripped this turn**, character roster, game_time/turn; and the raw action (`:678`, untruncated — contrast the ledger note at `:158` which truncates the same string to 90 chars).

**Does NOT reach it:** **the previous summary it is replacing** — so this is a from-scratch rewrite off the metric block, not a rolling update, and nothing carries forward between consecutive briefs; the action's quality, the reasoning, or the applied deltas (`:660-665` takes only narrative_state/action/llm_fn/rng) — **the summariser cannot know the decision was graded catastrophic**; advisor reactions; actor responses; the secret narrative (which also means the output never passes `_scrub_reasoning`, making it **the one adjudication output with no leak guard** — safe only because the model was never shown the secret); the interpretation; the transcript; the event ledger.

**AFFECTS:** overwrites `NarrativeState.situation_summary` (`:689`). **That field is display-only** — read at `narrative_state.py:233-234`, `cli/main.py:1110/:1962`, `cli/main_dashboard.py:1158/:1733`, and nowhere else. It is **not** in `to_llm_context()` (`:240-266`). The docstring at `:669-671` claiming it "feeds `to_llm_context()` for every downstream prompt" is **false**. It is not even appended to the save transcript.

**This is the game's most expensive orphan: one LLM call per turn writing a rolling narrative recap that no prompt ever reads.** On the parked campaign it is a ~400-char paragraph naming the mole investigation and the intelligence-sharing decision — exactly the continuity the inject generator lacks. What the generator gets instead is the mechanical digest ("Turns played: 17", "Transcript length: 1853 lines", and the same narrator sentence three times).

---

## 7. WINDOWING — THE ARITHMETIC ON A REAL SAVE

Constants in play:

| Constant | Value | Location | Applies to |
|---|---|---|---|
| `MAX_ADVISOR_TRANSCRIPT_CHARS` | **320,000 chars** | `context_builder.py:27` | the 8 shared-prefix calls; also the char bound on the inject last-turn slice |
| `_TRANSCRIPT_HEAD_SHARE` | **0.2** → 64,000 chars | `context_builder.py:54` | campaign-opening reservation |
| `MAX_INJECT_CONTINUITY_LINES` | **400 lines** | `context_builder.py:61` | inject last-turn slice |
| `_LEDGER_TITLE_MAX` | **60 chars** | `context_builder.py:64` | each ledger title |
| narrator tail | **20 lines**, bare literal, no char bound | `prompts.py:587` | narrator bridge |
| `recent_events` window | **last 3** (field capped at 10) | `narrative_state.py:256, :298-299` | all four `to_llm_context` consumers |
| `recent_injects` window | **5** (twice) | `sim_loop.py:392`, `conversation.py:353` | omissions only |
| actor cap | **3** | `narrative_adjudication.py:838`, `actor_simulation.py:273-274` | actor group |
| story digest | **3 lines × 100 chars** | `context_builder.py:595-596` | inject only |
| diplomacy transcript | **NONE** | `context_builder.py:441-512` | diplomacy conversation |

**On `saves/parked_campaign4_borrowed_faces.json`:** 1,853 transcript lines, 729,186 chars as the code counts them — **2.28× the budget**, ~182,000 tokens. 17 turn headers; `world.turn` is 18.

Replaying `context_builder.py:240-274`: `head_end = 183` (turn 1 only, 33,517 chars — turn 2 alone is 39,914 chars and 33,517 + 39,914 > 64,000, so the head loop breaks after one turn); `tail_start = 1282` (turns 12–17, 272,819 chars against a 286,483 tail budget). **Turns 2–11 inclusive — 10 of 17 completed turns, 1,099 lines — are deleted entirely** and replaced by one marker line. **13,351 chars of budget go unspent** because both loops must stop on whole-turn boundaries. Rendered history: 306,649 chars; a full advisor prompt: 314,695 chars (~78,700 tokens).

**What is lost, and why it matters:** the eight shared-prefix calls — the majority of the turn — contain no trace of turns 2–11's injects, decisions, adjudication reasoning, diplomatic calls or advisor warnings. Meanwhile the prompts still instruct the models to use them: `prompts.py:160` ("Reference past decisions, warnings, or outcomes from the conversation history"), `:228`, and `:289` — whose worked example is literally *"As I warned in Turn 2…"*, on a save where turn 2 is elided. `_HISTORY_HEADER` tells the model this is "everything that has happened, in order" (`:35-38`); the elision marker gives a line count but no turn numbers.

**Nothing substitutes for the loss.** `situation_summary` reaches no prompt. `recent_events` is frozen at seed values. `recent_injects` reaches one call and holds 5 titles. And the event ledger — the one structure designed to survive precisely this cut — goes only to the inject generator.

---

## 8. THE LEDGER ASYMMETRY

`NarrativeState.event_ledger` is the game's only per-turn compression of the campaign: one ~94-char line per inject stating what was staged and how it was left. It reaches **exactly one of ~15 calls**.

**Receives it:** `build_inject_generation_prompt` only. Chain: `sim_loop.py:320-321` (`recent_played_events()` with `n=None` → `list(self.event_ledger)`, `narrative_state.py:352-353`) → `:322-324` → `inject_generator.py:64-66` → `prompts.py:405` → `context_builder.py:428-431` → f-string `:103`. It also shrinks the scenario pool (`prompts.py:373`) and enables continuity rule 8 (`:422-424`).

**Does not receive it:** advisor Q&A, decision interpretation, pushback, all five omissions checks, the narrator, ADJ-1/2/3, the actor group, both diplomacy calls. None of their builders has the parameter; `to_llm_context()` omits it (`narrative_state.py:240-266`); `build_shared_context_prefix` never calls `render_event_ledger`.

**The asymmetry is exactly backwards.** The transcript-carrying prompts are the ones that lose ten turns to elision, and the artefact built to survive that cut is not in them — the full 17-entry ledger would cost ~1,600 chars against 13,351 chars of **unspent** budget. Conversely, the one prompt that does get the ledger never gets the history block: the string "GAME HISTORY" does not appear in the generated inject prompt for this campaign (48,908 chars total). **No prompt anywhere in the game ever holds both.**

**Worst case is a resumed campaign.** The parked save has **no `event_ledger` key** (it predates the field); `engine/persistence.py:134` reconstructs `NarrativeState` with the `default_factory=list`, so the ledger comes back **empty**. Turn 18's generator then sees no history block, an empty ledger, a useless digest, and turn 17's 94 lines. And because rule 8 is emitted only `if event_ledger` (`prompts.py:422`), an empty ledger **silently removes the DO-NOT-RESTAGE instruction** — the failure mode is unguarded, not degraded-but-guarded. This is precisely the state in which the repeated-submarine bug was possible.

---

## 9. ORPHANED STATE

### 9.1 Fields no prompt ever sees

| Field | Location | Status | What the game loses |
|---|---|---|---|
| `WorldState.spatial_state` | `models/world.py:40` | **Only occurrence repo-wide.** Never written, never read | No notion of where units physically are. No "where is HMS Montrose"; the generator cannot place an event where the player holds forces |
| `WorldState.posture` | `:37` | Set to `{}` everywhere; only non-empty write is the deprecated `sim_loop.py:714` | `red_intent`/`tempo` were meant to steer the adversary. **Nothing tells any model how aggressive Russia currently is except `escalation_risk`** |
| `WorldState.diplomatic_relationships` | `:58` | Only occurrence repo-wide | Dead duplicate of `StateActor.relationship_uk`; persisted in every save, reads as live state |
| `WorldState.discussion_transcript` | `:46` | Written (`sim_loop.py:488`) and cleared; **no read site** | Pure write-and-clear bookkeeping; not how discussion reaches prompts, contrary to its docstring |
| `WorldState.difficulty` | `:32` | Read only at `sim_loop.py:196` to scale deltas | **The generator writes the same events on "standard" and "brutal"** |
| `NarrativeState.previous_metrics` | `narrative_state.py:75` | Only consumer is `calculate_vibe` (`:173-174`) | **No prompt learns the direction of travel.** An advisor is told "Escalation: 82/100" whether it jumped from 45 or has been falling from 95 |
| `CharacterAttitude.last_interaction` | `:42` | Only occurrence repo-wide; null for all five after 17 turns | No prompt can say "you have not spoken to the Home Secretary since turn 4" |
| `StateActor.public_commitments` | `state_actors.py:16` | Only occurrence repo-wide | **An actor cannot be held to a promise it made** |
| `StateActor.recent_actions` | `:51` | Writer `add_action` (`:67-70`) has **zero callers**; read only by the intel panel | The "BEHAVIORAL TRACKING" section of the model is inert; every actor answers with no memory of its own prior answers |
| `StateActor.trust_trajectory` | `:52` | Written `:60-65`, read only at `intelligence.py:294` | France is told 44/100 but never that it fell 30 points in two turns |
| `StateActor.last_contacted_turn` | `:53` | Only occurrence repo-wide; never written | No prompt can express diplomatic neglect |
| `ActorResponse.action_taken` | `:83` | Never constructed, never requested | Nothing an ally *does* is fed back into the world |
| `StateActorSystem.turn` | `:90` | Never incremented, never read | Permanently 1 |

### 9.2 Scenario data loaded and never sent

| Section | Consequence |
|---|---|
| `initial_flags` (`initial_conditions.yaml:27-33`) | **Zero readers anywhere.** `us_commitment: uncertain`, `f35_pilots_murdered: true`, `severomorsk_attack_false_flag: true`, `public_awareness` — the scenario's entire opening factual state — **never reaches a model**. The only flags any advisor sees are the five metric-derived booleans |
| `intelligence` (`:48-68`) | `severomorsk_attribution`, `pilot_murders`, `cyber_attacks`, `russian_naval_deployment` are **invisible to the NSA whose knowledge domain is literally "intelligence"** |
| `intelligence_summary` (uk_knows / russia_knows) | Zero occurrences repo-wide. **Fog of war is not modelled at all** |
| `red_forces` (`:268`) | The generator is told Russia's goals but not its order of battle |
| `locations` | With dead `spatial_state`, geography exists nowhere in the prompt layer |
| `critical_infrastructure` (`:69-83`) | Never reaches the Home Secretary despite "infrastructure" being one of her routing keywords (`conversation.py:187`) |
| `environment` (`:533-537`) | `public_mood`, `media_coverage`, `economic_impact`, `weather` unused — while `prompts.py:602` explicitly asks the narrator to **invent** weather |
| `timeline` (`:35-47`) | The 5-entry chronology of how the crisis started is in no prompt |
| `objectives['russia']` | `prompts.py:431` interpolates only `objectives.uk`; `red_objectives` is what actually reaches the generator (`:434`), so `objectives.russia` silently diverges |
| `metadata.title/.scenario/.description/.start_date` | Only `start_time` is read. The scenario's own description is never given to any model; every prompt hardcodes its framing |
| `game_state.turn/.phase` | No reader; `WorldState` is built with `turn=1, phase='briefing'` hardcoded. **A scenario cannot start mid-crisis** |
| `characters[*].influence` | No reader. All advisors carry equal weight regardless of stated ranking |
| `characters.president_russia`, `chief_general_staff`, `head_military_intelligence`, `commander_northern_fleet` + their `.objectives` | Excluded by the `"note"` filter (`initial_conditions.py:76`, `prompts.py:268`). **Four fully-specified adversary personas exist in the data and are shown to no model.** Russia is roleplayed only as generic `StateActor` "RUS", and only when the keyword heuristic picks it — the default fallback list is `["USA","FRA","POL"]`, **so the adversary usually never speaks** |
| `scenario_library`: `cyber_scenarios`, `military_target_scenarios`, `civilian_target_scenarios`, `covert_operation_scenarios`, `uk_response_scenarios`, `public_reaction_scenarios`, `crisis_timeline`, `themes`, `llm_guidance`, `metadata` | Only 9 of 26 entries pooled (`prompts.py:368-370`) plus two escalation patterns. **Two-thirds of the mined library is invisible** — one reason the same naval set-piece keeps returning. `llm_guidance`, whose subkeys are `adaptation_principles`/`maintain_tension`/`avoid`, is **guidance written for the LLM that no LLM ever sees** |
| `diplomatic_profiles.yaml:322-355` (`llm_instructions`, per-country `outcome_assessment`) | Zero readers. Hand-authored scoring rules the model must reconstruct or ignore |

---

## 10. EVERY PLACE A CALL RUNS ON LESS THAN THE GAME HAS

Ranked by consequence:

1. **The action-quality adjudicator sees no transcript at all** — not the discussion, not the inject, not one prior turn. It is the call that moves the metrics. 320,000 chars of budget exist and it spends zero.
2. **Five PRO-tier omissions advisors judge the raw typed sentence**, not the interpretation the game just paid to produce (dead parameter, `conversation.py:313`).
3. **Advisor reactions are told the grade and never the effects.** `final_effects` is passed into the function and used only for casting.
4. **The situation summariser is shown neither the quality, the reasoning, the deltas, nor the summary it is replacing** — and its output reaches no prompt anyway.
5. **The diplomatic counterpart is ordered to act on a SECRET MOTIVE that a country-code mismatch guarantees is never in its prompt** (`'US'` vs `'USA'`, `narrative.py:47`).
6. **The diplomatic outcome assessor never sees the secret narrative or the UK decision that prompted the call**, and the per-country scoring rules written for it are unread.
7. **The pushback prompt asks the CDS to flag implausible deployments and wasted munitions with no order of battle and no stockpiles** — data that reached the interpretation prompt three lines earlier.
8. **Foreign capitals get three stale `recent_events` strings** where advisors get 320,000 chars — and those three are frozen at seed values because `add_event` is called only from `_check_and_trigger_crises`.
9. **Advisor trust and stance are frozen** in every real campaign: `_update_character_attitudes` is never called on the actor path, `stance_summary` has no caller at all.
10. **The narrator, whose job is foreshadowing, is blind to the secret narrative** and sees 20 unbounded lines of history.
11. **The inject generator never sees the campaign history**, and on a resumed save loses the ledger *and* the DO-NOT-RESTAGE rule.
12. **`KEY INTELLIGENCE FLAGS` is a third restatement of three numbers already printed twice** — and it displaces nothing, because the scenario's real opening facts (`initial_flags`) are wiped by `compute_risk_flags`.
13. **Eight of twelve call families select no model tier**; four intended `max_tokens` caps (150, 150, 400, and the omissions group) are silently dropped on Gemini, leaving the driver-wide 2048.
14. **The diplomacy conversation ships an uncapped, loosely-filtered transcript to a PRO model on every message**, with no exchange cap at all on the API path.
15. **`prime_minister` is offered to the pushback model as an advisor** who may object to the player's own decision.