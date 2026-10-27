"""Generate a synthetic match JSON file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from matchbrain.sim.simulator import DEMO_SCENARIO, DEMO_SEED, MatchSim, Scenario


def main() -> None:
    p = argparse.ArgumentParser(description="Generate a synthetic match")
    p.add_argument("--seed", type=int, default=DEMO_SEED)
    p.add_argument("--match-id", default="demo")
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()
    sim = MatchSim(seed=args.seed, match_id=args.match_id, scenario=DEMO_SCENARIO if args.seed == DEMO_SEED else Scenario())
    events = sim.run()
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(events))
        print(f"Wrote {len(events)} events to {args.out}  score={sim.score}")
    else:
        print(json.dumps({"score": sim.score, "events": len(events)}))


if __name__ == "__main__":
    main()
