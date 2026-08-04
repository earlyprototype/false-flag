"""Size and price a turn's prompts against a real saved campaign.

The synthetic campaign a test harness plays has a much smaller transcript
than a real one - short canned answers, few turns - so it is the wrong thing
to quote costs from. This builds the prompts a turn actually issues against
the transcript of a saved campaign, measures how much of each is a shared
prefix, and prices the turn both ways.

Usage:
    python3 dev-scripts/measure_prompt_costs.py saves/parked_campaign4_borrowed_faces.json
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Live OpenRouter pricing, checked 2026-08-04 (see issue #32). Dollars per
# million tokens. qwen3.5-flash exposes no cache pricing at all; qwen3.7's
# headline $0.030 applies only below 32,000 tokens, which no prompt here is.
MODELS = {
    "qwen/qwen3.5-flash-02-23": {"input": 0.065, "cached": None},
    "qwen/qwen3.7-flash": {"input": 0.100, "cached": 0.020},
}

# Characters per token. The transcript is English prose with heavy ASCII
# rulers, which tokenises a little denser than the usual 4.0 rule of thumb;
# 4.0 is kept as the round, conservative figure.
CHARS_PER_TOKEN = 4.0


def shared_prefix(a: str, b: str) -> int:
    limit = min(len(a), len(b))
    i = 0
    while i < limit and a[i] == b[i]:
        i += 1
    return i


def main():
    save_path = Path(sys.argv[1] if len(sys.argv) > 1
                     else "saves/parked_campaign4_borrowed_faces.json")
    save = json.loads(save_path.read_text(encoding="utf-8"))
    transcript = save.get("transcript") or save.get("full_transcript") or []
    if not transcript:
        print(f"no transcript in {save_path}")
        return

    from llm.context_builder import build_shared_context_prefix
    from llm.prompts import (
        build_advisor_context,
        build_critical_omissions_prompt,
        build_decision_interpretation_prompt,
        build_pushback_prompt,
    )
    from models.world import Metrics, WorldState

    world = WorldState(
        turn=len(transcript) // 100, scene=1, phase="decision",
        metrics=Metrics(escalation_risk=78, domestic_stability=32,
                        alliance_cohesion=54, casualties_mil=6, casualties_civ=14),
        flags={}, posture={}, narrative=None,
    )
    conditions = {
        "characters": {
            cid: {"role": cid.replace("_", " ").title(),
                  "knowledge_domains": ["military_operations"],
                  "key_concerns": ["escalation"], "pushback_triggers": ["risk"]}
            for cid in ("foreign_secretary", "chief_defence_staff",
                        "attorney_general", "home_secretary",
                        "national_security_advisor")
        },
        "constraints": {"legal": ["Article 51"]},
        "uk_forces": {"navy": "2 Type-45"},
        "stockpiles": {"missiles": 40},
    }

    decision = "Hold the deployment and convene the North Atlantic Council."
    prompts = [
        ("advisor_qa", build_advisor_context(
            world, conditions, "foreign_secretary", "Where does NATO stand?",
            transcript)),
        ("decision_interpretation", build_decision_interpretation_prompt(
            world, decision, conditions, transcript)),
        ("advisor_pushback", build_pushback_prompt(
            world, decision, "INTERPRETATION: hold", conditions, transcript)),
    ]
    for cid in ("foreign_secretary", "chief_defence_staff", "attorney_general",
                "home_secretary", "national_security_advisor"):
        prompts.append((f"omissions:{cid}", build_critical_omissions_prompt(
            world, conditions, cid, decision, ["Submarine detected"], transcript)))

    total_chars = sum(len(line) + 1 for line in transcript)
    print(f"{save_path.name}: {len(transcript):,} transcript lines, "
          f"{total_chars:,} chars (~{total_chars / CHARS_PER_TOKEN:,.0f} tokens)\n")

    dossier = build_shared_context_prefix(transcript, world)
    print(f"shared dossier: {len(dossier):,} chars "
          f"(~{len(dossier) / CHARS_PER_TOKEN:,.0f} tokens)\n")

    print(f"{'call':28} {'chars':>10} {'shared with 1st':>16} {'unique':>9}")
    first = prompts[0][1]
    billed_full = 0
    billed_cached = 0
    for name, prompt in prompts:
        shared = len(prompt) if prompt is first else shared_prefix(first, prompt)
        unique = len(prompt) - shared
        print(f"{name:28} {len(prompt):10,} {shared:16,} {unique:9,}")
        if prompt is first:
            billed_full += len(prompt)      # the first call writes the cache
        else:
            billed_cached += shared
            billed_full += unique

    print(f"\nper turn, these {len(prompts)} calls send "
          f"{sum(len(p) for _, p in prompts):,} chars")
    print(f"  billed at full rate:  {billed_full:,} chars")
    print(f"  billed at cache rate: {billed_cached:,} chars")

    print(f"\n{'model':30} {'no caching':>12} {'with caching':>14}")
    for model, price in MODELS.items():
        plain = sum(len(p) for _, p in prompts) / CHARS_PER_TOKEN / 1e6 * price["input"]
        if price["cached"] is None:
            print(f"{model:30} ${plain:11.4f} {'not offered':>14}")
        else:
            cached = (billed_full / CHARS_PER_TOKEN / 1e6 * price["input"]
                      + billed_cached / CHARS_PER_TOKEN / 1e6 * price["cached"])
            print(f"{model:30} ${plain:11.4f} ${cached:13.4f}")


if __name__ == "__main__":
    main()
