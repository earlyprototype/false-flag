"""Debug why certain models return 404"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
hf_token = os.getenv('HF_TOKEN') or os.getenv('HUGGINGFACE_TOKEN')

# Test a model that returned 404
model_id = "stable-diffusion-v1-5/stable-diffusion-v1-5"

api_url = f"https://api-inference.huggingface.co/models/{model_id}"
headers = {"Authorization": f"Bearer {hf_token}"}

print(f"Testing: {model_id}")
print(f"URL: {api_url}")
print("=" * 70)

# Try with a simple prompt
response = requests.post(
    api_url,
    headers=headers,
    json={"inputs": "a red apple"},
    timeout=30
)

print(f"Status Code: {response.status_code}")
print(f"Headers: {dict(response.headers)}")
print(f"\nFull Response:")
print(response.text)
print("\n" + "=" * 70)

# Also try getting model info
info_response = requests.get(
    f"https://huggingface.co/api/models/{model_id}",
    timeout=30
)
print(f"\nModel Info Status: {info_response.status_code}")
if info_response.status_code == 200:
    import json
    info = info_response.json()
    print(f"  Inference Status: {info.get('inference', 'Not specified')}")
    print(f"  Pipeline Tag: {info.get('pipeline_tag', 'Not specified')}")

