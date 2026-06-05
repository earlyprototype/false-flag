"""Find all text-to-image models with inference: warm"""

import requests
import json
import time

# Get top 100 text-to-image models
api_url = "https://huggingface.co/api/models"
params = {
    "pipeline_tag": "text-to-image",
    "sort": "downloads",
    "direction": -1,
    "limit": 100
}

print("Fetching top 100 text-to-image models...")
response = requests.get(api_url, params=params, timeout=30)
models = response.json()

warm_models = []

print(f"\nChecking {len(models)} models for 'inference: warm' status...")
print("="*70)

for i, model in enumerate(models, 1):
    model_id = model['id']
    
    # Get detailed model info
    detail_response = requests.get(
        f"https://huggingface.co/api/models/{model_id}",
        timeout=30
    )
    
    if detail_response.status_code == 200:
        detail = detail_response.json()
        inference_status = detail.get('inference', None)
        
        if inference_status == 'warm':
            downloads = model.get('downloads', 0)
            likes = model.get('likes', 0)
            
            print(f"✅ {model_id}")
            print(f"   Downloads: {downloads:,}, Likes: {likes}")
            
            warm_models.append({
                'id': model_id,
                'downloads': downloads,
                'likes': likes
            })
    
    # Small delay to avoid rate limiting
    if i % 10 == 0:
        print(f"   ... checked {i}/{len(models)}")
        time.sleep(1)

print("\n" + "="*70)
print(f"TOTAL WARM MODELS FOUND: {len(warm_models)}")
print("="*70)

if warm_models:
    print("\nAll models with free inference API access:")
    for model in warm_models:
        print(f"  - {model['id']}")

