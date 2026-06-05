"""Test the remaining warm models we haven't tried yet"""

import os
import time
from io import BytesIO
from PIL import Image
import requests
from dotenv import load_dotenv

# Simple test prompt
SIMPLE_PROMPT = "A news anchor at a desk, pixel art style, 16-bit graphics"

# Models we haven't tested yet (all with inference: warm)
REMAINING_MODELS = [
    ("ByteDance/Hyper-SD", "Hyper-SD (ByteDance)"),
    ("black-forest-labs/FLUX.1-Krea-dev", "FLUX.1 Krea Dev"),
    ("XLabs-AI/flux-RealismLora", "FLUX Realism LoRA"),
    ("HiDream-ai/HiDream-I1-Fast", "HiDream I1 Fast"),
    ("prithivMLmods/Castor-3D-Sketchfab-Flux-LoRA", "Castor 3D Sketchfab"),
]

def test_model_simple(model_id: str, model_name: str, hf_token: str) -> dict:
    """Test a model with simple parameters."""
    print(f"\n{'='*60}")
    print(f"Testing: {model_name}")
    print(f"Model: {model_id}")
    print('='*60)

    try:
        api_url = f"https://api-inference.huggingface.co/models/{model_id}"
        headers = {"Authorization": f"Bearer {hf_token}"}

        # Simple payload first
        payload = {
            "inputs": SIMPLE_PROMPT,
            "parameters": {
                "width": 1024,
                "height": 1024
            }
        }

        start_time = time.time()
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        elapsed = time.time() - start_time

        print(f"Status: {response.status_code}")
        print(f"Time: {elapsed:.1f}s")

        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            filename = f"test_{model_id.replace('/', '_')}.png"
            image.save(filename)
            print(f"✅ SUCCESS! Saved: {filename}")
            print(f"Size: {image.size}")
            return {"status": "success", "time": elapsed, "size": image.size, "filename": filename}

        elif response.status_code == 402:
            print(f"💳 Rate limited: {response.text[:100]}")
            return {"status": "rate_limited", "error": response.text}

        elif response.status_code == 404:
            print(f"❌ Model not found")
            return {"status": "not_found"}

        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return {"status": "error", "code": response.status_code, "response": response.text[:200]}

    except Exception as e:
        print(f"❌ Exception: {e}")
        return {"status": "exception", "error": str(e)}


def main():
    load_dotenv()
    hf_token = os.getenv('HF_TOKEN') or os.getenv('HUGGINGFACE_TOKEN')

    if not hf_token:
        print("❌ No HF_TOKEN found!")
        return

    print("🔬 TESTING REMAINING WARM MODELS")
    print(f"Models to test: {len(REMAINING_MODELS)}")
    print("="*60)

    results = []

    for model_id, model_name in REMAINING_MODELS:
        result = test_model_simple(model_id, model_name, hf_token)
        result['model_id'] = model_id
        result['model_name'] = model_name
        results.append(result)

        # Small delay between tests
        time.sleep(3)

    # Summary
    print("\n" + "="*60)
    print("📊 RESULTS SUMMARY")
    print("="*60)

    working = [r for r in results if r["status"] == "success"]
    rate_limited = [r for r in results if r["status"] == "rate_limited"]
    not_found = [r for r in results if r["status"] == "not_found"]
    errors = [r for r in results if r["status"] == "error"]

    print(f"\n✅ Working: {len(working)}")
    print(f"💳 Rate Limited: {len(rate_limited)}")
    print(f"❌ Not Found: {len(not_found)}")
    print(f"⚠️  Other Errors: {len(errors)}")

    if working:
        print("\n🎉 SUCCESSFUL MODELS:")
        for r in working:
            print(f"  • {r['model_name']} ({r['time']:.1f}s) - {r['filename']}")

    if rate_limited:
        print(f"\n💳 These models exist but you're rate limited:")
        for r in rate_limited:
            print(f"  • {r['model_name']}")

    print(f"\n🖼️  Check any generated images to see quality!")
    print(f"💡 Rate limits reset monthly - try again later!")


if __name__ == "__main__":
    main()







