"""Broadcast studio: four cooperating agents on a shared match blackboard.

Scout    — turns MatchEvents into InsightFacts (analytics, no prose)
Producer — ranks facts per persona with an explainable score
Narrator — grounded captions; Azure AI Foundry / GitHub Models when configured
Verifier — drops any caption whose numbers are not in the fact slots

This is a deterministic multi-agent pipeline (shared state + typed handoffs),
designed so each role can be swapped for a Microsoft Foundry agent later.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field

from matchbrain.catalog import DEMO_PATH, KEY_MOMENTS, MODEL_PATH, PERSONAS, TEAM_NAMES, roster
from matchbrain.engine.pass_model import PassDifficultyModel
from matchbrain.engine.producer import Producer
from matchbrain.engine.state import MatchState
from matchbrain.narrator.llm import Narrator, provider_name
from matchbrain.narrator.verifier import verify
from matchbrain.sim.cv_stub import run_stub


@dataclass
class Studio:
    events: list[dict]
    personas: list[dict]
    state: MatchState
    producers: dict[str, Producer]
    narrator: Narrator
    timeline: list[dict] = field(default_factory=list)
    cv_report: dict = field(default_factory=dict)
    warm_ms: float = 0.0

    @classmethod
    def load(cls, events: list[dict] | None = None, train_model: bool = True) -> "Studio":
        if events is None:
            events = json.loads(DEMO_PATH.read_text())
        t0 = time.perf_counter()
        if train_model:
            model = PassDifficultyModel.load_or_train(MODEL_PATH)
        else:
            model = PassDifficultyModel()
        studio = cls(
            events=events,
            personas=PERSONAS,
            state=MatchState(events[0]["match_id"] if events else "demo", pass_model=model),
            producers={p["persona_id"]: Producer(p) for p in PERSONAS},
            narrator=Narrator(),
        )
        studio.warm()
        studio.cv_report = run_stub(events)
        studio.warm_ms = (time.perf_counter() - t0) * 1000
        return studio

    def warm(self) -> None:
        last_emit_t = -1e9
        for event in self.events:
            t0 = time.perf_counter()
            facts = self.state.apply(event)
            snapshot = self.state.snapshot()
            cues: dict[str, list[dict]] = {}
            verified = 0
            rejected = 0
            for persona in self.personas:
                producer = self.producers[persona["persona_id"]]
                emitted = []
                for fact in facts:
                    headline, why, ok = self.narrator.render(fact, persona)
                    if not ok:
                        rejected += 1
                        continue
                    verified += 1
                    cue = producer.try_emit(fact, headline, why, snapshot)
                    if cue:
                        emitted.append(cue)
                cues[persona["persona_id"]] = emitted
            latency_ms = (time.perf_counter() - t0) * 1000
            interesting = bool(facts) or event["type"] in ("shot", "goal", "card", "kickoff", "period_end")
            if interesting or event["t"] - last_emit_t >= 12:
                self.timeline.append(
                    {
                        "t": event["t"],
                        "event": event,
                        "facts": facts,
                        "cues": cues,
                        "snapshot": snapshot,
                        "latency_ms": round(latency_ms, 3),
                        "verifier": {"passed": verified, "rejected": rejected},
                    }
                )
                last_emit_t = event["t"]

    def meta(self) -> dict:
        snap = self.timeline[-1]["snapshot"] if self.timeline else self.state.snapshot()
        return {
            "match_id": self.state.match_id,
            "teams": {
                "HOM": {"id": "HOM", "name": TEAM_NAMES["HOM"], "abbr": "NOR", "color": "#6ea0ff"},
                "AWY": {"id": "AWY", "name": TEAM_NAMES["AWY"], "abbr": "RIV", "color": "#ff7a59"},
            },
            "roster": roster(),
            "personas": self.personas,
            "key_moments": KEY_MOMENTS,
            "final": snap["score"],
            "events": len(self.events),
            "facts": len(self.state.facts),
            "timeline": len(self.timeline),
            "narrator": provider_name(),
            "warm_ms": round(self.warm_ms, 1),
            "cv_stub": self.cv_report,
            "agents": [
                {"id": "scout", "role": "Interpret events into insight facts"},
                {"id": "producer", "role": "Rank and schedule overlays per persona"},
                {"id": "narrator", "role": "Caption facts in the viewer's language"},
                {"id": "verifier", "role": "Reject captions with unsupported numbers"},
            ],
        }

    def recap(self, persona_id: str) -> dict:
        persona = next(p for p in self.personas if p["persona_id"] == persona_id)
        story_kinds = {"goal", "win_prob_swing", "period_summary", "pressing_shift", "control_chaos_shift"}
        stories = [f for f in self.state.facts if f["kind"] in story_kinds]
        ft = [f for f in stories if f["kind"] == "period_summary" and (f.get("metrics") or {}).get("label") == "full_time"]
        rest = sorted((f for f in stories if f not in ft), key=lambda f: f["importance"], reverse=True)
        top = (ft + rest)[:8]
        text = self.narrator.recap(top, persona, self.state.snapshot())
        return {"persona_id": persona_id, "lang": persona["lang"], "text": text, "fact_ids": [f["fact_id"] for f in top]}

    def forge_demo(self) -> dict:
        goals = [f for f in self.state.facts if f["kind"] == "goal"]
        goal = max(goals, key=lambda f: float((f.get("why") or {}).get("delta") or f.get("importance") or 0))
        persona = self.personas[0]
        real, why, ok = self.narrator.render(goal, persona)
        forged = real.replace(f"{round((goal['why']['after'] or 0) * 100)}%", "91%")
        if forged == real:
            forged = real + " 91%"
        caught, bad = verify(forged, goal)
        return {
            "fact_id": goal["fact_id"],
            "real": real,
            "why": why,
            "real_ok": ok,
            "forged": forged,
            "forged_ok": caught,
            "unsupported": bad,
        }
