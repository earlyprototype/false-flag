"""Test Replicate API for free image generation"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()
replicate_token = os.getenv('REPLICATE_API_TOKEN')

# Test prompts
TEST_PROMPTS = [
    "A news anchor at a desk, pixel art style",
    "A news anchor character, pixel art, retro game style",
]

def test_replicate_model(model_name: str, prompt: str):
    """Test a Replicate model."""
    print(f"\n{'='*60}")
    print(f"Testing Replicate: {model_name}")
    print(f"Prompt: {prompt[:50]}...")
    print('='*60)

    try:
        if not replicate_token:
            print("❌ REPLICATE_API_TOKEN not found in .env")
            return

        # Replicate API endpoint
        url = "https://api.replicate.com/v1/predictions"

        headers = {
            "Authorization": f"Token {replicate_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "version": model_name,
            "input": {
                "prompt": prompt,
                "width": 1024,
                "height": 1024,
                "num_inference_steps": 4,
                "guidance_scale": 3.5
            }
        }

        start_time = time.time()
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        elapsed = time.time() - start_time

        print(f"Status: {response.status_code}")
        print(f"Time: {elapsed:.1f}s")

        if response.status_code == 201:
            result = response.json()
            print("✅ Prediction started!")
            print(f"Prediction ID: {result['id']}")

            # Check status
            prediction_id = result['id']
            status_url = f"https://api.replicate.com/v1/predictions/{prediction_id}"

            for i in range(10):  # Check up to 10 times
                status_response = requests.get(status_url, headers=headers)
                status_data = status_response.json()

                print(f"  Status check {i+1}: {status_data['status']}")

                if status_data['status'] == 'succeeded':
                    image_url = status_data['output']
                    print(f"✅ SUCCESS! Image URL: {image_url}")

                    # Download image
                    image_response = requests.get(image_url)
                    with open(f"replicate_{model_name.split('/')[-1]}.png", "wb") as f:
                        f.write(image_response.content)
                    print(f"📁 Saved: replicate_{model_name.split('/')[-1]}.png")
                    return "success"

                elif status_data['status'] == 'failed':
                    print(f"❌ Failed: {status_data.get('error', 'Unknown error')}")
                    return "failed"

                time.sleep(2)  # Wait 2 seconds between checks

            print("⏰ Timeout waiting for completion")
            return "timeout"

        elif response.status_code == 402:
            print(f"💳 Rate limited: {response.text[:100]}")
            return "rate_limited"

        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return "error"

    except Exception as e:
        print(f"❌ Exception: {e}")
        return "exception"

def main():
    """Test various Replicate models."""
    print("🔬 TESTING REPLICATE API (FREE TIER)")
    print("="*60)

    if not replicate_token:
        print("❌ Please add REPLICATE_API_TOKEN to .env file")
        print("   Get one at: https://replicate.com/account/api-tokens")
        return

    # Popular image generation models on Replicate
    models_to_test = [
        ("black-forest-labs/flux-1.1-pro", "FLUX 1.1 Pro"),
        ("black-forest-labs/flux-dev", "FLUX Dev"),
        ("black-forest-labs/flux-schnell", "FLUX Schnell"),
        ("stability-ai/stable-diffusion-3-medium", "SD 3 Medium"),
        ("stability-ai/stable-diffusion-xl-1024-v1-0", "SDXL 1024"),
        ("stability-ai/sdxl", "SDXL"),
    ]

    results = []

    for model_name, display_name in models_to_test:
        result = test_replicate_model(model_name, TEST_PROMPTS[0])
        results.append((display_name, result))

        # Small delay between tests
        time.sleep(3)

    # Summary
    print("\n" + "="*60)
    print("📊 REPLICATE RESULTS")
    print("="*60)

    working = [name for name, result in results if result == "success"]
    rate_limited = [name for name, result in results if result == "rate_limited"]

    print(f"\n✅ Working: {len(working)}")
    if working:
        for name in working:
            print(f"  • {name}")

    print(f"\n💳 Rate Limited: {len(rate_limited)}")
    if rate_limited:
        for name in rate_limited:
            print(f"  • {name}")

    if not working:
        print("\n😔 All models rate limited")
        print("💡 Try again later or upgrade to paid tier")
        print("💡 Replicate has generous free limits normally")


if __name__ == "__main__":
    main()







