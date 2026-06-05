"""Test FLUX API with proper parameters and prompt formatting"""

import os
import time
from io import BytesIO
from typing import Optional
from PIL import Image
import requests
from dotenv import load_dotenv

# Load token
load_dotenv()
hf_token = os.getenv('HF_TOKEN') or os.getenv('HUGGINGFACE_TOKEN')

# Test prompts - start simple and build up
TEST_PROMPTS = [
    # Simple prompt
    "A news anchor at a desk",

    # With style
    "A news anchor at a desk, pixel art style, 16-bit graphics",

    # More specific
    "A news anchor character, male, business suit, sitting at modern TV news desk with world map backdrop, pixel art, retro game style",

    # Your full prompt
    """
    STYLE REQUIREMENTS: Classic LucasArts SCUMM engine adventure game aesthetic (1990-1995 era: The Secret of Monkey Island, Day of the Tentacle, Sam & Max Hit the Road, Full Throttle). MANDATORY specifications: DB16 palette ONLY (DawnBringer 16 colors - no other colors permitted), flat color fills with NO gradients, strong black pixel-perfect outlines on ALL shapes, NO anti-aliasing, NO blur, NO soft edges, sharp geometric forms, hand-drawn cartoon quality with bold readable silhouettes, expressive character design, clean composition suitable for VGA-era displays and modern CLI terminal rendering. Art style: comedic yet dramatic, exaggerated proportions, clear visual hierarchy, high contrast for readability. Technical: pixel-perfect edges, transparent PNG background where appropriate.

    Generate: A serious news anchor character (male, business suit, clean-cut appearance, slight worry in expression) sitting at modern TV news desk with world map backdrop, 3/4 view, professional studio setting
    """.strip()
]

def test_flux_with_params(prompt: str, model: str = "black-forest-labs/FLUX.1-schnell"):
    """Test FLUX with proper parameters."""
    api_url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {hf_token}"}

    # FLUX-specific parameters
    payload = {
        "inputs": prompt,
        "parameters": {
            "num_inference_steps": 4,
            "guidance_scale": 3.5,
            "width": 1024,
            "height": 1024,
            "negative_prompt": "blurry, low quality, deformed, extra limbs, mutated, ugly, poorly drawn face, bad anatomy, watermark, text, signature"
        }
    }

    print(f"\n{'='*60}")
    print(f"Testing: {model}")
    print(f"Prompt: {prompt[:100]}...")
    print('='*60)

    try:
        start_time = time.time()
        response = requests.post(api_url, headers=headers, json=payload, timeout=90)
        elapsed = time.time() - start_time

        print(f"Status: {response.status_code}")
        print(f"Time: {elapsed:.1f}s")

        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            filename = f"test_flux_{len(prompt[:50])}.png"
            image.save(filename)
            print(f"✅ Saved: {filename}")
            print(f"Size: {image.size}")
            return image
        else:
            print(f"❌ Error: {response.text[:200]}")
            return None

    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def main():
    """Test different prompts."""
    print("🧪 TESTING FLUX WITH PROPER PARAMETERS")
    print("="*60)

    for i, prompt in enumerate(TEST_PROMPTS, 1):
        print(f"\n📝 PROMPT {i}:")
        print(f"Length: {len(prompt)} characters")

        # Test with FLUX Schnell (fast)
        test_flux_with_params(prompt, "black-forest-labs/FLUX.1-schnell")

        # Small delay between tests
        time.sleep(3)

    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETE")
    print("Check the generated test images!")
    print("="*60)

if __name__ == "__main__":
    main()

