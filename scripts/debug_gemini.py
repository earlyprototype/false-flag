
print("Start")
import sys
print(f"Python: {sys.version}")
try:
    import google.generativeai as genai
    print("GenAI imported")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
print("Done")
