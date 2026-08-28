"""Export False Flag scenarios and game runs into the interop DTDL profile.

Two subcommands, both run from the false-flag repo root:

  python interop/export_run.py capture [--turns 4] [--seed 42] [--out-dir interop/sample_export]
      Drive a short deterministic mock campaign - the same loop
      dev-scripts/play_campaign.py runs (its QUESTIONS/DECISIONS are
      imported, its _dump_state writes the telemetry series via
      WARGAME_CALL_LOG) - and record run_record.json beside the engine's
      own call-log files. play_campaign.py discards the final session
      state at exit, which the export needs, so this adapts its loop
      rather than shelling out to it.

  python interop/export_run.py export [--scenario war_game_2025] [--run-dir interop/sample_export] [--out-dir interop/sample_export]
      Read (a) the scenario YAML -> one Exercise-instance document, and
      (b) the captured run -> one run-telemetry document, both shaped
      per interop/models/. Instance entities carry an Azure-DT-style
      "$metadata": {"$model": <dtmi>} binding.

Repo dependencies only (PyYAML).
"""

import argparse
import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

FALSE_FLAG_ROOT = Path(__file__).resolve().parents[1]
PROFILE_NOTE = ("False Flag interop profile - False Flag's twin model, in "
                "our own DTDL namespace, not claimed SEDL-conformant "
                "(the SEDL specification is unpublished). See "
                "interop/README.md.")

QUALITY_RE = re.compile(
    r"QUALITY:\s*(exceptional|good|adequate|poor|catastrophic)", re.IGNORECASE)


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _meta(model, **extra):
    return {"$model": model, "profile": PROFILE_NOTE, **extra}


# ---------------------------------------------------------------------------
# capture: run a short deterministic campaign and record it
# ---------------------------------------------------------------------------

def _load_play_campaign():
    """Import dev-scripts/play_campaign.py (no package) for its drive constants."""
    path = FALSE_FLAG_ROOT / "dev-scripts" / "play_campaign.py"
    spec = importlib.util.spec_from_file_location("play_campaign", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _quality_verdicts_from_call_log(log_path):
    """turn -> quality verdict, read from the run's own recorded adjudication replies."""
    verdicts = {}
    if not log_path.exists():
        return verdicts
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("family") != "quality_assessment":
                continue
            match = QUALITY_RE.search(entry.get("reply", ""))
            if match and entry.get("turn") is not None:
                verdicts[int(entry["turn"])] = match.group(1).lower()
    return verdicts


def capture(turns, seed, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    call_log_path = out_dir / "run.calls.jsonl"
    state_path = Path(str(call_log_path) + ".state.jsonl")
    for stale in (call_log_path, state_path):
        if stale.exists():
            stale.unlink()

    os.environ["WARGAME_LLM"] = "mock"
    os.environ["WARGAME_CALL_LOG"] = str(call_log_path)
    sys.path.insert(0, str(FALSE_FLAG_ROOT))

    pc = _load_play_campaign()
    from engine.game_manager import GameManager
    from llm import call_log

    call_log.reset()
    started_at = _now()
    gm = GameManager(scenario_id="war_game_2025", play_mode="emergent",
                     seed=seed, mystery_mode=True, endings=True)
    pc._dump_state(gm, 0)  # turn-0 baseline for the telemetry series

    turn_records = []
    for turn in range(1, turns + 1):
        call_log.set_field("turn", turn)
        inject = gm.get_turn_briefing()
        while gm.active_encounter is not None and gm.active_encounter.active:
            gm.process_diplomacy(
                "We are coordinating fully with NATO and will share our "
                "deployment plan within the hour.")
        gm.process_question(pc.QUESTIONS[turn % len(pc.QUESTIONS)])
        decision = pc.DECISIONS[turn % len(pc.DECISIONS)]
        interp = gm.interpret_decision(decision)
        pushback_roles = [p["role"] for p in interp.get("pushback", [])]
        result = gm.resolve_decision(decision)
        pc._dump_state(gm, turn, pushback_roles)
        turn_records.append({
            "turn": turn,
            "inject": {
                "id": str(inject.get("id", "")),
                "title": str(inject.get("title", "")),
                "channel": str(inject.get("channel", "briefing")),
            },
            "decision_text": decision,
            "interpretation": result.get("interpretation", ""),
            "reasoning": result.get("reasoning", ""),
            "effects": result.get("effects", {}),
            "pushback": result.get("pushback", []),
            "critical_concerns": result.get("critical_concerns", []),
            "pushback_roles": pushback_roles,
            "ending": (result.get("ending") or {}).get("title")
                      if result.get("ending") else None,
        })
        print(f"captured turn {turn}: {turn_records[-1]['inject']['title'][:60]}")
        if result.get("ending"):
            break

    verdicts = _quality_verdicts_from_call_log(call_log_path)
    for record in turn_records:
        record["quality_verdict"] = verdicts.get(record["turn"])

    run_record = {
        "config": {
            "scenario_id": "war_game_2025",
            "seed": seed,
            "turns_requested": turns,
            "turns_played": len(turn_records),
            "play_mode": "emergent",
            "provider": "mock",
            "started_at": started_at,
            "ended_at": _now(),
        },
        "turns": turn_records,
        "final_save": json.loads(json.dumps(gm.to_dict("interop_sample"),
                                            default=str)),
    }
    record_path = out_dir / "run_record.json"
    record_path.write_text(json.dumps(run_record, indent=2, ensure_ascii=False),
                           encoding="utf-8")
    print(f"wrote {record_path} ({len(turn_records)} turns), "
          f"call log + state series beside it")


# ---------------------------------------------------------------------------
# export (a): scenario YAML -> Exercise-instance document
# ---------------------------------------------------------------------------

def _load_yaml(path):
    import yaml
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _org_role(disposition):
    """Mechanical mapping from diplomatic disposition text to org role."""
    text = (disposition or "").lower()
    if "hostile" in text:
        return "adversary"
    if "neutral" in text:
        return "support"
    return "partner"


def _build_world_reference(ic):
    locations = ic.get("locations", {})
    all_locations = [loc for group in locations.values() for loc in group]
    organisations = [{
        "id": "uk-government",
        "name": "United Kingdom Government",
        "role": "lead",
        "staff": len([k for k, v in ic.get("characters", {}).items()
                      if "objectives" not in v]),
    }]
    for contact in ic.get("diplomatic_contacts", []):
        organisations.append({
            "id": contact["country_code"].lower(),
            "name": contact["leader_title"],
            "role": _org_role(contact.get("disposition")),
            "disposition": contact.get("disposition", ""),
            "accessLevel": contact.get("access_level", 0),
        })
    infra = ic.get("critical_infrastructure", {})
    cyber = ic.get("intelligence", {}).get("cyber_attacks", {})
    red = ic.get("red_forces", {})
    risks = [
        {"type": "infrastructure_sabotage", "severity": "high",
         "probability": "high",
         "note": f"{infra.get('attacks_count', 0)} attacks recorded; "
                 f"status {infra.get('status', 'unknown')}"},
        {"type": "naval_escalation", "severity": "high", "probability": "high",
         "note": f"Red operation {red.get('active_operation', 'unknown')}; "
                 f"heading {red.get('naval', {}).get('heading', 'unknown')}"},
        {"type": "cyber_attack", "severity": "medium", "probability": "high",
         "note": f"{cyber.get('increase', '')}; {cyber.get('attribution', '')}"},
    ]
    return {
        "$metadata": _meta("dtmi:falseflag:WorldReference;1"),
        "id": "world_war_game_2025",
        "location": "United Kingdom",
        "context": ic.get("metadata", {}).get("description", ""),
        "geographicScope": ", ".join(all_locations),
        "organisations": organisations,
        "risks": risks,
        "environmentalFactors": {k: str(v)
                                 for k, v in ic.get("environment", {}).items()},
    }


def _build_roles_and_participants(ic):
    roles, participants = [], []
    for key, char in ic.get("characters", {}).items():
        role = {
            "$metadata": _meta("dtmi:falseflag:Role;1"),
            "id": key,
            "name": char.get("role", key),
            "count": 1,
            "influence": char.get("influence"),
            "knowledgeDomains": char.get("knowledge_domains", []),
        }
        for src, dst in (("pushback_triggers", "pushbackTriggers"),
                         ("key_concerns", "keyConcerns"),
                         ("objectives", "objectives")):
            if char.get(src):
                role[dst] = char[src]
        roles.append(role)
        participants.append({
            "$metadata": _meta("dtmi:falseflag:Participant;1"),
            "id": f"user_{key}",
            "name": char.get("role", key),
            "characterId": key,
            "kind": "human" if key == "prime_minister" else "ai_agent",
            "assignedRole": key,
        })
    return roles, participants


def _build_timeline(scenario_cfg, episodes):
    hours_per_turn = 2  # each turn represents ~2 hours of game time (episodes README)
    scripted_scenes = [{
        "$metadata": _meta("dtmi:falseflag:Scene;1"),
        "id": f"scene_turn_{episode['turn']:03d}",
        "name": episode["data"].get("title", f"Turn {episode['turn']}"),
        "turnNumber": episode["turn"],
    } for episode in episodes]
    epilogue = int(scenario_cfg.get("epilogue_turns", 4))
    return {
        "$metadata": _meta("dtmi:falseflag:Timeline;1"),
        "id": "timeline_war_game_2025",
        "phases": [
            {
                "$metadata": _meta("dtmi:falseflag:Phase;1"),
                "id": "phase_scripted",
                "name": "Scripted Crisis",
                "duration": {"hours": hours_per_turn * len(episodes)},
                "scenarios": [{
                    "$metadata": _meta("dtmi:falseflag:Scenario;1"),
                    "id": "scenario_false_flag_crisis",
                    "name": "UK-Russia False Flag Crisis",
                    "scenes": scripted_scenes,
                }],
            },
            {
                "$metadata": _meta("dtmi:falseflag:Phase;1"),
                "id": "phase_emergent",
                "name": "Emergent Escalation",
                "duration": {"hours": hours_per_turn * epilogue},
                "scenarios": [{
                    "$metadata": _meta("dtmi:falseflag:Scenario;1"),
                    "id": "scenario_emergent_continuation",
                    "name": "Stochastic continuation",
                    "description": ("Turns generated at run time from campaign "
                                    "state; scenes exist only in the run record."),
                    "scenes": [],
                }],
            },
        ],
    }


def _build_injects(episodes):
    injects = []
    for episode in episodes:
        data = episode["data"]
        injects.append({
            "$metadata": _meta("dtmi:falseflag:Inject;1"),
            "id": data.get("id", f"turn_{episode['turn']:03d}"),
            "title": data.get("title", ""),
            "trigger": {"type": "time"},
            "timing": {"sceneRelative": episode["turn"] - 1, "seconds": 0},
            "channel": data.get("channel", "briefing"),
            "content": data.get("description", ""),
            "targets": ["Prime Minister"],
            "effects": [{"metric": e["metric"], "delta": str(e["delta"])}
                        for e in data.get("effects", [])],
            # expectedResponse / assessmentCriteria omitted BY DESIGN:
            # emergent adjudication (see interop/README.md).
        })
    return injects


def build_exercise_document(scenario_id, variant="standard"):
    scenario_dir = FALSE_FLAG_ROOT / "data" / "scenarios" / scenario_id
    ic = _load_yaml(scenario_dir / "initial_conditions.yaml")
    scenario_cfg = _load_yaml(scenario_dir / "scenarios.yaml")["scenarios"][variant]

    prefix = scenario_cfg.get("turn_prefix", "turn_")
    suffix = scenario_cfg.get("turn_suffix", "")
    episodes = []
    for turn in range(1, int(scenario_cfg.get("scripted_turns", 0)) + 1):
        path = scenario_dir / "episodes" / f"{prefix}{turn:03d}{suffix}.yaml"
        if path.exists():
            episodes.append({"turn": turn, "data": _load_yaml(path)})

    metadata = ic.get("metadata", {})
    roles, participants = _build_roles_and_participants(ic)
    uk_objectives = ic.get("objectives", {}).get("uk", {})
    statements = [uk_objectives.get("primary")] + list(
        uk_objectives.get("secondary", []))
    learning_objectives = [{
        "$metadata": _meta("dtmi:falseflag:LearningObjective;1"),
        "id": f"obj_{i + 1}",
        "statement": statement,
        # taxonomyLevel/assessmentCriteria omitted: these are operational
        # win conditions, not pedagogical objectives (see interop/README.md).
    } for i, statement in enumerate(statements) if statement]

    return {
        "$metadata": _meta("dtmi:falseflag:Exercise;1",
                           generatedAt=_now(),
                           source=f"data/scenarios/{scenario_id} (variant: {variant})"),
        "id": f"ex_{scenario_id}",
        "metadata": {
            "name": metadata.get("title", scenario_id),
            "type": "tabletop",
            "description": metadata.get("description", ""),
            "duration": {"hours": 2 * (len(episodes) +
                                       int(scenario_cfg.get("epilogue_turns", 0)))},
            "participants": {"total": 1, "max": 1},
            "startDate": metadata.get("start_date", ""),
            "startTime": metadata.get("start_time", ""),
        },
        "learningObjectives": learning_objectives,
        "timeline": _build_timeline(scenario_cfg, episodes),
        "worldReference": _build_world_reference(ic),
        "roles": roles,
        "participants": participants,
        "injects": _build_injects(episodes),
    }


# ---------------------------------------------------------------------------
# export (b): captured run -> run-telemetry document
# ---------------------------------------------------------------------------

METRIC_NAMES = ("escalation_risk", "domestic_stability", "alliance_cohesion",
                "casualties_civ", "casualties_mil")


def _read_state_series(state_path):
    lines = []
    with open(state_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(json.loads(line))
    return lines


def build_run_document(run_dir, scenario_id):
    run_record = json.loads((run_dir / "run_record.json").read_text(encoding="utf-8"))
    state_lines = _read_state_series(run_dir / "run.calls.jsonl.state.jsonl")
    config = run_record["config"]

    telemetry = {name: [] for name in METRIC_NAMES}
    telemetry["advisor_trust"] = []
    for entry in state_lines:
        turn = entry["turn"]
        stamp = f"T+{turn}"
        for name in METRIC_NAMES:
            telemetry[name].append(
                {"stamp": stamp, "turn": turn, "value": entry["metrics"][name]})
        for char_id, advisor in entry.get("advisors", {}).items():
            telemetry["advisor_trust"].append({
                "stamp": stamp, "turn": turn, "characterId": char_id,
                "trust": advisor["trust"],
                "relationship": advisor["relationship"],
            })

    telemetry["inject_triggered"] = [{
        "stamp": f"T+{t['turn']}", "turn": t["turn"],
        "injectId": t["inject"]["id"], "title": t["inject"]["title"],
        "channel": t["inject"]["channel"],
    } for t in run_record["turns"]]
    telemetry["participant_action"] = [{
        "stamp": f"T+{t['turn']}", "turn": t["turn"],
        "actionType": "decision", "text": t["decision_text"],
    } for t in run_record["turns"]]
    # Ninth stream: real engine phase transitions captured per state line.
    # Old captures without a "phases" field yield an empty stream — never
    # synthesized (owner ruling 27 Aug: no fabricated values).
    telemetry["phase_changed"] = [
        {"stamp": f"T+{entry['turn']}", "turn": entry["turn"], "phase": phase}
        for entry in state_lines
        for phase in entry.get("phases", [])
    ]

    decisions = [{
        "$metadata": _meta("dtmi:falseflag:emergent:AdjudicatedDecision;1"),
        "id": f"decision_t{t['turn']}",
        "turn": t["turn"],
        "playerDecisionText": t["decision_text"],
        "interpretation": t["interpretation"],
        "qualityVerdict": t["quality_verdict"],
        "reasoning": t["reasoning"],
        "effects": {k: int(v) for k, v in (t.get("effects") or {}).items()},
        "pushback": t.get("pushback", []),
        "criticalConcerns": t.get("critical_concerns", []),
        # This harness always commits the previewed text unamended, so any
        # raised objection was overridden.
        "overriddenObjectors": t.get("pushback_roles", []),
    } for t in run_record["turns"]]

    ledger_source = (run_record["final_save"].get("state", {})
                     .get("narrative_state", {}).get("event_ledger", []))
    ledger = [{
        "$metadata": _meta("dtmi:falseflag:emergent:EventLedgerEntry;1"),
        "id": f"ledger_t{entry['turn']}",
        "turn": entry["turn"],
        "title": entry["title"],
        "disposition": entry["disposition"],
        "note": entry.get("note", ""),
        "outcome": entry.get("outcome", ""),
        "effectsDirection": entry.get("effects_direction", {}),
        "objectors": entry.get("objectors", []),
    } for entry in ledger_source]

    return {
        "$metadata": _meta("dtmi:falseflag:emergent:Session;1",
                           generatedAt=_now(),
                           source="run_record.json + run.calls.jsonl.state.jsonl"),
        "id": f"session_{scenario_id}_seed{config['seed']}",
        "exercise": f"ex_{scenario_id}",
        "startedAt": config["started_at"],
        "endedAt": config["ended_at"],
        "seed": config["seed"],
        "playMode": config["play_mode"],
        "provider": config["provider"],
        "turnsPlayed": config["turns_played"],
        "telemetry": telemetry,
        "decisions": decisions,
        "ledger": ledger,
    }


# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    cap = sub.add_parser("capture", help="record a short deterministic mock campaign")
    cap.add_argument("--turns", type=int, default=4)
    cap.add_argument("--seed", type=int, default=42)
    cap.add_argument("--out-dir", default="interop/sample_export")

    exp = sub.add_parser("export", help="write exercise + run-telemetry documents")
    exp.add_argument("--scenario", default="war_game_2025")
    exp.add_argument("--variant", default="standard")
    exp.add_argument("--run-dir", default="interop/sample_export")
    exp.add_argument("--out-dir", default="interop/sample_export")

    args = parser.parse_args()
    if args.command == "capture":
        capture(args.turns, args.seed, Path(args.out_dir))
        return 0

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    exercise = build_exercise_document(args.scenario, args.variant)
    exercise_path = out_dir / f"exercise_{args.scenario}.json"
    exercise_path.write_text(json.dumps(exercise, indent=2, ensure_ascii=False),
                             encoding="utf-8")
    print(f"wrote {exercise_path}: {len(exercise['injects'])} injects, "
          f"{len(exercise['roles'])} roles")

    run_doc = build_run_document(Path(args.run_dir), args.scenario)
    run_path = out_dir / "run_telemetry.json"
    run_path.write_text(json.dumps(run_doc, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    metric_points = sum(len(run_doc["telemetry"][name]) for name in METRIC_NAMES)
    print(f"wrote {run_path}: {run_doc['turnsPlayed']} turns, "
          f"{len(run_doc['decisions'])} decisions, "
          f"{len(run_doc['telemetry']['inject_triggered'])} injects, "
          f"{metric_points} metric telemetry points")
    return 0


if __name__ == "__main__":
    sys.exit(main())
