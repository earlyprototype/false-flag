"""Quick script to fetch available Gemini models from Google API."""

import google.generativeai as genai
import os

# Get API key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    try:
        import config
        api_key = getattr(config, "GOOGLE_API_KEY", None)
    except ImportError:
        pass

if not api_key:
    print("ERROR: GOOGLE_API_KEY not found")
    exit(1)

genai.configure(api_key=api_key)

print("=" * 80)
print("AVAILABLE GEMINI MODELS (Text Generation)")
print("=" * 80)
print()

# List all models
all_models = genai.list_models()

text_gen_models = []
for model in all_models:
    # Filter for text generation models (support generateContent)
    if 'generateContent' in model.supported_generation_methods:
        # Focus on Gemini models (not Imagen, embedding, etc.)
        if 'gemini' in model.name.lower():
            text_gen_models.append(model)

# Sort by name
text_gen_models.sort(key=lambda m: m.name)

print(f"Found {len(text_gen_models)} Gemini text generation models:\n")

for model in text_gen_models:
    model_id = model.name.replace('models/', '')
    
    # Get display name if available
    display_name = getattr(model, 'display_name', 'N/A')
    
    # Check if it's a flash model (faster)
    is_flash = 'flash' in model_id.lower()
    speed_marker = " ⚡" if is_flash else ""
    
    print(f"• {model_id}{speed_marker}")
    if display_name != 'N/A':
        print(f"  Display: {display_name}")
    
    # Show supported methods
    methods = model.supported_generation_methods
    if 'batchGenerateContent' in methods:
        print(f"  ✓ Supports batch/parallel generation")
    
    print()

print("=" * 80)
print("\nRECOMMENDATIONS FOR MULTI-AGENT SIMULATION:")
print()
print("FASTEST:")
print("  • gemini-2.5-flash-lite")
print("  • gemini-2.0-flash-lite-001")
print()
print("BALANCED (Current):")
print("  • gemini-2.5-flash ⭐")
print("  • gemini-2.0-flash-001")
print()
print("HIGHEST QUALITY:")
print("  • gemini-2.5-pro")
print()
print("=" * 80)


