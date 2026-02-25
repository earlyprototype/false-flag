"""
Export all asset prompts to a text file for manual image generation.
Useful when API generation isn't available.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))
from generate_assets import parse_markdown_prompts, UNIVERSAL_STYLE_PROMPT

def export_prompts_to_file(output_file="prompts_for_manual_generation.txt"):
    """Export all prompts with full style requirements to a text file."""
    
    # Parse prompt files
    script_dir = Path(__file__).parent
    prompt_files = [
        script_dir.parent / "asset_generation_prompts.md",
        script_dir.parent / "intro_sequence_prompts.md"
    ]
    
    all_assets = []
    
    for prompt_file in prompt_files:
        if prompt_file.exists():
            assets = parse_markdown_prompts(str(prompt_file))
            all_assets.extend(assets)
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("  PIXEL ART ASSET GENERATION PROMPTS\n")
        f.write("  Total Assets: {}\n".format(len(all_assets)))
        f.write("  Style: LucasArts SCUMM (1990-1995)\n")
        f.write("  Palette: DB16 (DawnBringer 16)\n")
        f.write("="*80 + "\n\n")
        
        for i, asset in enumerate(all_assets, 1):
            f.write(f"\n{'='*80}\n")
            f.write(f"ASSET #{i}/{len(all_assets)}\n")
            f.write(f"{'='*80}\n\n")
            f.write(f"Filename: {asset.filename}\n")
            f.write(f"Dimensions: {asset.width}x{asset.height} pixels\n")
            f.write(f"Save to: assets/{asset.folder_path}/\n")
            f.write(f"Priority: {asset.priority}\n")
            f.write(f"\n{'-'*80}\n")
            f.write(f"FULL PROMPT (copy everything below this line):\n")
            f.write(f"{'-'*80}\n\n")
            f.write(asset.get_full_prompt())
            f.write(f"\n\n{'-'*80}\n")
            f.write(f"END OF PROMPT FOR {asset.filename}\n")
            f.write(f"{'-'*80}\n\n\n")
    
    print(f"[OK] Exported {len(all_assets)} prompts to: {output_file}")
    print(f"\nYou can now:")
    print(f"  1. Open {output_file}")
    print(f"  2. Copy each prompt (between the dashed lines)")
    print(f"  3. Paste into your image generation service")
    print(f"  4. Download and save to the specified folder with the specified filename")

if __name__ == "__main__":
    export_prompts_to_file()

