"""
Test multiple Hugging Face models to find the best one for pixel art.
Creates sample images from each model for comparison.
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

# Models to test - mix of popular general models and specialized ones
test_models = [
    # FLUX models (2024, state of the art)
    ("black-forest-labs/FLUX.1-schnell", "FLUX.1 Schnell (2024, Fast)"),
    
    # Stable Diffusion variants
    ("stabilityai/stable-diffusion-xl-base-1.0", "SDXL Base 1.0 (Popular)"),
    ("stabilityai/sdxl-turbo", "SDXL Turbo (Fast variant)"),
    ("segmind/SSD-1B", "SSD-1B (50% smaller than SDXL, fast)"),
    
    # Specialized/Fine-tuned models that might be better
    ("prompthero/openjourney-v4", "OpenJourney v4 (Midjourney-like)"),
    ("playgroundai/playground-v2.5-1024px-aesthetic", "Playground v2.5 (Aesthetic)"),
    ("SG161222/RealVisXL_V4.0", "RealVisXL v4 (Realistic)"),
    
    # Smaller/faster models
    ("runwayml/stable-diffusion-v1-5", "SD 1.5 (Classic, Fast)"),
]

# Test prompt - simple pixel art that should be easy to evaluate
test_prompt = """pixel art sprite, 16x16 pixels, simple red diamond icon, 
retro 1990s video game style, clean geometric shape, sharp edges, 
limited color palette, no anti-aliasing, VGA graphics aesthetic"""

print("="*70)
print("TESTING HUGGING FACE MODELS FOR PIXEL ART")
print("="*70)
print(f"Total models to test: {len(test_models)}")
print(f"Test prompt: {test_prompt[:80]}...")
print("="*70)

results = []

for model_id, model_name in test_models:
    print(f"\n[{len(results)+1}/{len(test_models)}] Testing: {model_name}")
    print(f"    Model ID: {model_id}")
    
    api_url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {hf_token}"}
    
    try:
        start_time = time.time()
        
        response = requests.post(
            api_url,
            headers=headers,
            json={"inputs": test_prompt},
            timeout=90
        )
        
        if response.status_code == 200:
            elapsed = time.time() - start_time
            image = Image.open(BytesIO(response.content))
            
            # Save with model name
            safe_name = model_id.replace('/', '_').replace('.', '_')
            filename = f"sample_{safe_name}.png"
            image.save(filename)
            
            print(f"    ✅ SUCCESS!")
            print(f"    Size: {image.size}")
            print(f"    Time: {elapsed:.1f}s")
            print(f"    Saved: {filename}")
            
            results.append({
                'model_id': model_id,
                'model_name': model_name,
                'filename': filename,
                'size': image.size,
                'time': elapsed,
                'status': 'SUCCESS'
            })
            
        elif response.status_code == 503:
            print(f"    ⏳ Model loading (cold start), waiting 20s...")
            time.sleep(20)
            
            # Retry
            start_time = time.time()
            response = requests.post(
                api_url,
                headers=headers,
                json={"inputs": test_prompt},
                timeout=90
            )
            
            if response.status_code == 200:
                elapsed = time.time() - start_time + 20  # Include wait time
                image = Image.open(BytesIO(response.content))
                
                safe_name = model_id.replace('/', '_').replace('.', '_')
                filename = f"sample_{safe_name}.png"
                image.save(filename)
                
                print(f"    ✅ SUCCESS after retry!")
                print(f"    Size: {image.size}")
                print(f"    Time: {elapsed:.1f}s (incl. wait)")
                print(f"    Saved: {filename}")
                
                results.append({
                    'model_id': model_id,
                    'model_name': model_name,
                    'filename': filename,
                    'size': image.size,
                    'time': elapsed,
                    'status': 'SUCCESS (retry)'
                })
            else:
                print(f"    ❌ Failed after retry: {response.status_code}")
                results.append({
                    'model_id': model_id,
                    'model_name': model_name,
                    'status': f'FAILED: {response.status_code}'
                })
                
        elif response.status_code == 403:
            print(f"    ⚠️  GATED - Requires approval at:")
            print(f"        https://huggingface.co/{model_id}")
            results.append({
                'model_id': model_id,
                'model_name': model_name,
                'status': 'GATED (needs approval)'
            })
            
        elif response.status_code == 404:
            print(f"    ❌ Model not found or not available")
            results.append({
                'model_id': model_id,
                'model_name': model_name,
                'status': 'NOT FOUND'
            })
            
        else:
            print(f"    ❌ Error {response.status_code}")
            error_text = response.text[:150]
            print(f"        {error_text}")
            results.append({
                'model_id': model_id,
                'model_name': model_name,
                'status': f'ERROR: {response.status_code}'
            })
            
    except Exception as e:
        print(f"    ❌ Exception: {str(e)[:100]}")
        results.append({
            'model_id': model_id,
            'model_name': model_name,
            'status': f'EXCEPTION: {str(e)[:50]}'
        })

# Print summary
print("\n" + "="*70)
print("RESULTS SUMMARY")
print("="*70)

successful = [r for r in results if 'SUCCESS' in r.get('status', '')]
print(f"\n✅ Successful: {len(successful)}/{len(results)}")

if successful:
    print("\nWorking models (sorted by speed):")
    successful.sort(key=lambda x: x.get('time', 999))
    
    for i, result in enumerate(successful, 1):
        print(f"\n{i}. {result['model_name']}")
        print(f"   File: {result['filename']}")
        print(f"   Size: {result['size']}")
        print(f"   Time: {result['time']:.1f}s")

print("\n" + "="*70)
print("CHECK THE GENERATED IMAGES TO SEE WHICH LOOKS BEST!")
print("="*70)
print("\nNext step: Pick the best-looking model and I'll update the script.")

