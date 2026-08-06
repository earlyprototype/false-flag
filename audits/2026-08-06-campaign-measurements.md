# Campaign measurements, 2026-08-06: the fixed engine re-measured

The register's measurement protocol, re-run unchanged against the engine with all five fix PRs
(#41 to #46) merged. The original numbers were taken at commit `9f0c3fa` and are quoted from
`ENGINE-ROUTING-ISSUES.md`; the new numbers were taken at the merge of PR #46 (`5c0e1a6`) plus
one measurement-tooling commit to `dev-scripts/fake_openrouter.py` described below. The engine
itself was not modified for these measurements.

## The protocol

Identical to the register's original recipe. Two headless campaigns through
`dev-scripts/play_campaign.py` against the local recording endpoint
`dev-scripts/fake_openrouter.py`, one with no artificial latency and one holding every call at
1.2 seconds. Scenario `war_game_2025`, default `standard` variant, seed 42, play mode `emergent`,
Mystery Mode on, endings on, one player question per turn (all of these are `play_campaign.py`
defaults except `--questions 1`, which is passed explicitly and is also the default).

```shell
python3 dev-scripts/fake_openrouter.py --port 8099 --log calls.jsonl --latency 0
# and, for the timing run, the same with --latency 1.2

WARGAME_LLM=openai_compat \
OPENAI_COMPAT_BASE_URL=http://127.0.0.1:8099/v1 \
OPENAI_COMPAT_MODEL=fake OPENAI_COMPAT_API_KEY=x \
NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost \
python3 dev-scripts/play_campaign.py --turns 18 --questions 1

python3 dev-scripts/analyse_calls.py calls.jsonl
```

Both campaigns reached the same terminal ending, TESTED AND FOUND WANTING (defeat), on turn 10,
and issued 159 game calls with byte-identical per-family character counts across the two latency
settings, which is the determinism claim doing its job. Raw logs are not committed; they
regenerate from the commands above in under two minutes.

### Measurement-tooling change made first

Two of the twelve call families had stopped classifying in `fake_openrouter.py` because the
campaign's fixes reshaped their prompts: the diplomatic outcome assessment and the counterpart's
conversation turns both relied on the word "diplomat" happening to sit inside the prompt's last
2,000 characters, which held only while transcript text drifted through that window. Both now
anchor on the prompts' own closing lines (`Your assessment:`, `Your response (as `), and the
outcome assessment has a canned reply that parses cleanly through the real parser. Without that
second fix the endpoint answered the outcome assessment with "Acknowledged.", which recorded
three `diplomacy_outcome` parse misses per run that belonged to the measurement rig rather than
the engine. `analyse_calls.py` needed no change; classification lives in the endpoint.

## Both health lines, from each run

A campaign can look flawless while the offline stand-in answered part of it, and a tolerant
parser can quietly substitute defaults; the two health lines are what make every number below
mean something. Both runs ended with, verbatim:

```
no calls fell back to the mock driver
parse health: 16 misses (narrative_stance.DEU x2, narrative_stance.FRA x4, narrative_stance.POL x10)
```

Every one of the 159 calls in each run was answered by the endpoint under measurement, and the
only parse misses in a full campaign are the sixteen `narrative_stance` lookups for the three
capitals that have a state actor but no authored Mystery stance. That is ER-046, the register's
one open entry, visible in the logs exactly as designed: a data gap, not a parser failure. The
original runs predate the parse-health line; their fallback line read the same.

## Before and after

The "before" figures are the register's, taken at `9f0c3fa` with the same protocol. Grouping
follows the register's: the deciding families are the action quality assessment, the state-actor
simulation and the diplomatic outcome assessment; the advisory families are the advisor Q&A, the
decision interpretation, the pushback and the critical-omissions scan; the adjudication outputs
are the character reactions and the situation summary; the story families are inject generation,
the narrator bridge and the diplomatic conversation.

| claim | before (`9f0c3fa`) | after (`5c0e1a6`) |
|---|---|---|
| calls per campaign | 148 | 159 |
| requests per turn | ~14.8 | 15.9 |
| deciding families' share of prompt characters | 5.9% | 5.8% |
| advisory families' share | 89.0% | 80.2% |
| adjudication outputs' share | 1.5% | 1.3% |
| story families' share | 3.7% | 12.8% |
| decision phase at 1.2 s/call | 8.5 s | 3.7 s |
| whole turn at 1.2 s/call | 12.2 s | 6.1 s scripted, 7.4 s generated |
| share of wall clock with exactly one call in flight | 76-80% | 53% |
| turn-nine referee's memory | 1 backstory line + 2 crisis banners | rolling summary + recent events + active crises + 9-row decisions ledger |
| player question in history-carrying prompts | twice | once |
| situation summary's output | reached no prompt | in five downstream families' prompts |

Readings, in order:

**Requests per turn rose by design.** The eleven extra calls are all turn six: the scripted call
from Washington used to answer itself in the player's name after one exchange (ER-033) and now
stays live for the player. `play_campaign.py` answers it with a non-closing line each time, so
the call runs to its eleven-exchange cap and then the outcome assessment fires; a real player
closing in the designed five to seven exchanges would sit between the old count and this one.
The same eleven calls explain the story families' share tripling: eleven counterpart prompts at
roughly 18,700 characters each is most of the difference, and the diplomacy family's mean size
also grew because the counterpart now receives the call's authored premise and the conversation
so far (ER-041) instead of a snapshot plus the UK's private metrics (ER-038, removed).

**The deciding share barely moved, and that is the correct outcome, not a failure to fix.** The
original 5.9 per cent was an indictment because the deciding calls' small prompts contained
almost nothing: a frozen clock, one turn-one backstory line and whatever crisis banners had
fired. The fix (ER-017, PR #44) gives them a compact rolling memory rather than the whole
transcript: the turn-nine quality-assessment prompt in the latency-0 run carries the SITUATION
SUMMARY block (filled by the previous turn's summary fold), three recent events, five active
crises, and a DECISIONS AND OUTCOMES ledger with one row per staged event turn 1 through turn 9.
Those prompts stay near four thousand characters while the advisory prompts grow with the
transcript, so the percentage share stays small by design; what changed is what the characters
say. One expected artifact of the harness: most ledger rows read OPEN with no decision note,
because the disposition inference deliberately claims engagement only when the decision's words
overlap the event title, and `play_campaign.py` cycles five canned decisions that mostly do not.
Turn 7's row shows the mechanism working: "Baltic Cable Survey Vessel Detected | ADVANCED |
Deploy a Type-45 to shadow the vessel and make a public statement."

**The decision phase hit its dependency floor.** 3.7 seconds is three dependency-ordered rounds
at 1.2 seconds each plus about a tenth of overhead, against the old seven sequential waits
(ER-023). Every turn's decide column read 3.7 s in the timing run.

**The remaining sequential time is accounted for, to the tenth of a second.** 42.1 seconds of
the 79.5-second campaign had exactly one call in flight. The calls that are inherently serial
are the ten advisor Q&As (a conversation turn each), the scripted call's eleven counterpart
exchanges plus one outcome assessment (a conversation), the nine narrator bridges and four
inject generations (the bridge takes the freshly generated inject's title as input, so the pair
cannot overlap). That is 35 calls at 1.2 seconds: 42.0 seconds. Nothing measurable is left on
the table by the round packing.

**Turn six's 20.6 seconds is the player's call, not engine seriality.** 15.7 seconds of briefing
is the eleven-exchange scripted call at 1.2 seconds per exchange plus the inject machinery; the
turn's decide column is the same 3.7 seconds as every other turn.

**The double-written question is gone (ER-024).** The turn-one decision-interpretation prompt
contains the turn-one question line "Prime Minister: Where does NATO stand on this?" exactly
once, and the final interpretation prompt has zero consecutive duplicate Prime Minister lines.
(A naive count over the whole final prompt finds each question twice, because the harness's
five-question cycle asks each question twice across ten turns.)

**The situation summary is consumed (ER-010, ER-020).** The canned summary text returned by the
turn-one summary fold appears in the turn-two inject-generation prompt (sequence 19 of the
latency-0 log) and thereafter in the prompts of five families: `inject_generation`,
`quality_assessment`, `actor_simulation`, `character_response` and `diplomacy_outcome`.

### Full per-family table, latency-0 run

```
call kind                   n  mean chars  max chars
critical_omissions         50      21,158     30,662
actor_simulation           22       3,719      4,442
character_response         12       1,765      2,083
diplomacy                  11      18,720     20,751
advisor_qa                 10      21,547     33,727
decision_interpretation    10      26,038     35,504
quality_assessment         10       3,947      4,248
advisor_pushback           10      20,823     30,289
situation_summary          10         761        781
narrator_bridge             9       3,115      3,863
inject_generation           4      10,838     13,021
diplomacy_outcome           1       3,867      3,867
```

Total 2,173,319 prompt characters, of which a prefix cache could match 1,641,953 (75.6 per
cent); 91 of 159 calls (57 per cent) open with the same first thousand characters as an earlier
call. Concurrency profile of the timing run: wall 79.5 s, at least one call in flight 78.1 s
(98 per cent), exactly one 42.1 s (53 per cent).

## Adversarial spot-checks, end to end

Both demonstrations run a real campaign turn (`play_campaign.py --turns 1 --questions 1`, same
seed and settings) against the endpoint with a `--fixtures` override substituting one hostile
reply, everything else answered by the standard canned replies. The clean baseline turn one ends
`risk=63 stab=48 coh=46` from initial metrics of 60/50/40. Both runs printed
"no calls fell back to the mock driver" and a parse-health line of two `narrative_stance` misses
(DEU, POL: the turn-one actors without authored stances) and nothing else, so neither hostile
reply cost a single parsed field.

**(a) Decorated quality reply with an annotated delta still moves the metrics** (the ER-015 and
ER-034 shapes). Fixture, served exactly once, to the quality-assessment call:

```json
{"QUALITY MULTIPLIER:": "**QUALITY: poor**\n**REASONING:** The decision ignores the alliance dimension entirely and commits forces without a legal basis.\nEFFECTS:\n- **escalation_risk: +8 (sharp rise)**\n- **alliance_cohesion: -6**\n- **domestic_stability: -3**\n**QUALITY MULTIPLIER: 0.5**"}
```

Turn one ends `risk=66 stab=47 coh=44`: escalation three points higher, stability one lower,
cohesion two lower than the clean baseline. Before the parser fixes this exact shape parsed to
nothing: the emphasised labels missed every `startswith` test, the annotated `+8` failed `int()`,
and the assessment fell back to `adequate` at multiplier 1.0 with placeholder text. Now the
labels, the bulleted annotated deltas and the explicit multiplier all land, and the movement is
damped by the 0.5 multiplier and the sixty-forty actor blend rather than discarded.

**(b) A worded refusal costs alliance cohesion instead of gaining it** (the ER-016 and ER-030
shape). Fixture, served three times, once per simulated capital's actor call:

```json
{"If you have redlines, enforce them.": "PUBLIC_RESPONSE: The United States cannot be party to this action and will say so publicly.\nPRIVATE_ASSESSMENT: London has overreached and must be walked back.\nTRUST_CHANGE: -8\nWILL_SUPPORT: absolutely not\nCONDITIONS: none\nINTEL_SHARED: none"}
```

Turn one ends `risk=74 stab=43 coh=18`: cohesion twenty-eight points below the clean baseline's
46 and twenty-two below its starting value of 40. Before the fix, "absolutely not" failed the
`"no" in content and "not" not in content` test, defaulted to `conditional`, and every refusing
capital contributed a small cohesion gain; the same reply with decorated labels also lost its
TRUST_CHANGE. Now the refusal registers as a refusal on all three actors and is priced
accordingly.

## Tuning

None needed, and here is what was checked rather than a bare assertion. The decision phase
measures at its three-round dependency floor (3.7 s at 1.2 s per call), so the round packing has
nothing left to give. The 53 per cent of wall clock with one call in flight decomposes exactly
into conversation turns and the inject-to-narrator data dependency, none of which a wider fan-out
can compress. The ledger's contribution to prompt growth is bounded and small: the deciding
prompts carrying it peak at 4,248 characters against advisory prompts over 35,000, and a
60-turn ledger costs under 11,000 characters against the 320,000-character history budget. No
metric showed drift attributable to a constant: the canonical campaign's escalation ratchet to
99 and defeat on turn 10 is the canned replies' fixed per-turn effects compounding, unchanged in
shape from the original runs. Every `MAX_*` bound and packing constant stands as merged.
