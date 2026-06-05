"""Test local image generation options"""

import os
import subprocess
import sys
from pathlib import Path

def check_local_options():
    """Check what local generation options are available."""

    print("🔬 CHECKING LOCAL IMAGE GENERATION OPTIONS")
    print("="*60)

    # Check if we have Python packages for local generation
    try:
        import diffusers
        print("✅ Diffusers library available")
        print("   Can run Stable Diffusion locally")
    except ImportError:
        print("❌ Diffusers not installed")
        print("   Install with: pip install diffusers torch")

    try:
        import torch
        print(f"✅ PyTorch available: {torch.__version__}")
        if torch.cuda.is_available():
            print(f"   GPU: {torch.cuda.get_device_name(0)}")
        else:
            print("   ⚠️  No GPU detected (will be slow)")
    except ImportError:
        print("❌ PyTorch not installed")

    # Check if we have ComfyUI or other tools
    comfyui_path = Path("ComfyUI")
    if comfyui_path.exists():
        print("✅ ComfyUI found locally")
    else:
        print("❌ ComfyUI not found")
        print("   Download from: https://github.com/comfyanonymous/ComfyUI")

    # Check system resources
    try:
        import psutil
        ram = psutil.virtual_memory()
        print(f"💾 RAM: {ram.total / 1024**3:.1f}GB")
        if ram.total < 8 * 1024**3:
            print("   ⚠️  Less than 8GB RAM - may struggle with larger models")
    except ImportError:
        print("⚠️  Can't check system resources")

    print("\n💡 LOCAL GENERATION OPTIONS:")
    print("   1. ComfyUI (most flexible)")
    print("   2. Stable Diffusion WebUI (easiest)")
    print("   3. Diffusers library (scriptable)")
    print("   4. Automatic1111 WebUI")

def setup_comfyui_workflow():
    """Show how to set up a ComfyUI workflow for pixel art."""

    print("\n🎨 COMFYUI PIXEL ART WORKFLOW:")
    print("="*60)

    print("1. Download ComfyUI:")
    print("   git clone https://github.com/comfyanonymous/ComfyUI")
    print("   cd ComfyUI")
    print("   pip install -r requirements.txt")

    print("\n2. Install pixel art models:")
    print("   - SD 1.5 base model")
    print("   - Pixel art LoRA or checkpoint")
    print("   - ControlNet for pixel art")

    print("\n3. Example workflow for pixel art:")
    print("   Load Base Model → Load Pixel Art LoRA →")
    print("   Positive Prompt: 'news anchor, pixel art, DB16 palette'")
    print("   Negative Prompt: 'photorealistic, smooth, gradients'")
    print("   Steps: 20, CFG: 7, Sampler: Euler a")

    print("\n4. Start ComfyUI:")
    print("   python main.py")
    print("   Open: http://127.0.0.1:8188")

def main():
    """Main check."""
    check_local_options()
    setup_comfyui_workflow()

    print("\n" + "="*60)
    print("🎯 RECOMMENDATIONS:")
    print("="*60)

    print("\n🚀 EASIEST TO SET UP:")
    print("   • Replicate API (if you get a token)")
    print("   • ComfyUI (most flexible for pixel art)")
    print("   • Leonardo.ai free tier")

    print("\n💰 FREE ALTERNATIVES:")
    print("   • Replicate: Generous free tier")
    print("   • Scaleway: Free until March 2025")
    print("   • Leonardo.ai: 150 daily tokens")
    print("   • Local generation: No limits")

    print("\n🎮 PIXEL ART SPECIFIC:")
    print("   • ComfyUI with pixel art LoRAs")
    print("   • Stable Diffusion with pixel art models")
    print("   • Use negative prompts to avoid realism")


if __name__ == "__main__":
    main()







