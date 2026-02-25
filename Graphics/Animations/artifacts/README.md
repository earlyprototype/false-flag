# Animation Artifacts

This folder stores timestamped snapshots of compiled scenes (and optionally assets) as an audit trail of the creative process.

Structure:
- `runs/YYYY-MM-DD_HH-MM-SS[_tag]/`
  - `compiled_scene.json`
  - `scene_schema.yaml`
  - `assets/` (optional, if `--include-assets` was used)
  - `meta.json`

Archive the current run:
```powershell
python -m Graphics.Animations.tools.archive_run compiled_scene.json `
  --scene Graphics/Animations/tools/scene_schema.yaml `
  --tag db16_nodither_32x32 `
  --include-assets
```


