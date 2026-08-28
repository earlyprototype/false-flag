"""Assemble dashboard_pack.json from the raw interop/demo_data exports.

One consolidated file with everything a labelled dashboard visual needs:
run metadata, the five per-turn metric series, per-advisor trust series,
the T+ inject list, decision points, event-ledger entries, LLM call stats
(per turn and per family), and the channel->layer mapping the dashboard
lanes use. Key names reuse the DTDL correspondence vocabulary verbatim
where it exists (metadata / timeline / injects / decisions / ledger /
telemetry names; see interop/README.md).

Run from anywhere:  python interop/demo_data/build_dashboard_pack.py
Reads its sibling files; writes dashboard_pack.json beside them.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parent
FALSE_FLAG_ROOT = DEMO_DIR.parents[1]

METRIC_NAMES = ("escalation_risk", "domestic_stability", "alliance_cohesion",
                "casualties_civ", "casualties_mil")

INTERPRETATION_SNIPPET_CHARS = 240

# Dashboard display lanes for the inject timeline. The channel values are
# verbatim the enum dtmi:falseflag:schema:Channel;1 (interop/models/
# inject.json) - False Flag's briefing-stream genres, not SimexBuilder's
# transport channels (CORRESPONDENCE.md open question 5). The layer names
# are ours: one visual lane per genre.
CHANNEL_LAYER_MAPPING = {
    "briefing": "command",          # COBRA / command briefings
    "intelligence": "intelligence",  # agency assessments
    "emergency": "civil",           # domestic emergency response
    "diplomatic": "diplomatic",     # allied and foreign-state traffic
    "flash_alert": "flash",         # immediate military alerts
}


def _load(name):
    return json.loads((DEMO_DIR / name).read_text(encoding="utf-8"))


def _load_jsonl(name):
    entries = []
    with open(DEMO_DIR / name, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def _ending_verdict(ending_id):
    """Look up the ending's verdict in the engine's own table."""
    if not ending_id:
        return None
    sys.path.insert(0, str(FALSE_FLAG_ROOT))
    try:
        from engine.endings import ENDINGS
        ending = ENDINGS.get(ending_id)
        return ending.verdict if ending else None
    except Exception:
        return None


def _advisor_names(state_lines):
    """characterId -> display name, from the turn-0 state baseline."""
    names = {}
    for entry in state_lines:
        for char_id, advisor in entry.get("advisors", {}).items():
            names.setdefault(char_id, advisor.get("name", char_id))
    return names


def _mean(values):
    return round(sum(values) / len(values), 1) if values else 0


def _call_bucket(entries):
    latencies = [e["latency_ms"] for e in entries
                 if e.get("latency_ms") is not None]
    return {
        "count": len(entries),
        "meanLatencyMs": _mean(latencies),
        "fallbackCount": sum(1 for e in entries if e.get("fallback")),
    }


def build_llm_calls(call_lines):
    per_turn, per_family = {}, {}
    for entry in call_lines:
        per_turn.setdefault(entry.get("turn") or 0, []).append(entry)
        per_family.setdefault(entry.get("family") or "unknown", []).append(entry)
    return {
        "totals": _call_bucket(call_lines),
        "perTurn": [{"turn": turn, **_call_bucket(entries)}
                    for turn, entries in sorted(per_turn.items())],
        "perFamily": [{"family": family, **_call_bucket(entries)}
                      for family, entries in sorted(per_family.items())],
    }


def build_pack():
    run_record = _load("run_record.json")
    run_telemetry = _load("run_telemetry.json")
    exercise = _load("exercise_war_game_2025.json")
    call_lines = _load_jsonl("run.calls.jsonl")
    state_lines = _load_jsonl("run.calls.jsonl.state.jsonl")

    config = run_record["config"]
    telemetry = run_telemetry["telemetry"]

    # Scripted turns = the scenes of the exercise timeline's scripted phase;
    # everything after them is generated at run time (phase_emergent).
    scripted_phase = next(p for p in exercise["timeline"]["phases"]
                          if p["id"] == "phase_scripted")
    scripted_turn_numbers = sorted(
        scene["turnNumber"]
        for scenario in scripted_phase["scenarios"]
        for scene in scenario["scenes"])
    scripted_turns = len(scripted_turn_numbers)
    scripted_inject_ids = {inject["id"] for inject in exercise["injects"]}

    ending_turn = next((t["turn"] for t in run_record["turns"] if t["ending"]),
                       None)
    ending_id = run_record["final_save"]["state"].get("ending_id")
    ending = None
    if ending_turn is not None:
        ending = {
            "turn": ending_turn,
            "title": next(t["ending"] for t in run_record["turns"]
                          if t["ending"]),
            "endingId": ending_id,
            "verdict": _ending_verdict(ending_id),
        }

    names = _advisor_names(state_lines)
    advisor_trust = {}
    for point in telemetry["advisor_trust"]:
        series = advisor_trust.setdefault(point["characterId"], {
            "name": names.get(point["characterId"], point["characterId"]),
            "series": [],
        })
        series["series"].append({
            "stamp": point["stamp"], "turn": point["turn"],
            "trust": point["trust"], "relationship": point["relationship"],
        })

    injects = [{
        "stamp": point["stamp"],
        "turn": point["turn"],
        "injectId": point["injectId"],
        "title": point["title"],
        "channel": point["channel"],
        "layer": CHANNEL_LAYER_MAPPING[point["channel"]],
        "scripted": point["injectId"] in scripted_inject_ids,
    } for point in telemetry["inject_triggered"]]

    decisions = [{
        "id": d["id"],
        "turn": d["turn"],
        "playerDecisionText": d["playerDecisionText"],
        "interpretationSnippet":
            d["interpretation"][:INTERPRETATION_SNIPPET_CHARS],
        "qualityVerdict": d["qualityVerdict"],
        "effects": d["effects"],
        "pushback": [p["role"] for p in d["pushback"]],
        "overriddenObjectors": d["overriddenObjectors"],
        "criticalConcerns": d["criticalConcerns"],
    } for d in run_telemetry["decisions"]]

    ledger = [{
        "id": e["id"],
        "turn": e["turn"],
        "title": e["title"],
        "disposition": e["disposition"],
        "objectors": e["objectors"],
    } for e in run_telemetry["ledger"]]

    return {
        "$metadata": {
            "generatedAt": datetime.now(timezone.utc).isoformat(
                timespec="seconds"),
            "profile": run_telemetry["$metadata"]["profile"],
            "source": ["run_record.json", "run_telemetry.json",
                       "exercise_war_game_2025.json", "run.calls.jsonl",
                       "run.calls.jsonl.state.jsonl"],
            "builder": "interop/demo_data/build_dashboard_pack.py",
        },
        "run": {
            "id": run_telemetry["id"],
            "exercise": run_telemetry["exercise"],
            "scenario_id": config["scenario_id"],
            "seed": config["seed"],
            "playMode": config["play_mode"],
            "provider": config["provider"],
            "turnsRequested": config["turns_requested"],
            "turnsPlayed": config["turns_played"],
            "startedAt": config["started_at"],
            "endedAt": config["ended_at"],
            "scriptedTurns": scripted_turns,
            "stochasticFrom": scripted_turns + 1,
            "ending": ending,
        },
        "metadata": exercise["metadata"],
        "timeline": {
            "phases": [{
                "id": phase["id"],
                "name": phase["name"],
                "turns": (scripted_turn_numbers
                          if phase["id"] == "phase_scripted"
                          else list(range(scripted_turns + 1,
                                          config["turns_played"] + 1))),
            } for phase in exercise["timeline"]["phases"]],
        },
        "telemetry": {name: telemetry[name] for name in METRIC_NAMES},
        "advisor_trust": advisor_trust,
        "injects": injects,
        "decisions": decisions,
        "ledger": ledger,
        "llm_calls": build_llm_calls(call_lines),
        "channel_layer_mapping": CHANNEL_LAYER_MAPPING,
    }


def main():
    pack = build_pack()
    out_path = DEMO_DIR / "dashboard_pack.json"
    out_path.write_text(json.dumps(pack, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    print(f"wrote {out_path}: {pack['run']['turnsPlayed']} turns, "
          f"{len(pack['injects'])} injects, {len(pack['decisions'])} decisions, "
          f"{len(pack['advisor_trust'])} advisors, "
          f"{pack['llm_calls']['totals']['count']} llm calls")
    return 0


if __name__ == "__main__":
    sys.exit(main())
