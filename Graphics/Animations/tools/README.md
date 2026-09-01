# Asset Generation Tool

`generate_assets.py` parses the two prompt documents in
`Graphics/Animations/`, calls the Hugging Face Inference API, then resizes and
quantises returned images through `image_processor.py`.

## Current contract

- Provider: Hugging Face Inference API.
- Default model: `black-forest-labs/FLUX.1-schnell`.
- Credentials: `HF_TOKEN` or `HUGGINGFACE_TOKEN`.
- Inputs: `asset_generation_prompts.md` and `intro_sequence_prompts.md`.
- Output: the repository-root `assets/` directory; failed names are written to
  `failed_assets.txt` in the launch directory.

The script calls `load_dotenv()`, so a local `.env` file works for this tool.
Do not commit that file or its token. Model access, pricing, quotas and latency
are account-dependent and must be checked with Hugging Face at run time.

## Run

The tool dependencies are not fully pinned by the game requirements. Install
them in the active environment, then launch from the repository root:

```powershell
.\.venv\Scripts\pip.exe install python-dotenv requests pillow numpy
$env:HF_TOKEN = "hf_..."
.\.venv\Scripts\python.exe Graphics\Animations\tools\generate_assets.py
```

Review generated files before using them. The script enforces dimensions and a
DB16 palette after generation; that does not guarantee artistic or content
fitness.
