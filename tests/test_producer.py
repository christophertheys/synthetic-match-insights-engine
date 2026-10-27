from matchbrain.catalog import PERSONAS
from matchbrain.engine.producer import Producer


def _fact(kind="pass_of_note", team="AWY", player="AWY-6", importance=0.7, t=4000):
    return {
        "fact_id": "f-x",
        "match_id": "demo",
        "t": t,
        "kind": kind,
        "importance": importance,
        "subject": {"team_id": team, "player_id": player},
        "metrics": {"minute": 67, "difficulty": 0.62},
        "why": {"driver": "pass_difficulty", "before": 0.5, "after": 0.62, "delta": 0.12, "window_s": 0},
        "evidence": ["e1"],
    }


def test_producer_prefers_focus_player():
    persona = next(p for p in PERSONAS if p["persona_id"] == "player-focus-ja")
    producer = Producer(persona)
    focus = producer.score(_fact(player="AWY-6"))
    other = producer.score(_fact(player="HOM-7"))
    assert focus["affinity"] > other["affinity"]
    assert focus["score"] > other["score"]


def test_metric_focus_filters_noise():
    persona = next(p for p in PERSONAS if p["persona_id"] == "pass-nerd-ar")
    producer = Producer(persona)
    snapshot = {"ball": {"x": 80, "y": 20}}
    pass_cue = producer.try_emit(_fact("pass_of_note"), "pass", "why", snapshot)
    sprint_cue = producer.try_emit(_fact("sprint", t=4010, importance=0.9), "sprint", "why", snapshot)
    assert pass_cue is not None
    assert sprint_cue is None
    goal = producer.try_emit(_fact("goal", t=4100, importance=0.9), "goal", "why", snapshot)
    assert goal is not None
