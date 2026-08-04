"""Summarise a fake_openrouter call log: call counts, critical path, prefix sharing.

Answers the three questions issue #32 turns on:

1. How many LLM calls does a turn make, and of what kind?
2. How much of a turn's wall clock is spent with exactly one call in flight?
   (Sequential time is the parallelisation headroom.)
3. How much of each prompt is a shared prefix with the other prompts in the
   same turn? (Shared prefix is what a provider's cache can match.)

Usage:
    python3 dev-scripts/analyse_calls.py calls.jsonl
"""

import json
import sys
from collections import Counter


def load(path):
    with open(path, encoding="utf-8") as handle:
        records = [json.loads(line) for line in handle if line.strip()]

    # Prefix analysis is done here rather than in the server, because doing it
    # per request compares every prompt against every earlier one and adds
    # minutes to the campaign it is supposed to be timing.
    try:
        with open(path + ".prompts", encoding="utf-8") as handle:
            prompts = [json.loads(line) for line in handle if line.strip()]
    except FileNotFoundError:
        return records

    seen = []
    # zip stops at the shorter input, so a truncated sidecar would silently
    # leave records unanalysed and a missing middle line would shift every
    # later pairing. Neither should look like a clean run.
    if len(records) != len(prompts):
        raise ValueError(f"{path} has {len(records)} records but "
                         f"{path}.prompts has {len(prompts)} prompts")
    for record, prompt in zip(records, prompts):
        reusable = 0
        for earlier in seen:
            limit = min(len(earlier), len(prompt))
            index = 0
            while index < limit and earlier[index] == prompt[index]:
                index += 1
            if index > reusable:
                reusable = index
        seen.append(prompt)
        record["cache_prefix_chars"] = reusable
    return records


def concurrency_profile(records):
    """Return (wall, busy, sequential) seconds across the whole log.

    ``sequential`` is time with exactly one call in flight — the part a fan-out
    could compress. ``busy`` is time with at least one call in flight.
    """
    events = []
    for record in records:
        events.append((record["t_start"], 1))
        events.append((record["t_end"], -1))
    events.sort()

    inflight = 0
    previous = events[0][0] if events else 0.0
    busy = 0.0
    sequential = 0.0
    for timestamp, delta in events:
        span = timestamp - previous
        if inflight >= 1:
            busy += span
        if inflight == 1:
            sequential += span
        inflight += delta
        previous = timestamp
    wall = events[-1][0] - events[0][0] if events else 0.0
    return wall, busy, sequential


def shared_prefix(a: str, b: str) -> int:
    limit = min(len(a), len(b))
    index = 0
    while index < limit and a[index] == b[index]:
        index += 1
    return index


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "calls.jsonl"
    records = load(path)
    if not records:
        print("empty log")
        return

    print(f"{len(records)} calls\n")

    kinds = Counter(r["kind"] for r in records)
    chars = {}
    for record in records:
        chars.setdefault(record["kind"], []).append(record["prompt_chars"])

    print(f"{'call kind':24} {'n':>4} {'mean chars':>11} {'max chars':>10}")
    for kind, count in kinds.most_common():
        sizes = chars[kind]
        print(f"{kind:24} {count:4d} {sum(sizes) // len(sizes):11,} {max(sizes):10,}")

    wall, busy, sequential = concurrency_profile(records)
    print(f"\nwall {wall:.1f}s | at least one call in flight {busy:.1f}s "
          f"({busy / wall * 100 if wall else 0:.0f}%) | exactly one {sequential:.1f}s "
          f"({sequential / wall * 100 if wall else 0:.0f}%)")

    duplicate_prefixes = Counter(r["prefix_1k"] for r in records)
    # For a prefix seen n times only n-1 calls match an *earlier* call; the
    # first establishes it. Counting all n reports 2/2 where it means 1/2.
    shared = sum(count - 1 for count in duplicate_prefixes.values() if count > 1)
    print(f"\ncalls whose first 1,000 chars match an earlier call: "
          f"{shared}/{len(records)} "
          f"({shared / len(records) * 100 if records else 0:.0f}%)")

    # The cacheable region: leading characters each prompt shares with the
    # closest prompt already sent. This is what a provider bills at the
    # cache-read rate instead of the full input rate.
    reusable = [r.get("cache_prefix_chars", 0) for r in records]
    total_chars = sum(r["prompt_chars"] for r in records)
    total_reusable = sum(reusable)
    print(f"total prompt characters sent: {total_chars:,}")
    print(f"of which a prefix cache could match: {total_reusable:,} "
          f"({total_reusable / total_chars * 100 if total_chars else 0:.1f}%)")

    print(f"\n{'call kind':24} {'mean cacheable prefix':>22} {'as % of prompt':>16}")
    by_kind = {}
    for record in records:
        by_kind.setdefault(record["kind"], []).append(record)
    for kind, _ in kinds.most_common():
        group = by_kind[kind]
        mean_prefix = sum(r.get("cache_prefix_chars", 0) for r in group) // len(group)
        mean_size = sum(r["prompt_chars"] for r in group) // len(group)
        print(f"{kind:24} {mean_prefix:22,} {mean_prefix / max(1, mean_size) * 100:15.0f}%")


if __name__ == "__main__":
    main()
