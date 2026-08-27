"""Self-check for the interop deliverables. Stdlib only, no test framework.

Run from the false-flag repo root AFTER capture + export:
    python interop/test_interop.py

Asserts: the model set validates structurally clean, and the sample export
documents carry the expected shape - top-level keys, at least one decision
point and one delivered inject from the run, full metric telemetry series,
and enum values that match the models (enums are read from the model files,
not duplicated here).
"""

import json
import sys
from pathlib import Path

INTEROP = Path(__file__).resolve().parent
sys.path.insert(0, str(INTEROP))

from validate_dtdl import validate_models  # noqa: E402


def _enum_values(model_file, interface_suffix, property_name):
    """Pull an enum's values out of a model file - the models are the authority."""
    data = json.loads((INTEROP / "models" / model_file).read_text(encoding="utf-8"))
    docs = data if isinstance(data, list) else [data]
    for doc in docs:
        if not doc.get("@id", "").endswith(interface_suffix):
            continue
        for element in doc.get("contents", []):
            if element.get("name") != property_name:
                continue
            schema = element["schema"]
            if isinstance(schema, str):  # reference into the schemas section
                for shared in doc.get("schemas", []):
                    if shared.get("@id") == schema:
                        schema = shared
                        break
            return {ev["enumValue"] for ev in schema["enumValues"]}
    raise AssertionError(f"enum {interface_suffix}.{property_name} not found in {model_file}")


def main():
    # 1. The model set is structurally legal DTDL v3.
    errors, count = validate_models(INTEROP / "models")
    assert not errors, "model validation failed:\n" + "\n".join(errors)
    print(f"PASS models: {count} interfaces structurally clean")

    # 2. Exercise document shape.
    exercise = json.loads(
        (INTEROP / "sample_export" / "exercise_war_game_2025.json")
        .read_text(encoding="utf-8"))
    for key in ("$metadata", "metadata", "learningObjectives", "timeline",
                "worldReference", "roles", "participants", "injects"):
        assert key in exercise, f"exercise document missing top-level key {key!r}"
    assert exercise["$metadata"]["$model"] == "dtmi:falseflag:Exercise;1"
    assert exercise["injects"], "exercise document has no injects"
    channels = _enum_values("inject.json", ":Inject;1", "channel")
    for inject in exercise["injects"]:
        assert inject["channel"] in channels, \
            f"inject {inject['id']} channel {inject['channel']!r} not in model enum"
    scenes = exercise["timeline"]["phases"][0]["scenarios"][0]["scenes"]
    assert [s["turnNumber"] for s in scenes] == list(range(1, len(scenes) + 1)), \
        "scene turnNumbers are not a contiguous 1:1 turn mapping"
    print(f"PASS exercise: {len(exercise['injects'])} injects, "
          f"{len(scenes)} scenes, channels within model enum")

    # 3. Run-telemetry document shape.
    run = json.loads((INTEROP / "sample_export" / "run_telemetry.json")
                     .read_text(encoding="utf-8"))
    for key in ("$metadata", "id", "exercise", "telemetry", "decisions", "ledger"):
        assert key in run, f"run document missing top-level key {key!r}"
    assert run["$metadata"]["$model"] == "dtmi:falseflag:emergent:Session;1"
    assert run["exercise"] == exercise["id"], "run does not reference the exercise"

    assert run["decisions"], "run document has no decision points"
    verdicts = _enum_values("emergent_assessment.json",
                            ":AdjudicatedDecision;1", "qualityVerdict")
    for decision in run["decisions"]:
        assert decision["playerDecisionText"], "decision point missing decision text"
        if decision["qualityVerdict"] is not None:
            assert decision["qualityVerdict"] in verdicts, \
                f"verdict {decision['qualityVerdict']!r} not in model enum"

    assert run["telemetry"]["inject_triggered"], "run has no delivered injects"
    for name in ("escalation_risk", "domestic_stability", "alliance_cohesion",
                 "casualties_civ", "casualties_mil"):
        assert run["telemetry"][name], f"metric telemetry series {name!r} is empty"

    assert run["ledger"], "run document has no ledger entries"
    dispositions = _enum_values("emergent_assessment.json",
                                ":EventLedgerEntry;1", "disposition")
    for entry in run["ledger"]:
        assert entry["disposition"] in dispositions, \
            f"ledger disposition {entry['disposition']!r} not in model enum"

    metric_points = sum(len(run["telemetry"][m]) for m in
                        ("escalation_risk", "domestic_stability",
                         "alliance_cohesion", "casualties_civ", "casualties_mil"))
    print(f"PASS run: {len(run['decisions'])} decision points, "
          f"{len(run['telemetry']['inject_triggered'])} injects delivered, "
          f"{metric_points} metric points, {len(run['ledger'])} ledger entries")
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
