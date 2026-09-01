# Gemini Provider Setup

Use this guide only when Google Gemini is the selected LLM provider. Model
availability, quotas and pricing change; check
[Google AI Studio](https://aistudio.google.com/apikey) and Google's current
account dashboard rather than relying on fixed limits in repository docs.
Other supported routes are in [LLM_PROVIDERS.md](LLM_PROVIDERS.md).

## Setup

1. Install the Gemini SDK in the project environment:

   ```powershell
   .\.venv\Scripts\pip.exe install google-generativeai
   ```

2. Create an API key in [Google AI Studio](https://aistudio.google.com/apikey).
   A key does not guarantee a free quota for the selected model.

3. Set the key and provider in the shell that launches the game:

   ```powershell
   $env:GOOGLE_API_KEY = "AIza..."
   $env:WARGAME_LLM = "gemini"
   .\.venv\Scripts\python.exe -m cli.main play
   ```

The playable application does not load a project-root `.env` file. Use a real
environment variable or the existing `config.py` fallback; never commit a key.

## Verify or recover

- Confirm the key is present with `Test-Path Env:GOOGLE_API_KEY`. Do not print
  the secret into logs or screenshots.
- If driver initialisation or a request fails, the router warns and falls back
  to deterministic mock output. Treat that warning as a degraded run, not a
  successful live-AI test.
- Use the in-game `/llm` menu for supported provider/model choices.
- Set `GEMINI_RPM` only from the current quota shown for your own account; do
  not copy old repository estimates.

To return deliberately to deterministic play:

```powershell
$env:WARGAME_LLM = "mock"
```

Google's [privacy policy](https://policies.google.com/privacy) applies to
prompts sent through Gemini.
