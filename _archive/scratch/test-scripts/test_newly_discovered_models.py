"""Test the newly discovered warm models"""

import os
import time
from io import BytesIO
from PIL import Image
import requests
from dotenv import load_dotenv

TEST_PROMPT = """
STYLE REQUIREMENTS: Classic LucasArts SCUMM engine adventure game aesthetic (1990-1995 era: The Secret of Monkey Island, Day of the Tentacle, Sam & Max Hit the Road, Full Throttle). MANDATORY specifications: DB16 palette ONLY (DawnBringer 16 colors - no other colors permitted), flat color fills with NO gradients, strong black pixel-perfect outlines on ALL shapes, NO anti-aliasing, NO blur, NO soft edges, sharp geometric forms, hand-drawn cartoon quality with bold readable silhouettes, expressive character design, clean composition suitable for VGA-era displays and modern CLI terminal rendering. Art style: comedic yet dramatic, exaggerated proportions, clear visual hierarchy, high contrast for readability. Technical: pixel-perfect edges, transparent PNG background where appropriate.

Generate: A serious news anchor character (male, business suit, clean-cut appearance, slight worry in expression) sitting at modern TV news desk with world map backdrop, 3/4 view, professional studio setting
"""

NEW_MODELS = [
    ("stabilityai/stable-diffusion-3.5-large", "SD 3.5 Large (NEW 2025)"),
    ("stabilityai/stable-diffusion-3.5-medium", "SD 3.5 Medium (NEW 2025)"),
    ("stabilityai/stable-diffusion-3-medium-diffusers", "SD 3 Medium"),
    ("Qwen/Qwen-Image", "Qwen Image"),
    ("ByteDance/SDXL-Lightning", "SDXL Lightning (FAST)"),
    ("HiDream-ai/HiDream-I1-Full", "HiDream I1 Full"),
    ("tencent/HunyuanImage-3.0", "Hunyuan Image 3.0"),
]

def test_model(model_id: str, model_name: str, hf_token: str) -> dict:
    """Test a single model."""
    print(f"\n{'='*70}")
    print(f"Testing: {model_name}")
    print(f"Model ID: {model_id}")
    print('='*70)
    
    try:
        api_url = f"https://api-inference.huggingface.co/models/{model_id}"
        headers = {"Authorization": f"Bearer {hf_token}"}
        
        start_time = time.time()
        
        response = requests.post(
            api_url,
            headers=headers,
            json={"inputs": TEST_PROMPT},
            timeout=120
        )
        
        # Handle cold start
        if response.status_code == 503:
            print(f"  ⏳ Model loading, waiting 25 seconds...")
            time.sleep(25)
            
            response = requests.post(
                api_url,
                headers=headers,
                json={"inputs": TEST_PROMPT},
                timeout=120
            )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            safe_name = model_id.replace('/', '_').replace('.', '_')
            filename = f"sample_NEW_{safe_name}.png"
            image.save(filename)
            
            print(f"  ✅ SUCCESS!")
            print(f"  Time: {elapsed:.1f}s")
            print(f"  Size: {image.size}")
            print(f"  Saved: {filename}")
            
            return {"status": "success", "time": elapsed, "size": image.size, "filename": filename}
        else:
            print(f"  ❌ FAILED: {response.status_code}")
            print(f"  Error: {response.text[:200]}")
            return {"status": "failed", "error_code": response.status_code}
            
    except Exception as e:
        print(f"  ❌ EXCEPTION: {e}")
        return {"status": "exception", "error": str(e)}


def main():
    load_dotenv()
    hf_token = os.getenv('HF_TOKEN') or os.getenv('HUGGINGFACE_TOKEN')
    
    if not hf_token:
        print("ERROR: No HF_TOKEN found!")
        return
    
    print("="*70)
    print("  TESTING NEWLY DISCOVERED MODELS")
    print(f"  Total: {len(NEW_MODELS)}")
    print("="*70)
    
    results = []
    
    for model_id, model_name in NEW_MODELS:
        result = test_model(model_id, model_name, hf_token)
        result['model_id'] = model_id
        result['model_name'] = model_name
        results.append(result)
        time.sleep(2)
    
    # Summary
    print("\n" + "="*70)
    print("RESULTS SUMMARY")
    print("="*70)
    
    successful = [r for r in results if r["status"] == "success"]
    print(f"\n✅ Successful: {len(successful)}/{len(results)}")
    
    if successful:
        successful.sort(key=lambda x: x["time"])
        print("\nWorking models (sorted by speed):")
        for i, r in enumerate(successful, 1):
            print(f"\n{i}. {r['model_name']}")
            print(f"   File: {r['filename']}")
            print(f"   Size: {r['size']}")
            print(f"   Time: {r['time']:.1f}s")


if __name__ == "__main__":
    main()

