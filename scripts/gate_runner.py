import json
import os
import subprocess
import sys
from pathlib import Path
import sys as _sys

ROOT = Path(__file__).resolve().parents[1]


def run_cmd(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = proc.communicate()
    return proc.returncode, out, err


def validate_yaml() -> list[str]:
    errors: list[str] = []
    # Basic existence checks
    scenario_dir = ROOT / "data" / "scenarios" / "war_game_2025"
    if not (scenario_dir / "initial_conditions.yaml").exists():
        errors.append("Missing initial_conditions.yaml")
    if not (scenario_dir / "events.yaml").exists():
        errors.append("Missing events.yaml")
    # Asset reference check (naive)
    try:
        content = (scenario_dir / "events.yaml").read_text(encoding="utf-8")
        for raw in content.splitlines():
            line = raw.strip()
            if line.startswith("image:"):
                path = line.split(":", 1)[1].strip()
                # strip quotes if any
                if (path.startswith('"') and path.endswith('"')) or (path.startswith("'") and path.endswith("'")):
                    path = path[1:-1]
                if not path.endswith(".md"):
                    errors.append(f"Asset must be .md: {path}")
                p = ROOT / path
                if not p.exists():
                    errors.append(f"Missing asset: {path}")
    except Exception as e:
        errors.append(f"Unable to read events.yaml: {e}")
    return errors


def seed_smoke() -> list[str]:
    errors: list[str] = []
    # Direct import to avoid CLI invocation issues
    try:
        # Ensure project root is importable when script runs from scripts/
        if str(ROOT) not in _sys.path:
            _sys.path.insert(0, str(ROOT))
        from engine.sim_loop import run_single_scene  # type: ignore
        transcript = run_single_scene(scenario_id="war_game_2025", seed=42, leader_mode="llm")
        joined = "\n".join(transcript)
        if "Action taken:" not in joined:
            errors.append("Expected an action to be taken in llm mode")
    except Exception as e:
        errors.append(f"Engine import/run failed: {e}")
    return errors


def check_icd() -> list[str]:
    # Placeholder: ensure ICD file exists
    if not (ROOT / "Collaboration" / "icd_v0_1.md").exists():
        return ["ICD file missing"]
    return []


def golden_transcript_mock_seed42() -> list[str]:
    errors: list[str] = []
    try:
        if str(ROOT) not in _sys.path:
            _sys.path.insert(0, str(ROOT))
        from engine.sim_loop import run_single_scene  # type: ignore
        actual = run_single_scene(scenario_id="war_game_2025", seed=42, leader_mode="llm")
        golden_path = ROOT / "Collaboration" / "golden" / "mock_seed42_scene1.txt"
        if not golden_path.exists():
            return ["Golden transcript missing: Collaboration/golden/mock_seed42_scene1.txt"]
        golden_text = golden_path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n").strip()
        actual_text = "\n".join(actual).strip()
        if golden_text != actual_text:
            errors.append("Golden transcript mismatch under mock seed 42")
    except Exception as e:
        errors.append(f"Golden check failed: {e}")
    return errors


def main() -> int:
    report = {"yaml": [], "seed_smoke": [], "icd": [], "golden_mock_seed42": []}
    report["yaml"] = validate_yaml()
    report["seed_smoke"] = seed_smoke()
    report["icd"] = check_icd()
    report["golden_mock_seed42"] = golden_transcript_mock_seed42()
    ok = all(len(v) == 0 for v in report.values())
    out_path = ROOT / "Collaboration" / "gate_report.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())


