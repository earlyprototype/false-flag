# Rate Limiting for LLM API Calls

**Date**: 12 November 2025  
**Status**: ✅ Implemented

---

## Overview

The game now includes automatic rate limiting to prevent exceeding Google Gemini API limits. This is **critical** for users on the free tier.

---

## Google Gemini API Limits

### Free Tier ⚠️ **Model-Specific Limits**
- **gemini-2.5-flash:** 10 requests per minute (RPM), 250K tokens/min (TPM)
- **gemini-2.5-pro:** 2 requests per minute (RPM), 125K tokens/min (TPM)
- **Daily limit:** 1,500 requests per day (RPD) for all models

**Important:** Flash models have 5× higher RPM limits than Pro models on free tier!

### Paid Tier (Pay-as-you-go)
- **All models:** 1,000 requests per minute (RPM)
- **4 million tokens per minute (TPM)**

**Source:** Google AI Studio Dashboard (Rate Limit tab)

---

## How It Works

### Automatic Rate Limiting

The game tracks all LLM API calls and automatically waits when necessary to stay within limits:

```python
# In llm/router.py
class RateLimiter:
    """Rate limiter for API calls."""
    
    def wait_if_needed(self, verbose: bool = True):
        """Wait if necessary to stay within rate limits."""
        # Tracks last N requests in a 60-second window
        # If limit reached, waits until oldest request expires
```

### User Experience

When the rate limit is approached, you'll see:

```
[Rate Limit] Waiting 45.3s to stay within 2 requests/min limit...
```

This is **normal** and prevents API errors!

---

## Configuration

### Default (Free Tier) - Auto-Detection ✨

The game now **automatically detects** which model you're using and applies the correct limit:
- **Flash models:** 10 RPM
- **Pro models:** 2 RPM

**No configuration needed!**

### Fast Mode: Flash-Only 🚀

Use the `--flash-only` flag to force all LLM calls to use Flash (5× faster):

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\python.exe -m cli.main play --variant fast_start --flash-only
```

**Benefits:**
- 5× higher rate limit (10 RPM vs 2 RPM)
- 90% cheaper per call
- 2-3× faster responses
- Can complete turn in ~1-2 minutes (vs 3-5 minutes with Pro)

### In-Game Menu

Type `/llm` during gameplay to:
- Switch all systems to Flash
- Configure hybrid Pro/Flash
- See current configuration

### Paid Tier Users

Set the `GEMINI_RPM` environment variable to override auto-detection:

**Windows (PowerShell):**
```powershell
$env:GEMINI_RPM = "1000"
.\.venv\Scripts\python.exe -m cli.main play
```

**Linux/Mac:**
```bash
export GEMINI_RPM=1000
python -m cli.main play
```

---

## Game Timing Impact

### Free Tier - Flash-Only (10 RPM) ⚡
With `--flash-only` (10-20 calls per turn):
- **Turn time**: 1-2 minutes per turn
- Minimal rate-limit waiting (10 RPM allows ~6 calls/min)
- **Full game (15 turns)**: 15-30 minutes
- **Recommended for free tier users**

### Free Tier - Hybrid (Mixed Pro/Flash)
With hybrid configuration (2-8 Pro calls + Flash calls per turn):
- **Turn time**: 3-5 minutes per turn
- Significant waiting due to Pro's 2 RPM limit
- **Full game (15 turns)**: 45-75 minutes

### Free Tier - Pro-Only (2 RPM) 🐌
With Pro-only (10-20 calls per turn):
- **Turn time**: 5-10 minutes per turn
- Extensive waiting between each call
- **Full game (15 turns)**: 75-150 minutes
- **Not recommended for free tier**

### Paid Tier (1000 RPM) 🚀
- **Turn time**: 10-30 seconds per turn
- No rate-limit waiting
- **Full game (15 turns)**: 5-10 minutes

---

## Model Configuration Impact

Use `/llm` command in-game or `python -m cli.main settings` to adjust:

### All Flash (Budget)
- **~5-7 calls per turn**
- Free tier: ~2-3 minutes per turn
- Cost: ~$0.10 per game

### Recommended Hybrid
- **~8-10 calls per turn**
- Free tier: ~3-5 minutes per turn
- Cost: ~$0.62 per game

### All Pro (Maximum Quality)
- **~8-10 calls per turn**
- Free tier: ~3-5 minutes per turn
- Cost: ~$1.00 per game

---

## Technical Details

### Rate Limiter Implementation

**File**: `llm/router.py`

**Features**:
- ✅ Sliding window tracking (60-second window)
- ✅ Automatic waiting with progress messages
- ✅ Per-provider configuration (only Gemini rate-limited)
- ✅ Thread-safe (uses global instance)
- ✅ Environment variable configuration

**Integration Points**:
- `generate_text()` - Single LLM call
- `batch_generate_text()` - Multiple sequential calls (with rate limiting between each)

### Disabling Rate Limiting

For testing or if using a different provider:

```python
# Set to a very high number
$env:GEMINI_RPM = "999999"
```

Or use mock/offline mode:
```python
# In config.py
LLM_PROVIDER = "mock"  # No rate limiting
```

---

## Troubleshooting

### "Rate Limit" messages appear even with paid tier

**Solution**: Set `GEMINI_RPM=1000` environment variable

### Game seems to hang

**Check**: Is a rate limit message displayed? This is normal waiting.

### Getting API errors anyway

**Possible causes**:
1. Daily limit (1,500 RPD) exceeded - check Google AI Studio
2. Token limit exceeded - reduce complexity or switch to Flash
3. API key issues - verify key is correct in `config.py`

---

## Future Enhancements

Potential improvements:
- [ ] Config file support (currently env var only)
- [ ] Token-based rate limiting (TPM tracking)
- [ ] Progress bar during rate limit waits
- [ ] Batch API support (single request for multiple prompts)
- [ ] Request queuing and priority system

---

**Questions?** Check `config.example.py` for configuration examples.

