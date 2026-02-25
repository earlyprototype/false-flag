# SDXL Cutscene Image Generation - Implementation Guide

**Feature**: Generate dramatic cutscene images for key moments using Stable Diffusion XL  
**Status**: 🔲 Not Implemented - Design Proposal  
**Priority**: P3 - Enhancement (Cool but not critical)  
**Estimated Effort**: 4-8 hours (integration) + hosting costs  

---

## Vision

**Dramatic moments get AI-generated images**:

```
TURN 7: NUCLEAR ADDRESS

[Generated Image: UK PM at podium, dramatic lighting, 
British flag, serious expression, war room background]

"I will speak clearly to Vladimir Putin: if one russian 
military soldier breaks the sovereignty of this nation..."
```

**Key Moments to Illustrate**:
- Intro scenes (Russian submarines, COBRA room)
- Major decisions (nuclear threats, diplomatic calls)
- Crisis events (explosions, attacks, military deployments)
- Endings (victory, defeat, cabinet revolt)

---

## Hosting Options (Cheapest → Most Powerful)

### Option 1: Free Tier Services (£0/month)

#### Hugging Face Inference API (FREE)

**Pros**:
- ✅ Completely free
- ✅ No hosting required
- ✅ Simple API
- ✅ SDXL Turbo available (fast)

**Cons**:
- ❌ Rate limited (slow during peak)
- ❌ Queue times can be long
- ❌ May timeout
- ❌ Not guaranteed uptime

**Setup**:
```python
# pip install huggingface_hub
from huggingface_hub import InferenceClient

client = InferenceClient(token="your_hf_token")  # Free token

image = client.text_to_image(
    "UK Prime Minister giving nuclear address, dramatic lighting, "
    "war room, British flag, photorealistic, cinematic",
    model="stabilityai/stable-diffusion-xl-base-1.0"
)
```

**Cost**: £0/month  
**Generation Time**: 10-60 seconds (queue dependent)  
**Best For**: Testing/prototyping

---

#### Replicate (Pay-per-use, very cheap)

**Pros**:
- ✅ Only pay for what you use
- ✅ Fast generation (~5-10 seconds)
- ✅ Reliable
- ✅ Multiple SDXL models available

**Cons**:
- ❌ Requires credit card
- ❌ Not free (but very cheap)

**Pricing**:
- SDXL: ~$0.0025 per image (¼ penny!)
- 100 images = $0.25
- 1000 images = $2.50

**Setup**:
```python
# pip install replicate
import replicate

output = replicate.run(
    "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
    input={
        "prompt": "UK Prime Minister nuclear address, dramatic, cinematic",
        "negative_prompt": "cartoon, anime, low quality",
        "width": 1024,
        "height": 768,
        "num_outputs": 1
    }
)
```

**Cost**: ~£0.002 per image  
**Generation Time**: 5-10 seconds  
**Best For**: Production use (RECOMMENDED)

---

### Option 2: Self-Hosted Cloud GPU (£10-50/month)

#### RunPod (Cheapest Cloud GPU)

**Pros**:
- ✅ Full control
- ✅ Fast generation (2-5 seconds)
- ✅ No per-image costs
- ✅ Can run 24/7 or on-demand

**Cons**:
- ❌ Monthly cost
- ❌ Need to set up server
- ❌ Maintenance required

**Pricing**:
- **On-Demand**: £0.20-0.40/hour (only when generating)
- **24/7 Pod**: £10-30/month (RTX 3060)
- **Powerful Pod**: £30-50/month (RTX 4090)

**Setup**:
1. Create RunPod account
2. Deploy SDXL template (one-click)
3. Get API endpoint
4. Call from your game

**Cost**: £10-50/month (or £0.20/hour on-demand)  
**Generation Time**: 2-5 seconds  
**Best For**: Heavy usage, full control

---

#### Vast.ai (Even Cheaper)

**Pros**:
- ✅ Cheapest GPU rental
- ✅ Spot pricing (£0.10-0.20/hour)
- ✅ Fast

**Cons**:
- ❌ Less reliable (spot instances)
- ❌ More technical setup
- ❌ Can lose instance

**Pricing**:
- RTX 3060: £0.10-0.15/hour
- RTX 4090: £0.30-0.50/hour

**Cost**: £0.10-0.50/hour (only when running)  
**Generation Time**: 2-5 seconds  
**Best For**: Budget-conscious, technical users

---

### Option 3: Managed Services (£20-100/month)

#### Stability AI Official API

**Pros**:
- ✅ Official API
- ✅ Very reliable
- ✅ Fast
- ✅ Best quality

**Cons**:
- ❌ More expensive
- ❌ Credit-based system

**Pricing**:
- $10 for 1000 credits
- SDXL = 6.5 credits per image
- ~150 images per $10
- ~$0.065 per image (6.5p)

**Cost**: £20-100/month depending on usage  
**Generation Time**: 3-5 seconds  
**Best For**: Production, quality matters

---

## My Recommendation: Replicate (Pay-per-use)

**Why Replicate is Perfect for This**:

1. **Cost-Effective for Game Use**:
   - Average playthrough: ~10-20 images
   - Cost per playthrough: £0.02-0.04 (2-4 pence!)
   - 100 playthroughs: £2-4
   - No monthly fees

2. **Simple Integration**:
   - One API call
   - No server management
   - Reliable uptime

3. **Fast Enough**:
   - 5-10 seconds per image
   - Can generate while showing text
   - Player won't notice delay

4. **Scalable**:
   - Start cheap
   - Only pay for actual usage
   - No commitment

---

## Implementation Design

### Architecture

```
Game Event
    ↓
Check if cutscene moment
    ↓
Generate prompt from context
    ↓
Call SDXL API (async)
    ↓
Cache image locally
    ↓
Display in terminal (if supported) or save to file
```

---

### Code Structure

```python
# In llm/image_generator.py

import replicate
import os
from pathlib import Path
from typing import Optional
import hashlib

class SDXLGenerator:
    """Generate cutscene images using Stable Diffusion XL."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize SDXL generator.
        
        Args:
            cache_dir: Directory to cache generated images
        """
        self.api_token = os.getenv("REPLICATE_API_TOKEN")
        if not self.api_token:
            raise ValueError("REPLICATE_API_TOKEN not set")
        
        self.cache_dir = cache_dir or Path("generated_images")
        self.cache_dir.mkdir(exist_ok=True)
        
        # SDXL model on Replicate
        self.model = "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
    
    def generate_cutscene(
        self,
        scene_type: str,
        context: dict,
        use_cache: bool = True
    ) -> Optional[Path]:
        """Generate a cutscene image.
        
        Args:
            scene_type: Type of scene ('intro', 'nuclear_threat', 'diplomatic_call', etc.)
            context: Context dict with details (turn, metrics, etc.)
            use_cache: Whether to use cached images
        
        Returns:
            Path to generated image, or None if generation fails
        """
        # Build prompt from scene type and context
        prompt = self._build_prompt(scene_type, context)
        
        # Check cache
        if use_cache:
            cache_path = self._get_cache_path(prompt)
            if cache_path.exists():
                return cache_path
        
        try:
            # Generate image
            output = replicate.run(
                self.model,
                input={
                    "prompt": prompt,
                    "negative_prompt": self._get_negative_prompt(),
                    "width": 1024,
                    "height": 768,
                    "num_inference_steps": 25,
                    "guidance_scale": 7.5,
                    "scheduler": "K_EULER"
                }
            )
            
            # Download and cache
            image_url = output[0] if isinstance(output, list) else output
            cache_path = self._download_and_cache(image_url, prompt)
            
            return cache_path
        
        except Exception as e:
            print(f"[WARNING] Failed to generate cutscene image: {e}")
            return None
    
    def _build_prompt(self, scene_type: str, context: dict) -> str:
        """Build SDXL prompt from scene type and context."""
        
        base_style = "cinematic, dramatic lighting, photorealistic, high detail, 4k"
        
        prompts = {
            "intro_cobra_room": (
                f"UK government COBRA emergency briefing room, "
                f"large table, officials in suits, serious expressions, "
                f"wall displays showing maps, crisis atmosphere, "
                f"{base_style}"
            ),
            
            "intro_russian_submarines": (
                f"Russian nuclear submarines surfacing in dark ocean, "
                f"moonlight, ominous, military, threatening, "
                f"aerial view, {base_style}"
            ),
            
            "nuclear_address": (
                f"UK Prime Minister at podium giving speech, "
                f"British flag background, dramatic lighting, "
                f"serious expression, war room setting, "
                f"tension, {base_style}"
            ),
            
            "diplomatic_call": (
                f"Secure video conference call, split screen, "
                f"world leaders, flags, serious discussion, "
                f"modern technology, {base_style}"
            ),
            
            "military_action": (
                f"UK military forces deploying, "
                f"ships, aircraft, dramatic sky, "
                f"action, tension, {base_style}"
            ),
            
            "explosion_attack": (
                f"Industrial facility explosion at night, "
                f"flames, smoke, emergency response, "
                f"dramatic, disaster, {base_style}"
            ),
            
            "victory_ending": (
                f"UK Prime Minister addressing nation, "
                f"relief, hope, British flag, "
                f"daylight, optimistic, {base_style}"
            ),
            
            "defeat_ending": (
                f"Empty COBRA briefing room, abandoned, "
                f"papers scattered, dim lighting, "
                f"aftermath, somber, {base_style}"
            ),
            
            "cabinet_revolt": (
                f"UK cabinet meeting, officials standing, "
                f"confrontation, tension, dramatic, "
                f"political crisis, {base_style}"
            )
        }
        
        return prompts.get(scene_type, prompts["intro_cobra_room"])
    
    def _get_negative_prompt(self) -> str:
        """Negative prompt to avoid unwanted styles."""
        return (
            "cartoon, anime, illustration, painting, drawing, "
            "low quality, blurry, distorted, ugly, bad anatomy"
        )
    
    def _get_cache_path(self, prompt: str) -> Path:
        """Get cache path for a prompt."""
        # Hash prompt to create filename
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        return self.cache_dir / f"{prompt_hash}.png"
    
    def _download_and_cache(self, url: str, prompt: str) -> Path:
        """Download image from URL and cache locally."""
        import requests
        
        cache_path = self._get_cache_path(prompt)
        
        response = requests.get(url)
        response.raise_for_status()
        
        cache_path.write_bytes(response.content)
        return cache_path
```

---

### Integration into Game

```python
# In cli/main.py

from llm.image_generator import SDXLGenerator

# Initialize generator
try:
    image_gen = SDXLGenerator()
    IMAGES_ENABLED = True
except ValueError:
    print("[INFO] SDXL image generation disabled (no API token)")
    IMAGES_ENABLED = False

# Generate cutscene images at key moments
def display_cutscene(scene_type: str, context: dict):
    """Display a cutscene with optional image."""
    
    if IMAGES_ENABLED:
        print("\n[Generating cutscene image...]")
        
        image_path = image_gen.generate_cutscene(
            scene_type,
            context,
            use_cache=True
        )
        
        if image_path:
            # Display image in terminal (if supported)
            display_image_in_terminal(image_path)
            
            # Or just save and notify
            print(f"[Cutscene image saved: {image_path}]")
    
    # Continue with text


# Example usage in intro
def show_intro():
    # Scene 1: Russian submarines
    display_cutscene("intro_russian_submarines", {})
    
    scroll_text("The Barents Sea lies black and restless...")
    wait_for_space()
    
    # Scene 2: COBRA room
    display_cutscene("intro_cobra_room", {})
    
    scroll_text("You are seated at the head of a long mahogany table...")
    wait_for_space()


# Example usage in nuclear threat
def handle_nuclear_threat(world: WorldState):
    display_cutscene("nuclear_address", {
        "turn": world.turn,
        "escalation": world.metrics.escalation_risk
    })
    
    scroll_text("I will speak clearly to Vladimir Putin...")
```

---

### Displaying Images in Terminal

**Option 1: iTerm2 / Kitty (Mac/Linux)**
```python
def display_image_in_terminal(image_path: Path):
    """Display image inline in terminal (iTerm2/Kitty)."""
    if os.getenv("TERM_PROGRAM") == "iTerm.app":
        # iTerm2 inline images
        os.system(f"imgcat {image_path}")
    elif os.getenv("TERM") == "xterm-kitty":
        # Kitty graphics protocol
        os.system(f"kitty +kitten icat {image_path}")
    else:
        # Fallback: just save
        print(f"[Image saved: {image_path}]")
```

**Option 2: Windows Terminal (Limited)**
```python
def display_image_in_terminal(image_path: Path):
    """Display image (Windows - opens in default viewer)."""
    if os.name == 'nt':
        # Open in default image viewer
        os.startfile(image_path)
    else:
        print(f"[Image saved: {image_path}]")
```

**Option 3: Rich Library (ASCII Art)**
```python
from PIL import Image
from rich.console import Console

def display_image_as_ascii(image_path: Path):
    """Display image as ASCII art in terminal."""
    img = Image.open(image_path)
    img = img.resize((80, 40))  # Terminal size
    
    # Convert to ASCII (simplified)
    # ... ASCII conversion logic ...
    
    console.print(ascii_art)
```

**Option 4: Save to Folder (Simplest)**
```python
def display_image_in_terminal(image_path: Path):
    """Just save image and notify player."""
    print(f"\n[Cutscene image generated: {image_path}]")
    print("[Open in image viewer to see]")
```

---

## Cost Analysis

### Replicate (Recommended)

**Typical Playthrough**:
- Intro scenes: 3 images
- Major decisions: 5-8 images
- Ending: 1 image
- **Total**: ~10-15 images per playthrough

**Cost per playthrough**: £0.02-0.04 (2-4 pence)

**100 playthroughs**: £2-4  
**1000 playthroughs**: £20-40  

**With caching** (same prompts reused):
- First playthrough: £0.03
- Subsequent playthroughs: £0.00 (cached)

---

### RunPod (Self-Hosted)

**On-Demand** (only when generating):
- £0.20/hour
- Generate 100 images in 10 minutes = £0.03
- Similar to Replicate but more setup

**24/7 Pod** (always available):
- £15/month for RTX 3060
- Unlimited generations
- **Break-even**: ~750 images/month vs Replicate

---

## Setup Guide (Replicate - Recommended)

### Step 1: Get API Token

1. Go to https://replicate.com
2. Sign up (free)
3. Go to Account → API Tokens
4. Copy your token

### Step 2: Install Dependencies

```bash
pip install replicate pillow requests
```

### Step 3: Set Environment Variable

**Windows PowerShell**:
```powershell
$env:REPLICATE_API_TOKEN="your_token_here"
```

**Or in `config.py`**:
```python
REPLICATE_API_TOKEN = "your_token_here"
```

### Step 4: Test Generation

```python
import replicate

output = replicate.run(
    "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
    input={
        "prompt": "UK Prime Minister giving nuclear address, dramatic, cinematic",
        "width": 1024,
        "height": 768
    }
)

print(f"Image URL: {output[0]}")
```

### Step 5: Integrate into Game

Add the `SDXLGenerator` class above and integrate into key moments.

---

## Optimization Strategies

### 1. Aggressive Caching

```python
# Cache by scene type, not full prompt
cache_key = f"{scene_type}_{turn_number}"

# Reuse images across playthroughs
# "intro_cobra_room" always looks the same
```

**Savings**: 90% reduction in API calls after first playthrough

---

### 2. Pre-Generate Common Scenes

```python
# Generate all intro scenes once
common_scenes = [
    "intro_russian_submarines",
    "intro_cobra_room",
    "nuclear_address",
    "diplomatic_call",
    "victory_ending",
    "defeat_ending"
]

for scene in common_scenes:
    image_gen.generate_cutscene(scene, {}, use_cache=True)
```

**Cost**: £0.02 one-time  
**Benefit**: Instant cutscenes for all playthroughs

---

### 3. Optional Feature

```python
# Make images opt-in
ENABLE_CUTSCENES = typer.Option(
    False,
    "--cutscenes/--no-cutscenes",
    help="Generate AI cutscene images (requires API token)"
)
```

**Benefit**: Players who don't want images don't pay

---

### 4. Batch Generation

```python
# Generate multiple images in parallel
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [
        executor.submit(image_gen.generate_cutscene, scene, {})
        for scene in scenes_to_generate
    ]
    
    images = [f.result() for f in futures]
```

**Benefit**: Faster generation for intro sequences

---

## Alternative: Hugging Face (Free)

If you want to avoid any costs:

```python
from huggingface_hub import InferenceClient

client = InferenceClient(token="your_free_hf_token")

image = client.text_to_image(
    "UK Prime Minister nuclear address, dramatic, cinematic",
    model="stabilityai/stable-diffusion-xl-base-1.0"
)

image.save("cutscene.png")
```

**Pros**: Completely free  
**Cons**: Slow (30-60 seconds), unreliable, may timeout

---

## UI/UX Considerations

### Option 1: Inline Display (Best)

```
[Generating cutscene...]

╔════════════════════════════════════════╗
║                                        ║
║     [Image displayed here]             ║
║                                        ║
╚════════════════════════════════════════╝

TURN 7: NUCLEAR ADDRESS

"I will speak clearly to Vladimir Putin..."
```

---

### Option 2: Save and Notify (Simplest)

```
[Cutscene image generated: generated_images/nuclear_address.png]
[Open in image viewer to see]

TURN 7: NUCLEAR ADDRESS

"I will speak clearly to Vladimir Putin..."
```

---

### Option 3: Gallery Mode

```
[5 cutscene images generated this playthrough]
[View gallery: generated_images/]

- intro_submarines.png
- cobra_room.png
- nuclear_address.png
- diplomatic_call_russia.png
- victory_ending.png
```

---

## Recommended Implementation Plan

### Phase 1: Basic Integration (2 hours)

1. Add `SDXLGenerator` class
2. Integrate Replicate API
3. Generate intro scenes only
4. Save to folder (no inline display)

**Cost**: £0.01 per playthrough

---

### Phase 2: Key Moments (2 hours)

1. Add cutscenes for major decisions
2. Nuclear threats
3. Diplomatic calls
4. Endings

**Cost**: £0.03 per playthrough

---

### Phase 3: Optimization (2 hours)

1. Implement caching
2. Pre-generate common scenes
3. Make opt-in feature

**Cost**: £0.00 per playthrough (after first)

---

### Phase 4: Display Enhancement (2 hours)

1. Inline terminal display (if supported)
2. Or open in viewer automatically
3. Gallery mode

---

## Final Recommendation

**Start with Replicate + Caching**:

1. **Cost**: ~£0.03 first playthrough, £0.00 after (cached)
2. **Speed**: 5-10 seconds per image
3. **Quality**: Excellent (SDXL)
4. **Reliability**: Very high
5. **Setup**: Simple (one API token)

**Total Investment**:
- Setup time: 2-4 hours
- First 100 playthroughs: £2-4
- After caching: Nearly free

**This adds massive atmosphere for minimal cost.**

---

## Example Cutscene Prompts

```python
CUTSCENE_PROMPTS = {
    "intro_submarines": (
        "Russian nuclear submarines surfacing in dark ocean at night, "
        "moonlight reflecting on water, ominous atmosphere, "
        "aerial view, military vessels, threatening, "
        "cinematic, dramatic lighting, photorealistic, 4k"
    ),
    
    "cobra_room": (
        "UK government COBRA emergency briefing room interior, "
        "large conference table, officials in suits, "
        "wall displays showing maps and data, "
        "serious atmosphere, crisis meeting, "
        "cinematic, dramatic lighting, photorealistic, 4k"
    ),
    
    "nuclear_threat_pm": (
        "UK Prime Minister at podium giving serious speech, "
        "British flag in background, dramatic lighting, "
        "tense expression, war room setting, "
        "cinematic, photorealistic, 4k"
    ),
    
    "russian_fleet": (
        "Russian naval fleet in North Atlantic, "
        "warships, submarines, stormy seas, "
        "military power, threatening, "
        "cinematic, dramatic, photorealistic, 4k"
    ),
    
    "explosion_drax": (
        "Power station explosion at night, "
        "flames, smoke, emergency vehicles, "
        "industrial disaster, dramatic, "
        "cinematic, photorealistic, 4k"
    )
}
```

---

**Let me know if you want me to implement the basic version!** 🎨

**Estimated total cost for your development**: £5-10 for testing + £0-2/month in production (with caching)

