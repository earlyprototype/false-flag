"""Analyze what makes the 4 working models special"""

import requests
import json

WORKING = [
    "black-forest-labs/FLUX.1-schnell",
    "black-forest-labs/FLUX.1-dev",
    "stabilityai/stable-diffusion-xl-base-1.0",
    "stabilityai/stable-diffusion-3-medium-diffusers"
]

NOT_WORKING_BUT_WARM = [
    "stabilityai/stable-diffusion-3.5-large",
    "Qwen/Qwen-Image",
    "ByteDance/SDXL-Lightning",
    "tencent/HunyuanImage-3.0"
]

def analyze_model(model_id):
    """Get full model details."""
    response = requests.get(
        f"https://huggingface.co/api/models/{model_id}",
        timeout=30
    )
    
    if response.status_code == 200:
        return response.json()
    return None

print("="*70)
print("ANALYZING WORKING MODELS")
print("="*70)

for model_id in WORKING:
    info = analyze_model(model_id)
    if info:
        print(f"\n{model_id}:")
        print(f"  inference: {info.get('inference')}")
        print(f"  library_name: {info.get('library_name')}")
        print(f"  pipeline_tag: {info.get('pipeline_tag')}")
        
        # Check config
        config = info.get('config', {})
        if config:
            print(f"  config keys: {list(config.keys())}")
            if 'diffusers' in config:
                print(f"    diffusers pipeline: {config['diffusers']}")
        
        # Check if there's a specific inference config
        if 'inference' in info and isinstance(info['inference'], dict):
            print(f"  inference config: {info['inference']}")

print("\n" + "="*70)
print("ANALYZING NON-WORKING (BUT WARM) MODELS")
print("="*70)

for model_id in NOT_WORKING_BUT_WARM:
    info = analyze_model(model_id)
    if info:
        print(f"\n{model_id}:")
        print(f"  inference: {info.get('inference')}")
        print(f"  library_name: {info.get('library_name')}")
        print(f"  pipeline_tag: {info.get('pipeline_tag')}")
        
        config = info.get('config', {})
        if config:
            print(f"  config keys: {list(config.keys())}")
            if 'diffusers' in config:
                print(f"    diffusers pipeline: {config['diffusers']}")
        
        if 'inference' in info and isinstance(info['inference'], dict):
            print(f"  inference config: {info['inference']}")

