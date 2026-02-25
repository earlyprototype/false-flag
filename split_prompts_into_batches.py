"""
Split the prompts file into batches of max 9 images for easier manual generation.
"""

import re

# Read the full prompts file
with open('prompts_for_manual_generation.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Split by asset markers
assets = re.split(r'={80}\nASSET #\d+/32\n={80}', content)

# First part is header
header = assets[0]
asset_prompts = assets[1:]  # Remove header

print(f"Found {len(asset_prompts)} assets")

# Split into batches of 9
batch_size = 9
batches = []
for i in range(0, len(asset_prompts), batch_size):
    batch = asset_prompts[i:i + batch_size]
    batches.append(batch)

print(f"Creating {len(batches)} batches")

# Create batch files
for batch_num, batch in enumerate(batches, 1):
    batch_file = f"prompts_batch_{batch_num}.txt"
    
    with open(batch_file, 'w', encoding='utf-8') as f:
        # Write batch header
        f.write("="*80 + "\n")
        f.write(f"  PIXEL ART ASSET GENERATION PROMPTS - BATCH {batch_num}/{len(batches)}\n")
        f.write(f"  Assets in this batch: {len(batch)}\n")
        f.write(f"  Total assets: {len(asset_prompts)}\n")
        f.write("  Style: LucasArts SCUMM (1990-1995)\n")
        f.write("  Palette: DB16 (DawnBringer 16)\n")
        f.write("="*80 + "\n")
        
        # Write assets in this batch
        for asset_num, asset_content in enumerate(batch, 1):
            global_num = (batch_num - 1) * batch_size + asset_num
            f.write("\n\n")
            f.write("="*80 + "\n")
            f.write(f"ASSET #{asset_num}/{len(batch)} (Global: #{global_num}/{len(asset_prompts)})\n")
            f.write("="*80 + "\n")
            f.write(asset_content)
    
    print(f"✓ Created: {batch_file} ({len(batch)} assets)")

print(f"\n✅ Done! Created {len(batches)} batch files")
print(f"\nBatch breakdown:")
for i, batch in enumerate(batches, 1):
    start = (i-1) * batch_size + 1
    end = start + len(batch) - 1
    print(f"  Batch {i}: Assets {start}-{end} ({len(batch)} total)")

