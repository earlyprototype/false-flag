import json

with open('available_text_to_image_models.json') as f:
    data = json.load(f)

models_to_check = [
    'stable-diffusion-v1-5/stable-diffusion-v1-5',
    'stabilityai/stable-diffusion-2-1', 
    'CompVis/stable-diffusion-v1-4',
    'playgroundai/playground-v2.5-1024px-aesthetic',
    'SG161222/RealVisXL_V4.0'
]

for model in data:
    if model['id'] in models_to_check:
        print(f"\n{model['id']}:")
        print(f"  Gated: {model.get('gated', 'Not specified')}")
        print(f"  Private: {model.get('private', False)}")
        print(f"  Disabled: {model.get('disabled', False)}")
        print(f"  Tags: {', '.join(model.get('tags', [])[:8])}")

