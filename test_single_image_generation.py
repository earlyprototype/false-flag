"""
Quick test to verify Gemini 2.5 Flash Image generation works with the SDK.
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
from io import BytesIO

# Load API key
load_dotenv()
api_key = os.getenv('GOOGLE_API_KEY')

if not api_key:
    print("ERROR: GOOGLE_API_KEY not found in .env file")
    exit(1)

print("Testing Gemini 2.5 Flash Image generation...")
print("="*70)

# Configure API
genai.configure(api_key=api_key)

# Test prompt (simple)
test_prompt = """STYLE REQUIREMENTS: Classic LucasArts SCUMM engine adventure game aesthetic (1990-1995 era: The Secret of Monkey Island, Day of the Tentacle, Sam & Max Hit the Road, Full Throttle). MANDATORY specifications: DB16 palette ONLY (DawnBringer 16 colors - no other colors permitted), flat color fills with NO gradients, strong black pixel-perfect outlines on ALL shapes, NO anti-aliasing, NO blur, NO soft edges, sharp geometric forms, hand-drawn cartoon quality with bold readable silhouettes, expressive character design, clean composition suitable for VGA-era displays and modern CLI terminal rendering. Art style: comedic yet dramatic, exaggerated proportions, clear visual hierarchy, high contrast for readability. Technical: pixel-perfect edges, transparent PNG background where appropriate, exact dimensions as specified.

---

16x16 pixel art icon, red dot or diamond, Russian forces symbol, DB16 palette (DawnBringer 16 colors), bright red color, clean geometric design, LucasArts tactical UI style, suitable for pulsing animation on map, retro gaming aesthetic"""

print(f"Prompt: {test_prompt[:100]}...")
print("\nGenerating image...")

try:
    # Create model with image generation config
    generation_config = {
        "temperature": 0.4,
        "top_p": 1.0,
        "top_k": 32,
        "max_output_tokens": 8192,
        "response_modalities": ["IMAGE"],
    }
    
    # Try gemini-2.0-flash-exp (free tier experimental model)
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        generation_config=generation_config
    )
    
    # Generate
    response = model.generate_content(test_prompt)
    
    print(f"Response received!")
    print(f"  Candidates: {len(response.candidates) if hasattr(response, 'candidates') else 0}")
    
    # Try to extract image
    if hasattr(response, 'candidates') and len(response.candidates) > 0:
        candidate = response.candidates[0]
        print(f"  Candidate content parts: {len(candidate.content.parts) if hasattr(candidate.content, 'parts') else 0}")
        
        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
            for i, part in enumerate(candidate.content.parts):
                print(f"  Part {i}: {type(part)}")
                
                # Check for inline image data
                if hasattr(part, 'inline_data') and part.inline_data:
                    print(f"    Found inline_data!")
                    image_bytes = part.inline_data.data
                    image = Image.open(BytesIO(image_bytes))
                    
                    print(f"\nSUCCESS!")
                    print(f"  Image size: {image.size}")
                    print(f"  Image mode: {image.mode}")
                    
                    # Save test image
                    image.save('test_generated_image.png')
                    print(f"  Saved to: test_generated_image.png")
                    
                    exit(0)
                
                # Check for text (might be error message)
                if hasattr(part, 'text'):
                    print(f"    Text content: {part.text[:200]}")
    
    print("\nNo image data found in response")
    print(f"Full response: {response}")
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()

