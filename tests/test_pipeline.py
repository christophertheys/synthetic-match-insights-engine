from collections import Counter

from matchbrain.agents.studio import Studio
from matchbrain.catalog import DEMO_PATH, TEAM_NAMES
from matchbrain.engine.pass_model import PassDifficultyModel
from matchbrain.engine.state import MatchState
import json


def test_demo_scoreline_and_facts():
    events = json.loads(DEMO_PATH.read_text())
    state = MatchState("demo", pass_model=PassDifficultyModel())
    for event in events:
        state.apply(event)
    assert state.score == {"HOM": 2, "AWY": 3}
    kinds = Counter(f["kind"] for f in state.facts)
    assert kinds["goal"] == 5
    assert kinds["win_prob_swing"] >= 1
    assert kinds["pass_of_note"] > 0
    assert kinds["period_summary"] == 2
    assert kinds["pressing_shift"] >= 1
    winner = [f for f in state.facts if f["kind"] == "goal" and f["t"] > 80 * 60][0]
    assert winner["subject"]["player_id"] == "AWY-6"
    assert winner["why"]["after"] > 0.9


def test_studio_emits_persona_cues():
    events = json.loads(DEMO_PATH.read_text())
    studio = Studio.load(events=events, train_model=False)
    meta = studio.meta()
    assert meta["teams"]["HOM"]["name"] == TEAM_NAMES["HOM"]
    assert meta["facts"] >= 8
    analyst = []
    casual = []
    for tick in studio.timeline:
        analyst.extend(tick["cues"]["analyst-en"])
        casual.extend(tick["cues"]["casual-es-home"])
    assert analyst
    assert casual
    assert any(c["lang"] == "es" for c in casual)
    assert any(c["data"]["why"] for c in analyst)
    assert any(c["producer_reason"]["score"] > 0 for c in analyst)
    fujita = [c for tick in studio.timeline for c in tick["cues"]["player-focus-ja"] if (c["data"].get("anchor") or {}).get("player_id") == "AWY-6"]
    assert fujita
