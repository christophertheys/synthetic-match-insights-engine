"""Spike 1: can the simulator produce a believable 90-minute match in under 5 seconds?

Gate:
  - single match generation < 5 s
  - per-match averages inside public aggregate norms
  - every event validates against docs/ideation/schemas/match_event.schema.json
"""

from __future__ import annotations

import json
import statistics as st
import sys
import time
from collections import Counter
from pathlib import Path

from sim import MatchSim, Scenario

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "docs/ideation/schemas/match_event.schema.json").read_text())

NORMS = {
    "passes": (850, 1150),
    "pass_accuracy": (0.78, 0.87),
    "shots": (18, 32),
    "goals": (2.0, 3.4),
    "turnovers": (150, 320),
}

TYPE_MAP = {"string": str, "integer": int, "number": (int, float), "boolean": bool, "array": list, "object": dict, "null": type(None)}


def validate(ev: dict, schema: dict = SCHEMA) -> list[str]:
    """Minimal draft-2020-12 subset: required, type, enum, min/max, $ref to $defs."""
    errs = []
    for key in schema.get("required", []):
        if key not in ev:
            errs.append(f"missing {key}")
    for key, val in ev.items():
        spec = schema["properties"].get(key)
        if spec is None:
            errs.append(f"unknown field {key}")
            continue
        if "$ref" in spec:
            spec = SCHEMA["$defs"][spec["$ref"].split("/")[-1]]
            errs += [f"{key}.{e}" for e in validate(val, spec)]
            continue
        types = spec.get("type")
        if types:
            types = types if isinstance(types, list) else [types]
            py = tuple(t for name in types for t in (TYPE_MAP[name] if isinstance(TYPE_MAP[name], tuple) else (TYPE_MAP[name],)))
            if not isinstance(val, py) or (isinstance(val, bool) and bool not in py):
                errs.append(f"{key} type {type(val).__name__}")
        if "enum" in spec and val not in spec["enum"]:
            errs.append(f"{key}={val!r} not in enum")
        if "minimum" in spec and isinstance(val, (int, float)) and val < spec["minimum"]:
            errs.append(f"{key} < min")
        if "maximum" in spec and isinstance(val, (int, float)) and val > spec["maximum"]:
            errs.append(f"{key} > max")
    return errs


def summarise(events: list[dict]) -> dict:
    passes = [e for e in events if e["type"] == "pass"]
    return {
        "passes": len(passes),
        "pass_accuracy": sum(e["outcome"] == "success" for e in passes) / max(1, len(passes)),
        "shots": sum(e["type"] == "shot" for e in events),
        "goals": sum(e["type"] == "goal" for e in events),
        "turnovers": sum(e["type"] == "turnover" for e in events),
    }


def main() -> int:
    n = 200
    t0 = time.perf_counter()
    times, summaries, bad, total_events = [], [], Counter(), 0
    for seed in range(n):
        s = time.perf_counter()
        events = MatchSim(seed=seed, match_id=f"m{seed:03d}").run()
        times.append(time.perf_counter() - s)
        summaries.append(summarise(events))
        total_events += len(events)
        if seed < 20:
            for ev in events:
                for err in validate(ev):
                    bad[err] += 1
    wall = time.perf_counter() - t0

    print(f"Generated {n} matches, {total_events:,} events in {wall:.1f}s")
    print(f"Per match: mean {st.mean(times) * 1000:.0f} ms, max {max(times) * 1000:.0f} ms")
    ok = max(times) < 5.0

    print("\nPer-match averages vs norms:")
    for key, (lo, hi) in NORMS.items():
        vals = [s[key] for s in summaries]
        mean = st.mean(vals)
        inside = lo <= mean <= hi
        ok &= inside
        fmt = f"{mean:.3f}" if key == "pass_accuracy" else f"{mean:.1f}"
        print(f"  {key:<14} {fmt:>8}  (norm {lo}-{hi})  {'OK' if inside else 'OUT'}")

    print(f"\nSchema validation on 20 matches: {sum(bad.values())} errors")
    for err, c in bad.most_common(5):
        print(f"  {c:>6}  {err}")
    ok &= not bad

    sc = MatchSim(seed=49, match_id="demo", scenario=Scenario(red_card=("HOM", 60), momentum_shift=("AWY", 60, 1.25), high_press="AWY"))
    demo = sc.run()
    out = ROOT / "data/sample/demo_redcard_comeback.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(demo))
    goals = [(round(e["t"] / 60), e["team_id"]) for e in demo if e["type"] == "goal"]
    print(f"\nDemo scenario (seed 49, HOM red card 60', AWY surge): final {sc.score}, goals {goals}")
    print(f"Wrote {out.relative_to(ROOT)}")

    print(f"\nGATE: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
