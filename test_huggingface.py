"""
Test Hugging Face image generation with free tier
"""

import os
from dotenv import load_dotenv
import requests
from PIL import Image
from io import BytesIO

# Load API key
load_dotenv()

# Check for Hugging Face token
hf_token = os.getenv('HF_TOKEN') or os.getenv('HUGGINGFACE_TOKEN')

if not hf_token:
    print("="*70)
    print("HUGGING FACE TOKEN NOT FOUND")
    print("="*70)
    print("\nTo get a free token:")
    print("1. Go to: https://huggingface.co/settings/tokens")
    print("2. Create account (free)")
    print("3. Click 'New token' -> 'Read' access")
    print("4. Add to .env file:")
    print("   HF_TOKEN=your_token_here")
    print("\n" + "="*70)
    exit(1)

print("Testing Hugging Face Image Generation (FREE)")
print("="*70)

# Test with Stable Diffusion XL (free inference available)
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {hf_token}"}

# Simple test prompt
test_prompt = "pixel art, 16x16, red diamond icon, clean geometric shape, retro gaming style, DB16 palette colors, no background"

print(f"Model: Stable Diffusion XL Base 1.0")
print(f"Prompt: {test_prompt}\n")
print("Generating...")

try:
    response = requests.post(
        API_URL,
        headers=headers,
        json={"inputs": test_prompt},
        timeout=60
    )
    
    if response.status_code == 200:
        # Load image from response
        image = Image.open(BytesIO(response.content))
        
        print(f"\n✅ SUCCESS!")
        print(f"  Image size: {image.size}")
        print(f"  Mode: {image.mode}")
        
        image.save('test_hf_image.png')
        print(f"  Saved: test_hf_image.png")
        print(f"\n🎉 Hugging Face FREE generation WORKS!")
        
    elif response.status_code == 503:
        print(f"\n⏳ Model is loading (cold start)")
        print(f"   Response: {response.json()}")
        print(f"\n   Wait ~20 seconds and try again")
        
    else:
        print(f"\n❌ Error {response.status_code}")
        print(f"   Response: {response.text}")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")

