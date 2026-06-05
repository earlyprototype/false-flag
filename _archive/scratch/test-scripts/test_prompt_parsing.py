"""
Quick test to verify prompt parsing works correctly.
"""

import sys
from pathlib import Path

# Add tools directory to path
sys.path.append(str(Path("Graphics/Animations/tools")))
from generate_assets import parse_markdown_prompts

def test_parsing():
    """Test parsing of both prompt files."""
    
    prompt_files = [
        "Graphics/Animations/asset_generation_prompts.md",
        "Graphics/Animations/intro_sequence_prompts.md"
    ]
    
    all_assets = []
    
    for prompt_file in prompt_files:
        print(f"\n{'='*70}")
        print(f"Parsing: {prompt_file}")
        print(f"{'='*70}")
        
        try:
            assets = parse_markdown_prompts(prompt_file)
            print(f"[OK] Found {len(assets)} assets\n")
            
            for i, asset in enumerate(assets, 1):
                print(f"{i}. {asset.filename}")
                print(f"   Size: {asset.width}x{asset.height}")
                print(f"   Folder: {asset.folder_path}")
                print(f"   Priority: {asset.priority}")
                print(f"   Prompt length: {len(asset.prompt_text)} chars")
                print()
            
            all_assets.extend(assets)
            
        except Exception as e:
            print(f"[ERROR] parsing {prompt_file}: {e}")
    
    print(f"\n{'='*70}")
    print(f"TOTAL ASSETS: {len(all_assets)}")
    print(f"{'='*70}")
    
    # Group by folder
    by_folder = {}
    for asset in all_assets:
        folder = asset.folder_path
        if folder not in by_folder:
            by_folder[folder] = []
        by_folder[folder].append(asset)
    
    print(f"\nAssets by folder:")
    for folder, assets in sorted(by_folder.items()):
        print(f"  {folder}: {len(assets)} assets")

if __name__ == "__main__":
    test_parsing()

