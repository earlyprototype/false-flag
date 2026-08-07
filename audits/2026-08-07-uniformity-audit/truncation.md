# Truncation-detection audit — FALSE FLAG

Branch `claude/game-audit-pr-review-u6ujyq`, HEAD ca4a2cb ("Add the call-log tap and extend parse health with truncation/residue"). Read-only audit; all paths relative to /home/user/false-flag.

## 0. Executive answer

**No call site can currently tell when the model stopped on length.** The router already threads a `meta_out` dict (llm/router.py:289, :309-310 single; :418, :437-438 batch) and logs `finish_reason` to the call log (llm/router.py:346, :510), and `record_truncation` exists (llm/parse_health.py:41-53) — but **no driver accepts `meta_out` and nothing calls `record_truncation`** (grep: its only occurrences are the definition and snapshot/total/reset in parse_health.py). `finish_reason` is therefore always `None` in every call-log record. The minimal uniform fix is 4 driver-side insertions (2 drivers × single+batch), enumerated in §5, plus a game.zip rebuild — no call-site changes needed.

**CRITICAL side-finding (live regression in the shipped browser build):** the router now passes `meta_out` to any driver whose signature admits it *including via a `**kwargs` catch-all* (llm/router.py:298-301, :309-310). The browser bridge's fault probe wraps the live driver's methods in `def wrapper(*args, **kwargs)` (docs/py/bridge.py:285-303, installed at :536 via install_fault_probe :309-334, openai_compat only :324). That wrapper's catch-all makes `accepts('meta_out')` true, so the router forwards `meta_out=...` through the wrapper into `OpenAICompatDriver.generate_text`, which does **not** accept it (llm/openai_compat_driver.py:153-160) → `TypeError` on **every live LLM call in the browser build**, retried once (same failure), then silent mock fallback (llm/router.py:317-330) with an on-page "call failed before it got an answer" fault report. Same for the batch path (`meta_out=metas` at llm/router.py:437-438 → wrapper → llm/openai_compat_driver.py:239-240). docs/game.zip vendors llm/ and its copies are **byte-identical to the working tree** (verified by SHA-256: router.py fbba0b83…, openai_compat_driver.py 827f3ee6… both MATCH), so the committed bundle ships this bug. Fixing the drivers to accept `meta_out` (§5) incidentally cures it; the probe should also preserve the wrapped signature (e.g. `wrapper.__signature__ = inspect.signature(fn)`) so router introspection stays truthful.

## 1. Every LLM generation call site

All generation funnels through `llm.router.generate_text` (llm/router.py:245) / `batch_generate_text` (llm/router.py:368) — either directly, or via an injected `llm_generate_fn`/`llm_batch_fn` that is always the router pair (bound at engine/sim_loop.py:467, :560, :621, :639-640; engine/game_manager.py:368/:378-379 and :594-597; cli/main.py:1215, :1877-1879, :1888-1890; cli/main_dashboard.py:1237, :1651-1653, :1662-1664; engine/decision_phase.py wraps the same pair with quiet_generate :97-123 which passes kwargs through). api/server.py has **no** direct LLM calls — it drives GameManager only (api/server.py:25, :266). docs/py/bridge.py has **no** driver of its own — it sets `WARGAME_LLM=openai_compat` env (docs/py/bridge.py:549) and GameManager runs the ordinary router + OpenAICompatDriver under Pyodide (requests → pyodide-http sync XHR, docs/worker.js:97, :206-210).

Tier mapping: llm/model_config.py:35-50. Driver-default cap when a site passes none: **2048** for both live drivers (llm/gemini_driver.py:94/:97; llm/openai_compat_driver.py:145), overridable by GEMINI_MAX_TOKENS / OPENAI_COMPAT_MAX_TOKENS config.

| # | Call site (dispatch) | LLMContext family | max_tokens | Tier |
|---|---|---|---|---|
| 1 | agents/conversation.py:201 | ADVISOR_QA | none → 2048 | PRO |
| 2 | agents/conversation.py:237 | DECISION_INTERPRETATION | none → 2048 | FLASH |
| 3 | agents/conversation.py:268 | ADVISOR_PUSHBACK | none → 2048 | FLASH |
| 4 | agents/conversation.py:390-393 → generate_group (llm/fanout.py:67 batch / :81 sequential) | CRITICAL_OMISSIONS (5 advisor prompts) | none → 2048 | PRO |
| 5 | engine/narrative_adjudication.py:273-274 | QUALITY_ASSESSMENT | **400** | PRO |
| 6 | engine/narrative_adjudication.py:591-593 → generate_group | CHARACTER_RESPONSE (≤4 prompts) | **150** (CHARACTER_RESPONSE_MAX_TOKENS, engine/narrative_adjudication.py:641) | FLASH |
| 7 | engine/narrative_adjudication.py:796-798 | SITUATION_SUMMARY | **400** (raised from 250 in 5533965) | PRO |
| 8 | engine/actor_simulation.py:145-146 → generate_group | ACTOR_SIMULATION (one prompt per capital, ~5) | none → 2048 | PRO |
| 9 | engine/actor_simulation.py:111 (simulate_actor_response, legacy single-country path) | none (no context arg) | none → 2048 | none → provider default model |
| 10 | engine/diplomacy.py:356 (encounter outcome, reached from .end at :538+) | DIPLOMACY_OUTCOME | none → 2048 | PRO |
| 11 | engine/diplomacy.py:524 (process_turn) | DIPLOMACY_CONVERSATION | none → 2048 | PRO |
| 12 | engine/narrator.py:37-44 | NARRATOR | **150** | FLASH |
| 13 | llm/inject_generator.py:74 | INJECT_GENERATION | none → 2048 | PRO |
| 14 | dev-scripts/debug_llm.py:30 (dev tool) | none | none → 2048 | — |
| 15 | dev-scripts/spike/index.html:190 (spike, calls a driver directly) | — | — | — |

Notes:
- The Pyodide/browser build adds **no** new call sites: docs/game.zip packs `models, engine, llm, agents, data, assets/placeholders` + bridge.py (dev-scripts/build_play_bundle.py:33-38), so rows 1-13 are exactly the browser's call sites too, running on OpenAICompatDriver.
- llm/fanout.py batch path failure marker: per-prompt `"[ERROR: ...]"` strings (guards at engine/narrative_adjudication.py:604, engine/actor_simulation.py:150, agents/conversation.py:400).
- llm/client.py is a Protocol only (no calls). Mock driver (llm/mock_driver.py:1140, :1329) and offline driver (llm/offline_driver.py:15) accept-and-ignore `**kwargs`; they return canned text and can never truncate — no change needed there.

## 2. Driver-side truncation signals and unpack points

### GeminiDriver (llm/gemini_driver.py)
- API signal: `response.candidates[0].finish_reason == FinishReason.MAX_TOKENS` (google.generativeai protos enum, name `"MAX_TOKENS"`, value 2).
- **Single** unpack: llm/gemini_driver.py:182-188. `if response.text: return response.text.strip()` (:183-184) — a reply truncated mid-text (MAX_TOKENS *with* partial text) returns here silently; finish_reason is only read on the empty-response error path (:187). Fix point: add `meta_out: Optional[dict] = None` to the signature at :141-144; between :182 and the return at :184, read `response.candidates[0].finish_reason`, store its name in `meta_out['finish_reason']`, and call `record_truncation("gemini", self.model_name)` when it is MAX_TOKENS.
- **Batch** unpack: llm/gemini_driver.py:235-239 inside `generate_single` (thread-pool worker, defined :219). Same silent-partial shape at :235-236. Fix point: add `meta_out: Optional[list] = None` to `batch_generate_text` (:195-196), pass the per-prompt index into `generate_single`, fill `meta_out[i]['finish_reason']` beside :235-239. parse_health is already thread-safe (llm/parse_health.py:8, :17).

### OpenAICompatDriver (llm/openai_compat_driver.py) — also the browser/Pyodide driver
- API signal: `choices[0]["finish_reason"] == "length"`.
- **Single** unpack: llm/openai_compat_driver.py:217-230. `data = response.json()` (:217), `choices[0]` in hand at :223; finish_reason is only read on the empty-completion error path (:227-229); a truncated non-empty reply returns at :230 undetected. Fix point: add `meta_out: Optional[dict] = None` to the signature (:153-160); just before :230, `fr = choices[0].get('finish_reason')`, fill `meta_out['finish_reason'] = fr`, `record_truncation("openai_compat", self.model_name)` when `fr == "length"`. Filling before the empty-check raise at :225-229 also covers the reasoning-model empty-completion case.
- **Batch** unpack: llm/openai_compat_driver.py:263-268 — `generate_single` delegates to `self.generate_text` (:265-266), so once generate_text takes `meta_out`, the batch method (:239-240) only needs a `meta_out: Optional[list] = None` parameter and to pass `meta_out=meta_out[index]` per call. Thread-pool ordering is by index (:277-287), so per-index dicts are race-free.

### Router (llm/router.py) — already done, no change needed
- Single: meta created :289, forwarded when accepted :309-310, logged :339-349 (finish_reason :346). Batch: metas :418, forwarded :437-438 (batch_kwargs :424-439), sequential fallback forwards per-index :486-488, logged :501-515.
- One gap worth noting: the call log (llm/call_log.py) records finish_reason but only when logging is enabled; the in-game defect counter is `record_truncation`, which is why it must be called **in the drivers**, not derived from the log.

### Mock / Offline drivers — nothing to do
- llm/mock_driver.py:1140 and :1329, llm/offline_driver.py:15 already swallow `meta_out` via `**kwargs`; canned text never truncates.

### Browser build shipping
- docs/game.zip vendors the full llm/ package (verified: 16 files including openai_compat_driver.py, router.py, parse_health.py; hashes match working tree). After any driver edit, **rerun `python3 dev-scripts/build_play_bundle.py`** or the browser keeps the old drivers (dev-scripts/build_play_bundle.py:24, :33-38). The bridge's parse-health line (docs/py/bridge.py:1290-1306, reading `parse_health.total()` which includes truncations per llm/parse_health.py:81-85) will then surface truncations on-page with zero extra work.
- Bridge fault probe: make `_watch_calls`'s wrapper signature-transparent (docs/py/bridge.py:288) — today it converts the router's careful signature inspection into "accepts everything", which is the mechanism of the CRITICAL bug in §0 and would mask any future signature mismatch the same way.

## 3. Truncation-sensitivity classification

SENSITIVE = field-parsed output or output that must end cleanly / is persisted; TOLERANT = a cut is only cosmetic.

| # | Family | Class | Why (parser / consumer) |
|---|---|---|---|
| 5 | QUALITY_ASSESSMENT | **SENSITIVE (highest)** | Line-parsed QUALITY / REASONING / EFFECTS×3 / QUALITY MULTIPLIER (prompt engine/narrative_adjudication.py:258-270, parsed by _parse_quality_response via :275). The load-bearing fields (EFFECTS, MULTIPLIER) are **last**, exactly where a cap-hit lands; loss silently defaults the adjudication. |
| 7 | SITUATION_SUMMARY | **SENSITIVE** | Prose, but persisted: folds into narrative_state.situation_summary and re-enters every downstream prompt (engine/narrative_adjudication.py:809-826) — a mid-sentence cut compounds turn over turn. This is the family that produced the original incident. |
| 13 | INJECT_GENERATION | **SENSITIVE** | Must be well-formed fenced YAML (llm/inject_generator.py:84-104); a truncated fence/document fails yaml parse → inject silently dropped (quiet-turn fallback). Failure is *indirectly* visible today only as a parse warning, not identified as truncation. |
| 8/9 | ACTOR_SIMULATION | **SENSITIVE** | Six labeled fields, INTEL_SHARED last (engine/actor_simulation.py:80-92, parsed :160+). Trailing-field loss on cap-hit. |
| 10 | DIPLOMACY_OUTCOME | **SENSITIVE** | OUTCOME / ALLIANCE_COHESION_DELTA / SUMMARY labels (engine/diplomacy.py:348-352, parsed :358-379+). Delta is mid-payload; cut loses SUMMARY (cosmetic) or delta (state-affecting). |
| 4 | CRITICAL_OMISSIONS | **SENSITIVE** | CONCERN / RECOMMENDATION labels (agents/conversation.py:425-447); truncation mid-CONCERN or lost RECOMMENDATION → record_miss + placeholder (:440-447), currently indistinguishable from model omission. |
| 3 | ADVISOR_PUSHBACK | SENSITIVE (mild) | "Role: message" lines + NO PUSHBACK sentinel (agents/conversation.py:273-307); a cut mid-line clips an advisor's warning; orphan-line handling records misses. |
| 2 | DECISION_INTERPRETATION | TOLERANT-ish | No field parser — returned raw (agents/conversation.py:237-238), displayed and re-fed as prose; a cut clips the trailing FEASIBILITY-style lines but breaks nothing structurally. |
| 1 | ADVISOR_QA | TOLERANT | Free prose displayed verbatim (agents/conversation.py:201-205). |
| 11 | DIPLOMACY_CONVERSATION | TOLERANT | Free dialogue line (engine/diplomacy.py:524-528). |
| 6 | CHARACTER_RESPONSE | TOLERANT (cosmetic cut) — but see §4 | 2-3 sentence reaction; empty result already falls back (engine/narrative_adjudication.py:596-607). |
| 12 | NARRATOR | TOLERANT | Atmospheric bridge; failure path returns a canned line (engine/narrator.py:46-48). |

## 4. Caps that are tight for what the prompt requests

| Call site | Prompt asks for | Cap | Verdict |
|---|---|---|---|
| engine/narrative_adjudication.py:273 (QUALITY_ASSESSMENT) | 1 quality word + a full REASONING paragraph + 3 signed effect lines + a multiplier, in exact labeled format (:258-270) | 400 | **Tight.** A generous paragraph alone can spend 200+ tokens; the state-bearing fields sit after it. On openai_compat reasoning models, thinking tokens bill against max_tokens (config.example.py:28-31, docs/LLM_PROVIDERS.md:185-186) → likely empty/cut. Runs on the PRO tier where longer reasoning is the point. |
| engine/narrative_adjudication.py:796-798 (SITUATION_SUMMARY) | 4-6 full sentences folding the whole campaign, with explicit "finish the final sentence" rule (:776-793) | 400 | **Adequate now** (250 was the incident; 6 sentences ≈ 150-220 tokens), but zero detection means regression is invisible; this is the call the class-wide fix exists for. |
| engine/narrative_adjudication.py:591-593 + :641 (CHARACTER_RESPONSE) | 2-3 in-character sentences (:676) | 150 | Adequate for plain models; **zero headroom for thinking models** — the code's own comment (:637-640) says the cap exists because such a model "spends its whole budget thinking and returns nothing"; on Gemini 2.5 Flash (thinking counts toward max_output_tokens) 150 invites empty replies → RuntimeError at llm/gemini_driver.py:188 → mock fallback. |
| engine/narrator.py:43 (NARRATOR) | 2-3 atmospheric sentences | 150 | Same shape as above; cosmetic on cut, mock-fallback on thinking-model empty. Acceptable. |
| llm/inject_generator.py:74 (INJECT_GENERATION) | Complete fenced YAML document: id, title, multi-paragraph description, channel, effects list (pool exemplars are 250-400 words, llm/mock_driver.py:581-981) | none → 2048 | Usually fine, but this is the most cap-fragile *format* in the game (any cut = whole inject lost), and on a PRO-tier thinking model 2048 minus thinking can pinch. Worth finish_reason coverage first, cap tuning only if the counter fires. |
| All uncapped field-parsed sites (#4, #8, #10) | Multi-field labeled output | none → 2048 | Not tight; included for completeness. |

## 5. Minimal uniform fix (what remains to be written)

1. **llm/openai_compat_driver.py — generate_text (:153-160, unpack :217-230):** add `meta_out: Optional[dict] = None`; before the return at :230 (and before the empty-completion raise at :225-229), set `meta_out['finish_reason'] = choices[0].get('finish_reason')` and call `llm.parse_health.record_truncation` when it equals `"length"`.
2. **llm/openai_compat_driver.py — batch_generate_text (:239-240, worker :263-268):** add `meta_out: Optional[list] = None`; pass `meta_out=meta_out[index] if meta_out else None` through the `self.generate_text` delegation at :265-266.
3. **llm/gemini_driver.py — generate_text (:141-144, unpack :182-188):** add `meta_out: Optional[dict] = None`; before the return at :184, read `response.candidates[0].finish_reason` (guard empty candidates), store its `.name`, record_truncation on `MAX_TOKENS`.
4. **llm/gemini_driver.py — batch_generate_text (:195-196, worker :219-241):** add `meta_out: Optional[list] = None`; fill per index inside `generate_single` beside :235-239.
5. **docs/py/bridge.py:288 (_watch_calls):** give the wrapper the wrapped function's signature (`functools.wraps` + `wrapper.__signature__ = inspect.signature(fn)`), fixing the live TypeError-on-every-browser-call regression (§0) independently of, and in addition to, steps 1-2.
6. **Rebuild docs/game.zip** (`python3 dev-scripts/build_play_bundle.py`) — it vendors llm/ and docs/py/bridge.py; without a rebuild the browser build is left behind.

No call-site edits are required: the router already forwards `meta_out` wherever the signature admits it (llm/router.py:309-310, :437-438, :486-488), the call log already records it (:346, :510), and the browser's parse-health reporter already surfaces `record_truncation` counts on-page (docs/py/bridge.py:1290-1306 via llm/parse_health.py:81-85). Call sites that want to *react* (e.g. retry the situation summary uncapped) can later read the counter or take a meta param, but detection itself becomes uniform with the six steps above.
