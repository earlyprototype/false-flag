"""Compare inference status between working and non-working models"""

import requests
import json

models = {
    "Working": [
        "black-forest-labs/FLUX.1-schnell",
        "black-forest-labs/FLUX.1-dev",
        "stabilityai/stable-diffusion-xl-base-1.0"
    ],
    "Not Working": [
        "stable-diffusion-v1-5/stable-diffusion-v1-5",
        "stabilityai/stable-diffusion-2-1",
        "CompVis/stable-diffusion-v1-4",
        "playgroundai/playground-v2.5-1024px-aesthetic"
    ]
}

for category, model_list in models.items():
    print(f"\n{'='*70}")
    print(f"{category} Models:")
    print('='*70)
    
    for model_id in model_list:
        response = requests.get(
            f"https://huggingface.co/api/models/{model_id}",
            timeout=30
        )
        
        if response.status_code == 200:
            info = response.json()
            print(f"\n{model_id}:")
            print(f"  inference: {info.get('inference', 'NOT SPECIFIED')}")
            print(f"  pipeline_tag: {info.get('pipeline_tag', 'NOT SPECIFIED')}")
            
            # Check for specific inference config
            if 'config' in info:
                print(f"  config keys: {list(info['config'].keys())}")
        else:
            print(f"\n{model_id}: API Error {response.status_code}")

