"""Reconcile dashboard_pack.json against the raw interop/demo_data exports.

Every count the dashboard pack claims is re-derived from the raw files
(run_record.json, run_telemetry.json, exercise_war_game_2025.json,
run.calls.jsonl, run.calls.jsonl.state.jsonl) and asserted equal.

Metric telemetry series are turns+1 points long: the exporter writes a
turn-0 baseline before the first turn, then one point per adjudicated
turn (stamps T+0 .. T+<turnsPlayed>).

Run from anywhere:  python interop/demo_data/verify_pack.py
Exits 0 with a PASS line, or fails on the first broken assert.
"""

import json
import sys
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parent

METRIC_NAMES = ("escalation_risk", "domestic_stability", "alliance_cohesion",
                "casualties_civ", "casualties_mil")


def _load(name):
    return json.loads((DEMO_DIR / name).read_text(encoding="utf-8"))


def _load_jsonl(name):
    with open(DEMO_DIR / name, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    pack = _load("dashboard_pack.json")
    run_record = _load("run_record.json")
    run_telemetry = _load("run_telemetry.json")
    exercise = _load("exercise_war_game_2025.json")
    call_lines = _load_jsonl("run.calls.jsonl")
    state_lines = _load_jsonl("run.calls.jsonl.state.jsonl")

    turns_played = run_record["config"]["turns_played"]
    checks = 0

    def ok(condition, label):
        nonlocal checks
        assert condition, f"FAIL: {label}"
        checks += 1

    # --- run metadata ------------------------------------------------------
    ok(pack["run"]["turnsPlayed"] == turns_played == len(run_record["turns"]),
       "turnsPlayed mismatch across pack / config / turn records")
    ok(pack["run"]["seed"] == run_record["config"]["seed"],
       "seed mismatch")
    ok(pack["run"]["provider"] == run_record["config"]["provider"] == "mock",
       "provider/driver mismatch")
    ok(pack["run"]["id"] == run_telemetry["id"], "session id mismatch")

    # --- decision points: one per turn played ------------------------------
    ok(len(pack["decisions"]) == turns_played,
       "decision points != turns played")
    ok(len(pack["decisions"]) == len(run_telemetry["decisions"]),
       "pack decisions != run_telemetry decisions")
    ok([d["turn"] for d in pack["decisions"]]
       == list(range(1, turns_played + 1)),
       "decision turns are not 1..turnsPlayed")
    for packed, raw in zip(pack["decisions"], run_telemetry["decisions"]):
        ok(packed["effects"] == raw["effects"],
           f"decision t{raw['turn']} effects diverge from run_telemetry")
        ok(raw["qualityVerdict"] is not None
           and packed["qualityVerdict"] == raw["qualityVerdict"],
           f"decision t{raw['turn']} quality verdict missing or diverged")
        ok(packed["playerDecisionText"] == raw["playerDecisionText"],
           f"decision t{raw['turn']} player text diverged")
        ok(raw["interpretation"].startswith(packed["interpretationSnippet"]),
           f"decision t{raw['turn']} snippet is not a prefix of the "
           "interpretation")

    # --- injects: one per turn played --------------------------------------
    ok(len(pack["injects"]) == turns_played,
       "inject count != turns played")
    ok(len(pack["injects"]) == len(run_telemetry["telemetry"]["inject_triggered"]),
       "pack injects != run_telemetry inject_triggered")
    scripted_ids = {inject["id"] for inject in exercise["injects"]}
    ok(sum(1 for i in pack["injects"] if i["scripted"]) == len(scripted_ids),
       "scripted inject count != exercise document injects")
    for inject in pack["injects"]:
        ok(inject["scripted"] == (inject["injectId"] in scripted_ids),
           f"inject {inject['injectId']} scripted flag wrong")
        ok(inject["scripted"] == (inject["turn"] <= pack["run"]["scriptedTurns"]),
           f"inject t{inject['turn']} scripted flag disagrees with "
           "scriptedTurns boundary")

    # --- metric telemetry: turns+1 points (T+0 baseline + one per turn) ----
    expected_points = turns_played + 1
    ok(len(state_lines) == expected_points,
       "raw state series != turns+1 lines")
    for name in METRIC_NAMES:
        series = pack["telemetry"][name]
        ok(len(series) == expected_points,
           f"{name} series != turns+1 points")
        ok(series == run_telemetry["telemetry"][name],
           f"{name} series diverges from run_telemetry")
        ok(series[0]["stamp"] == "T+0"
           and series[-1]["stamp"] == f"T+{turns_played}",
           f"{name} stamps do not run T+0..T+{turns_played}")

    # --- advisor trust: per-advisor series, turns+1 points each ------------
    raw_trust = run_telemetry["telemetry"]["advisor_trust"]
    packed_points = sum(len(a["series"]) for a in pack["advisor_trust"].values())
    ok(packed_points == len(raw_trust),
       "advisor trust points != run_telemetry advisor_trust")
    for char_id, advisor in pack["advisor_trust"].items():
        ok(len(advisor["series"]) == expected_points,
           f"advisor {char_id} series != turns+1 points")

    # --- event ledger ------------------------------------------------------
    ok(len(pack["ledger"]) == len(run_telemetry["ledger"]) == turns_played,
       "ledger entries != run_telemetry ledger != turns played")
    objector_turns_pack = {e["turn"] for e in pack["ledger"] if e["objectors"]}
    objector_turns_raw = {e["turn"] for e in run_telemetry["ledger"]
                          if e["objectors"]}
    ok(objector_turns_pack == objector_turns_raw,
       "ledger objector turns diverge from run_telemetry")

    # --- llm call stats ----------------------------------------------------
    totals = pack["llm_calls"]["totals"]
    ok(totals["count"] == len(call_lines),
       "llm totals.count != run.calls.jsonl lines")
    ok(sum(b["count"] for b in pack["llm_calls"]["perTurn"]) == totals["count"],
       "perTurn counts do not sum to total")
    ok(sum(b["count"] for b in pack["llm_calls"]["perFamily"]) == totals["count"],
       "perFamily counts do not sum to total")
    raw_fallbacks = sum(1 for e in call_lines if e.get("fallback"))
    ok(totals["fallbackCount"] == raw_fallbacks,
       "fallbackCount != raw fallback lines")
    ok(sum(b["fallbackCount"] for b in pack["llm_calls"]["perTurn"])
       == raw_fallbacks,
       "perTurn fallbacks do not sum to raw fallbacks")
    raw_families = {e.get("family") or "unknown" for e in call_lines}
    ok({b["family"] for b in pack["llm_calls"]["perFamily"]} == raw_families,
       "perFamily families diverge from raw call log")

    # --- channel -> layer mapping ------------------------------------------
    mapping = pack["channel_layer_mapping"]
    for inject in pack["injects"]:
        ok(inject["channel"] in mapping,
           f"inject channel {inject['channel']} missing from mapping")
        ok(inject["layer"] == mapping[inject["channel"]],
           f"inject t{inject['turn']} layer disagrees with mapping")

    print(f"PASS: {checks} checks. "
          f"{turns_played} turns played = {len(pack['decisions'])} decisions "
          f"= {len(pack['injects'])} injects = {len(pack['ledger'])} ledger "
          f"entries; metric series {expected_points} points each (turns+1: "
          f"T+0 baseline included); "
          f"{len(pack['advisor_trust'])} advisors x {expected_points} points "
          f"= {packed_points} trust points; "
          f"{totals['count']} llm calls ({totals['fallbackCount']} fallbacks).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
