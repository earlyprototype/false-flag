"""Configuration template for the wargame.

Copy this file to config.py and add your API keys.
config.py is in .gitignore so your keys stay private.

Provider overview and setup walkthroughs: docs/LLM_PROVIDERS.md
"""

# LLM Provider Selection
# Options: "mock" (default, offline), "openai_compat", "gemini", "offline"
#
# "openai_compat" speaks the standard OpenAI chat-completions protocol and
# works with OpenRouter, Groq, Cerebras, Mistral, Ollama, LM Studio, and any
# other OpenAI-style endpoint. Pick ONE of the preset blocks below.
LLM_PROVIDER = "mock"

# ---------------------------------------------------------------------------
# PRESET 1 (RECOMMENDED): OpenRouter + Gemini 2.5 Flash-Lite - 1M context
#
# Why this one, measured against this game's real workload (see
# docs/LLM_PROVIDERS.md for the full arithmetic):
#   - 1,048,576-token window on EVERY endpoint OpenRouter routes to, so a
#     whole campaign fits with room to spare. The largest single prompt in a
#     real 18-turn campaign is ~136K tokens when every call gets the full
#     transcript; a 128K model cannot hold one, which is why the transcript
#     windows in llm/context_builder.py exist.
#   - No reasoning tokens by default. Models that think by default return an
#     EMPTY completion when max_tokens is small - and this code passes
#     max_tokens=400 for adjudication and 150 for character responses. An
#     empty completion silently degrades to the mock advisor (llm/router.py),
#     which is invisible to the player. Avoid reasoning-by-default models
#     unless the driver is taught to send reasoning={"effort": "none"}.
#   - $0.10 per million input tokens, $0.40 per million output.
#     A 7-turn campaign costs ~$0.10; a 10-turn campaign ~$0.17.
#     Twenty testers playing one 10-turn campaign each: ~$3.40.
#
# Sign up at https://openrouter.ai/keys. For a key you are sharing with
# testers, set a per-key credit limit in the OpenRouter dashboard - that, not
# OPENAI_COMPAT_RPM, is what actually caps your exposure.
# ---------------------------------------------------------------------------
# LLM_PROVIDER = "openai_compat"
# OPENAI_COMPAT_BASE_URL = "https://openrouter.ai/api/v1"
# OPENAI_COMPAT_API_KEY = "PASTE-YOUR-OPENROUTER-KEY"  # keys begin sk-or-v1-
# OPENAI_COMPAT_MODEL = "google/gemini-2.5-flash-lite"
# OPENAI_COMPAT_RPM = 60  # a turn is ~17 sequential calls; 60 never throttles
#                         # normal play but caps a runaway loop

# ---------------------------------------------------------------------------
# PRESET 1b: cheapest 1M option - Qwen3.5 Flash (~40% less again)
# $0.065/M input, $0.26/M output. One provider (Alibaba) at a full 1,000,000
# tokens, no reasoning by default. Twenty testers x 10 turns: ~$2.20.
# Quality is unbenchmarked on OpenRouter - try it, keep PRESET 1 as the
# fallback if advisors start blurring into one voice.
# ---------------------------------------------------------------------------
# LLM_PROVIDER = "openai_compat"
# OPENAI_COMPAT_BASE_URL = "https://openrouter.ai/api/v1"
# OPENAI_COMPAT_API_KEY = "PASTE-YOUR-OPENROUTER-KEY"
# OPENAI_COMPAT_MODEL = "qwen/qwen3.5-flash-02-23"
# OPENAI_COMPAT_RPM = 60

# ---------------------------------------------------------------------------
# PRESET 1c: OpenRouter free models (hosted, $0) - NOT for the shared link
# ":free" models are capped at 20 requests/min and 50 requests/day (1,000/day
# after a one-time $10 credit purchase), counted globally per account. A turn
# is ~17 calls, so 50/day is THREE TURNS and 1,000/day is ~58 turns shared
# across every tester at once. Free endpoints also generally require the
# account-wide model-training/logging toggle to be on, meaning whatever
# testers type as Prime Minister may be retained and trained on.
# Fine for solo offline-ish dev; wrong for a passphrase-shared key.
# Browse: https://openrouter.ai/models?q=%3Afree
# ---------------------------------------------------------------------------
# LLM_PROVIDER = "openai_compat"
# OPENAI_COMPAT_BASE_URL = "https://openrouter.ai/api/v1"
# OPENAI_COMPAT_API_KEY = "PASTE-YOUR-OPENROUTER-KEY"
# OPENAI_COMPAT_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"
# OPENAI_COMPAT_RPM = 18  # stay just under OpenRouter's 20 req/min cap
# # NOTE: this model reasons at "high" effort by default and cannot be set
# # below "medium". Every call pays a thinking pass, and the max_tokens=150
# # and max_tokens=400 call sites will very likely come back empty and fall
# # through to the mock advisor without saying so. Do not use it as-is.

# ---------------------------------------------------------------------------
# PRESET 2: Groq free tier (hosted, $0, very fast)
# Sign up at https://console.groq.com/keys - free tier is ~30 requests/min,
# 1,000+ requests/day depending on model (no credit card required).
# ---------------------------------------------------------------------------
# LLM_PROVIDER = "openai_compat"
# OPENAI_COMPAT_BASE_URL = "https://api.groq.com/openai/v1"
# OPENAI_COMPAT_API_KEY = "PASTE-YOUR-GROQ-KEY"  # keys begin gsk_
# OPENAI_COMPAT_MODEL = "llama-3.3-70b-versatile"
# OPENAI_COMPAT_RPM = 28  # stay just under Groq's 30 req/min cap

# ---------------------------------------------------------------------------
# PRESET 3: Ollama running locally (offline, $0, private)
# Install from https://ollama.com then run:  ollama pull qwen3:8b
# No API key needed. LM Studio works the same way with
# OPENAI_COMPAT_BASE_URL = "http://localhost:1234/v1".
# ---------------------------------------------------------------------------
# LLM_PROVIDER = "openai_compat"
# OPENAI_COMPAT_BASE_URL = "http://localhost:11434/v1"
# OPENAI_COMPAT_MODEL = "qwen3:8b"
# # No OPENAI_COMPAT_RPM needed - local servers have no rate limits.

# Optional generation settings for openai_compat (defaults shown)
# OPENAI_COMPAT_TEMPERATURE = 0.7  # 0.0 = deterministic, 1.0 = creative
# OPENAI_COMPAT_MAX_TOKENS = 2048

# ---------------------------------------------------------------------------
# Google Gemini (legacy path - free tier now much more limited; the Pro
# models are paid-only as of April 2026. See docs/LLM_PROVIDERS.md.)
# ---------------------------------------------------------------------------
# LLM_PROVIDER = "gemini"
# GOOGLE_API_KEY = "YOUR_API_KEY_HERE"  # https://aistudio.google.com/apikey
# GEMINI_MODEL = "gemini-2.5-flash"  # or "gemini-2.5-flash-lite"
# GEMINI_TEMPERATURE = 0.7
# GEMINI_MAX_TOKENS = 2048
# Rate limiting: the game auto-throttles Gemini calls (GEMINI_RPM env var
# overrides; free tier Flash is ~5-10 RPM with a small daily cap).
