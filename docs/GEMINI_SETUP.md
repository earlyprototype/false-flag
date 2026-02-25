# Gemini LLM Integration Setup Guide

This guide shows you how to enable intelligent advisor responses using Google's Gemini 2.5 Flash.

## Quick Start

### 1. Install the Gemini SDK

```powershell
.\.venv\Scripts\pip.exe install google-generativeai
```

### 2. Get Your Free API Key

1. Visit [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (starts with `AIza...`)

### 3. Set Your API Key

**Option A: Environment Variable (Recommended)**

```powershell
# PowerShell (current session)
$env:GOOGLE_API_KEY = "AIza..."

# PowerShell (permanent - current user)
[System.Environment]::SetEnvironmentVariable('GOOGLE_API_KEY', 'AIza...', 'User')
```

**Option B: Create `.env` file**

Create a file called `.env` in the project root:

```
GOOGLE_API_KEY=AIza...
```

### 4. Enable Gemini in the Game

```powershell
# PowerShell (current session)
$env:WARGAME_LLM = "gemini"

# PowerShell (permanent - current user)
[System.Environment]::SetEnvironmentVariable('WARGAME_LLM', 'gemini', 'User')
```

### 5. Play with Real AI!

```powershell
.\.venv\Scripts\python.exe -m cli.main play
```

Now when you ask questions like:
- "CDS, what are our military options?"
- "NSA, what's Russia's likely next move?"
- "Foreign Secretary, will NATO support us?"

You'll get intelligent, context-aware responses from Gemini! 🎯

---

## Troubleshooting

### "google-generativeai package not installed"

```powershell
.\.venv\Scripts\pip.exe install google-generativeai
```

### "GOOGLE_API_KEY environment variable not set"

Make sure you've set the API key (see step 3 above).

To verify it's set:
```powershell
echo $env:GOOGLE_API_KEY
```

### "Failed to initialize Gemini driver"

The game will automatically fall back to mock mode. Check:
1. API key is valid
2. You have internet connection
3. SDK is installed in the correct venv

### Rate Limits

Gemini's free tier has generous limits:
- **15 requests per minute**
- **1 million tokens per minute**
- **1,500 requests per day**

This is more than enough for gameplay! If you hit limits, the game will show an error message but won't crash.

---

## Model Information

**Model Used:** `gemini-2.5-flash`

- **Context Window:** 1 million tokens
- **Speed:** Very fast (~1-2 seconds per response)
- **Cost:** FREE for API usage
- **Quality:** Excellent for conversational AI

---

## Switching Back to Mock Mode

```powershell
$env:WARGAME_LLM = "mock"
```

Or simply unset the variable:
```powershell
Remove-Item Env:\WARGAME_LLM
```

---

## Privacy & Security

- Your API key is stored locally (never committed to git)
- Prompts sent to Gemini include game context but no personal data
- Google's privacy policy applies: https://policies.google.com/privacy

---

## Advanced Configuration

### Use a Different Model

Edit `llm/gemini_driver.py` line 24:

```python
def __init__(self, model_name: str = "gemini-2.5-pro"):  # Higher quality, slower
```

Available models:
- `gemini-2.5-flash` (default, fast)
- `gemini-2.5-flash-lite` (faster, lighter)
- `gemini-2.5-pro` (highest quality, slower)

### Adjust Temperature

Edit `llm/gemini_driver.py` lines 52-56:

```python
self.generation_config = genai.GenerationConfig(
    temperature=0.9,  # Higher = more creative (0.0 - 1.0)
    top_p=0.95,
    top_k=40,
    max_output_tokens=2048,
)
```

---

**Ready to play? Set your API key and enjoy intelligent advisors!** 🚀

