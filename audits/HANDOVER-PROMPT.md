# Handover prompt

Paste the text below to brief a fresh session on this work.

---

You are working on FALSE FLAG (github.com/earlyprototype/false-flag), an LLM-driven UK
political-military crisis wargame written in Python. It runs as a terminal application and as a
browser build that executes the same engine inside Pyodide. The test suite is run with
`python -m pytest tests/` and 335 tests pass.

## Where to start

Read `audits/HANDOVER.md` first. It describes how the engine talks to a language model, what is
wrong with it, and the order the problems should be addressed in. Then read
`audits/ENGINE-ROUTING-ISSUES.md`, which is the register of forty-five filed defects, each with the
file and line that establishes it and what it causes during play.

`audits/2026-08-05-llm-context/` is an earlier reference trace of every call the engine makes. It is
useful for orientation and it is not authoritative: several of its claims were found to be wrong.
Treat it as a lead.

## Your task

<state the task here>

## How to work

**Verify before you write.** Every claim in the register carries a file and line. Open it and
confirm it says what the entry says before you act on it or repeat it. Line numbers drift, and a
parameter can sit in a function signature with no caller ever supplying it. If an entry says a piece
of information reaches a prompt, follow it to the formatted string that inserts it.

**Demonstrate rather than reason.** Where an entry describes how a parser behaves, run the parser on
the stated input and confirm the stated output. Most of these are a five-line script. A claim you
have run is worth more than one you have read.

**State inputs with results.** If you report that something produced a number, say exactly what you
fed it. Two people who both "verified" a figure and got different answers have wasted the check.

**Do not write an absolute you have not tested.** "Never", "every", "nothing", "only", "inert",
"no-op". Each of these fails on one counter-example, and finding that counter-example is a minute's
work. Where the honest claim is narrower, the narrower claim is usually still serious.

**Count the fallbacks.** A failed call to the language model is answered by the built-in offline
driver rather than raising, so a campaign can appear to run flawlessly while no model answered any
part of it. `dev-scripts/play_campaign.py` counts these and prints the result. Any measurement you
report must quote that line. A run with fallbacks does not support a measurement.

## Reproducing the measurements

```shell
python3 dev-scripts/fake_openrouter.py --port 8099 --log calls.jsonl --latency 0

WARGAME_LLM=openai_compat \
OPENAI_COMPAT_BASE_URL=http://127.0.0.1:8099/v1 \
OPENAI_COMPAT_MODEL=fake OPENAI_COMPAT_API_KEY=x \
NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost \
python3 dev-scripts/play_campaign.py --turns 18 --questions 1

python3 dev-scripts/analyse_calls.py calls.jsonl
```

Scenario `war_game_2025`, default `standard` variant, seed 42, play mode `emergent`, Mystery Mode
on, endings on, one question per turn. That reaches an ending on turn 10 and issues 148 calls. Add
`--latency 1.2` to the endpoint for timing work.

## Constraints

Never handle the plaintext OpenRouter API key. Do not open, decrypt or print
`docs/shared-key.json`; it is committed deliberately and is live on the public site. Do not add a
verifier or canary field to the shared key blob, do not lower the 600,000 PBKDF2 iterations, do not
weaken the key derivation or the authenticated encryption, do not persist the decrypted key, and do
not add a base URL override to the play page. Each is a deliberate decision.

After any change under `llm/`, `engine/`, `agents/`, `models/` or to `docs/py/bridge.py`, run
`python dev-scripts/build_play_bundle.py`. Without it the test named
`test_the_bundle_matches_the_repo` in `tests/test_opening_beats.py` fails, which is its purpose.

Campaigns run from a fixed random seed must replay identically. Avoid iterating over sets of strings
and anything else whose order depends on the `PYTHONHASHSEED` environment variable.

## Filing new findings

Append to `audits/ENGINE-ROUTING-ISSUES.md` in the existing shape: a permanent `ER-nnn` identifier
allocated in sequence and never reused, a status, a severity, an area, what is observed, the file
and line that establishes it, and what it causes during play. An entry that turns out to be mistaken
is marked `invalid` with a note rather than deleted, so anything citing that identifier still
resolves. Keep the index table at the top in step with the entries below it. An entry without
evidence is not ready to file.

## Writing for the operator

One reader: a sharp, attentive person with no machine-learning background who is the final authority
on this project. Never use a bare identifier, statistic or term of art; explain each in ordinary
words in the same sentence. Lead with the answer, then the reasoning. Give every number its scale
and its baseline. Complete sentences, no fragments, no em dashes. Mark what is established, what is
inferred and what is speculation inside the sentence. State the limits of the analysis before the
reader finds them. If you were wrong earlier, say what you said, say it was wrong, and say what is
true instead. Be modest in claim and calm in tone.

Decisions about what to change belong to the operator. Investigate and report freely; do not begin
changing engine behaviour without being asked.
