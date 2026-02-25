"""Configuration template for the wargame.

Copy this file to config.py and add your API keys.
config.py is in .gitignore so your keys stay private.
"""

# LLM Provider Selection
# Options: "mock", "gemini", "offline"
LLM_PROVIDER = "gemini"

# Google Gemini API Key
# Get your free key from: https://aistudio.google.com/apikey
GOOGLE_API_KEY = "YOUR_API_KEY_HERE"

# Gemini Model Selection
# Options: "gemini-2.5-flash" (fast), "gemini-2.5-pro" (best quality), "gemini-2.5-flash-lite" (fastest)
GEMINI_MODEL = "gemini-2.5-flash"

# Generation Settings
GEMINI_TEMPERATURE = 0.7  # 0.0 = deterministic, 1.0 = creative
GEMINI_MAX_TOKENS = 2048

# Rate Limiting
# Google Gemini Free Tier: 2 requests per minute (RPM)
# Google Gemini Paid Tier: 1000 requests per minute
# Set via environment variable: GEMINI_RPM=2
# The game enforces this automatically to prevent API errors.
# If you have a paid account, set GEMINI_RPM=1000 in your environment.

