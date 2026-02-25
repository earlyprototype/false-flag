from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Task:
    id: str
    team: str
    status: str
    spec_path: Path
    branch: str
    has_handover: bool


def parse_task_yaml(path: Path) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    list_key: str | None = None
    list_buf: List[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()  # no strip() to preserve indent intent
        if not line or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - ") or line.startswith("- "):
            # list item
            val = line.split("-", 1)[1].strip()
            if list_key is not None:
                list_buf.append(val)
            continue
        if ":" in line:
            # flush previous list
            if list_key is not None:
                data[list_key] = list_buf
                list_key, list_buf = None, []
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if val == "":
                # start of list
                list_key = key
                list_buf = []
            else:
                data[key] = val
    if list_key is not None:
        data[list_key] = list_buf
    return data


def collect_tasks() -> List[Task]:
    tasks_dir = ROOT / "Collaboration" / "tasks"
    handover_dir = ROOT / "Collaboration" / "handover"
    tasks: List[Task] = []
    for f in sorted(tasks_dir.glob("*.yaml")):
        d = parse_task_yaml(f)
        tid = str(d.get("id", f.stem))
        spec_path = ROOT / str(d.get("spec_path", ""))
        has_handover = False
        if handover_dir.exists():
            handover_path = handover_dir / f"{tid}.md"
            has_handover = handover_path.exists()
        tasks.append(
            Task(
                id=tid,
                team=str(d.get("team", "?")),
                status=str(d.get("status", "pending")),
                spec_path=spec_path,
                branch=str(d.get("branch", "")),
                has_handover=has_handover,
            )
        )
    return tasks


def read_gate_report() -> Dict[str, Any] | None:
    p = ROOT / "Collaboration" / "gate_report.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def main() -> int:
    tasks = collect_tasks()
    gate = read_gate_report()
    summary = {
        "tasks": [
            {
                "id": t.id,
                "team": t.team,
                "status": t.status,
                "spec_exists": t.spec_path.exists(),
                "branch": t.branch,
                "handover": t.has_handover,
            }
            for t in tasks
        ],
        "gate_report": gate,
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


