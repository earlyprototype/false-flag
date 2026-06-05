"""Test alternative approaches and models that might not be rate limited"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()
hf_token = os.getenv('HF_TOKEN')

# Models that might work differently or have different limits
ALTERNATIVE_MODELS = [
    # Smaller/faster models that might have different limits
    ("CompVis/stable-diffusion-v1-4", "SD 1.4 (Classic)"),
    ("runwayml/stable-diffusion-v1-5", "SD 1.5"),
    ("stabilityai/stable-diffusion-2-1", "SD 2.1"),

    # Models from different providers that might not share the same limits
    ("SG161222/RealVisXL_V4.0", "RealVisXL v4.0"),
    ("Lykon/DreamShaper", "DreamShaper"),

    # Community models that might be hosted differently
    ("cagliostrolab/animagine-xl-3.1", "Animagine XL 3.1"),
    ("dataautogpt3/ProteusV0.3", "Proteus v0.3"),
]

def test_alternative_model(model_id: str, model_name: str):
    """Test a model with minimal parameters."""
    print(f"\n{'='*50}")
    print(f"Testing: {model_name}")
    print(f"Model: {model_id}")
    print('='*50)

    try:
        api_url = f"https://api-inference.huggingface.co/models/{model_id}"
        headers = {"Authorization": f"Bearer {hf_token}"}

        # Very simple payload
        payload = {
            "inputs": "A simple test image",
            "parameters": {
                "width": 512,
                "height": 512
            }
        }

        response = requests.post(api_url, headers=headers, json=payload, timeout=30)

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            print(f"✅ SUCCESS! This model works!")
            return "success"
        elif response.status_code == 402:
            print(f"💳 Rate limited")
            return "rate_limited"
        elif response.status_code == 404:
            print(f"❌ Model not available")
            return "not_available"
        else:
            print(f"⚠️  Other error: {response.text[:100]}")
            return "other_error"

    except Exception as e:
        print(f"❌ Exception: {e}")
        return "exception"

def main():
    print("🔍 TESTING ALTERNATIVE MODELS")
    print("These might not be subject to the same rate limits...")
    print("="*60)

    results = {}

    for model_id, model_name in ALTERNATIVE_MODELS:
        result = test_alternative_model(model_id, model_name)
        results[model_id] = result
        time.sleep(2)  # Small delay

    # Summary
    print("\n" + "="*60)
    print("📊 ALTERNATIVE MODELS RESULTS")
    print("="*60)

    working = [k for k, v in results.items() if v == "success"]
    rate_limited = [k for k, v in results.items() if v == "rate_limited"]
    not_available = [k for k, v in results.items() if v == "not_available"]

    print(f"\n✅ Working: {len(working)}")
    print(f"💳 Rate Limited: {len(rate_limited)}")
    print(f"❌ Not Available: {len(not_available)}")

    if working:
        print("
🎉 These models still work!"        for model in working:
            print(f"  • {model}")

    if not working:
        print("
😔 All alternative models are also limited."        print("💡 Rate limits reset monthly")
        print("💡 Or upgrade to HuggingFace PRO for more credits")
        print("💡 Or use the batch files for manual generation")


if __name__ == "__main__":
    main()







