# FALSE FLAG — Authored/Static Content Audit (branch claude/game-audit-pr-review-u6ujyq)

Severity key: **breaks-play** / **confuses-player** / **polish**.
All paths absolute under /home/user/false-flag.

---

## SECTION 1 — INVENTORY OF AUTHORED/STATIC TEXT SOURCES

### 1.1 Canonical scenario data (the ground truth everything else must match)
- `data/scenarios/war_game_2025/initial_conditions.yaml`
  - Timeline: `:35-45` (Severomorsk explosions 2025-10-01 killing ~100, `:40-41`; two F-35 pilots "found shot dead in Norfolk" 2025-10-04, `:43`; COBRA convened 5 Oct 17:00, `:45`).
  - Intelligence assessment: `:47-66` (GCHQ high confidence Dagestani extremists `:50`; Russia "falsely blames UK; claims frogman outfit found" `:51`; pilot murders `confidence: low`, "likely tracked before killed; traditional special forces activity" `:53-55`; cyber +65% `:57-59`; 15-submarine surge `:61-66`).
  - 617 Sqn at RAF_Marham with "2 pilots murdered 4 Oct" note: `:192-199`. Named locations incl. RAF_Marham (Norfolk) `:309` and Severomorsk `:322`.
  - Red objectives / Operation Tuman: `:269`, `:296-302`. Diplomatic contacts: `:382-436`. Advisor character sheets: `:441-530`. Verdict: internally consistent; this file IS the anchor.
  - **Nuance (polish):** the pilots are consistently *shot/murdered* in every repo source; nothing anywhere says "crash". If any external description says the pilots died in a crash, the repo does not support it — no in-repo contradiction found.

### 1.2 Current initial situation_summary seed (post-ER-048 rewrite)
- `models/narrative_state.py:486-496` — re-checked clause by clause against the scenario:
  - "Two RAF F-35 pilots were murdered in Norfolk … likely Russian special-forces operation" — grounded (`initial_conditions.yaml:43`, `:53-55`). It does slightly overstate confidence ("intelligence assesses as a likely") vs the authored `confidence: low` (`initial_conditions.yaml:54`) — **polish**.
  - "terrorist attack on the Severomorsk naval base killed over a hundred Russian sailors; GCHQ attributes it to Dagestani extremists, but Moscow falsely blames the United Kingdom" — grounded (`:40-41`, `:49-51`).
  - Submarine surge, cyber attacks climbing, Russian diplomats leaving London, NATO commitment uncertain — grounded (`:61-66`, `:57-59`, `:29`, `:28`, `:346-347`).
  - Verdict: **grounded**; each event carries its own place and attribution. No remaining confabulation bait found in the seed itself.
- Seed companions:
  - `recent_events` `models/narrative_state.py:509-513` — grounded.
  - `active_crises` `models/narrative_state.py:499-503` — grounded ("Russian Northern Fleet Exercise" matches turn_002's "snap Russian naval exercise").
  - `game_time` default `models/narrative_state.py:428` = "Sunday 5th October 2025, 17:00" — grounded (`initial_conditions.yaml:10-11`).
  - Seeded characters `models/narrative_state.py:443-479`: includes `usa_nsa` "US National Security Advisor" (`:444-450`) inside the player's advisor-attitude dict. `GameManager.get_advisors_state()` (`engine/game_manager.py:457-482`) returns it, so API/dashboard advisor lists show a US official among the UK cabinet, and the seeded UK cabinet list also omits the Attorney General (no `attorney_general` character — see `engine/game_manager.py:285-301` comment "Roles with no seeded character (e.g. the Attorney General) are simply skipped"), so AG pushback never costs trust and the AG never appears in trust panels — **confuses-player**.

### 1.3 Actor/country stances — the rosters and the gap (detail in Section 5)
- Simulated-actor roster: `data/state_actors.yaml` — USA `:5`, FRA `:36`, DEU `:69`, POL `:99`, RUS `:124` (5 countries).
- Mystery-mode stances: `data/scenarios/war_game_2025/narratives.yaml` — both narratives author stances only for RUS/USA/CHN/IRL (`:8-27`, `:35-54`).
- Gap: **FRA, DEU, POL simulated with no authored stance**; CHN and IRL have stances but no simulated actor. Diplomacy switchboard (8 countries, `engine/diplomacy.py:105-106`) additionally exposes Ukraine with no stance. Miss is recorded, not fixed: `models/narrative.py:109-111`.
- Related roster mismatch (**polish/confuses-player**): `initial_conditions.yaml` diplomatic_contacts lists USA/RUS/FRA/DEU/CHN/IRL (`:382-436`) — no Poland or Ukraine — while the live switchboard (`engine/diplomacy.py:105-106`) offers US/France/Germany/Poland/Russia/Ukraine/Ireland/China. A front end using `GameManager.get_diplomatic_contacts()` (`engine/game_manager.py:815-845`) shows a different country list from one using `list_diplomatic_channels()` (`engine/game_manager.py:546-554`).

### 1.4 Advisor personas
- Scenario character sheets: `initial_conditions.yaml:441-530` (UK team `:443-501`; Russian NPC team `:503-530`, marked "Controlled by game injects"). Grounded and consistent with the intro cast.
- Cold-open cast descriptions: `assets/placeholders/intro_stage.md:57-93`. Grounded, but contains raw Rich markup `[cyan bold]…[/cyan bold]` (`:59,66,73,79,85`) — presentation leak, see Section 3.
- Diplomatic personas: `data/diplomatic_profiles.yaml` (US `:5-42`, France `:44-81`, Germany `:83-120`, Poland `:122-159`, Russia `:161-193`, Ukraine `:195-232`, Ireland `:234-272`, China `:274-316`). Grounded against the scenario (Russian ambassador's opener even reprises the Severomorsk accusation, `:191`). One in-joke persona line for Ireland (`:244`, "Have you tried... not having a crisis?") is authored intentionally.
  - **Contradiction (confuses-player):** Ukraine exists here and in the switchboard but nowhere else — no state_actors entry, no narrative stance, no diplomatic_contact — so in Mystery mode a Ukraine call runs with no stance (records a `narrative_stance` miss via `models/narrative.py:109-111`).

### 1.5 Scripted diplomatic-call premise
- `data/scenarios/war_game_2025/episodes/turn_006.yaml:28-45` — mandatory US President call; premise text `:32-35` grounded ("wants assurances before committing to Article 5").
- **Contradiction (confuses-player, borderline breaks-play):** the inject text promises "*** INCOMING SECURE CALL: US PRESIDENT ***" (`turn_006.yaml:17-19`), but the encounter is opened through the ordinary access gate (`engine/diplomacy.py:139-180`, used in the constructor `:448`): US *leader* requires Alliance Cohesion ≥ 60 (`data/diplomatic_profiles.yaml:12`). A player at cohesion 30-59 gets the **US National Security Advisor** answering a call announced as the President; below 30 the encounter constructs inactive with "US is not accepting the call" (`engine/diplomacy.py:461-474`) — i.e. the White House phones you and then refuses its own call. The scripted premise is never guaranteed to match the voice on the line.
- **Contradiction (polish):** `turn_004.yaml:20` names "President Trump" — the only named real person in the game — while the scenario everywhere else deliberately keeps leaders unnamed ("President (unspecified)", `initial_conditions.yaml:385,394,404,412,421`; comments only say "Trump-era", `initial_conditions.yaml:28`, `scenario_library.yaml:38`).

### 1.6 Mystery-mode secrets/roles
- `data/scenarios/war_game_2025/narratives.yaml` — RUSSIA_AGGRESSION `:2-27`, CHINA_PROXY_WAR `:29-54`. Rendered by `models/narrative.py:53-140` (`to_llm_context`, briefing vs roleplay audiences).
- Grounded against the scenario, with one wrinkle: neither narrative's `description` mentions the two authored precipitating events (the Norfolk murders / Severomorsk false flag); RUSSIA_AGGRESSION says the crisis motive is "Arctic shipping lanes" concessions (`:9`) while `initial_conditions.yaml:296-302` (red_objectives / Operation Tuman) says "Neutralize Anglo-Saxons as obstacle; fracture NATO". Both truths are injected into the same generation prompts (inject prompt carries red_objectives at `llm/prompts.py:482-484` AND the narrative block via `llm/context_builder.py:456-459`), so in Mystery mode the generator holds two subtly different accounts of *why* Russia is doing this — **confuses-player** (drift risk across a long campaign).
- Stances gap = ER-046, Section 5.

### 1.7 Dossier static blocks
- `llm/context_builder.py:303-393` `build_shared_context_prefix` — header block `:334-341` ("UK CRISIS WARGAME - SHARED BRIEFING DOSSIER…"), history header `_HISTORY_HEADER` `:35-38`, CURRENT SITUATION tail `:357-369`, event-ledger block `:80-125`, standing voice instruction appended `:389-391`. Grounded/mechanical; no contradictions found.
- `llm/prompts.py:25-32` `ADVISOR_VOICE_INSTRUCTIONS` (incl. British-English lines `:30-31`). On-role where used; see Section 4 for where it *doesn't* reach.
- `llm/prompts.py:35-76` `_state_bands` prose bands — grounded, numbers-to-words only.

### 1.8 Opening SITREP / turn-1 briefing text
- `data/scenarios/war_game_2025/episodes/turn_001.yaml:7-59` — grounded point-for-point against initial_conditions (shot dead in Norfolk `:43`; Severomorsk 1 Oct, >100 dead, GCHQ/Dagestani `:47-49`; 15 subs `:51-52`; cyber +65% `:54`; diplomats departing `:56`).
- `turn_001_fast.yaml` — same room text + compressed beats; grounded.
- **Duplication (polish):** the turn-1 briefing description (`turn_001.yaml:8-36`) restates nearly verbatim the COBRA-room scene the player has just read in the cold open (`assets/placeholders/intro_stage.md:45-101` Scene III): mahogany table, windowless room, the same five advisor vignettes, the same "clears their throat" beat. On every front end that shows both (CLI, dashboard, browser), a new player reads the same scene twice back-to-back.
- Scripted follow-ons `turn_002.yaml`–`turn_006.yaml`: grounded continuations (Kilo-class off Orkney reprises `initial_conditions.yaml:289-292`). They embed advisor dialogue with markdown `**Speaker:**` headings — see Section 3.
- `data/scenarios/war_game_2025/events.yaml` — legacy: `:16` grants a `mission_progress` delta but `models/world.py:6-11` has no such metric (and `llm/prompts.py:64` notes "Mission progress removed"). File appears unconsumed by the current loop (only `load_inject_for_turn` is imported, `engine/sim_loop.py:18`) — **polish** (dead/contradictory data waiting to be re-wired).

### 1.9 Narrator intro prompt (turn-bridge narrator)
- `llm/prompts.py:623-700` `build_narrator_intro_prompt`. Called via `engine/narrator.py:11-48`; gated to turn > 1 / ≥5 transcript lines (`engine/narrator.py:30-31`, `engine/sim_loop.py:396-408`) — so it is NOT a game-start scene-setter (see Section 2).
- **Contradiction (polish):** the prompt embeds `build_world_state_summary` (`llm/prompts.py:660`) which appends ADVISOR_VOICE_INSTRUCTIONS (`llm/prompts.py:107-108`) — so the same prompt tells the model "You are the Narrator of a high-stakes political thriller" (`:673`) and "IMPORTANT: You are a real advisor in COBRA" (`:26`). Two incompatible identities in one prompt.

### 1.10 Cold-open script
- `assets/placeholders/intro_stage.md` (loaded by `engine/intro.py:9-27`, structured by `engine/opening.py:144-162`).
  - Scenes II–III and YOUR ROLE: grounded (15 subs, 7+8 split `:30-32`; COBRA 17:00).
  - **Ungrounded/missing beat (polish):** Scene I (`:4-20`) is set *at Severomorsk* on 2 Oct 03:15 — the morning after the terrorist attack that killed ~100 sailors there (`initial_conditions.yaml:40-41`) — and never mentions the attack, the bodies, or the false-flag accusation. The cold open therefore introduces neither of the two events the whole scenario turns on (no pilot murders, no Severomorsk bombing); a player meets those for the first time inside the turn-1 wall of text the intro was built to pace.
  - Raw Rich markup in the asset (`:59-85`) — Section 3.

---

## SECTION 2 — SCENE-SETTING AT GAME START, PER FRONT END

The shared cold open exists precisely to fix this ("The browser build … inherited none of it and opened cold on the briefing" — `engine/opening.py:10-17`). Whether a fresh emergent-mode player sees it depends entirely on front end (`play_mode` never gates the intro anywhere):

| Front end | Intro shown? | Where |
|---|---|---|
| `cli/main.py` | **YES** | intro loop `cli/main.py:647-704` (`get_opening_scenes`, imported `:73`); turn-1 briefing deliberately flows on unsplit, `cli/main.py:939-941` (`flows_from_intro`) |
| `cli/main_dashboard.py` | **YES** | title sequence + paneled scenes `cli/main_dashboard.py:628-728` (`split_intro_sections(get_intro_lines(200))` `:639`) |
| Headless `GameManager` | **NO** | `GameManager.get_turn_briefing()` `engine/game_manager.py:149-216` returns only the turn's inject; no method on GameManager exposes the opening beats, and the turn-1 narrator bridge is explicitly suppressed (`engine/sim_loop.py:396-408` "Turn > 1"; `engine/narrator.py:30-31` needs ≥5 transcript lines). Scene-setting is left as each front end's job — undocumented, so every new consumer opens cold by default. |
| `api/server.py` `/game/new` | **NO — the gap** | `api/server.py:259-318`: pushes only the inject (`:287-291`) and "BRIEFING COMPLETE" (`:294-296`). The stub comment `:283-284` ("Push Narrator Intro if available … Note: sim_loop might have added lines") is wrong twice: sim_loop's narrator only runs turn > 1, and nothing here ever touches `engine.opening`. The Next.js `frontend/` sits on this API, so its players are the ones who saw no intro. **breaks-play** for the emergent mode specifically: in emergent the player also gets no metrics and no structured panels, so the inject wall of text is literally the entire game start. |
| `docs/py/bridge.py` | **YES** | `new_game` queues the beats before the first briefing, `docs/py/bridge.py:633-639`; rendered by `_emit_scene` `:458-496`; turn-1 briefing split for pacing `:775-789`. |

Verdict: **per-front-end gap, not an engine gap.** The engine authored the fix (`engine/opening.py`), two CLIs and the browser adopted it; `api/server.py` never did (and GameManager gives it no push). Fix belongs either in `/game/new` (emit `get_opening_scenes()` as transcript events before the inject) or as a `GameManager.get_opening_scenes()` passthrough so no front end has to know about `engine.opening`.

Related turn-1 nuance: in emergent/immersive mode CLI the "intelligence briefing" panel is also gated `world.turn > 1` (`cli/main.py:982`), consistent with the intro flowing into turn 1 — not a bug, noted for completeness.

---

## SECTION 3 — MARKDOWN LEAKAGE

### 3.1 What the prompts actually say
**No prompt in the codebase instructs the model to avoid markdown.** Grep for markdown/asterisk/plain-text across prompt builders finds only:
- Three prompts that *demand* markdown: advisor answers `llm/prompts.py:196-200` ("Use **bold** … Use *italics* … bullet points"), decision interpretation `llm/prompts.py:272`, pushback `llm/prompts.py:335`.
- One partial prophylactic: the situation-summary fold, "no headings, no numbers, no bullet points" `engine/narrative_adjudication.py:779-780` (does not forbid `**emphasis**`).
- The narrator bridge's "Format: Just the narrative text. No 'Here is the text:' or quotes." `llm/prompts.py:691` (anti-preamble, not anti-markdown).
- Parser-side mitigation only: `llm/parsing.py:3-15,39` strips markdown decoration *from labels* so parsing survives; it does not clean player-facing prose.

### 3.2 Player-facing call families with NO markdown guidance at all
- Actor public statements (`PUBLIC_RESPONSE`, shown as DIPLOMATIC CABLE / INTERNATIONAL RESPONSE): `engine/actor_simulation.py:44-97`.
- Inject generation (description shown verbatim as the turn briefing): `llm/prompts.py:475-506`.
- Narrator bridge: `llm/prompts.py:673-699`.
- Diplomatic conversation replies: `engine/diplomacy.py:246-276` (and the YAML-side `llm_instructions`, `data/diplomatic_profiles.yaml:322-336`).
- Diplomatic outcome SUMMARY (printed in the CALL ENDED block, `engine/diplomacy.py:567-572`): prompt `engine/diplomacy.py:333-354`.
- Advisor end-of-turn reactions: `engine/narrative_adjudication.py:664-678`.
- Adjudication REASONING (player-facing "ACTION ASSESSMENT"): `engine/narrative_adjudication.py:227-260` area.
- Situation summary (emergent mode's primary display): partial rule only, `engine/narrative_adjudication.py:770-794`.

### 3.3 Which front ends render markdown vs print it raw
- **CLI (`cli/main.py`)**: mixed. Advisor answers pass through `format_advisor_response` → `highlight_keywords`, which converts `**`/`*`/leading `- ` to Rich markup (`cli/formatters.py:106-112`; used `cli/main.py:1311,1672`). Interpretation and reasoning panels use real Markdown rendering (`cli/display_utils.py:231,337`, `cli/rich_ui.py:33-42`). **But briefing/inject text is echoed raw** (`cli/main.py:943-967` → `scroll_text`/`print_briefing_line` `:528-546`, plain `typer.echo`) — so any `**bold**` in an inject prints literal asterisks *even in the Rich CLI*.
- **Dashboard (`cli/main_dashboard.py`)**: intro panels strip `**` crudely (`:648` `content.replace("**","")`) but keep `## SCENE I: …` heading lines in the panel body (`:686-688` only filters `===`), so **raw `##` markdown headings are shown to the player in the dashboard intro** — one confirmed source of "raw markdown visible". Advisor answers converted as in CLI (`:1340`).
- **Browser build (`docs/`)**: renders **ANSI only, never markdown** — bridge docstring `docs/py/bridge.py:12-14`, page renderer `docs/app.js:96` (`ansi.render`). Everything the engine emits is `pen.wrap`ped verbatim: advisor answers (`bridge.py:872-881`), reasoning (`:990-991`), reactions (`:1007-1017`), international responses (`:1029`), calls (`:930-963`), briefings (`:777-782`). Consequence: the advisor prompt's *mandatory* `**bold**` instruction (`llm/prompts.py:196-200`) guarantees literal asterisks on this front end. Same for the cold open's Rich markup `[cyan bold]` (`assets/placeholders/intro_stage.md:59-85`): `_emit_scene` (`bridge.py:477-493`) has no markup handling, so the browser cold open shows `[cyan bold]THE NATIONAL SECURITY ADVISOR[/cyan bold]` raw — **confuses-player**. (CLI handles those lines via `console.print` markup detection, `cli/main.py:667-668,685-688`.)
- **HTTP API / Next.js (`api/server.py`, `frontend/`)**: SSE events carry raw engine text (`api/server.py:287-291,723-727,847-880`); the only client-side cleaning found strips Rich `[bold]` tags in the intel panel (`frontend/components/panels/IntelligencePanel.tsx:121-128`) — nothing renders or strips markdown in transcript content.

### 3.4 Authored content that itself contains markup (leaks on every non-Rich surface)
- Scripted inject episodes embed markdown bold speaker headings: `turn_001_fast.yaml:77,82,87,92,99`; `turn_002.yaml:20,26,32,37`; `turn_002_fast.yaml:18,24,30,37,43,56,75`; `turn_003.yaml:17,23,29,34,40,46`; `turn_003_fast.yaml:22,30,37,42,47,52,69`; `turn_004.yaml:13+` (all `**Speaker:**` blocks); `turn_005.yaml` (`**MISSILE LAUNCH DETECTED**`, numbered `**HOLD FIRE**` options). These are shown raw by cli/main.py briefing echo, the browser bridge, and the HTTP API — **confuses-player** (and they teach the LLM inject-generator that markdown is the house style, since scripted turns enter the transcript that seeds generation).
- Cold-open asset Rich markup: `assets/placeholders/intro_stage.md:59-85` — renders correctly only where `cli/main.py:685-688` special-cases it — **confuses-player** on browser.
- `engine/intelligence.py` emits Rich markup in player-facing intel text (`:34-35,58,69-92,…`): fine in CLI, raw over the API unless each client strips it (only the intel panel does).

---

## SECTION 4 — BRITISH ENGLISH / TONE COVERAGE

The instruction lives in `ADVISOR_VOICE_INSTRUCTIONS`, `llm/prompts.py:25-32` (British-English lines `:30-31`). It travels two ways: appended to the shared dossier (`llm/context_builder.py:389-391`) and appended by `build_world_state_summary` (`llm/prompts.py:107-108`).

### Carries the British-English instruction (UK voices — correct)
- Advisor answers — `llm/prompts.py:113-204` via `get_advisor_context` → shared prefix (`:146,180`).
- Decision interpretation — `llm/prompts.py:237` (shared prefix).
- Pushback — `llm/prompts.py:314`.
- Critical omissions — `llm/prompts.py:566`.
- Inject generation, *first-inject/no-transcript path only* — `llm/prompts.py:458` (`build_world_state_summary`).
- Narrator bridge — `llm/prompts.py:660` — carries it **by accident**: it inherits the whole advisor-voice block, including "You are a real advisor in COBRA" (`:26`), inside a prompt whose own identity is "You are the Narrator" (`:673`). Right spelling, wrong persona — **polish**.

### UK-voiced, player-facing prompts that DO NOT carry it (the gaps)
- **Advisor end-of-turn reactions** — `engine/narrative_adjudication.py:644-680` (`build_character_response_prompt`; context is `narrative_state.to_llm_context()` `:652`, which contains no voice block — see `models/narrative_state.py:258-297`). UK cabinet members reacting in American English is the most visible gap — **confuses-player**.
- **Situation summary fold** (emergent mode's main display) — `engine/narrative_adjudication.py:770-794`. No voice/spelling instruction — **confuses-player** for emergent mode.
- **Inject generation, main transcript path** (every stochastic turn) — `llm/prompts.py:475-506` over `get_stochastic_inject_context` (`llm/context_builder.py:430-480`), which carries no voice block. Injects are written as UK intelligence briefings — **confuses-player**.
- **Adjudication quality/REASONING** (shown as ACTION ASSESSMENT) — prompt at `engine/narrative_adjudication.py:227-260` area; no voice block — **polish**.
- **Diplomatic outcome SUMMARY** — `engine/diplomacy.py:333-354` deliberately takes `_state_bands` *without* the voice block (ER-027, `llm/prompts.py:20-24`) because the numeric-answer rule conflicted; but the British-English line was thrown out with it, and the SUMMARY is printed to the player (`engine/diplomacy.py:567-572`) — **polish** (the ER-027 fix over-rotated: the spelling line is not the metric line).
- **Narrator system_instruction** — `engine/narrator.py:41` ("You are a master storyteller…") adds no spelling guidance (the embedded world summary happens to, per above).

### Intentional exemptions (foreign actors speaking as their own governments)
- State-actor simulation prompts — `engine/actor_simulation.py:44-97` (USA/FRA/DEU/POL/RUS speak as themselves) — **intentional**.
- Diplomatic conversation replies — `engine/diplomacy.py:246-276` + `data/diplomatic_profiles.yaml:322-336` (foreign counterpart voices; the US President being American is the point) — **intentional**.
- Authored US stance text using "defense" — `data/scenarios/war_game_2025/narratives.yaml:14-15` — **intentional** (US voice).

---

## SECTION 5 — ER-046 SPECIFICS: SIMULATED COUNTRIES vs AUTHORED STANCES

### Rosters
- **Actor-simulation roster** (what the multi-agent sim can simulate): `data/state_actors.yaml` — `USA` `:5`, `FRA` `:36`, `DEU` `:69`, `POL` `:99`, `RUS` `:124`. Loaded by `models/state_actors.py:103-117`; display names `engine/actor_simulation.py:13-19`; selection logic `identify_relevant_actors` `engine/actor_simulation.py:279-329` (always-relevant set USA/FRA/DEU/POL `:292`; defaults USA/FRA/POL `:317`, USA/POL `:307`; RUS reachable via explicit mention `:300-303`).
- **Diplomacy switchboard roster**: `engine/diplomacy.py:105-106` — US, France, Germany, Poland, Russia, Ukraine, Ireland, China (profiles for all 8 in `data/diplomatic_profiles.yaml`).
- **Authored mystery-mode stances**: `data/scenarios/war_game_2025/narratives.yaml` — RUSSIA_AGGRESSION: RUS `:8-12`, USA `:13-17`, CHN `:18-22`, IRL `:23-27`; CHINA_PROXY_WAR: RUS `:35-39`, USA `:40-44`, CHN `:45-49`, IRL `:50-54`. Same four countries in both narratives.

### Exact missing sets
- Actor simulation (both narratives): **FRA, DEU, POL** are simulated every turn a relevant action occurs but have **no authored stance** — `build_actor_prompt` renders the narrative per-actor (`engine/actor_simulation.py:40-43`), the lookup misses (`models/narrative.py:88,109-111`, `record_miss("narrative_stance", …)`), and the actor falls back to its generic `state_actors.yaml` hidden agendas.
- Diplomacy (both narratives): calls to **France, Germany, Poland, Ukraine** get the global truth but no stance (`llm/context_builder.py:579-583` → `models/narrative.py:88` miss). CHN and IRL stances *are* used here (China/Ireland calls) but are unreachable in the actor sim (no CHN/IRL actor).
- **Compounding bug (confuses-player):** for the missing countries the roleplay INSTRUCTIONS block is still emitted — "Act according to your secret motive at all times" (`models/narrative.py:127-137`) — pointing at a SECRET MOTIVE section that was never rendered. Same class as ER-001 (a rule naming an absent block).
- **Consistency hazard (confuses-player):** in CHINA_PROXY_WAR the actors that *would* most need re-colouring (FRA with its authored `secret_russia_backchannel` hidden agenda, `data/state_actors.yaml:47-51`; DEU gas dependency `:85-87`) run on their default agendas, so the world's behaviour cannot reflect the drawn narrative for 3 of the 5 simulated capitals — the mystery is undetectable through exactly the channels (allied behaviour) a player would probe.

Severity for ER-046 overall: **confuses-player** (mystery mode only; emergent/original modes have `world.narrative = None` so the gap is silent there).

---

## APPENDIX — CONSOLIDATED FINDINGS BY SEVERITY

**breaks-play**
1. `api/server.py:259-318` — `/game/new` emits no cold open/scene-setting at all (comment stub `:283-284`); emergent-mode players on the HTTP API/Next.js front end start on a bare inject. (Class: per-front-end adoption gap of `engine/opening.py`.)

**confuses-player**
2. `turn_006.yaml:17-19` vs `engine/diplomacy.py:139-180,461-474` + `data/diplomatic_profiles.yaml:12` — mandatory "US PRESIDENT" call can be answered by the NSA or refused outright depending on cohesion; scripted premise not guaranteed by the mechanics.
3. Authored markdown in scripted injects (`turn_001_fast.yaml:77-99`, `turn_002.yaml:20-37`, `turn_002_fast.yaml:18-75`, `turn_003.yaml:17-46`, `turn_003_fast.yaml:22-69`, `turn_004.yaml:13+`, `turn_005.yaml`) prints raw `**…**` in cli/main.py briefings (`:528-546,943-967`), browser (`docs/py/bridge.py:777-782`) and API.
4. Advisor prompts *require* markdown (`llm/prompts.py:196-200,272,335`) while the browser build renders none (`docs/py/bridge.py:12-14`, `docs/app.js:96`) — guaranteed literal asterisks in advisor answers there; no player-facing call family carries an anti-markdown instruction (Section 3.2).
5. Rich markup in the cold-open asset (`assets/placeholders/intro_stage.md:59-85`) renders raw in the browser (`docs/py/bridge.py:477-493`); `## SCENE` headings render raw in the dashboard intro (`cli/main_dashboard.py:686-688`).
6. ER-046: FRA/DEU/POL simulated without stances; UKR callable without stance; roleplay instructions point at absent SECRET MOTIVE (`models/narrative.py:127-137`); details Section 5.
7. British-English instruction missing from advisor reactions (`engine/narrative_adjudication.py:644-680`), situation summary (`:770-794`), and the main inject path (`llm/prompts.py:475-506`) — UK voices in American English.
8. `usa_nsa` seeded inside the UK advisor-attitude dict (`models/narrative_state.py:444-450`) surfaces a US official in UK advisor panels via `engine/game_manager.py:457-482`; no `attorney_general` character seeded, so AG trust is untracked (`engine/game_manager.py:285-301`).
9. Two competing accounts of Russian motive fed to the same Mystery-mode generator (`narratives.yaml:9` "Arctic shipping lanes" vs `initial_conditions.yaml:296-302` Operation Tuman; both enter the inject prompt via `llm/prompts.py:482-484` and `llm/context_builder.py:456-459`).
10. Diplomatic-contact lists disagree: `initial_conditions.yaml:382-436` (6 countries, no POL/UKR) vs switchboard `engine/diplomacy.py:105-106` (8) — two API surfaces report different worlds (`engine/game_manager.py:546-554` vs `:815-845`).

**polish**
11. `turn_004.yaml:20` names "President Trump"; every other source keeps leaders unnamed (`initial_conditions.yaml:385-427`).
12. Seed slightly overstates murder attribution confidence vs `confidence: low` (`models/narrative_state.py:487-488` vs `initial_conditions.yaml:54`).
13. Cold-open Scene I is set at Severomorsk post-attack and never mentions the attack or the pilot murders (`assets/placeholders/intro_stage.md:4-20`); the intro sets scenery but neither precipitating event.
14. COBRA room description duplicated between intro Scene III (`intro_stage.md:45-101`) and `turn_001.yaml:8-36`.
15. Narrator prompt carries the advisor identity block ("You are a real advisor in COBRA") inside "You are the Narrator" (`llm/prompts.py:26,660,673`).
16. Diplomatic outcome SUMMARY lost the British-English line along with ER-027's metric-voice removal (`engine/diplomacy.py:333-354`, `llm/prompts.py:20-24`).
17. `data/scenarios/war_game_2025/events.yaml:16` grants `mission_progress`, a metric that no longer exists (`models/world.py:6-11`; `llm/prompts.py:64`).
18. `engine/intelligence.py:34-92+` emits Rich markup over the HTTP API; only `frontend/components/panels/IntelligencePanel.tsx:121-128` strips it.
