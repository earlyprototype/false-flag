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
| **OpenRouter `:free` models** | $0 (optional one-time $10) | 20 req/min; **50 req/day** free, 1,000/day after a one-time $10 credit purchase | ~5 min, key signup | Very good — free variants of 70B-class models (e.g. Llama 3.3 70B) |
| **Groq** | $0 | ~30 req/min, ~6K tokens/min, ~1K–14.4K req/day per model | ~5 min, key signup, no card | Very good (Llama 3.3 70B) and extremely fast |
| **Cerebras** | $0 | 30 req/min, ~1M tokens/day, 8K context cap on free tier | ~5 min, key signup, no card | Good (Qwen3 32B, Llama 4 Scout); 8K context can pinch long transcripts |
| **Mistral La Plateforme** | $0 (Experiment plan) | Low RPM (~2/min community-reported); phone verification; **prompts may train their models** | ~10 min | Good (Mistral Small/Large) but slow under the RPM cap |
| **Google Gemini** | $0 (reduced) | Flash/Flash-Lite only: ~5–10 req/min, ~100–250 req/day; **Pro removed from free tier (Apr 2026)** | Already wired in | Flash is decent; the old Pro-quality free path is gone |
| **Anthropic Claude API** | Paid per token | Cheapest current model: Claude Haiku 4.5 at $1/M input, $5/M output | ~5 min, card required | Excellent; a ~50-request game session ≈ **$0.15–0.40** |

Sources checked 2 Aug 2026: OpenRouter docs (openrouter.ai/docs/api-reference/limits),
Groq/Cerebras/Mistral pricing & rate-limit pages via current third-party trackers
(pricepertoken.com, tokenmix.ai), Google AI Studio rate-limit reporting, and the
Anthropic model catalog. Free tiers change often — treat the numbers as indicative
and check the provider dashboard.

Note on Claude: there is currently no documented way to spend a Claude Code /
claude.ai *subscription* on arbitrary API calls like this game's — API usage is
billed per token to an API account. At Haiku 4.5 prices that's still pocket
change per session (roughly 75K input + 25K output tokens ≈ $0.20).

## Recommended setups

### For building and testing: mock mode (the default)

Do nothing. With no `config.py` and no environment variables, the game runs in
**mock** mode: fully offline, deterministic, and — since the recent voices
update — each advisor answers with their own persona (the CDS talks force
posture, the Attorney General talks legality, etc.). It won't reason about your
specific decision, but it exercises the entire turn loop, which is what you
want for development and CI.

### For actually playing: Groq or OpenRouter (free, hosted)

**Top pick: Groq.** No credit card, ~1,000+ requests/day free (a full game
uses well under 100), fast enough that advisors answer near-instantly, and the
free Llama 3.3 70B is genuinely good at in-character strategic advice.

1. Create a key at <https://console.groq.com/keys> (Google/GitHub login, no card).
2. Copy `config.example.py` to `config.py` and uncomment the Groq preset:

   ```python
   LLM_PROVIDER = "openai_compat"
   OPENAI_COMPAT_BASE_URL = "https://api.groq.com/openai/v1"
   OPENAI_COMPAT_API_KEY = "gsk_..."      # your key
   OPENAI_COMPAT_MODEL = "llama-3.3-70b-versatile"
   OPENAI_COMPAT_RPM = 28
   ```

3. Play:

   ```powershell
   .\.venv\Scripts\python.exe -m cli.main play
   ```

**Runner-up: OpenRouter.** One key unlocks dozens of `:free` models
(`https://openrouter.ai/models?q=%3Afree`). The catch: 50 requests/day on a
pure-free account, which one long session can exhaust. A one-time $10 credit
purchase (never expires, you don't have to spend it) raises that to 1,000/day
permanently — the best "almost free" deal going. Use the OpenRouter preset in
`config.example.py`.

If an API call fails mid-game (rate limit, network), the game retries once and
then quietly answers that one prompt from the mock advisor pool — it never
crashes the session.

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
