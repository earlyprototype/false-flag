# Handover: the engine's language-model layer

This describes how FALSE FLAG talks to a language model, what is wrong with it, and what to do
about it in what order. It assumes no prior knowledge of the codebase and none of machine learning.
The defect list itself lives in `ENGINE-ROUTING-ISSUES.md` alongside this file; every claim here is
traceable to an entry there.

## The shape of the system

A turn of play issues roughly fifteen requests to a language model. They fall into twelve kinds,
which divide cleanly by what they are for.

Three of those kinds send several prompts in one concurrent group rather than one at a time, which
is why the counts below do not add up the way a list of twelve would suggest: the five advisors
scanning for omissions, the foreign governments responding to a decision, and the advisors reacting
to its outcome. Measured over a ten-turn campaign the engine sent 14.8 requests a turn on average:
8.0 advisory, 3.3 from the deciding kinds, 2.2 from the adjudication outputs and 1.3 carrying the
story.

**Four kinds advise the player and change nothing.** The advisor question-and-answer, the reading of
the player's typed decision, the advisors' pushback against it, and the critical-omissions scan in
which five advisors separately check whether the Prime Minister has forgotten something
catastrophic. These four open with an identical block of briefing text, so a provider can reuse its
cached work across them. They account for eight of the fifteen requests, because the omissions scan
is five separately addressed but identically shaped calls.

**Three kinds decide what actually happens.** The action quality assessment, which scores the
decision and proposes changes to the three headline metrics; the state-actor simulation, in which up
to three foreign governments respond and their responses are converted into metric changes; and the
diplomatic outcome assessment, which scores a phone call and moves alliance standing.

**Two kinds are outputs of the adjudication.** The advisors' spoken reactions, which the player
sees, and a rolling situation summary.

**Three kinds carry the story.** The generation of each turn's event from turn seven onward, the
atmospheric bridge between turns, and the diplomatic conversation itself.

The first grouping received 89.0 per cent of every prompt character the engine sent over a measured
ten-turn campaign. The second received 5.9 per cent. That imbalance is the single most important
fact in this handover and it is the through-line of most of what follows.

## The four things that matter most

**The parsers fail toward silence.** The engine asks the model to answer in a labelled format and
then reads those labels back with literal string tests. Four separate parsers do this, and every one
of them, when the test misses, falls back to a value that reads as "nothing happened" rather than as
an error. A decision whose effects were dropped shows the player a placeholder assessment. A foreign
government's refusal becomes a bland acknowledgement scored as a small win. A cabinet that objected
in a bulleted list is read as a cabinet that did not object, and the player never sees the
confirmation gate. An advisor who names a catastrophic omission without also naming a fix is
discarded. In every case the request succeeded, so nothing is logged and no counter moves. See
Nine register entries cover this one class: `ER-015` and `ER-034` on the parser that scores the
decision, `ER-016` and `ER-030` on the one that reads a foreign government's reply, `ER-029` on the
one that scores a phone call, `ER-035` and `ER-036` on the two that read the advisors' objections,
`ER-042` on the one that applies a generated event's effects, and `ER-045` on what happens when one
request in a concurrent group fails.

Two of these need no unusual model behaviour at all. A number written as `+8 (sharp rise)` is enough
to drop it, and a refusal phrased as "absolutely not" is enough to invert it.

**The calls that decide the outcome know almost nothing.** All the campaign history goes to the
advisory calls. The three calls that set the metrics share a small fixed summary whose event list is
seeded on turn one and never updated with anything that happened afterwards. At turn nine of the
measured campaign the referee was looking at one line of turn-one backstory and two crisis banners.
This is register entry `ER-017`, on what the deciding calls are shown.

**The configuration does not reach the code.** The table that assigns a model tier to each kind of
call produces names that the driver used by the public deployment discards outright, so every call
runs on the same model whatever the table says. Separately, five of the twelve kinds never consult
the table at all. And the component that spaces out requests to stay inside a provider's rate limit
is thrown away and rebuilt every time the game switches tier, which happens constantly, so the limit
is never reached and the provider starts refusing calls, which are then answered by a built-in
offline stand-in without a word to anyone. Three register entries cover this: `ER-019` on the model
table being discarded by the shipped driver, `ER-005` on the five kinds that never consult it, and
`ER-032` on the rate limiter losing its history.

**One authored feature is entirely unreachable.** Mystery Mode ships per-country secret motives,
public postures and intelligence-sharing levels. The lookup that would deliver them compares country
codes as exact strings, and the two halves of the codebase spell those codes differently: the
scenario data says `USA` and `RUS`, the diplomacy engine says `US` and `Russia`. Nothing ever
matches, and the miss is silent. This is register entry `ER-012`, on the unreachable per-country
content.

## What a player actually experiences

Worth stating plainly, because the defect list is written from the code's side.

On the public browser build, the campaign's one scripted phone call from the US President plays
itself: the engine answers "Thank you." in the player's name, the call ends after one exchange, and
the player is graded on it. In the two play modes whose entire definition is hiding the numbers, the
call still ends by printing one. The foreign counterpart has been told the Prime Minister's private
domestic-stability score, and has not been told why he telephoned.

From turn seven onward every event is model-generated. If a generated event writes its effect in a
form the parser does not accept, the event is narrated in full, enters the transcript and the event
ledger, and changes nothing.

A campaign started from a fixed seed does not replay identically in Mystery Mode, and reloading a
save replays random draws the campaign already spent.

## The order I would fix them in

**First, make failure visible.** Nothing else is safe to reason about while a failed parse and a
successful one look identical. That means logging every parse miss and every fallback, and counting
them where the player or the operator can see the count. This is small and it changes what every
subsequent measurement means.

**Second, fix the parsers at the source rather than one at a time.** Four parsers share one defect
in four places. Asking the model for structured output and validating it removes the class. If that
is too large a change, the minimum is to make each parser tolerant of decoration and to recover
numbers by searching for a signed integer rather than converting a whole line. That second technique
is already correct in one place in this codebase and can be copied.

**Third, decide what the deciding calls should see,** and give it to them. This is the largest
change in the list and the one that most changes how the game plays, because it is what makes
consequences follow from the campaign rather than from a snapshot.

**Fourth, repair or remove the routing table.** It currently does nothing on the shipped path, and a
table that does nothing is worse than no table, because it invites the belief that a setting was
applied. The rate limiter belongs in the same piece of work.

**Fifth, the rest,** in severity order from the register.

## What has not been established

No call was made to a live provider from the environment this was produced in, so no claim here
depends on one, and no frequency is claimed anywhere. Several entries turn on how a real model
formats its answer; how often that happens needs a run against a live provider by someone who can
hold the key.

The HTTP server's missing briefing after turn one was established by reading the source, not by
running the server.

The measurements come from a local recording endpoint, not from a real provider. Both runs used the
`war_game_2025` scenario in its default `standard` variant, seed 42, play mode `emergent`, Mystery
Mode on, endings on, and one player question per turn; one ran with no artificial latency and one
held every call at 1.2 seconds. Each reached an ending on turn 10 and issued 148 requests, and each
ended with `play_campaign.py` reporting "no calls fell back to the mock driver", meaning zero of the
148 were answered by the built-in offline driver instead of the endpoint. That confirmation is what
makes the counts mean anything, and a run without it does not support a measurement. The exact
commands are in the register under "How the measurements below were taken"; any future measurement
should use them and quote the fallback line.

## Ground rules for working here

Run `python -m pytest tests/` and expect 335 to pass.

After any change under `llm/`, `engine/`, `agents/`, `models/` or to `docs/py/bridge.py`, run
`python dev-scripts/build_play_bundle.py`, or the test named `test_the_bundle_matches_the_repo` will
fail, which is what it is for.

Campaigns run from a fixed seed must replay identically, so avoid iterating over sets of strings or
anything else whose order depends on the environment.

Never handle the plaintext OpenRouter key, and do not open, decrypt or print `docs/shared-key.json`.
Do not add a verifier field to the shared key blob, lower the 600,000 iterations of the key
derivation, weaken the authenticated encryption, persist the decrypted key, or add a base URL
override to the play page. Each of those is a deliberate decision.

A failed call to the language model is answered by the built-in offline driver rather than raising,
so a whole campaign can appear to run flawlessly while no model answered any part of it. Any
measurement must count those fallbacks and report the count. `dev-scripts/play_campaign.py` does
this and prints the result; quote its line.
