"""
Automated pixel art asset generation using Hugging Face Inference API (FREE!).
Parses prompt files, generates images, and post-processes them to exact specifications.
"""

import os
import re
import sys
import time
import requests
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))
from image_processor import process_generated_image, save_with_transparency

# Universal style prompt to prepend to all asset prompts
UNIVERSAL_STYLE_PROMPT = """STYLE REQUIREMENTS: Classic LucasArts SCUMM engine adventure game aesthetic (1990-1995 era: The Secret of Monkey Island, Day of the Tentacle, Sam & Max Hit the Road, Full Throttle). MANDATORY specifications: DB16 palette ONLY (DawnBringer 16 colors - no other colors permitted), flat color fills with NO gradients, strong black pixel-perfect outlines on ALL shapes, NO anti-aliasing, NO blur, NO soft edges, sharp geometric forms, hand-drawn cartoon quality with bold readable silhouettes, expressive character design, clean composition suitable for VGA-era displays and modern CLI terminal rendering. Art style: comedic yet dramatic, exaggerated proportions, clear visual hierarchy, high contrast for readability. Technical: pixel-perfect edges, transparent PNG background where appropriate, exact dimensions as specified.

---

"""


class AssetPrompt:
    """Represents a single asset generation task."""
    
    def __init__(
        self,
        prompt_text: str,
        filename: str,
        dimensions: Tuple[int, int],
        folder_path: str,
        priority: str = "MEDIUM",
        source_file: str = ""
    ):
        self.prompt_text = prompt_text
        self.filename = filename
        self.width, self.height = dimensions
        self.folder_path = folder_path
        self.priority = priority
        self.source_file = source_file
    
    def get_full_prompt(self) -> str:
        """Return prompt with universal style requirements prepended."""
        return UNIVERSAL_STYLE_PROMPT + self.prompt_text
    
    def get_output_path(self, base_dir: str = "assets") -> str:
        """Get full output file path."""
        full_path = Path(base_dir) / self.folder_path / self.filename
        return str(full_path)
    
    def __repr__(self):
        return f"AssetPrompt({self.filename}, {self.width}×{self.height}, {self.folder_path})"


def extract_file_organization(content: str) -> Dict[str, str]:
    """
    Extract filename to folder path mapping from File Organization section.
    
    Returns:
        Dict mapping filename to folder path
    """
    file_map = {}
    
    # Look for File Organization section
    org_match = re.search(
        r'###\s+File Organization:.*?```(.*?)```',
        content,
        re.DOTALL | re.IGNORECASE
    )
    
    if not org_match:
        return file_map
    
    org_content = org_match.group(1)
    
    # Parse tree structure - simpler approach: track current path as we go
    lines = org_content.split('\n')
    path_stack = []  # Stack of directory names
    prev_depth = -1
    
    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue
        
        # Remove tree drawing characters to get the actual name
        name = re.sub(r'^[│├└─ \t]+', '', line).strip()
        
        if not name or name == 'assets' or name == 'assets/':
            continue
        
        # Calculate depth by counting leading spaces (4 spaces per level after assets/)
        # Count spaces before the first non-space/tree char
        stripped = line.lstrip()
        indent_len = len(line) - len(stripped)
        current_depth = max(0, (indent_len - 4) // 4)  # Adjust for assets/ being at indent 0
        
        if name.endswith('/'):
            # It's a directory
            dir_name = name.rstrip('/')
            
            # Adjust path_stack to current depth
            if current_depth > prev_depth:
                # Going deeper
                path_stack.append(dir_name)
            elif current_depth == prev_depth:
                # Same level - replace last
                if path_stack:
                    path_stack[-1] = dir_name
                else:
                    path_stack.append(dir_name)
            else:
                # Going shallower - pop back to depth and add
                path_stack = path_stack[:current_depth]
                path_stack.append(dir_name)
            
            prev_depth = current_depth
            
        elif name.endswith('.png'):
            # It's a file - record with current path
            filename = name
            if path_stack:
                folder_path = '/'.join(path_stack)
                file_map[filename] = folder_path
    
    return file_map


def parse_markdown_prompts(markdown_file: str) -> List[AssetPrompt]:
    """
    Parse a markdown prompt file and extract all asset generation tasks.
    
    Returns:
        List of AssetPrompt objects
    """
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    prompts = []
    
    # Extract file organization mapping (for files without explicit Folder: markers)
    file_org_map = extract_file_organization(content)
    
    # Pattern to match asset sections
    # Looks for: **Filename:** xxx.png followed by size info and prompt in ```
    pattern = r'\*\*Filename:\*\*\s+`([^`]+)`\s+\*\*(?:Size|Suggested size):\*\*\s+([0-9×x]+)\s+pixels?\s+.*?```\s*\n(.*?)\n```'
    
    matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        filename = match.group(1).strip()
        size_str = match.group(2).strip()
        prompt_text = match.group(3).strip()
        
        # Parse dimensions (handle both × and x)
        size_str = size_str.replace('×', 'x')
        if 'x' in size_str.lower():
            parts = size_str.lower().split('x')
            width = int(parts[0].strip())
            height = int(parts[1].strip())
        else:
            print(f"Warning: Could not parse dimensions from '{size_str}' for {filename}")
            continue
        
        # Try to find folder path (look backwards for **Folder:** marker)
        folder_match = re.search(
            r'\*\*Folder:\*\*\s+`([^`]+)`',
            content[:match.start()],
            re.IGNORECASE
        )
        
        if folder_match:
            # Get the last occurrence before this prompt
            all_folder_matches = list(re.finditer(
                r'\*\*Folder:\*\*\s+`([^`]+)`',
                content[:match.start()],
                re.IGNORECASE
            ))
            if all_folder_matches:
                folder_path = all_folder_matches[-1].group(1).strip()
            else:
                folder_path = file_org_map.get(filename, "unknown")
        else:
            # No explicit folder marker, check file organization map
            folder_path = file_org_map.get(filename, "unknown")
        
        # Fix paths for intro sequence files (prepend "intro/" if missing)
        if (folder_path.startswith("scene") or folder_path == "ui") and \
           os.path.basename(markdown_file) == "intro_sequence_prompts.md":
            folder_path = f"intro/{folder_path}"
        
        # Try to find priority
        priority_match = re.search(
            r'###\s+Priority:\s+(\w+)',
            content[:match.start()],
            re.IGNORECASE
        )
        priority = priority_match.group(1).upper() if priority_match else "MEDIUM"
        
        asset = AssetPrompt(
            prompt_text=prompt_text,
            filename=filename,
            dimensions=(width, height),
            folder_path=folder_path,
            priority=priority,
            source_file=os.path.basename(markdown_file)
        )
        
        prompts.append(asset)
    
    return prompts


def generate_image_huggingface(prompt: str, hf_token: str, model: str = "black-forest-labs/FLUX.1-schnell"):
    """
    Generate an image using Hugging Face Inference API (FREE!) with proper parameters.

    Args:
        prompt: Text prompt for image generation
        hf_token: Hugging Face API token
        model: Model ID to use (default: FLUX.1-schnell)

    Returns:
        PIL Image object if successful, "RATE_LIMIT" if rate limited, None if other error
    """
    try:
        api_url = f"https://api-inference.huggingface.co/models/{model}"
        headers = {"Authorization": f"Bearer {hf_token}"}

        # Proper API format with parameters (not just {"inputs": prompt})
        payload = {
            "inputs": prompt,
            "parameters": {
                "num_inference_steps": 4,  # FLUX schnell optimized for speed
                "guidance_scale": 3.5,     # FLUX recommended guidance
                "width": 1024,
                "height": 1024,
                "negative_prompt": "blurry, low quality, deformed, extra limbs, mutated, ugly, poorly drawn face, bad anatomy, watermark, text, signature, realistic, photorealistic, gradient, anti-aliasing, smooth edges"
            }
        }

        print(f"  📡 Generating with {model}...")
        start_time = time.time()

        # Make API request with proper parameters
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=120  # Longer timeout for image generation
        )

        elapsed = time.time() - start_time
        print(f"  ⏱️  API call took {elapsed:.1f}s")

        if response.status_code == 200:
            # Load image from response bytes
            image = Image.open(BytesIO(response.content))
            print(f"  ✅ Generated: {image.size}")
            return image

        elif response.status_code == 402:
            print(f"  💳 Rate limit exceeded: {response.text[:100]}")
            return "RATE_LIMIT"  # Special return value for rate limits

        elif response.status_code == 503:
            # Model is loading (cold start) - common on free tier
            print(f"  ⏳ Model loading (cold start), waiting 25 seconds...")
            time.sleep(25)

            # Retry after wait
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))
                print(f"  ✅ Generated after retry: {image.size}")
                return image
            else:
                print(f"  ✗ API error after retry: {response.status_code}")
                return None
        else:
            print(f"  ✗ API error {response.status_code}: {response.text[:200]}")
            return None

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None


def generate_asset(
    asset: AssetPrompt,
    api_key: str,
    base_output_dir: Path = Path("assets"),
    retry_count: int = 2
) -> bool:
    """
    Generate and process a single asset.
    
    Returns:
        True if successful, False otherwise
    """
    print(f"\n{'='*70}")
    print(f"📝 Asset: {asset.filename}")
    print(f"   Size: {asset.width}×{asset.height}")
    print(f"   Path: {asset.folder_path}")
    print(f"   Priority: {asset.priority}")
    print(f"{'='*70}")
    
    full_prompt = asset.get_full_prompt()
    
    # Try generation with retries
    for attempt in range(retry_count):
        if attempt > 0:
            print(f"  ⟳ Retry attempt {attempt + 1}/{retry_count}")
            time.sleep(2)  # Brief delay before retry
        
        print(f"  🎨 Generating image via Hugging Face API...")
        generated_image = generate_image_huggingface(full_prompt, api_key)

        if generated_image == "RATE_LIMIT":
            # Definite rate limit (402) - wait longer and retry
            print(f"  💳 Rate limit detected - waiting 60s before retry...")
            time.sleep(60)
            continue  # This will retry the loop
        elif generated_image is None:
            # Other error - don't retry immediately
            break

        if generated_image:
            print(f"  ✓ Image generated: {generated_image.size}")
            
            # Post-process image
            print(f"  🔧 Processing: resizing to {asset.width}×{asset.height} and applying DB16 palette...")
            processed_image = process_generated_image(
                generated_image,
                asset.width,
                asset.height,
                apply_db16=True
            )
            
            # Ensure output directory exists
            output_path = asset.get_output_path(base_output_dir)
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)
            
            # Save processed image
            save_with_transparency(processed_image, output_path)
            
            return True
    
    print(f"  ✗ Failed after {retry_count} attempts")
    return False


def main():
    """Main execution function."""
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv('HF_TOKEN') or os.getenv('HUGGINGFACE_TOKEN')
    
    if not api_key:
        print("="*70)
        print("  ❌ ERROR: HUGGING FACE TOKEN NOT FOUND")
        print("="*70)
        print("\nTo get a FREE token:")
        print("1. Go to: https://huggingface.co/settings/tokens")
        print("2. Create account (free)")
        print("3. Click 'New token' -> 'Read' access")
        print("4. Add to .env file:")
        print("   HF_TOKEN=your_token_here")
        print("\n" + "="*70)
        sys.exit(1)

    # Check if we're likely rate limited
    print("💡 FREE TIER LIMITS:")
    print("   • ~50-100 images per month")
    print("   • Rate limits reset monthly")
    print("   • If limited: wait or upgrade to PRO")
    print("   • Alternative: Use batch files for manual generation")
    print("="*70)
    
    print("="*70)
    print("  🎨 AUTOMATED PIXEL ART ASSET GENERATION")
    print("  🤖 API: Hugging Face (FREE!)")
    print("  ⚡ Model: FLUX.1 Schnell (2024, FAST)")
    print("  🎯 Palette: DB16 (DawnBringer 16)")
    print("  🕹️  Style: LucasArts SCUMM (1990-1995)")
    print("="*70)
    
    # Parse prompt files (relative to script directory)
    script_dir = Path(__file__).parent
    prompt_files = [
        script_dir.parent / "asset_generation_prompts.md",
        script_dir.parent / "intro_sequence_prompts.md"
    ]
    
    all_assets = []
    
    for prompt_file in prompt_files:
        if os.path.exists(prompt_file):
            print(f"\n📄 Parsing: {prompt_file}")
            assets = parse_markdown_prompts(prompt_file)
            print(f"   Found {len(assets)} assets")
            all_assets.extend(assets)
        else:
            print(f"\n⚠️  Warning: {prompt_file} not found, skipping")
    
    if not all_assets:
        print("\n❌ No assets found to generate!")
        sys.exit(1)
    
    print(f"\n📊 Total assets to generate: {len(all_assets)}")
    print(f"\n🚀 Starting generation...")

    # Track results
    successful = []
    failed = []

    # Add small delays between generations to avoid rate limits
    print(f"\n⚠️  Note: Free tier has rate limits. Adding delays between generations...")
    print(f"💡 Expected total time: ~{len(all_assets) * 15} minutes (with delays)")

    print(f"\n🚀 Starting generation...")
    print("="*70)

    # Set base output directory (project root / assets)
    project_root = script_dir.parent.parent.parent
    base_output_dir = project_root / "assets"

    print(f"\n📁 Output directory: {base_output_dir}")

    # Generate each asset
    start_time = time.time()

    for i, asset in enumerate(all_assets, 1):
        print(f"\n\n{'#'*70}")
        print(f"# Progress: {i}/{len(all_assets)}")
        print(f"{'#'*70}")
        
        success = generate_asset(asset, api_key, base_output_dir)
        
        if success:
            successful.append(asset)
        else:
            failed.append(asset)
        
        # Safe delay between generations to avoid rate limiting (free tier)
        if i < len(all_assets):
            delay = 5  # 5 seconds between generations
            print(f"⏳ Waiting {delay}s before next generation (rate limit protection)...")
            time.sleep(delay)
    
    # Summary
    elapsed = time.time() - start_time
    
    print(f"\n\n{'='*70}")
    print("  GENERATION COMPLETE")
    print(f"{'='*70}")
    print(f"✓ Successful: {len(successful)}/{len(all_assets)}")
    print(f"✗ Failed: {len(failed)}/{len(all_assets)}")
    print(f"⏱  Time elapsed: {elapsed:.1f} seconds")
    print(f"{'='*70}")
    
    if failed:
        print("\n❌ Failed assets:")
        for asset in failed:
            print(f"   - {asset.filename} ({asset.folder_path})")
        
        # Write failed list to file
        with open("failed_assets.txt", "w") as f:
            f.write("# Failed Asset Generation\n\n")
            for asset in failed:
                f.write(f"{asset.filename}\n")
                f.write(f"  Path: {asset.folder_path}\n")
                f.write(f"  Size: {asset.width}×{asset.height}\n")
                f.write(f"  Source: {asset.source_file}\n\n")
        
        print("\n📝 Failed assets logged to: failed_assets.txt")
    
    if successful:
        print(f"\n✅ Successfully generated {len(successful)} assets!")
        print(f"   Output directory: {base_output_dir}")


if __name__ == "__main__":
    main()

