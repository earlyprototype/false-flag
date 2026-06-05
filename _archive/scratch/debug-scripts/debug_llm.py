import os
import sys
import random
import traceback

# Ensure root is in path
sys.path.append(os.getcwd())

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

print("--- LLM DIAGNOSTIC TOOL ---")

# 1. Check Environment
print(f"Current working directory: {os.getcwd()}")
try:
    import config
    print(f"Config found. LLM_PROVIDER = {getattr(config, 'LLM_PROVIDER', 'Not Set')}")
    key = getattr(config, 'GOOGLE_API_KEY', '')
    print(f"API Key found: {'Yes' if key else 'No'} (Length: {len(key)})")
except ImportError:
    print("ERROR: config.py not found!")

# 2. Test Generation
print("\nTesting generation...")
try:
    from llm.router import generate_text
    
    rng = random.Random(42)
    response = generate_text("Explain why the sky is blue in one sentence.", rng, show_spinner=False)
    print(f"\n[RESPONSE]: {response}")
    
    if "mock" in response.lower() or "[LLM response" in response:
        print("\n[WARNING] Output looks like MOCK data. Check driver initialization.")
    else:
        print("\n[SUCCESS] Real LLM response received.")
        
except Exception as e:
    print(f"\n[CRITICAL ERROR] Generation failed: {e}")
    traceback.print_exc()


