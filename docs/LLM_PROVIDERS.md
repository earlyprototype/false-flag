# LLM Providers Guide

FALSE FLAG was originally built on Google Gemini's once-generous free tier.
That tier has been heavily cut back (Pro models are paid-only as of April
2026), so this guide covers every way to run the game's AI advisors today —
free hosted APIs, local models, and paid options — via the new
`openai_compat` provider, which speaks the standard OpenAI chat-completions
protocol and works with almost every LLM service in existence.

## State of free LLM access — August 2026

| Provider | Cost | Limits (free) | Setup effort | Quality for this game |
|---|---|---|---|---|
| **Mock mode** (built-in) | $0, offline | None | Zero — it's the default | Canned but in-character per-advisor lines; fine for dev/testing, not reactive |
| **Ollama / LM Studio** (local) | $0, offline | None (your hardware) | ~10 min, one download | Good with an 8–14B instruct model (Qwen3 8B/14B, Llama 3.1 8B); slower on CPU-only |
| **OpenRouter `:free` models** | $0 (optional one-time $10) | 20 req/min; **50 req/day** free, 1,000/day after a one-time $10 credit purchase — i.e. **3 turns/day**, or ~58 turns/day after the $10, *shared across all users of the key* | ~5 min, key signup | Mid-tier; free endpoints generally need the account-wide training/logging toggle on |
| **OpenRouter paid, 1M-context class** | ~$0.10/M input | Effectively none (credit-based); set a per-key credit limit | ~5 min, key signup + card | **Best fit** — see "What this game actually costs" below. A 10-turn campaign is ~$0.17 |
| **Groq** | $0 | ~30 req/min, ~6K tokens/min, ~1K–14.4K req/day per model | ~5 min, key signup, no card | Very good (Llama 3.3 70B) and extremely fast |
| **Cerebras** | $0 | 30 req/min, ~1M tokens/day, 8K context cap on free tier | ~5 min, key signup, no card | Good (Qwen3 32B, Llama 4 Scout); 8K context can pinch long transcripts |
| **Mistral La Plateforme** | $0 (Experiment plan) | Low RPM (~2/min community-reported); phone verification; **prompts may train their models** | ~10 min | Good (Mistral Small/Large) but slow under the RPM cap |
| **Google Gemini** | $0 (reduced) | Flash/Flash-Lite only: ~5–10 req/min, ~100–250 req/day; **Pro removed from free tier (Apr 2026)** | Already wired in | Flash is decent; the old Pro-quality free path is gone |
| **Anthropic Claude API** | Paid per token | Cheapest current model: Claude Haiku 4.5 at $1/M input, $5/M output | ~5 min, card required | Excellent; a ~50-request game session ≈ **$0.15–0.40** |

Sources: OpenRouter rows re-checked **4 Aug 2026** against the live
`https://openrouter.ai/api/v1/models` and `/models/{id}/endpoints` APIs plus
openrouter.ai/docs/api-reference/limits and /docs/features/prompt-caching.
Groq/Cerebras/Mistral rows last checked 2 Aug 2026 via third-party trackers
(pricepertoken.com, tokenmix.ai); Google AI Studio rate-limit reporting and the
Anthropic model catalog likewise. Free tiers change often — treat the numbers as
indicative and check the provider dashboard.

Note on Claude: there is currently no documented way to spend a Claude Code /
claude.ai *subscription* on arbitrary API calls like this game's — API usage is
billed per token to an API account. At Haiku 4.5 prices that's still pocket
change per session (roughly 75K input + 25K output tokens ≈ $0.20).

## What this game actually cost in the 4 Aug 2026 measurement

The tables below are dated measurements, not current provider quotes. Call
counts came from instrumented mock-mode campaigns. Token counts were built from
an 18-turn save that is no longer present in this tree, so the exact run is not
reproducible without restoring that fixture from history. Its transcript-size
evidence is preserved in
[`audits/2026-08-05-llm-context/README.md`](../audits/2026-08-05-llm-context/README.md)
and the full
[`SCHEMATIC.md`](../audits/2026-08-05-llm-context/SCHEMATIC.md). Treat the cost
figures as historical comparison data and remeasure before a purchasing call.

### A turn is ~17 LLM calls, and input dominates completely

| Call type | Calls per turn |
|---|---|
| Critical-omissions check (one per advisor) | 5.0 |
| Advisor Q&A (one per responding advisor, per question) | 2.0 |
| Adjudication: quality + character responses + situation summary | ~4.0 |
| State-actor simulation | ~3.0 |
| Decision interpretation | 1.0 |
| Advisor pushback | 1.0 |
| Narrator bridge | ~0.9 |
| Stochastic inject generation | 0.4–0.6 |
| **Total** | **~17.3** |

(The CLI re-runs interpretation + pushback + 5 omissions when the player
revises a decision, so a revised turn costs ~24 calls. The browser build calls
`resolve_decision` only and never doubles.)

| Campaign | Calls | Input tokens | Output tokens | Input share |
|---|---|---|---|---|
| 7 turns (`fast_start`), windowed | 126 | 910,112 | 24,360 | **97.4%** |
| 10 turns (`standard`), windowed | 180 | 1,558,184 | 34,800 | **97.8%** |
| 18 turns (long CLI game), windowed | 324 | 3,447,658 | 62,640 | **98.2%** |

**Input is ~98% of all tokens.** A model priced cheaply on output and dearly on
input is a trap here. Compare on the input price first; output price barely
moves the total.

### The context window you actually need

The binding constraint is the **largest single prompt**, not the per-turn sum.

| Mode | Largest single prompt, turn 18 | Minimum viable window |
|---|---|---|
| Windowed (today: 500/400/100-line slices) | ~45K tokens | 64K |
| Full transcript to every call | ~136K tokens | 200K+ |

So a 128K model genuinely cannot run a full-context 18-turn campaign — which
is exactly why `MAX_ADVISOR_TRANSCRIPT_LINES = 500` and
`MAX_INJECT_CONTINUITY_LINES = 400` exist in `llm/context_builder.py`. A 1M
window is not required at 18 turns, but at ~8.4K transcript tokens per turn it
buys roughly **120 turns** of headroom, i.e. you never think about it again.
Since 1M models now cost the same as 128K ones, take the 1M.

### Windowed vs full context, in money

| Campaign | Windowed input | Full-context input | Ratio |
|---|---|---|---|
| 7 turns | 910K | 1.53M | 1.7× |
| 10 turns | 1.56M | 3.21M | 2.1× |
| 18 turns | 3.45M | 10.87M | 3.2× |

Full context is **3.2× the tokens at 18 turns, not 15×** — because only five of
the ~17 call types embed the transcript at all. The adjudicator, character
responses, situation summary and actor simulation all run off
`NarrativeState.to_llm_context()`, a compact digest that never grows.

At current prices full context is **not** ruinous:

| Model (1M context) | $/M in | 7-turn | 10-turn | 18-turn | 20 testers × 10 turns |
|---|---|---|---|---|---|
| `google/gemini-2.5-flash-lite` | 0.10 | $0.16 | $0.34 | $1.11 | **$6.69** |
| `qwen/qwen3.5-flash-02-23` | 0.065 | $0.11 | $0.22 | $0.72 | $4.35 |
| `openai/gpt-5.6-luna` | 0.10 | $0.17 | $0.34 | $1.12 | $6.83 |
| `minimax/minimax-m3` | 0.30 | $0.49 | $1.00 | $3.34 | $20.08 |
| `anthropic/claude-sonnet-5` | 2.00 | $3.31 | $6.79 | $22.36 | $134 |

Windowed costs roughly half those figures (e.g. Flash-Lite: $0.10 / $0.17 /
$0.37, and **$3.39** for twenty 10-turn testers).

**The cheapest big win is not the model — it's the five critical-omissions
calls.** In full-context mode they alone are 630K of the 1.15M input tokens per
turn, because there are five of them and each would carry the whole
transcript. Leaving just those five windowed at 100 lines (a "hybrid" mode)
gives 4.60M input tokens per 18-turn campaign instead of 10.87M — 87% of the
continuity benefit for 42% of the token growth.

### Prompt caching does not help yet, and here is why

OpenRouter does expose caching (implicit for OpenAI, Gemini 2.5+, DeepSeek,
Groq, xAI, Moonshot, Z.AI; explicit `cache_control` breakpoints for Anthropic
and Qwen), with cache reads at 0.1×–0.5× of input price. On paper that would
cut a full-context campaign by ~70%.

It will not work against this codebase as written, for two reasons:

1. **The transcript is not a prefix.** `build_advisor_context` opens with
   role-specific text ("You are the {role}…", knowledge domains, key concerns)
   and only *then* embeds the transcript. Every advisor and every call type has
   a different prefix, so prefix-matching caches miss. Hoisting the shared
   transcript block to the very top of every prompt, with the role and
   instructions after it, is a prerequisite.
2. **TTLs are 3–30 minutes.** Within a turn (17 calls in a minute or two) a
   cache would hit; across turns, while the player is thinking, it will often
   have expired.

Worth doing later; do not price a model on the assumption it is already true.

### Choosing a model: what disqualifies one

- **Reasoning by default is the trap.** `assess_action_quality` passes
  `max_tokens=400`; character responses and the situation summary pass
  `max_tokens=150`. A model that thinks before answering can spend that entire
  budget on reasoning and return empty content. `OpenAICompatDriver` then
  raises, `llm/router.py` retries once and falls through to
  `MockDeterministicDriver` — which happily returns a well-formed
  `QUALITY: adequate / REASONING: …` block. The game keeps playing and *nothing
  visible goes wrong*, while the adjudicator has quietly stopped being an LLM.
  Prefer a model with reasoning off by default, or teach the driver to send
  `reasoning: {"effort": "none"}`.
- **Advertised windows are not served windows.** OpenRouter's model list shows
  the best window any provider offers; individual endpoints differ wildly.
  `deepseek/deepseek-v4-flash-0731` is listed at 1,048,576 but has providers at
  384K and 262K. `meta-llama/llama-4-scout` is listed at 1,310,720 but only
  Google serves it — Groq and Novita serve 131K. Check
  `/api/v1/models/{id}/endpoints` and pin the provider (`provider.order` +
  `allow_fallbacks: false`) before relying on a big window.
- **OpenRouter does not currently publish latency or throughput** through the
  endpoints API — `latency_last_30m` and `throughput_last_30m` are `null` for
  every endpoint checked. Latency below can only be reasoned about, not
  measured, so prefer the small/fast model classes and avoid reasoning passes:
  ~17 calls run **sequentially** and the browser player waits through all of
  them, so 3s/call is a 50-second turn and 15s/call is over four minutes.

### Verdict: NVIDIA Nemotron 3 Ultra (free)

`nvidia/nemotron-3-ultra-550b-a55b:free` — **not suitable as the primary
model; usable only as an offline-ish solo fallback.** It is the one free model
that genuinely serves a 1,000,000-token window (NVIDIA's own endpoint, 99.7%
uptime over the last day — note the *paid* variant maxes out at 512,288 via
Together, so the free one really does have the bigger window). But:

- **Rate limit kills it for a shared link.** 20 req/min and 50 req/day, or
  1,000/day after a one-time $10 credit purchase, counted globally per account.
  At ~17 calls/turn that is **three turns a day** free, or ~58 turns/day after
  the $10 — i.e. about **five 10-turn campaigns a day across all testers
  combined**, and 20 req/min means a single player's turn is throttled to ~51
  seconds of pure waiting before any inference time.
- **Reasoning cannot be turned down.** Its supported efforts are `high` and
  `medium` only, with `high` the default — there is no `none` and no `low`. So
  every one of the ~17 calls pays a thinking pass, and the `max_tokens=150` /
  `max_tokens=400` call sites will very likely return empty and fall through to
  the mock advisor silently (see above). This alone disqualifies it as-is.
- **Data policy.** The NVIDIA endpoint logs usage for security and product
  improvement, and OpenRouter will not route to logging providers unless the
  account-wide model-training toggle is enabled. Everything testers type as
  Prime Minister may be retained and trained on.
- **Quality is mid-tier anyway**: Artificial Analysis intelligence index 37.8,
  against 51.2 for `openai/gpt-5.6-luna` and 49.9 for
  `deepseek/deepseek-v4-flash-0731` — both of which cost about $0.10/M input.

The paid variant (`nvidia/nemotron-3-ultra-550b-a55b`, $0.60/$3.60) is 6× the
input price of Flash-Lite for a lower benchmark score and a smaller real
window. It is not worth it for this game.

## Recommended setups

### For building and testing: mock mode (the default)

Do nothing. With no `config.py` and no environment variables, the game runs in
**mock** mode: fully offline, deterministic, and — since the recent voices
update — each advisor answers with their own persona (the CDS talks force
posture, the Attorney General talks legality, etc.). It won't reason about your
specific decision, but it exercises the entire turn loop, which is what you
want for development and CI.

### For actually playing: OpenRouter + Gemini 2.5 Flash-Lite (paid, pennies)

**Top pick: `google/gemini-2.5-flash-lite` via OpenRouter.** It is the only
candidate that satisfies all four constraints at once — 1M context, fast, cheap,
and drop-in with the driver exactly as it is today:

- 1,048,576 tokens on **every** endpoint OpenRouter routes to (Google and
  Google AI Studio only), so there is no provider to pin and no chance of
  silently landing on a 128K route.
- No reasoning tokens by default, so the `max_tokens=150`/`400` call sites
  behave and nothing degrades to the mock advisor unnoticed.
- $0.10/M input, $0.40/M output. A 7-turn campaign is ~$0.10 windowed,
  ~$0.16 with the full transcript. **Twenty testers, one 10-turn campaign
  each: $3.39 windowed, $6.69 full-context.**
- Flash-Lite class is the latency tier this game needs — ~17 calls run
  sequentially and the browser player waits through every one.

1. Create a key at <https://openrouter.ai/keys>.
2. **Set a per-key credit limit in the OpenRouter dashboard.** For a key shared
   with testers behind a passphrase, that limit is what actually caps your
   exposure — `OPENAI_COMPAT_RPM` throttles one browser session, not the link.
3. Copy `config.example.py` to `config.py` and uncomment PRESET 1.

**Cheaper alternate:** `qwen/qwen3.5-flash-02-23` at $0.065/$0.26, also 1M
(single Alibaba endpoint, 100% uptime last 24h) and also reasoning-free —
about 35% less again, but unbenchmarked, so watch for advisors blurring into
one voice.

**Smarter alternate, needs one driver line:** `openai/gpt-5.6-luna` scores 51.2
on Artificial Analysis' intelligence index versus 37.8 for Nemotron 3 Ultra,
for the same $0.10/M input and a 1,050,000-token window. It reasons by
default, but it is one of the few models that accepts
`reasoning: {"effort": "none"}` — add that to the payload in
`llm/openai_compat_driver.py` and it becomes the best value on the board.
One caveat specific to this game: OpenRouter flags it `is_moderated: true`,
so a NATO-escalation scenario with strikes and casualties may occasionally
trip a content filter. `google/gemini-2.5-flash-lite` and
`qwen/qwen3.5-flash-02-23` are both unmoderated.

**Not recommended for the shared link:** OpenRouter `:free` models. 20 req/min
and 50 req/day (1,000/day after a one-time $10 credit purchase), counted
globally per account — at ~17 calls per turn that is three turns a day, or
about five 10-turn campaigns a day shared across every tester after the $10.
Free endpoints also generally require the account-wide model-training toggle,
so testers' prompts may be retained and trained on.

**Groq** remains a good no-card option for solo local play — ~30 req/min and
1,000+ req/day, extremely fast — but its models top out well below 1M context,
so a long campaign will still be running on windowed slices.

If an API call fails mid-game (rate limit, network), the game retries once and
then quietly answers that one prompt from the mock advisor pool — it never
crashes the session. That is deliberate resilience, but note it is *silent*:
if you pick a model that returns empty completions, the game will look fine
and quietly stop using the model.

### For unlimited private play: Ollama (local)

Runs entirely on your machine. No keys, no quotas, works offline.

1. Install Ollama for Windows from <https://ollama.com/download> and launch it
   (it serves an OpenAI-compatible API on `http://localhost:11434/v1`).

   > **Important:** set the environment variable `OLLAMA_CONTEXT_LENGTH=8192`
   > before starting the server. Ollama's default context window is 4,096
   > tokens and this game's adjudication prompts measurably exceed 3,500 —
   > past the ceiling, Ollama silently truncates the prompt and the advisors
   > start reasoning from an incomplete briefing with no visible error.
   > If calls run long on modest hardware, also raise the request timeout:
   > `OPENAI_COMPAT_TIMEOUT=300` (seconds; default 60).

   **Bigger brains than your RAM:** MoE models activate only a few billion
   parameters per token, and [BigMoeOnEdge](https://github.com/Helldez/BigMoeOnEdge)
   streams the routed experts from disk so the model no longer has to fit in
   memory. Measured on a 4-core, 15 GB, GPU-less VM with this game's actual
   prompts: Qwen3-30B-A3B (18.5 GB — un-loadable in plain Ollama on that box)
   ran at 3.4–5.4 tok/s generation with a 3,495-token briefing prefilling at
   18.4 tok/s (~3 min). Roughly double the per-call latency of a dense 3B, for
   a different class of advisor. Its `bmoe-cli` is a CLI rather than an
   OpenAI-compatible server, so wiring it to the game needs a small shim
   around its `--session` JSON mode; worthwhile only where quality outranks
   turn speed.
2. Pull a model. The game's prompts are modest, so an 8–14B instruct model is
   plenty:

   ```powershell
   ollama pull qwen3:8b        # best all-rounder at 8B, ~5 GB, runs on 8 GB VRAM
   # or, if you have 12-16 GB VRAM:
   ollama pull qwen3:14b       # noticeably better advisor prose
   # or a smaller fallback for older machines:
   ollama pull llama3.1:8b
   ```

3. In `config.py`:

   ```python
   LLM_PROVIDER = "openai_compat"
   OPENAI_COMPAT_BASE_URL = "http://localhost:11434/v1"
   OPENAI_COMPAT_MODEL = "qwen3:8b"
   # No API key, no OPENAI_COMPAT_RPM needed.
   ```

4. Play as usual. First response after startup is slower (model load); after
   that expect a few seconds per advisor reply on a mid-range GPU, longer on
   CPU-only machines (where a 3–4B model such as `qwen3:4b` is a better fit).

**LM Studio** works identically — start its local server and use
`OPENAI_COMPAT_BASE_URL = "http://localhost:1234/v1"` with the model name shown
in the LM Studio UI.

### If you'd rather just pay a little: Claude Haiku or Gemini paid tier

Claude Haiku 4.5 (via any OpenAI-compat proxy you may run, or a future native
driver) and paid Gemini Flash both cost well under $0.50 per full game
session. The Gemini path still works exactly as before — see
[GEMINI_SETUP.md](GEMINI_SETUP.md) — just with billing enabled.

## Configuration reference

All settings can be set in `config.py` or as environment variables
(environment wins):

| Setting | Meaning | Default |
|---|---|---|
| `LLM_PROVIDER` / `WARGAME_LLM` env | `mock`, `openai_compat`, `gemini`, `offline` | `mock` |
| `OPENAI_COMPAT_BASE_URL` | API root, e.g. `https://openrouter.ai/api/v1` | required |
| `OPENAI_COMPAT_MODEL` | Model id, e.g. `qwen3:8b` | required |
| `OPENAI_COMPAT_API_KEY` | Bearer token (omit for local servers) | none |
| `OPENAI_COMPAT_RPM` | Client-side requests/min throttle; 0 = off | 0 |
| `OPENAI_COMPAT_TEMPERATURE` | Sampling temperature | 0.7 |
| `OPENAI_COMPAT_MAX_TOKENS` | Max completion tokens | 2048 |

Notes:

- The in-game Flash/Pro model-tier menu (`LLM Model Settings`) only affects the
  Gemini provider; `openai_compat` always uses `OPENAI_COMPAT_MODEL`.
- Rate limiting: set `OPENAI_COMPAT_RPM` just below your provider's cap and
  the game will pace itself instead of burning requests into 429 errors.
- Resilience: any provider error falls back per-call to the mock advisors
  after one retry, so a flaky connection degrades gracefully instead of
  crashing the game.
