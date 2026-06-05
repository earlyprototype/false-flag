"""List all available Google image generation models via Gemini API."""

import os
from dotenv import load_dotenv

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    print("❌ google-generativeai not installed")
    print("Install with: pip install google-generativeai")
    GENAI_AVAILABLE = False
    exit(1)

def list_image_models():
    """List all available image generation models from Google."""
    load_dotenv()
    
    # Get API key
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        try:
            import config
            api_key = getattr(config, "GOOGLE_API_KEY", None)
        except ImportError:
            pass
    
    if not api_key:
        print("❌ No GOOGLE_API_KEY found in environment or config.py")
        print("Get your API key from: https://aistudio.google.com/apikey")
        return
    
    genai.configure(api_key=api_key)
    
    print("=" * 80)
    print("GOOGLE IMAGE GENERATION MODELS")
    print("=" * 80)
    print()
    
    # List all models
    print("📋 Fetching available models from Google API...")
    print()
    
    try:
        models = genai.list_models()
        
        image_models = []
        text_models = []
        other_models = []
        
        for model in models:
            # Check if model supports image generation
            if hasattr(model, 'supported_generation_methods'):
                methods = model.supported_generation_methods
                
                # Image generation models
                if 'generateImages' in methods or 'image' in model.name.lower():
                    image_models.append(model)
                # Text generation models
                elif 'generateContent' in methods:
                    text_models.append(model)
                else:
                    other_models.append(model)
        
        # Display image generation models
        if image_models:
            print("🎨 IMAGE GENERATION MODELS")
            print("-" * 80)
            for model in image_models:
                print(f"\n✅ {model.name}")
                if hasattr(model, 'display_name'):
                    print(f"   Display Name: {model.display_name}")
                if hasattr(model, 'description'):
                    print(f"   Description: {model.description}")
                if hasattr(model, 'supported_generation_methods'):
                    print(f"   Methods: {', '.join(model.supported_generation_methods)}")
                if hasattr(model, 'input_token_limit'):
                    print(f"   Input Token Limit: {model.input_token_limit}")
                if hasattr(model, 'output_token_limit'):
                    print(f"   Output Token Limit: {model.output_token_limit}")
            print()
        else:
            print("⚠️  No dedicated image generation models found in API response")
            print()
        
        # Display text generation models (for reference)
        print("\n📝 TEXT GENERATION MODELS (for reference)")
        print("-" * 80)
        for model in text_models[:5]:  # Show first 5
            print(f"  • {model.name}")
        if len(text_models) > 5:
            print(f"  ... and {len(text_models) - 5} more")
        print()
        
        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Image Generation Models: {len(image_models)}")
        print(f"Text Generation Models: {len(text_models)}")
        print(f"Other Models: {len(other_models)}")
        print(f"Total Models: {len(list(models))}")
        
        # Model names for copy-paste
        if image_models:
            print("\n📋 MODEL NAMES (for copy-paste):")
            print("-" * 80)
            for model in image_models:
                print(f"  {model.name}")
        
        print()
        print("=" * 80)
        print()
        
        # Additional info about Imagen
        print("ℹ️  IMAGEN INFORMATION")
        print("-" * 80)
        print()
        print("According to Google's documentation, Imagen models may be accessed via:")
        print("  • Vertex AI API (requires GCP project)")
        print("  • Gemini API (via AI Studio)")
        print()
        print("Model naming convention:")
        print("  • imagen-3.0-generate-001")
        print("  • imagen-3.0-fast-generate-001")
        print("  • imagen-4.0-generate-001")
        print("  • imagen-4.0-ultra-001")
        print()
        print("⚠️  Note: Some models may require separate API access or GCP setup")
        print()
        
    except Exception as e:
        print(f"❌ Error fetching models: {e}")
        print()
        print("This might mean:")
        print("  1. API key is invalid")
        print("  2. Network connection issue")
        print("  3. API endpoint changed")
        print()
        import traceback
        print("Full error:")
        traceback.print_exc()


if __name__ == "__main__":
    if GENAI_AVAILABLE:
        list_image_models()

