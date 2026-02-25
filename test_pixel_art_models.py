"""
Test different Hugging Face models to find the best one for pixel art generation
"""

import os
from dotenv import load_dotenv
import requests
from PIL import Image
from io import BytesIO
import time

load_dotenv()
hf_token = os.getenv('HF_TOKEN') or os.getenv('HUGGINGFACE_TOKEN')

if not hf_token:
    print("ERROR: HF_TOKEN not found")
    exit(1)

# Models to test (from newest/best to older)
models = [
    ("black-forest-labs/FLUX.1-schnell", "FLUX.1 Schnell (2024, FAST, FREE)"),
    ("black-forest-labs/FLUX.1-dev", "FLUX.1 Dev (2024, High Quality)"),
    ("nerijs/pixel-art-xl", "Pixel Art XL (Specialized for pixel art)"),
    ("stabilityai/stable-diffusion-xl-base-1.0", "SDXL Base 1.0 (Current)"),
]

test_prompt = "pixel art, 16x16, simple red diamond icon, retro gaming style, clean geometric shape"

print("Testing Hugging Face Models for Pixel Art")
print("="*70)
print(f"Prompt: {test_prompt}\n")

for model_id, model_name in models:
    print(f"\nTesting: {model_name}")
    print(f"Model ID: {model_id}")
    print("-" * 70)
    
    api_url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {hf_token}"}
    
    try:
        response = requests.post(
            api_url,
            headers=headers,
            json={"inputs": test_prompt},
            timeout=90
        )
        
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            filename = f"test_{model_id.replace('/', '_')}.png"
            image.save(filename)
            
            print(f"✅ SUCCESS!")
            print(f"   Size: {image.size}")
            print(f"   Saved: {filename}")
            print(f"   → This model works!")
            
        elif response.status_code == 503:
            print(f"⏳ Model loading (cold start)")
            print(f"   Waiting 20 seconds...")
            time.sleep(20)
            
            # Retry
            response = requests.post(
                api_url,
                headers=headers,
                json={"inputs": test_prompt},
                timeout=90
            )
            
            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))
                filename = f"test_{model_id.replace('/', '_')}.png"
                image.save(filename)
                
                print(f"✅ SUCCESS after retry!")
                print(f"   Size: {image.size}")
                print(f"   Saved: {filename}")
                print(f"   → This model works!")
            else:
                print(f"❌ Failed after retry: {response.status_code}")
                
        elif response.status_code == 403:
            print(f"⚠️  GATED MODEL - Requires approval")
            print(f"   Visit: https://huggingface.co/{model_id}")
            
        else:
            print(f"❌ Error {response.status_code}")
            print(f"   {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print()

print("\n" + "="*70)
print("TESTING COMPLETE")
print("="*70)
print("\nRecommendation: Use the first model that succeeded!")

