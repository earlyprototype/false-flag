"""
Test multiple HuggingFace image generation models
to find the best one for pixel art
"""

import os
import time
from io import BytesIO
from PIL import Image
import requests
from dotenv import load_dotenv

# Test prompt (shorter for faster generation)
TEST_PROMPT = """
STYLE REQUIREMENTS: Classic LucasArts SCUMM engine adventure game aesthetic (1990-1995 era: The Secret of Monkey Island, Day of the Tentacle, Sam & Max Hit the Road, Full Throttle). MANDATORY specifications: DB16 palette ONLY (DawnBringer 16 colors - no other colors permitted), flat color fills with NO gradients, strong black pixel-perfect outlines on ALL shapes, NO anti-aliasing, NO blur, NO soft edges, sharp geometric forms, hand-drawn cartoon quality with bold readable silhouettes, expressive character design, clean composition suitable for VGA-era displays and modern CLI terminal rendering. Art style: comedic yet dramatic, exaggerated proportions, clear visual hierarchy, high contrast for readability. Technical: pixel-perfect edges, transparent PNG background where appropriate.

Generate: A serious news anchor character (male, business suit, clean-cut appearance, slight worry in expression) sitting at modern TV news desk with world map backdrop, 3/4 view, professional studio setting
"""

# Expanded list of models to test
MODELS_TO_TEST = [
    # FLUX variants (Black Forest Labs - 2024)
    ("black-forest-labs/FLUX.1-schnell", "FLUX.1 Schnell (2024, Fast)"),
    ("black-forest-labs/FLUX.1-dev", "FLUX.1 Dev (2024, Quality)"),
    
    # Stable Diffusion XL variants (2023)
    ("stabilityai/stable-diffusion-xl-base-1.0", "SDXL Base 1.0 (Popular)"),
    ("stabilityai/sdxl-turbo", "SDXL Turbo (Fast)"),
    ("stabilityai/stable-diffusion-2-1", "SD 2.1"),
    
    # Smaller/faster models
    ("segmind/SSD-1B", "SSD-1B (Smaller, Fast)"),
    ("segmind/Segmind-Vega", "Segmind Vega"),
    
    # Artistic/Stylized models
    ("prompthero/openjourney-v4", "OpenJourney v4 (Midjourney-style)"),
    ("playgroundai/playground-v2.5-1024px-aesthetic", "Playground v2.5"),
    ("Lykon/DreamShaper", "DreamShaper"),
    
    # Realism models
    ("SG161222/RealVisXL_V4.0", "RealVisXL v4.0"),
    
    # Classic Stable Diffusion
    ("runwayml/stable-diffusion-v1-5", "SD 1.5"),
    ("CompVis/stable-diffusion-v1-4", "SD 1.4"),
    
    # Anime/illustration
    ("Linaqruf/animagine-xl-3.1", "Animagine XL 3.1"),
    ("cagliostrolab/animagine-xl-3.0", "Animagine XL 3.0"),
    
    # Pixel art specific
    ("nerijs/pixel-art-xl", "Pixel Art XL"),
    
    # Other interesting models
    ("kandinsky-community/kandinsky-2-2-decoder", "Kandinsky 2.2"),
    ("DeepFloyd/IF-I-XL-v1.0", "DeepFloyd IF XL"),
    ("dataautogpt3/OpenDalleV1.1", "OpenDALLE v1.1"),
    ("digiplay/PixelArt_Diffusion", "PixelArt Diffusion"),
]


def test_model(model_id: str, model_name: str, hf_token: str) -> dict:
    """Test a single model and return results."""
    print(f"\n{'='*70}")
    print(f"Testing: {model_name}")
    print(f"Model ID: {model_id}")
    print('='*70)
    
    try:
        api_url = f"https://api-inference.huggingface.co/models/{model_id}"
        headers = {"Authorization": f"Bearer {hf_token}"}
        
        start_time = time.time()
        
        # Make API request
        response = requests.post(
            api_url,
            headers=headers,
            json={"inputs": TEST_PROMPT},
            timeout=120  # Longer timeout for slower models
        )
        
        # Handle cold start (503)
        if response.status_code == 503:
            print(f"  ⏳ Model loading (cold start), waiting 25 seconds...")
            time.sleep(25)
            
            response = requests.post(
                api_url,
                headers=headers,
                json={"inputs": TEST_PROMPT},
                timeout=120
            )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            # Success! Save the image
            image = Image.open(BytesIO(response.content))
            safe_name = model_id.replace('/', '_').replace('.', '_')
            filename = f"sample_{safe_name}.png"
            image.save(filename)
            
            print(f"  ✅ SUCCESS!")
            print(f"  Time: {elapsed:.1f}s")
            print(f"  Size: {image.size}")
            print(f"  Saved: {filename}")
            
            return {
                "model_id": model_id,
                "model_name": model_name,
                "status": "success",
                "time": elapsed,
                "size": image.size,
                "filename": filename
            }
        else:
            error_msg = response.text[:200]
            print(f"  ❌ FAILED: {response.status_code}")
            print(f"  Error: {error_msg}")
            
            return {
                "model_id": model_id,
                "model_name": model_name,
                "status": "failed",
                "error_code": response.status_code,
                "error": error_msg
            }
            
    except Exception as e:
        print(f"  ❌ EXCEPTION: {e}")
        return {
            "model_id": model_id,
            "model_name": model_name,
            "status": "exception",
            "error": str(e)
        }


def main():
    """Main execution."""
    load_dotenv()
    hf_token = os.getenv('HF_TOKEN') or os.getenv('HUGGINGFACE_TOKEN')
    
    if not hf_token:
        print("ERROR: No HF_TOKEN found in .env file!")
        return
    
    print("="*70)
    print("  TESTING MULTIPLE HUGGINGFACE IMAGE GENERATION MODELS")
    print(f"  Total models to test: {len(MODELS_TO_TEST)}")
    print("="*70)
    
    results = []
    
    for model_id, model_name in MODELS_TO_TEST:
        result = test_model(model_id, model_name, hf_token)
        results.append(result)
        time.sleep(2)  # Small delay between tests
    
    # Summary
    print("\n" + "="*70)
    print("RESULTS SUMMARY")
    print("="*70)
    
    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] != "success"]
    
    print(f"\n✅ Successful: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")
    
    if successful:
        print("\n" + "="*70)
        print("WORKING MODELS (sorted by speed):")
        print("="*70)
        successful.sort(key=lambda x: x["time"])
        
        for i, r in enumerate(successful, 1):
            print(f"\n{i}. {r['model_name']}")
            print(f"   Model ID: {r['model_id']}")
            print(f"   File: {r['filename']}")
            print(f"   Size: {r['size']}")
            print(f"   Time: {r['time']:.1f}s")
    
    if failed:
        print("\n" + "="*70)
        print("FAILED MODELS:")
        print("="*70)
        
        for r in failed:
            print(f"\n- {r['model_name']}")
            print(f"  ID: {r['model_id']}")
            if 'error_code' in r:
                print(f"  Error: {r['error_code']} - {r['error'][:100]}")
            else:
                print(f"  Error: {r['error'][:100]}")
    
    print("\n" + "="*70)
    print("CHECK THE GENERATED IMAGES TO SEE WHICH LOOKS BEST!")
    print("="*70)


if __name__ == "__main__":
    main()

