from collections import Counter

from matchbrain.sim.cv_stub import run_stub
from matchbrain.sim.simulator import MatchSim


def summarise(events):
    passes = [e for e in events if e["type"] == "pass"]
    return {
        "passes": len(passes),
        "pass_accuracy": sum(e["outcome"] == "success" for e in passes) / max(1, len(passes)),
        "shots": sum(e["type"] == "shot" for e in events),
        "goals": sum(e["type"] == "goal" for e in events),
    }


def test_simulator_stays_inside_public_norms():
    summaries = [summarise(MatchSim(seed=s, match_id=f"c{s}").run()) for s in range(12)]
    mean_passes = sum(s["passes"] for s in summaries) / len(summaries)
    mean_acc = sum(s["pass_accuracy"] for s in summaries) / len(summaries)
    mean_shots = sum(s["shots"] for s in summaries) / len(summaries)
    mean_goals = sum(s["goals"] for s in summaries) / len(summaries)
    assert 700 < mean_passes < 1400
    assert 0.72 < mean_acc < 0.90
    assert 12 < mean_shots < 40
    assert 1.0 < mean_goals < 5.0


def test_event_types_are_schema_safe():
    events = MatchSim(seed=3, match_id="c3").run()
    allowed = {
        "kickoff",
        "pass",
        "carry",
        "shot",
        "tackle",
        "interception",
        "pressure",
        "turnover",
        "foul",
        "card",
        "substitution",
        "goal",
        "period_end",
    }
    types = Counter(e["type"] for e in events)
    assert set(types) <= allowed
    assert types["pass"] > 100


def test_cv_stub_reports_scores():
    events = MatchSim(seed=3, match_id="c3").run()
    report = run_stub(events, seed=1)
    assert 0.5 < report["precision"] <= 1
    assert 0.5 < report["recall"] <= 1
