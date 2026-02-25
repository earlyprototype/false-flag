"""
Query HuggingFace API to find ACTUALLY available text-to-image models
"""

import requests
import json

def find_text_to_image_models():
    """Query HF API for available text-to-image models."""
    
    print("="*70)
    print("  QUERYING HUGGINGFACE API FOR AVAILABLE MODELS")
    print("="*70)
    
    # HuggingFace API endpoint for listing models
    api_url = "https://huggingface.co/api/models"
    
    params = {
        "pipeline_tag": "text-to-image",  # Filter by task
        "sort": "downloads",  # Sort by most popular
        "direction": -1,  # Descending
        "limit": 50  # Get top 50
    }
    
    try:
        response = requests.get(api_url, params=params, timeout=30)
        
        if response.status_code == 200:
            models = response.json()
            
            print(f"\n✅ Found {len(models)} text-to-image models")
            print("\n" + "="*70)
            print("TOP TEXT-TO-IMAGE MODELS (by downloads):")
            print("="*70)
            
            for i, model in enumerate(models, 1):
                model_id = model.get('id', 'Unknown')
                downloads = model.get('downloads', 0)
                likes = model.get('likes', 0)
                
                # Check if it has inference API enabled
                inference_api = "inference" in model.get('tags', [])
                
                print(f"\n{i}. {model_id}")
                print(f"   Downloads: {downloads:,}")
                print(f"   Likes: {likes}")
                print(f"   Inference API: {'✅ YES' if inference_api else '❌ NO'}")
                
                # Show tags
                tags = model.get('tags', [])
                if tags:
                    print(f"   Tags: {', '.join(tags[:5])}")
            
            # Save to file
            with open("available_text_to_image_models.json", "w") as f:
                json.dump(models, f, indent=2)
            
            print("\n" + "="*70)
            print("✅ Full list saved to: available_text_to_image_models.json")
            print("="*70)
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text[:500])
            
    except Exception as e:
        print(f"❌ Exception: {e}")


if __name__ == "__main__":
    find_text_to_image_models()

