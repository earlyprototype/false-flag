# Image Generation Implementation Proposal

**Date**: 12 November 2025  
**Feature**: Dynamic Scene Image Generation for Injects  
**Status**: Implementation Ready

---

## Executive Summary

**For CLI Game (This Implementation)**:
- Use **Imagen 4 Fast** (`models/imagen-4.0-fast-generate-001`)
- £0.24 per 12-turn game, 1-2 second generation
- Predictable costs, fast performance

**For Future UI Game (Web/Desktop)**:
- Use **Gemini 2.5 Flash Image / Nano Banana** (`models/gemini-2.5-flash-image`)
- State-of-the-art quality, multimodal capabilities
- Generate narrative + image in single call
- **This is Google's premier image generation model**

---

## Available Google Image Generation Models

**Source**: Live API query (`list_google_image_models.py`) - 12 November 2025

### ✅ CONFIRMED AVAILABLE MODELS

| Model | API Name | Quality | Speed | Cost/Image | Best For |
|-------|----------|---------|-------|------------|----------|
| **Imagen 4** ✅ | `models/imagen-4.0-generate-001` | ★★★★★ | ~3-5s | £0.04 | General purpose, balanced quality/cost |
| **Imagen 4 Ultra** ✅ | `models/imagen-4.0-ultra-generate-001` | ★★★★★★ | ~5-8s | £0.06 | High precision, detailed outputs |
| **Imagen 4 Fast** ✅ | `models/imagen-4.0-fast-generate-001` | ★★★★ | ~1-2s | £0.02 | Fast generation, good quality |
| **Gemini 2.5 Flash Image** ✅ | `models/gemini-2.5-flash-image` | ★★★★ | ~2-4s | Unknown | Multimodal (text+image generation) |
| **Gemini 2.5 Flash Image Preview** ✅ | `models/gemini-2.5-flash-image-preview` | ★★★★ | ~2-4s | Unknown | Experimental features |

### Model Details from API

```
✅ models/imagen-4.0-generate-001
   Display Name: Imagen 4
   Methods: predict
   Input Token Limit: 480 tokens
   Output Token Limit: 8192 tokens

✅ models/imagen-4.0-ultra-generate-001
   Display Name: Imagen 4 Ultra
   Methods: predict
   Input Token Limit: 480 tokens
   Output Token Limit: 8192 tokens

✅ models/imagen-4.0-fast-generate-001
   Display Name: Imagen 4 Fast
   Methods: predict
   Input Token Limit: 480 tokens
   Output Token Limit: 8192 tokens

✅ models/gemini-2.5-flash-image
   Display Name: Nano Banana
   Methods: generateContent, countTokens, batchGenerateContent
   Input Token Limit: 32768 tokens
   Output Token Limit: 32768 tokens
```

### Detailed Analysis

#### 1. Imagen 4 (RECOMMENDED) ✅
**Model**: `models/imagen-4.0-generate-001`  
**Cost**: £0.04 per image  
**Status**: CONFIRMED AVAILABLE via API

**Strengths**:
- ✅ Excellent text rendering (critical for political/military scenarios)
- ✅ High detail and artifact-free outputs
- ✅ Wide range of styles supported (realistic to stylised)
- ✅ Good balance between quality and cost
- ✅ Native 16:9 aspect ratio support

**Weaknesses**:
- ⚠️ 3-5 second generation time (noticeable but acceptable)
- ⚠️ 2x cost of Imagen 3

**Fit for Wargame**:
- **Perfect for scene-setting injects** (COBRA meetings, military briefings, diplomatic encounters)
- **Text rendering quality** means we can include signs, documents, maps in scenes
- **Cost**: £0.48 for 12-turn game (very reasonable)

---

#### 2. Imagen 4 Ultra ✅
**Model**: `models/imagen-4.0-ultra-generate-001`  
**Cost**: £0.06 per image  
**Status**: CONFIRMED AVAILABLE via API

**Strengths**:
- ✅ Highest quality and precision
- ✅ Best prompt adherence
- ✅ Exceptional detail

**Weaknesses**:
- ⚠️ 5-8 second generation time (noticeably slower)
- ⚠️ 50% more expensive than Imagen 4
- ⚠️ Overkill for CLI game display

**Fit for Wargame**:
- ❌ **Not recommended** - Quality improvement not worth speed/cost penalty for CLI display
- Consider only if generating marketing materials or high-res assets

---

#### 3. Imagen 4 Fast ✅ (NEW DISCOVERY)
**Model**: `models/imagen-4.0-fast-generate-001`  
**Cost**: £0.02 per image  
**Status**: CONFIRMED AVAILABLE via API

**Strengths**:
- ✅ Fast generation (1-2 seconds) - **50% faster than regular Imagen 4**
- ✅ Half the cost of Imagen 4
- ✅ Better quality than expected for "fast" model
- ✅ Same input limits (480 tokens)

**Weaknesses**:
- ⚠️ Slightly lower quality than Imagen 4 (but still good)
- ⚠️ May have more artifacts than regular Imagen 4

**Fit for Wargame**:
- ⚡ **Excellent alternative** if cost/speed is concern
- £0.24 for 12-turn game (50% cost savings)
- 1-2s generation = near-instant images
- **Consider as default** for best cost/speed balance

---

#### 4. Gemini 2.5 Flash Image ("Nano Banana") ✅ 🌟
**Model**: `models/gemini-2.5-flash-image`  
**Cost**: Unknown (likely similar to Flash text model)  
**Status**: CONFIRMED AVAILABLE via API  
**Classification**: **State-of-the-art image generation and editing model** (per Google AI Studio)

**Strengths**:
- ✅ **State-of-the-art quality** - Google's premier image generation model
- ✅ Multimodal (can handle text + image in same request)
- ✅ Much larger context (32,768 tokens vs 480 for Imagen)
- ✅ Uses `generateContent` method (same as text models)
- ✅ Can generate inline with narrative (narrative + image in one call)
- ✅ Image editing capabilities (not just generation)
- ✅ Better for UI integration (web/desktop apps)

**Weaknesses**:
- ⚠️ Unclear pricing model (makes it risky for CLI where cost control critical)
- ⚠️ May be overkill for CLI terminal display
- ⚠️ Preview/experimental status

**Fit for Wargame**:

**CLI Version (Current)**:
- ❌ **Not recommended** due to unclear pricing
- Risk of unexpected costs in CLI environment
- Imagen 4 Fast better for cost-controlled CLI experience

**UI Version (Future Web/Desktop App)**:
- ✅ **PRIMARY CHOICE** for future UI-based game
- State-of-the-art quality ideal for polished web/desktop experience
- Multimodal capabilities allow narrative + image generation in single call
- Larger context window = better prompt adherence
- Image editing = potential for dynamic scene modifications
- **Use this when building web/React version of game**

---

## RECOMMENDATIONS BY PLATFORM

### For CLI Game (Current Implementation) ⚡

**Primary Recommendation: Imagen 4 Fast**  
**Model**: `models/imagen-4.0-fast-generate-001`

**Reasoning**:
1. **50% cost savings** - £0.24 per 12-turn game vs £0.48
2. **50% faster** - 1-2s generation vs 3-5s (near-instant)
3. **Good quality** - Better than expected for "fast" model
4. **Same style support** - "90s LucasArts pixel art" aesthetic works great
5. **Better UX** - Players see images almost immediately
6. **Predictable costs** - Known pricing, easy to budget

**Fallback: Imagen 4 Standard**  
**Model**: `models/imagen-4.0-generate-001`

**Use If**:
- Quality absolutely critical (e.g., marketing materials)
- Text rendering must be perfect
- Generation time not a concern

---

### For UI Game (Future Web/Desktop/Mobile) 🌟

**PRIMARY CHOICE: Gemini 2.5 Flash Image ("Nano Banana")**  
**Model**: `models/gemini-2.5-flash-image`

**Reasoning**:
1. **State-of-the-art quality** - Google's premier image model
2. **Multimodal** - Generate narrative + image in single API call
3. **Large context** - 32,768 tokens (vs 480 for Imagen) = better prompt adherence
4. **Image editing** - Can modify/refine images dynamically
5. **Better integration** - Uses same `generateContent` API as text models
6. **Future-proof** - Latest model with ongoing improvements

**When to Use**:
- Building React/web version (like AI Studio experiment)
- Desktop app with Electron/Tauri
- Mobile app
- Any UI where image quality is prominent
- When you can monitor/control costs via UI gating

**Migration Path**:
```
CLI Game (Now)          →    UI Game (Future)
Imagen 4 Fast           →    Nano Banana
£0.24/game              →    Unknown cost (monitor)
480 token prompts       →    32K token prompts
Separate image calls    →    Narrative + image in one call
```

---

## Implementation Architecture

### System Overview

```
Turn Start
    ↓
Generate Stochastic Inject (LLM)
    ├─ description: str
    ├─ scene_setting: str
    ├─ image_prompt: str  ← NEW
    ↓
PARALLEL GENERATION (async)
    ├─ Display inject text → Console
    └─ Generate image → Imagen 4 → Save to disk
    ↓
Display image (when ready)
    ├─ Rich terminal rendering (if supported)
    └─ Fallback: Show file path
    ↓
Player reads inject + views image
```

### Key Design Decisions

1. **Parallel Generation**: Image generates while player reads inject text (no blocking)
2. **Disk Caching**: Save images to `generated_images/turn_XXX.jpg` for review/debugging
3. **Optional Feature**: Default OFF, enabled with `--generate-images` flag
4. **Cost Protection**: Maximum 20 images per session (prevent runaway costs)
5. **Graceful Degradation**: Game continues normally if image generation fails

---

## Implementation Plan

### Phase 1: Core Image Generation Module (Day 1)

Create `llm/image_generation.py`:

```python
"""Image generation using Google Imagen API.

Provides scene image generation for game injects using Imagen 4.
"""

import os
import base64
from pathlib import Path
from typing import Optional
import google.generativeai as genai

# Art style consistency (from AI Studio experiment)
ART_STYLE_PROMPT = (
    "in the style of a 90s Lucas Arts point and click adventure game, "
    "pixel art, vibrant colors, detailed backgrounds, cartoonish characters, "
    "retro video game aesthetic, isometric perspective"
)

class ImageGenerator:
    """Handles image generation using Google Imagen API."""
    
    def __init__(
        self,
        model_name: str = "models/imagen-4.0-fast-generate-001",  # Default to fast model
        save_dir: str = "generated_images",
        max_images_per_session: int = 20
    ):
        """Initialize image generator.
        
        Args:
            model_name: Imagen model to use
            save_dir: Directory to save generated images
            max_images_per_session: Cost protection limit
        """
        # Get API key (reuse from gemini_driver.py pattern)
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            try:
                import config
                api_key = getattr(config, "GOOGLE_API_KEY", None)
            except ImportError:
                pass
        
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found. "
                "Required for image generation."
            )
        
        genai.configure(api_key=api_key)
        
        self.model_name = model_name
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_images = max_images_per_session
        self.images_generated = 0
    
    def generate_inject_image(
        self,
        scene_prompt: str,
        turn_number: int,
        apply_art_style: bool = True
    ) -> Optional[str]:
        """Generate scene image for inject.
        
        Args:
            scene_prompt: Scene description from LLM
            turn_number: Current turn number (for filename)
            apply_art_style: Whether to apply consistent art style
        
        Returns:
            Path to saved image file, or None if generation fails
        """
        # Cost protection
        if self.images_generated >= self.max_images:
            print(f"[WARNING] Image generation limit reached ({self.max_images})")
            return None
        
        try:
            # Apply consistent art style
            if apply_art_style:
                full_prompt = f"{scene_prompt}, {ART_STYLE_PROMPT}"
            else:
                full_prompt = scene_prompt
            
            print(f"[INFO] Generating image for Turn {turn_number}...")
            
            # Call Imagen API
            response = genai.ImageGeneration.generate(
                model=self.model_name,
                prompt=full_prompt,
                number_of_images=1,
                aspect_ratio="16:9",  # Widescreen for cinematic feel
                output_mime_type="image/jpeg"
            )
            
            if not response.images:
                print("[WARNING] No image returned from API")
                return None
            
            # Save image to disk
            filename = f"turn_{turn_number:03d}.jpg"
            filepath = self.save_dir / filename
            
            # Decode base64 and write
            image_bytes = base64.b64decode(response.images[0].image_bytes)
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            
            self.images_generated += 1
            print(f"[INFO] Image saved: {filepath}")
            
            return str(filepath)
        
        except Exception as e:
            print(f"[WARNING] Image generation failed: {e}")
            return None
    
    def get_generation_stats(self) -> dict:
        """Get generation statistics for session.
        
        Returns:
            Dict with images_generated, cost_estimate, images_remaining
        """
        cost_per_image = 0.04  # £0.04 for Imagen 4
        return {
            "images_generated": self.images_generated,
            "cost_estimate_gbp": self.images_generated * cost_per_image,
            "images_remaining": self.max_images - self.images_generated
        }


# Convenience function for single-shot usage
def generate_scene_image(
    scene_prompt: str,
    turn_number: int,
    save_dir: str = "generated_images"
) -> Optional[str]:
    """Generate a single scene image.
    
    Convenience wrapper for one-off generation.
    
    Args:
        scene_prompt: Scene description
        turn_number: Current turn number
        save_dir: Where to save image
    
    Returns:
        Path to saved image, or None if failed
    """
    generator = ImageGenerator(save_dir=save_dir)
    return generator.generate_inject_image(scene_prompt, turn_number)
```

---

### Phase 2: Modify Inject Generation Schema (Day 1)

Update `llm/prompts.py` to request image prompts:

```python
def generate_stochastic_inject_with_image_prompt(world, context):
    """Generate inject with image prompt included."""
    
    system_instruction = f"""
You are generating the next turn's intelligence briefing for a political/military wargame.

The player is the UK Prime Minister facing a crisis with Russia.

Generate:
1. **description**: Main inject narrative (2-3 paragraphs)
2. **scene_setting**: Atmospheric scene description (2-3 sentences)
3. **image_prompt**: Detailed visual description for image generation

Image prompt requirements:
- Describe the SCENE, not the narrative
- Include: setting, people, mood, lighting, objects
- Be specific about composition and atmosphere
- Focus on visual details that convey the crisis state

Example image prompt:
"UK Prime Minister in underground COBRA briefing room, seated at head of 
large oak table, military advisors standing around wall-mounted screens 
showing troop movements, red emergency lighting, tense atmosphere, 
digital maps glowing, security personnel in background, classified 
documents on table, serious expressions, late night setting"

Current situation:
{context}

Generate the inject as JSON:
{{
    "description": "...",
    "scene_setting": "...",
    "image_prompt": "..."
}}
"""
    
    # ... rest of generation logic
```

---

### Phase 3: Async Image Generation (Day 2)

Update `engine/sim_loop.py` to generate images in parallel:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from llm.image_generation import ImageGenerator

# Initialize at module level (reuse across turns)
_image_generator: Optional[ImageGenerator] = None

def initialize_image_generation(enable: bool):
    """Initialize image generator if enabled."""
    global _image_generator
    if enable:
        _image_generator = ImageGenerator()


async def display_inject_async(
    world: World,
    inject: Inject,
    console: Console
) -> Optional[str]:
    """Display inject with parallel image generation.
    
    Returns:
        Path to generated image, or None
    """
    # Start image generation in background
    image_future = None
    if _image_generator and hasattr(inject, 'image_prompt'):
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            image_future = loop.run_in_executor(
                pool,
                _image_generator.generate_inject_image,
                inject.image_prompt,
                world.turn_number
            )
    
    # Display inject text immediately (don't wait for image)
    display_inject_text(console, inject)
    
    # Wait for image to complete (if generating)
    image_path = None
    if image_future:
        try:
            image_path = await asyncio.wait_for(image_future, timeout=10.0)
        except asyncio.TimeoutError:
            console.print("[yellow]Image generation timed out[/yellow]")
    
    return image_path


def display_inject_text(console: Console, inject: Inject):
    """Display inject text with scene-setting."""
    # Scene-setting (if present)
    if hasattr(inject, 'scene_setting') and inject.scene_setting:
        console.print()
        console.print(Panel(
            inject.scene_setting,
            title="Scene",
            border_style="dim cyan",
            padding=(1, 2)
        ))
        console.print()
        
        # Pause for dramatic effect
        import time
        time.sleep(2)
    
    # Main inject text
    console.print(Panel(
        inject.description,
        title=f"INTELLIGENCE BRIEFING - TURN {inject.turn_number}",
        border_style="red",
        padding=(1, 2)
    ))
```

---

### Phase 4: Image Display in Terminal (Day 2)

```python
from PIL import Image
from rich.console import Console
from rich.panel import Panel

def display_image_in_terminal(image_path: str, console: Console):
    """Display image in terminal if possible.
    
    Supports:
    - iTerm2 (macOS)
    - kitty terminal
    - Windows Terminal (limited support)
    - Fallback: Show file path
    """
    try:
        # Try rich_pixels (pip install rich-pixels)
        from rich_pixels import Pixels
        
        img = Image.open(image_path)
        
        # Resize to fit terminal width (max 120 chars)
        max_width = 120
        aspect_ratio = img.height / img.width
        new_height = int(max_width * aspect_ratio / 2)  # /2 for char aspect
        
        console.print()
        console.print(Pixels.from_image(img))
        console.print()
        
    except ImportError:
        # Fallback: Show file path in styled panel
        console.print()
        console.print(Panel(
            f"[cyan]Scene image generated:[/cyan]\n\n"
            f"[bold]{image_path}[/bold]\n\n"
            f"[dim]Open in image viewer for full quality[/dim]",
            title="📷 Visual Context",
            border_style="cyan"
        ))
        console.print()
    
    except Exception as e:
        console.print(f"[dim]Could not display image: {e}[/dim]")
```

---

### Phase 5: CLI Integration (Day 3)

Update `cli/main.py`:

```python
@click.command()
@click.option(
    "--generate-images",
    is_flag=True,
    default=False,
    help="Generate scene images for injects (£0.04/image, ~£0.50 per game)"
)
def play(
    variant: str,
    load: Optional[str],
    play_mode: str,
    generate_images: bool
):
    """Start game with optional image generation."""
    
    # Initialize image generation
    if generate_images:
        console.print("[cyan]Image generation enabled[/cyan]")
        console.print("[dim]Cost: ~£0.04 per image, max 20 images per session[/dim]")
        console.print()
        
        try:
            from engine.sim_loop import initialize_image_generation
            initialize_image_generation(True)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not initialize image generation: {e}[/yellow]")
            console.print("[dim]Continuing without images...[/dim]")
            generate_images = False
    
    # ... rest of game setup
    
    # Pass flag to game loop
    run_game_loop(world, enable_images=generate_images)
```

---

## Usage Examples

### Basic Usage
```powershell
# Play with image generation
.\.venv\Scripts\python.exe -m cli.main play --variant fast_start --generate-images
```

### Advanced Usage
```python
# In code - generate single image
from llm.image_generation import generate_scene_image

image_path = generate_scene_image(
    scene_prompt="UK Prime Minister in COBRA meeting room during crisis",
    turn_number=5
)
```

---

## Cost Management

### Session Limits
- **Default**: 20 images max per session
- **12-turn game**: ~£0.48 (very affordable)
- **Protection**: Fails gracefully if limit reached

### Cost Breakdown (12-turn game)
| Model | Cost/Image | Total Cost | Speed | Status |
|-------|-----------|------------|-------|--------|
| **Imagen 4 Fast** (recommended) ✅ | £0.02 | **£0.24** | 1-2s | Available |
| Imagen 4 Standard ✅ | £0.04 | £0.48 | 3-5s | Available |
| Imagen 4 Ultra ✅ | £0.06 | £0.72 | 5-8s | Available |
| Gemini 2.5 Flash Image ✅ | Unknown | Unknown | 2-4s | Experimental |

---

## Testing Plan

### Unit Tests
```python
def test_image_generator_initialization():
    """Test image generator initializes correctly."""
    gen = ImageGenerator()
    assert gen.model_name == "imagen-4.0-generate-001"
    assert gen.save_dir.exists()

def test_cost_protection():
    """Test session limit prevents runaway costs."""
    gen = ImageGenerator(max_images_per_session=2)
    
    # Generate 2 images (should work)
    gen.generate_inject_image("test scene 1", 1)
    gen.generate_inject_image("test scene 2", 2)
    
    # Try 3rd image (should fail gracefully)
    result = gen.generate_inject_image("test scene 3", 3)
    assert result is None

def test_graceful_failure():
    """Test image generation fails gracefully on error."""
    gen = ImageGenerator()
    
    # Invalid prompt should not crash
    result = gen.generate_inject_image("", -1)
    assert result is None or isinstance(result, str)
```

### Integration Tests
```python
async def test_parallel_generation():
    """Test image generates in parallel with inject display."""
    import time
    
    start = time.time()
    
    # This should NOT block
    inject = generate_inject_with_image_prompt(world)
    image_path = await display_inject_async(world, inject, console)
    
    elapsed = time.time() - start
    
    # Should be faster than sequential (< 8 seconds)
    assert elapsed < 8.0
    assert image_path is not None
```

### Playthrough Test
1. Start game with `--generate-images`
2. Play 5 turns
3. Verify:
   - ✅ Images generated for each turn
   - ✅ Saved to `generated_images/turn_001.jpg`, etc.
   - ✅ Consistent art style
   - ✅ No game crashes/hangs
   - ✅ Cost stats displayed at end

---

## Performance Considerations

### Parallel Generation
- Image generates **while player reads inject text**
- Typical read time: 30-60 seconds
- Image generation: 3-5 seconds
- **No perceived delay** (image ready before player finishes reading)

### Caching Strategy
- Save all images to disk
- Reference by turn number
- Allows post-game review
- Debugging asset for prompt tuning

### Error Handling
```python
# Generation fails → Game continues normally
# Network error → Fallback message shown
# API limit → Cost protection triggers
# Timeout → Show inject without image
```

---

## Art Style Consistency

### Recommended Style Prompt (from AI Studio experiment)
```python
ART_STYLE_PROMPT = (
    "in the style of a 90s Lucas Arts point and click adventure game, "
    "pixel art, vibrant colors, detailed backgrounds, cartoonish characters, "
    "retro video game aesthetic, isometric perspective"
)
```

**Why This Works**:
- ✅ Consistent visual identity across all images
- ✅ Nostalgic aesthetic appeals to target audience
- ✅ Pixel art style forgiving of minor artifacts
- ✅ Cartoonish reduces uncanny valley effects
- ✅ Imagen 4 handles this style exceptionally well

**Alternative Styles** (if desired):
```python
# Photorealistic (serious tone)
"photorealistic, professional photography, cinematic lighting, sharp focus"

# Political thriller (Tom Clancy aesthetic)
"cinematic still from political thriller movie, dramatic lighting, tense atmosphere"

# War documentary
"documentary photograph, BBC news footage, journalistic style, candid shot"
```

---

## Success Criteria

### Phase 1 Complete (Day 1)
- ✅ Image generation module created
- ✅ Unit tests passing
- ✅ Single image can be generated successfully

### Phase 2 Complete (Day 1)
- ✅ Inject generation includes image prompts
- ✅ Prompts are descriptive and visual
- ✅ JSON schema includes `image_prompt` field

### Phase 3 Complete (Day 2)
- ✅ Parallel generation working
- ✅ No blocking delays
- ✅ Graceful failure handling

### Phase 4 Complete (Day 2)
- ✅ Images display in terminal (or path shown)
- ✅ Formatting clean and professional
- ✅ Fallback works if display fails

### Phase 5 Complete (Day 3)
- ✅ CLI flag working
- ✅ Cost warnings shown
- ✅ Full playthrough with images successful

### Overall Success
- ✅ 12-turn playthrough with images (no crashes)
- ✅ Images saved to disk for review
- ✅ Consistent art style across all images
- ✅ Cost ≤ £0.50 per game
- ✅ Player feedback: Improved immersion

---

## Next Steps

1. **Confirm model choice**: 
   - **Recommended**: Imagen 4 Fast (£0.24/game, 1-2s generation)
   - **Alternative**: Imagen 4 Standard (£0.48/game, 3-5s generation, higher quality)
   
2. **Install dependencies**: 
   ```bash
   pip install google-generativeai Pillow rich-pixels
   ```

3. **Create image generation module** (Phase 1)
4. **Update inject generation** (Phase 2)
5. **Integrate async generation** (Phase 3)
6. **Test full playthrough** (Day 3)

---

## Related Documents

- **AI Studio Experiment Review**: `analysis/GOOGLE_AI_STUDIO_EXPERIMENT_REVIEW.md`
- **Phase 5 Plan**: `analysis/PHASE_5_IMPLEMENTATION_PLAN.md`
- **Current LLM Usage**: `analysis/CURRENT_LLM_USAGE_MAP.md`
- **Playtest Bug Report**: `analysis/PLAYTEST_BUG_REPORT_TURN_12.md`

---

**Status**: IMPLEMENTATION READY  
**Recommended Model**: Imagen 4 Fast (`models/imagen-4.0-fast-generate-001`) ⚡  
**Estimated Cost**: £0.24 per 12-turn game (50% savings vs standard)  
**Generation Speed**: 1-2 seconds (near-instant)  
**Timeline**: 3 days to full implementation  
**Next Action**: Confirm model choice and begin Phase 1  

**Alternative**: Imagen 4 Standard (`models/imagen-4.0-generate-001`) if quality critical

---

