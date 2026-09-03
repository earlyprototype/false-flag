# Handover: the engine's language-model layer

> **Historical snapshot (6 August 2026).** The former "briefing audience"
> security design described below is retired. Current code gives Mystery truth
> only to faction-roleplay prompts; public-output prompts receive player-safe
> qualitative context. See [`../docs/BUILD_STATE.md`](../docs/BUILD_STATE.md).

This describes how FALSE FLAG talks to a language model as the system now stands, after the
six-PR fix campaign (#41 to #46) that closed 45 of the 46 entries in `ENGINE-ROUTING-ISSUES.md`.
It assumes no prior knowledge of the codebase and none of machine learning. The register beside
this file keeps every defect's history: what was observed, how it was fixed and by which PR. The
measurements quoted here are from `2026-08-06-campaign-measurements.md`, taken with the register's
own protocol against the fixed engine.

## The shape of the system

A turn of play issues roughly sixteen requests to a language model. They fall into twelve kinds,
which divide cleanly by what they are for, and every one of the twelve now dispatches through the
router with a named context, so the per-call model table governs all of them (ER-005, ER-019).

Three of those kinds send several prompts in one concurrent group rather than one at a time: the
five advisors scanning for omissions, the foreign governments responding to a decision, and the
advisors reacting to its outcome. Measured over a ten-turn campaign the engine sent 15.9 requests
a turn on average: 8.0 advisory, 3.3 from the deciding kinds, 2.2 from the adjudication outputs
and 2.4 carrying the story. The count rose from the audit's 14.8 because the campaign's one
scripted phone call is now actually played by the player rather than answering itself (ER-033),
which adds up to a dozen conversation calls on the turn it fires.

**Four kinds advise the player and change nothing**: the advisor question-and-answer, the reading
of the player's typed decision, the pushback against it, and the critical-omissions scan. These
open with an identical briefing dossier, deliberately, so a provider's prefix cache can reuse its
work across them: 75.6 per cent of all prompt characters in a measured campaign were
cache-matchable. The dossier now renders the metrics once instead of three times (ER-009), the
omissions scan receives the structured interpretation of the decision it is auditing (ER-002),
At that time, Mystery Mode gave the briefing audience judge-plausibility
instructions instead of telling it to deceive the player it advises (ER-021).

**Three kinds decide what actually happens**: the action quality assessment, the state-actor
simulation, and the diplomatic outcome assessment. These were the audit's biggest finding: they
used to see a frozen clock, one turn-one backstory line and whatever crisis banners had fired.
All three now carry the campaign's memory (ER-017): a rolling situation summary, the recent
events, the active crises, and a decisions-and-outcomes ledger with one line per staged event
saying how the player left it. Their prompts stay near four thousand characters by design - the
memory is compact, not a transcript - so their share of prompt characters remains small (5.8 per
cent) while the content changed from almost nothing to an account of the whole campaign. The
state-actor prompt gets an actor-facing variant of that context without the UK cabinet's private
trust scores (ER-014).

**Two kinds are outputs of the adjudication**: the advisors' spoken reactions, and the rolling
situation summary, which is now a fold - previous summary plus this turn's event, decision and
outcome in, a running four-to-six-sentence synopsis out - and is consumed by five downstream
families instead of reaching no prompt at all (ER-010). It also fills the story generator's
"STORY SO FAR" block, which used to hold a mechanical digest (ER-020).

**Three kinds carry the story**: inject generation from turn seven onward, the narrator bridge
between turns (now told what the player decided, ER-043), and the diplomatic conversation. The
foreign counterpart now receives the call's authored premise and a fail-closed filtered
transcript (ER-041, ER-018) and no longer receives the UK's private metrics (ER-038).

## The four load-bearing mechanisms

**Parsing is tolerant and misses are loud.** Every structured-output parser reads its labels
through shared decoration-tolerant utilities in `llm/parsing.py`: emphasis and bullets on a label
no longer drop a field, numbers are recovered by searching for a signed integer rather than
converting a whole line, and worded refusals ("absolutely not") register as refusals. When a
parser still cannot read a field it records the miss in `llm/parse_health` instead of silently
defaulting. Read it via `parse_health.snapshot()`: `misses` counts fields where the model's
answer could not be read (keyed `family.field`), `fallbacks` counts whole calls that degraded to
a default. `play_campaign.py` prints both as its `parse health:` line, and the front ends surface
the same registry. A healthy full campaign against the recording endpoint shows exactly sixteen
misses, all `narrative_stance.*` - that is ER-046, the one open register entry, a content gap
described below, not a parser failure.

**The decision phase runs three dependency-ordered rounds.** Committing a decision used to issue
seven sequential waits; `engine/decision_phase.py` now runs interpretation alongside the actor
simulation, then pushback alongside the omissions scan and the quality assessment, then the
reactions alongside the summary fold, on a three-worker pool with per-task seeds pre-drawn in a
fixed order so results are independent of thread scheduling (ER-023). Measured at 1.2 seconds a
call the decision phase takes 3.7 seconds - three rounds plus overhead, its dependency floor -
against 8.5 seconds before. A typical turn fell from 12.2 to between 6.1 and 7.4 seconds, and
the share of wall clock with exactly one call in flight fell from 76-80 per cent to 53 per cent,
all of which decomposes into conversation turns and the inject-to-narrator data dependency,
which no fan-out can compress.

**Routing is provider-aware.** `llm/model_config.py:resolve_model_name(provider, tier)` turns the
per-context tier table into a real model name for the provider in use: Gemini keeps the tier
names, the OpenAI-compatible driver resolves `OPENAI_COMPAT_MODEL_FLASH` / `_PRO` (environment
first, then config) with `OPENAI_COMPAT_MODEL` as fallback, so the table and the `--flash-only`
flag now select real models on the shipped provider instead of being discarded (ER-019). Rate
limiters persist in a dict keyed by provider and rate, thread-safe, so tier alternation no longer
discards the request history that enforces the cap (ER-032). The play page lets a player choose a
model, and the worker pins the shared key to the OpenRouter endpoint regardless of what any
message claims (ER-028).

**Campaigns replay and resume deterministically.** The Mystery narrative draw comes from the
seeded generator on every front end (ER-025), both save formats persist the random generator's
position and restore it after construction (ER-037), and a resumed mid-turn save no longer
re-runs the briefing or re-applies its effects (ER-004). The measured campaign's two runs, at
different latencies, produced byte-identical per-family character counts.

## What remains

**ER-046, open by design.** Both shipped Mystery narratives author stances for RUS, USA, CHN and
IRL; the state-actor roster simulates USA, FRA, DEU, POL and RUS. Only USA and RUS overlap, so
three simulated capitals play with no authored stance behind them and two authored stances have
no actor to voice them. The gap is visible in every campaign log as `narrative_stance.FRA/POL/DEU`
parse misses. Closing it is authoring work - stances for the missing capitals or actors for the
missing stances - not engine work.

**Artifacts to know about, none blocking.** The event ledger's disposition inference is
deliberately conservative: it marks an event ADVANCED or RESOLVED only when the decision's words
overlap the event's title, so ledger rows for decisions phrased without naming the event read
OPEN with no note. And the measurement harness plays the scripted call to its eleven-exchange
cap because its canned line never closes the conversation; a real player closing in the designed
five to seven exchanges makes a shorter turn six.

## The current measurements

Full detail, protocol and the before/after table are in `2026-08-06-campaign-measurements.md`.
The headline: 159 calls over a ten-turn seed-42 campaign, 2,173,319 prompt characters, 75.6 per
cent cache-matchable, decision phase 3.7 seconds at 1.2 seconds a call. Both measured runs ended
with, verbatim:

```
no calls fell back to the mock driver
parse health: 16 misses (narrative_stance.DEU x2, narrative_stance.FRA x4, narrative_stance.POL x10)
```

The first line establishes that every call was answered by the endpoint under measurement rather
than the built-in offline stand-in; the second that the only unparsed fields in a full campaign
are ER-046's missing stances. Any future measurement should quote both lines, and a run without
the first does not support a measurement.

Adversarial spot-checks from the same document: a quality assessment reply with emphasised labels
and an annotated delta (`**escalation_risk: +8 (sharp rise)**`) moves the metrics instead of
parsing to nothing, and an actor reply of `WILL_SUPPORT: absolutely not` from every capital costs
twenty-eight points of alliance cohesion against baseline instead of gaining any. Both ran
end-to-end through a real campaign turn using the recording endpoint's `--fixtures` mode.

## Ground rules for working here

Run `python -m pytest tests/` and expect 465 to pass.

After any change under `llm/`, `engine/`, `agents/`, `models/` or to `docs/py/bridge.py`, run
`python dev-scripts/build_play_bundle.py`, or the test named `test_the_bundle_matches_the_repo`
will fail, which is what it is for.

Campaigns run from a fixed seed must replay identically, so avoid iterating over sets of strings
or anything else whose order depends on the environment.

Never handle the plaintext OpenRouter key, and do not open, decrypt or print
`docs/shared-key.json`. Do not add a verifier field to the shared key blob, lower the 600,000
iterations of the key derivation, weaken the authenticated encryption, persist the decrypted key,
or add a base URL override to the play page. Each of those is a deliberate decision.

A failed call to the language model is answered by the built-in offline driver rather than
raising, so a whole campaign can appear to run flawlessly while no model answered any part of it.
Any measurement must count those fallbacks and report the count. `dev-scripts/play_campaign.py`
does this and prints the result; quote its line, and quote its `parse health:` line with it.
