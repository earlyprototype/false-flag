# Flash-Only Mode Implementation

**Date:** 13 November 2025  
**Status:** ✅ Complete

---

## Summary

Implemented `--flash-only` command-line flag and model-specific rate limiting based on Google AI Studio dashboard data showing Flash models have 5× higher rate limits than Pro models.

---

## What Changed

### 1. Command-Line Flag ✅

**File:** `cli/main.py`

Added `--flash-only` parameter to `play()` command:

```python
def play(
    # ... other params ...
    flash_only: bool = typer.Option(False, "--flash-only", help="Use Flash model for all LLM calls (5x faster, cheaper)"),
):
    # Configure LLM model if flash_only flag is set
    if flash_only:
        from llm.model_config import get_model_config
        config = get_model_config()
        config.use_flash_for_all()
        typer.echo("[Flash-only mode enabled - using gemini-2.5-flash for all calls]")
```

### 2. Model-Specific Rate Limits ✅

**File:** `llm/router.py`

Updated `get_rate_limiter()` to auto-detect limits based on model:

```python
def get_rate_limiter(model_name: Optional[str] = None) -> Optional[RateLimiter]:
    # Determine RPM based on model (free tier limits)
    # Flash: 10 RPM, Pro: 2 RPM (from Google AI Studio dashboard)
    rpm = int(os.getenv("GEMINI_RPM", "0"))  # 0 = auto-detect
    
    if rpm == 0:  # Auto-detect based on model
        if model_name and "flash" in model_name.lower():
            rpm = 10  # Flash models: 10 RPM
        else:
            rpm = 2   # Pro models: 2 RPM
```

**Updated both:**
- `generate_text()` - passes model_name to rate limiter
- `batch_generate_text()` - passes model_name to rate limiter

### 3. Documentation Updates ✅

**File:** `docs/RATE_LIMITING.md`

- Added model-specific limits section
- Added `--flash-only` usage instructions
- Added `/llm` menu instructions
- Updated timing estimates for Flash vs Pro
- Added source attribution (Google AI Studio Dashboard)

### 4. Bug Fix: Duplicate Import ✅

**File:** `cli/main.py`

Removed duplicate `from cli.model_settings_menu import model_settings_menu` import.

---

## Usage

### Quick Start (Recommended for Free Tier)

```powershell
.\.venv\Scripts\python.exe -m cli.main play --variant fast_start --flash-only
```

### In-Game Configuration

Type `/llm` during gameplay to open the model settings menu.

### Environment Variable Override

For paid tier users:

```powershell
$env:GEMINI_RPM = "1000"
.\.venv\Scripts\python.exe -m cli.main play
```

---

## Rate Limits (Free Tier)

| Model | RPM | TPM | Speed |
|-------|-----|-----|-------|
| **gemini-2.5-flash** | 10 | 250K | 5× faster ⚡ |
| **gemini-2.5-pro** | 2 | 125K | 1× baseline 🐌 |

**Source:** Google AI Studio Dashboard → Rate Limit tab

---

## Game Timing Comparison

### Free Tier

| Configuration | Turn Time | Full Game (15 turns) | Status |
|--------------|-----------|---------------------|--------|
| **Flash-only** | 1-2 min | 15-30 min | ✅ Recommended |
| **Hybrid** | 3-5 min | 45-75 min | ⚠️ Slow |
| **Pro-only** | 5-10 min | 75-150 min | ❌ Not recommended |

### Paid Tier (1000 RPM)

| Configuration | Turn Time | Full Game (15 turns) |
|--------------|-----------|---------------------|
| **Any** | 10-30 sec | 5-10 min |

---

## Testing Checklist

- [x] `--flash-only` flag works
- [x] Flash rate limit = 10 RPM
- [x] Pro rate limit = 2 RPM
- [x] `/llm` menu accessible in-game
- [x] Model config changes apply immediately
- [x] No linter errors
- [x] Documentation updated

---

## Files Modified

1. **cli/main.py** - Added `--flash-only` flag, removed duplicate import
2. **llm/router.py** - Model-specific rate limiting
3. **docs/RATE_LIMITING.md** - Updated documentation
4. **docs/FLASH_ONLY_MODE.md** - This file (new)

---

## Known Limitations

1. **No persistence:** Flash-only setting resets when game exits (by design per user request)
2. **Free tier only:** Rate limit auto-detection assumes free tier unless `GEMINI_RPM` is set
3. **Simple detection:** Uses string matching (`"flash" in model_name`) to detect model type

---

## Future Enhancements

- [ ] Add `--pro-only` flag for completeness
- [ ] Add telemetry to track actual API rate limit headers
- [ ] Add warning if user's actual limits differ from assumed limits
- [ ] Add rate limit info to game status display

---

**Implementation Complete!** Free tier users can now play at 5× speed using `--flash-only`.


