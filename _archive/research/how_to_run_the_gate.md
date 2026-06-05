# How to run the gate (PowerShell)

- Activate the virtual environment
```powershell
cd "C:\Users\Fab2\Desktop\AI\wargame"
.\.venv\Scripts\activate
```

- Run the gate
```powershell
.\.venv\Scripts\python.exe scripts\gate_runner.py
```

- Expected success: JSON with empty arrays for `yaml`, `seed_smoke`, `icd`, `golden_mock_seed42`.

## Fixing a golden transcript mismatch
If you intentionally changed behaviour and the golden fails, regenerate the snapshot in UTF-8.

- Option A (recommended): use Out-File with UTF-8
```powershell
.\.venv\Scripts\python.exe -m cli.main --scenario war_game_2025 --seed 42 --leader llm |
  Out-File -Encoding utf8 Collaboration\golden\mock_seed42_scene1.txt
```

- Option B: Python one-liner
```powershell
.\.venv\Scripts\python.exe -c "from engine.sim_loop import run_single_scene; from pathlib import Path; t=run_single_scene('war_game_2025',42,'llm'); Path('Collaboration/golden/mock_seed42_scene1.txt').write_text('\n'.join(t), encoding='utf-8')"
```

## Determinism guardrails
Ensure the router uses the deterministic mock driver:
```powershell
Remove-Item Env:WARGAME_LLM -ErrorAction SilentlyContinue
# or
$env:WARGAME_LLM = 'mock'
```

## Quick verification
```powershell
Get-Content -TotalCount 10 .\Collaboration\golden\mock_seed42_scene1.txt
Select-String "Action taken:" .\Collaboration\golden\mock_seed42_scene1.txt
```

Only update the snapshot when transcript changes are intentional.
