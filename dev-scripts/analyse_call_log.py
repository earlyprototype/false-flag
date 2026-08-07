"""Turn a WARGAME_CALL_LOG file into verification-matrix evidence.

Reads the JSONL the router writes when WARGAME_CALL_LOG is set and prints,
per matrix row, what the log proves: which model answered each family
(routing), whether any reply was cut on its cap (truncation), whether the
context each fix was supposed to deliver actually reached its prompts
(input side), and a raw-vs-parsed re-parse of every structured reply
(output side). Exit code 1 when any check fails, so a shakedown can gate
on it.

Usage: python3 dev-scripts/analyse_call_log.py <log.jsonl>
"""

import json
import sys
from collections import Counter, defaultdict


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    path = sys.argv[1]
    records = load(path)
    failures = []

    by_family = defaultdict(list)
    for r in records:
        by_family[r.get("family") or "(none)"].append(r)

    # --- 1. Routing: which model answered each family -----------------------
    print("== ROUTING (family -> tier -> models seen, calls, fallbacks) ==")
    for family in sorted(by_family):
        rs = by_family[family]
        models = Counter((r.get("tier"), r.get("model")) for r in rs)
        fb = sum(1 for r in rs if r.get("fallback"))
        for (tier, model), n in sorted(models.items(), key=lambda kv: str(kv[0])):
            print(f"  {family:28s} {str(tier):6s} {str(model):40s} x{n}"
                  + (f"  FALLBACKS={fb}" if fb else ""))
        if fb:
            failures.append(f"{family}: {fb} calls fell back to the mock driver")

    # --- 2. Truncation ------------------------------------------------------
    print("\n== FINISH REASONS ==")
    reasons = Counter((r.get("family"), r.get("finish_reason")) for r in records)
    for (family, reason), n in sorted(reasons.items(), key=lambda kv: str(kv[0])):
        print(f"  {str(family):28s} {str(reason):12s} x{n}")
    cut = [r for r in records
           if str(r.get("finish_reason", "")).lower() in ("length", "max_tokens")]
    if cut:
        failures.append(f"{len(cut)} replies cut on their output cap "
                        f"(turns {sorted({r.get('turn') for r in cut})})")

    missing_reason = [r for r in records
                      if not r.get("fallback") and r.get("finish_reason") is None]
    if missing_reason:
        failures.append(
            f"{len(missing_reason)} live replies carried no finish_reason - "
            f"the driver did not report it "
            f"(families {sorted({r.get('family') for r in missing_reason})})")

    # --- 3. Input side: what reached which prompt ---------------------------
    print("\n== INPUT-SIDE CHECKS ==")

    def check(name, ok, detail=""):
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))
        if not ok:
            failures.append(f"{name}: {detail}")

    def prompts(family):
        return by_family.get(family, [])

    # ER-017/010: each turn's synopsis reply appears in the NEXT turn's
    # deciding prompts
    summaries = {r["turn"]: r["reply"].strip() for r in prompts("situation_summary")
                 if r.get("turn") is not None and not r.get("fallback")}
    fed, missed = 0, []
    for r in prompts("quality_assessment"):
        prev = summaries.get((r.get("turn") or 0) - 1)
        if prev is None:
            continue
        probe = prev[:120]
        if probe and probe in r["prompt"]:
            fed += 1
        else:
            missed.append(r.get("turn"))
    check("ER-017/010 synopsis feeds next turn's quality prompt",
          fed > 0 and not missed, f"fed={fed} missing on turns {missed}")

    # ER-003: the event ledger block reaches deciding prompts
    ledgered = sum(1 for r in prompts("quality_assessment")
                   if "DECISIONS AND OUTCOMES" in r["prompt"]
                   or "EVENT" in r["prompt"].upper())
    check("ER-003 ledger/decisions block present in quality prompts",
          ledgered == len(prompts("quality_assessment")),
          f"{ledgered}/{len(prompts('quality_assessment'))}")

    # ER-012: actor prompts carry authored stances (mystery on: USA/RUS at
    # minimum; after ER-046 all simulated capitals)
    actor_rs = prompts("actor_simulation")
    with_stance = sum(1 for r in actor_rs if "SECRET MOTIVE" in r["prompt"])
    check("ER-012/046 actor prompts carry a stance block",
          actor_rs and with_stance == len(actor_rs),
          f"{with_stance}/{len(actor_rs)}")

    # ER-014: no UK advisor-trust block in actor prompts
    leaky = [r["turn"] for r in actor_rs if "trust:" in r["prompt"].lower()
             and "advisor" in r["prompt"].lower()]
    check("ER-014 actor prompts free of UK advisor trust", not leaky, str(leaky))

    # ER-018/038: encounter prompts carry no UK private metrics numbers
    dip = prompts("diplomacy_conversation")
    metric_leak = [r["turn"] for r in dip
                   if "escalation_risk" in r["prompt"] or "Escalation Risk:" in r["prompt"]]
    check("ER-038 encounter prompts free of raw UK metrics", not metric_leak,
          str(metric_leak))

    # ER-041: the scripted call's prompt carries its premise
    premised = [r for r in dip if "WHY YOU ARE CALLING" in r["prompt"]]
    check("ER-041 scripted-call premise present on the call turn",
          bool(premised) or not dip,
          f"{len(premised)} premised calls of {len(dip)} conversation calls")

    # ER-021: mystery on - briefing-audience prompts must NOT carry the
    # roleplay deception order; roleplay prompts must
    deceive = "Act according to your secret motive"
    briefing_leak = [f for f in ("quality_assessment", "critical_omissions",
                                 "advisor_qa", "inject_generation")
                     for r in prompts(f) if deceive in r["prompt"]]
    check("ER-021 no roleplay deception order in briefing-audience prompts",
          not briefing_leak, str(set(briefing_leak)))

    # ER-043: narrator prompt names the player's last decision
    narr = prompts("narrator")
    with_dec = sum(1 for r in narr if "LAST DECISION" in r["prompt"].upper())
    check("ER-043 narrator told the last decision",
          not narr or with_dec > 0, f"{with_dec}/{len(narr)}")

    # ER-008: prompt sizes bounded - report the max per family
    print("\n  prompt size max per family (chars):")
    for family in sorted(by_family):
        sizes = [len(r["prompt"]) for r in by_family[family]]
        print(f"    {family:28s} max={max(sizes):7d} mean={sum(sizes)//len(sizes):7d} n={len(sizes)}")

    # --- 4. Output side: re-parse structured replies ------------------------
    print("\n== OUTPUT-SIDE RE-PARSE ==")
    sys.path.insert(0, ".")
    from llm import parse_health
    parse_health.reset()

    from engine.actor_simulation import _parse_actor_response
    empties = []
    for r in by_family.get("actor_simulation", []):
        if r.get("fallback"):
            continue
        parsed = _parse_actor_response("PROBE", r["reply"])
        if not parsed.public_response.strip():
            empties.append(r.get("turn"))
    check("ER-049 every live actor reply yields a public response",
          not empties, f"empty on turns {empties}")

    snap = parse_health.snapshot()
    print(f"\n  re-parse health: misses={sum(snap['misses'].values())} "
          f"residue_lines={sum(snap['residue'].values())}")
    for k, v in snap["misses"].items():
        print(f"    miss {k} x{v}")
    for k, v in snap["residue"].items():
        print(f"    residue {k} x{v}")

    # --- verdict ------------------------------------------------------------
    print("\n== VERDICT ==")
    if failures:
        for f in failures:
            print(f"  FAIL {f}")
        sys.exit(1)
    print(f"  all checks passed over {len(records)} calls")


if __name__ == "__main__":
    main()
