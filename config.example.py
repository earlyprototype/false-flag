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
# PRESET 1: OpenRouter free models (hosted, $0)
# Sign up at https://openrouter.ai/keys - free ":free" models are limited to
# ~20 requests/min and 50 requests/day (1,000/day after a one-time $10 credit
# purchase). Browse free models: https://openrouter.ai/models?q=%3Afree
# ---------------------------------------------------------------------------
# LLM_PROVIDER = "openai_compat"
# OPENAI_COMPAT_BASE_URL = "https://openrouter.ai/api/v1"
# OPENAI_COMPAT_API_KEY = "PASTE-YOUR-OPENROUTER-KEY"  # keys begin sk-or-v1-
# OPENAI_COMPAT_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
# OPENAI_COMPAT_RPM = 18  # stay just under OpenRouter's 20 req/min cap

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
