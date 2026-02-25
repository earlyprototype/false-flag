"""
Simple batch image generation using Diffusers library.
Alternative to ComfyUI if you want code-based generation.
"""

import os
import re
from pathlib import Path
from PIL import Image
import torch
from diffusers import StableDiffusionPipeline

def parse_batch_file(batch_file: str) -> list:
    """Parse a batch file and extract prompts."""
    assets = []

    with open(batch_file, 'r') as f:
        content = f.read()

    # Split by asset sections
    sections = re.split(r'={80,}', content)

    for section in sections:
        if 'FULL PROMPT' in section and 'Filename:' in section:
            # Extract filename
            filename_match = re.search(r'Filename:\s*(.+?)\.png', section)
            if not filename_match:
                continue

            filename = filename_match.group(1) + '.png'

            # Extract dimensions
            dim_match = re.search(r'Dimensions:\s*(\d+)x(\d+)', section)
            if dim_match:
                width, height = int(dim_match.group(1)), int(dim_match.group(2))
            else:
                width, height = 512, 512

            # Extract folder path
            path_match = re.search(r'Save to:\s*(.+?)/', section)
            folder_path = path_match.group(1) if path_match else 'assets'

            # Extract prompt (between FULL PROMPT and END OF PROMPT)
            prompt_match = re.search(
                r'FULL PROMPT.*?:(.*?)-{10,}(.*?)-{10,}',
                section,
                re.DOTALL
            )

            if prompt_match:
                prompt_text = prompt_match.group(2).strip()
                assets.append({
                    'filename': filename,
                    'prompt': prompt_text,
                    'width': width,
                    'height': height,
                    'folder': folder_path
                })

    return assets

def generate_image_with_diffusers(prompt: str, width: int = 512, height: int = 512):
    """Generate image using Diffusers."""
    try:
        print(f"🎨 Generating: {width}x{height}")

        # Load model (you'll need to download one first)
        # pipe = StableDiffusionPipeline.from_pretrained(
        #     "SG161222/RealVisXL_V4.0",
        #     torch_dtype=torch.float32  # CPU only
        # )

        # For now, create a placeholder
        print("⚠️  Model not loaded - install a checkpoint first!")
        print("   Download from: https://civitai.com/models/4201/realistic-vision-v60-b1")

        return None

    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Process batch files and generate images."""
    print("🎨 BATCH IMAGE GENERATION")
    print("="*50)

    # Find batch files
    batch_files = [
        "prompts_batch_1.txt",
        "prompts_batch_2.txt",
        "prompts_batch_3.txt",
        "prompts_batch_4.txt"
    ]

    all_assets = []

    for batch_file in batch_files:
        if os.path.exists(batch_file):
            print(f"\n📄 Parsing: {batch_file}")
            assets = parse_batch_file(batch_file)
            print(f"   Found {len(assets)} assets")
            all_assets.extend(assets)

    if not all_assets:
        print("❌ No assets found!")
        return

    print(f"\n📊 Total assets to generate: {len(all_assets)}")

    # Generate each asset
    for i, asset in enumerate(all_assets, 1):
        print(f"\n{'='*50}")
        print(f"Asset {i}/{len(all_assets)}: {asset['filename']}")
        print(f"Size: {asset['width']}x{asset['height']}")
        print(f"Path: {asset['folder']}")
        print('='*50)

        # Generate image
        image = generate_image_with_diffusers(
            asset['prompt'],
            asset['width'],
            asset['height']
        )

        if image:
            # Ensure output directory exists
            output_dir = Path(asset['folder'])
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save image
            output_path = output_dir / asset['filename']
            image.save(output_path)
            print(f"✅ Saved: {output_path}")
        else:
            print(f"❌ Failed to generate: {asset['filename']}")

    print(f"\n🎉 Batch generation complete!")
    print(f"📁 Check output directories for generated images")

if __name__ == "__main__":
    main()







