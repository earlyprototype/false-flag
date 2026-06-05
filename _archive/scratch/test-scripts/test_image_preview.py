"""
Test gemini-2.5-flash-image-preview model
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
from io import BytesIO

# Load API key
load_dotenv()
api_key = os.getenv('GOOGLE_API_KEY')

print("Testing gemini-2.5-flash-image-preview...")
print("="*70)

# Configure API
genai.configure(api_key=api_key)

# Simple test prompt
test_prompt = "A simple red dot, 16x16 pixels, pixel art style, DB16 palette"

print(f"Prompt: {test_prompt}\n")

try:
    # Create model with image generation config
    generation_config = {
        "temperature": 0.4,
        "top_p": 1.0,
        "top_k": 32,
        "max_output_tokens": 8192,
        "response_modalities": ["IMAGE"],
    }
    
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash-image-preview",
        generation_config=generation_config
    )
    
    print("Generating...")
    response = model.generate_content(test_prompt)
    
    print("SUCCESS! Response received")
    
    # Extract image
    if hasattr(response, 'candidates') and len(response.candidates) > 0:
        candidate = response.candidates[0]
        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
            for part in candidate.content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    image_bytes = part.inline_data.data
                    image = Image.open(BytesIO(image_bytes))
                    
                    print(f"Image generated!")
                    print(f"  Size: {image.size}")
                    print(f"  Mode: {image.mode}")
                    
                    image.save('test_preview_image.png')
                    print(f"  Saved: test_preview_image.png")
                    exit(0)
    
    print("No image in response")
    
except Exception as e:
    print(f"ERROR: {e}")

