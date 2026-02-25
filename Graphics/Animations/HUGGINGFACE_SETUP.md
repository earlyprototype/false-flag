# 🎉 Hugging Face Image Generation - FREE Solution!

**Status:** ✅ WORKING & TESTED  
**Cost:** FREE (no billing required)  
**Speed:** ~5-10 seconds per image

---

## Quick Start

Your Hugging Face token is already configured! Just run:

```bash
python Graphics/Animations/tools/generate_assets.py
```

This will generate all 32 pixel art assets automatically!

---

## What Changed

We switched from Google Gemini (requires paid tier) to **Hugging Face Inference API** (FREE!):

- ✅ **Model:** Stable Diffusion XL Base 1.0
- ✅ **Free tier:** Generous limits (10-15 requests/minute)
- ✅ **Cold start handling:** Automatic 20s wait if needed
- ✅ **All post-processing intact:** DB16 palette + exact dimensions

---

## Features

### Automatic Processing
1. Parses 32 assets from markdown files
2. Prepends universal LucasArts style prompt
3. Generates via Hugging Face API
4. Resizes to exact dimensions (nearest-neighbor)
5. Converts to DB16 palette
6. Saves to correct folders with correct filenames

### Progress Tracking
- Shows "Processing X/32"
- Displays size and path for each asset
- Retry logic (2 attempts per asset)
- Logs failures to `failed_assets.txt`

### Estimated Time
- **~32 images × 8 seconds = ~4-5 minutes total**
- Plus processing time (~2 seconds per image)
- **Total: ~8-10 minutes for all assets**

---

## Output Structure

```
assets/
├── backgrounds/        (2 assets - 320×180)
├── ui/                 (4 assets - various sizes)
├── ui/icons/          (2 assets - 16×16)
└── intro/
    ├── scene1_severomorsk/  (4 assets)
    ├── scene2_northwood/    (6 assets)
    ├── scene3_cobra/        (7 assets)
    └── ui/                  (4 assets)
```

---

## Troubleshooting

### Rate Limiting
If you hit rate limits:
- Free tier: ~10-15 requests/minute
- Script includes 1-second delays between requests
- If needed, increase delay in the script

### Cold Starts
First request to a model can take ~20 seconds:
- Script automatically waits
- Subsequent requests are faster
- This is normal for free tier

### Model Loading Errors (503)
If you get 503 errors:
- Model is "warming up"
- Script waits 20 seconds automatically
- Usually works on retry

---

## Alternative Models

If you want different styles, edit `generate_assets.py`:

### Pixel Art Specialized
```python
model = "nerijs/pixel-art-xl"  # Trained specifically for pixel art
```

### Faster (Lower Quality)
```python
model = "stabilityai/stable-diffusion-2-1"  # Faster generation
```

### Current (Best Quality)
```python
model = "stabilityai/stable-diffusion-xl-base-1.0"  # Default (best)
```

---

## Manual Token Setup (if needed)

If token isn't working:

1. Go to: https://huggingface.co/settings/tokens
2. Create free account
3. Click "New token"
4. Select "Read" access
5. Copy token
6. Add to `.env` file:
   ```
   HF_TOKEN=hf_your_token_here
   ```

---

## Comparison: Gemini vs Hugging Face

| Feature | Google Gemini | Hugging Face |
|---------|---------------|--------------|
| **Cost** | Paid tier required | FREE |
| **Quality** | High | High |
| **Speed** | ~5 sec/image | ~8 sec/image |
| **Free tier** | 0 quota for images | Generous limits |
| **Setup** | Complex (billing) | Simple (free token) |
| **Result** | ❌ Blocked | ✅ **WORKS!** |

---

## Next Steps

1. **Run the script:**
   ```bash
   python Graphics/Animations/tools/generate_assets.py
   ```

2. **Review generated images** in `assets/` directory

3. **Re-generate specific assets** if needed (edit prompt files)

4. **Integrate into game pipeline**

---

## Technical Details

### API Endpoint
```
https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0
```

### Request Format
```python
{
    "inputs": "your prompt here"
}
```

### Response
- Raw image bytes (PNG)
- Typical size: 1024×1024 (automatically resized by post-processor)

### Post-Processing
1. Resize to exact dimensions (e.g., 64×96, 16×16)
2. Convert to DB16 palette (16 specific colors)
3. Preserve transparency
4. Save as PNG

---

## Free Tier Limits

**Hugging Face Inference API:**
- ~10-15 requests per minute
- No daily limit on free tier
- Cold starts add ~20 seconds first time
- Unlimited usage for personal projects

**Our script handles:**
- ✅ Automatic rate limiting (1 sec delays)
- ✅ Cold start waits (20 sec)
- ✅ Retry logic (2 attempts)
- ✅ Error logging

---

**Ready to generate! Run the script and watch your pixel art come to life! 🎨**

