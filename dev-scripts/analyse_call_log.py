"""Turn a WARGAME_CALL_LOG file into verification-matrix evidence.

Reads the JSONL the router writes when WARGAME_CALL_LOG is set and prints,
per matrix row, what the log proves: which model answered each family
(routing), whether any reply was cut on its cap (truncation), whether the
context each fix was supposed to deliver actually reached its prompts
(input side), and a raw-vs-parsed re-parse of every structured reply
(output side). Exit code 1 when any check fails, so a shakedown can gate
on it.

When the campaign harness also wrote a state file beside the log
(<log>.state.jsonl - see dev-scripts/play_campaign.py), it additionally
verifies advisor-attitude drift (ER-007) and the pushback-override trust
cost (ER-013), checks for empty-completion fallbacks (ER-071) and the
advisory prompt bound (ER-072), and prints a rough per-family token cost
table.

Usage: python3 dev-scripts/analyse_call_log.py <log.jsonl>
"""

import json
import os
import sys
from collections import Counter, defaultdict

# Families whose prompts carry the advisor transcript and are therefore
# bounded by MAX_ADVISOR_TRANSCRIPT_CHARS (llm/context_builder.py, 60k).
# The ceiling here allows 10% headroom for the fixed prompt scaffolding
# around the bounded transcript block.
ADVISORY_FAMILIES = ("advisor_qa", "advisor_pushback", "critical_omissions",
                     "decision_interpretation")
ADVISORY_PROMPT_CEILING = 66_000


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

    # The mock/offline drivers have no finish_reason to report - the check
    # is about a LIVE driver failing to say how its reply ended, so a mock
    # shakedown (WARGAME_LLM=mock) does not fail on it.
    missing_reason = [r for r in records
                      if not r.get("fallback") and r.get("finish_reason") is None
                      and r.get("provider") not in ("mock", "offline")]
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

    # --- 5. ER-071: empty-completion fallbacks ------------------------------
    # The reasoning-control fix means no call should ever come back empty and
    # be answered by the mock driver in the model's name. Any fallback=true
    # record is a regression.
    print("\n== ER-071 EMPTY-COMPLETION FALLBACKS ==")
    fb_records = [r for r in records if r.get("fallback")]
    fb_split = Counter(r.get("family") or "(none)" for r in fb_records)
    if fb_split:
        for family, n in sorted(fb_split.items()):
            print(f"  {family:28s} x{n}")
    check("ER-071 zero empty-completion fallbacks", not fb_records,
          f"{len(fb_records)} fallback records"
          + (f" ({dict(fb_split)})" if fb_split else ""))

    # --- 6. ER-072: advisory prompts bounded --------------------------------
    print("\n== ER-072 ADVISORY PROMPT BOUND ==")
    oversize = []
    for family in ADVISORY_FAMILIES:
        rs = by_family.get(family, [])
        if not rs:
            print(f"  {family:28s} (no calls)")
            continue
        biggest = max(len(r["prompt"]) for r in rs)
        print(f"  {family:28s} max={biggest:7d} chars "
              f"(ceiling {ADVISORY_PROMPT_CEILING})")
        if biggest > ADVISORY_PROMPT_CEILING:
            oversize.append((family, biggest))
    check(f"ER-072 advisory prompts within {ADVISORY_PROMPT_CEILING} chars",
          not oversize,
          ", ".join(f"{f}={n}" for f, n in oversize))

    # --- 7. State-file checks: ER-007 drift, ER-013 trust cost --------------
    state_path = path + ".state.jsonl"
    print("\n== STATE-FILE CHECKS (advisor attitudes, ER-007/ER-013) ==")
    if not os.path.exists(state_path):
        print(f"  no state file beside the log ({state_path}) - "
              "run the campaign harness with WARGAME_CALL_LOG set to get "
              "attitude-drift evidence; checks skipped")
    else:
        dumps = sorted(load(state_path), key=lambda d: d.get("turn", 0))

        def trust_of(dump):
            return {cid: a.get("trust") for cid, a in dump.get("advisors", {}).items()}

        if len(dumps) < 2:
            check("ER-007 advisor attitudes drift over the campaign", False,
                  f"only {len(dumps)} state dump(s) - nothing to compare")
        else:
            first, last = dumps[0], dumps[-1]
            print(f"  drift, turn {first.get('turn')} -> turn {last.get('turn')}:")
            drifted = []
            for cid, a0 in first.get("advisors", {}).items():
                a1 = last.get("advisors", {}).get(cid, {})
                t0, t1 = a0.get("trust"), a1.get("trust")
                mark = ""
                if t0 != t1:
                    drifted.append(cid)
                    mark = "  <- drifted"
                print(f"    {a0.get('name', cid):32s} trust {str(t0):>3} -> {str(t1):>3}  "
                      f"{a0.get('relationship', '?'):8s} -> {a1.get('relationship', '?'):8s}"
                      f"{mark}")
            check("ER-007 advisor attitudes drift over the campaign",
                  bool(drifted),
                  f"trust moved for {drifted}" if drifted else
                  "no advisor's trust moved between the first and last state dump")

        # ER-013/ER-073: on any turn whose interpretation drew pushback (and
        # the harness committed the identical text), the cost must actually
        # have been charged. The dump's "pushback_costs" field is the
        # manager's own record of who paid (net trust can mask a -1 behind
        # the same turn's attitude drift, so deltas alone are not evidence).
        pushback_dumps = [d for d in dumps if d.get("pushback_roles")]
        if not pushback_dumps:
            print("  no pushback occurred in this run - ER-013 trust-cost "
                  "check skipped (nothing to verify)")
        else:
            for dump in pushback_dumps:
                turn = dump.get("turn")
                roles = dump["pushback_roles"]
                costs = dump.get("pushback_costs")
                if costs is None:
                    print(f"  turn {turn}: state dump predates the "
                          "pushback_costs record - cannot verify this turn")
                    continue
                print(f"  turn {turn}: objectors {roles} -> charged {costs}")
                # After the ER-073 persona-title bridge, every known cabinet
                # role must resolve; "government leader" is the PM (free).
                expected = [r for r in roles
                            if str(r).strip().lower() != "government leader"]
                check(f"ER-013/073 pushback on turn {turn} charged the objectors",
                      bool(costs) or not expected,
                      f"charged {len(costs)} of {len(expected)} chargeable objectors"
                      if costs or not expected else
                      f"objectors {expected} committed over unamended but "
                      "nobody was charged")

    # --- 8. Cost estimate ---------------------------------------------------
    print("\n== COST ESTIMATE (rough: chars/4 as tokens) ==")
    print(f"  {'family':28s} {'calls':>6s} {'prompt~tok':>11s} {'reply~tok':>10s}")
    tot_p = tot_r = 0
    for family in sorted(by_family):
        rs = by_family[family]
        p = sum(len(r["prompt"]) for r in rs) // 4
        rep = sum(len(r.get("reply") or "") for r in rs) // 4
        tot_p += p
        tot_r += rep
        print(f"  {family:28s} {len(rs):6d} {p:11,d} {rep:10,d}")
    print(f"  {'TOTAL':28s} {len(records):6d} {tot_p:11,d} {tot_r:10,d}")
    print("  note: this is an estimate (4 chars per token heuristic); "
          "actual billed tokens depend on the provider's tokenizer")

    # --- verdict ------------------------------------------------------------
    print("\n== VERDICT ==")
    if failures:
        for f in failures:
            print(f"  FAIL {f}")
        sys.exit(1)
    print(f"  all checks passed over {len(records)} calls")


if __name__ == "__main__":
    main()
