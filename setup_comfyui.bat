@echo off
echo 🎨 ComfyUI Setup Script for Wargame Pixel Art Generation
echo ========================================================
echo.

echo 🔍 Checking Python installation...
python --version
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.10+
    pause
    exit /b 1
)

echo ✅ Python found!

echo 📦 Checking existing packages...
python -c "import torch; print(f'✅ PyTorch {torch.__version__} already installed!')"

echo 📦 Installing additional required packages...
pip install diffusers transformers accelerate
pip install pillow psutil

echo 📦 Installing ComfyUI requirements...
pip install -r https://raw.githubusercontent.com/comfyanonymous/ComfyUI/master/requirements.txt

echo 🚀 Downloading ComfyUI...
if not exist ComfyUI (
    git clone https://github.com/comfyanonymous/ComfyUI
)

echo 📁 Setting up directories...
cd ComfyUI
if not exist models\checkpoints mkdir models\checkpoints
if not exist models\loras mkdir models\loras

echo 🎯 Creating pixel art workflow starter...
echo To get started:
echo 1. Download a model: https://civitai.com/models/4201/realistic-vision-v60-b1
echo 2. Place .safetensors file in: models\checkpoints\
echo 3. Run: python main.py
echo 4. Open: http://127.0.0.1:8188
echo 5. Copy prompts from: ../prompts_batch_1.txt
echo.

echo ✅ Setup complete! Ready to generate pixel art!
pause
