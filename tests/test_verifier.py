from matchbrain.narrator.llm import Narrator
from matchbrain.narrator.verifier import verify

GOAL = {
    "fact_id": "f-0001",
    "match_id": "demo",
    "t": 5310,
    "kind": "goal",
    "importance": 0.95,
    "subject": {"team_id": "AWY", "player_id": "AWY-6"},
    "metrics": {
        "minute": 89,
        "xg": 0.04,
        "shot_speed_kmh": 90,
        "score_home": 2,
        "score_away": 3,
        "assist_player_id": "AWY-8",
    },
    "why": {"driver": "win_probability", "before": 0.03, "after": 0.98, "delta": 0.95, "window_s": 0},
    "evidence": ["demo-000001", "demo-000002"],
    "audience_tags": ["casual", "analyst"],
}


def test_template_captions_verify():
    narrator = Narrator()
    for mode in ("casual", "analyst"):
        for lang in ("en", "es", "ar", "ja"):
            text, why, ok = narrator.render(GOAL, {"mode": mode, "lang": lang})
            assert ok, (mode, lang, text, verify(text, GOAL))
            assert why


def test_forged_number_rejected():
    narrator = Narrator()
    text, _, ok = narrator.render(GOAL, {"mode": "casual", "lang": "en"})
    assert ok
    forged = text.replace("98%", "91%")
    if forged == text:
        forged = text + " 91%"
    caught, bad = verify(forged, GOAL)
    assert not caught
    assert "91" in bad
