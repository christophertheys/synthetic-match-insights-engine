"""Live match state: running picture of the game, updated after every event."""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field

from matchbrain.catalog import roster
from matchbrain.engine.pass_model import PassDifficultyModel
from matchbrain.engine.winprob import table as win_table
from matchbrain.engine.winprob import win_prob

TEAMS = ("HOM", "AWY")
PITCH_X, PITCH_Y = 105.0, 68.0
ROLE_PACE = {"GK": 0.45, "DF": 0.95, "MF": 1.18, "FW": 1.08}


def opp(team: str) -> str:
    return "AWY" if team == "HOM" else "HOM"


def to_display(team: str, x: float, y: float) -> dict:
    if team == "HOM":
        return {"x": round(x, 2), "y": round(y, 2)}
    return {"x": round(PITCH_X - x, 2), "y": round(PITCH_Y - y, 2)}


@dataclass
class PlayerLive:
    player_id: str
    team_id: str
    number: int
    role: str
    name: str
    on_pitch: bool = True
    distance_km: float = 0.0
    max_speed_kmh: float = 0.0
    passes: int = 0
    passes_ok: int = 0
    shots: int = 0
    goals: int = 0
    last_x: float | None = None
    last_y: float | None = None
    milestones: set = field(default_factory=set)


class MatchState:
    def __init__(self, match_id: str, pass_model: PassDifficultyModel | None = None):
        self.match_id = match_id
        self.pass_model = pass_model or PassDifficultyModel()
        self.score = {"HOM": 0, "AWY": 0}
        self.men = {"HOM": 11, "AWY": 11}
        self.t = 0.0
        self.period = 1
        self.possession = "HOM"
        self.chain_len = 0
        self.chain_lengths: deque[int] = deque(maxlen=40)
        self.window: deque[dict] = deque()
        self.shots: dict[str, dict] = {}
        self.wp = {"HOM": 0.5, "AWY": 0.5, "DRAW": 0.0}
        self.ppda = {"HOM": 12.0, "AWY": 12.0}
        self.control = 0.55
        self.tempo = 10.0
        self.last_ppda_emit = {"HOM": 12.0, "AWY": 12.0}
        self.last_control_emit = 0.55
        self.last_tempo_emit = 10.0
        self.fact_n = 0
        self.facts: list[dict] = []
        self.last_pass: dict | None = None
        self.ball = {"x": 52.5, "y": 34.0, "team_id": "HOM"}
        self.players = {
            p["player_id"]: PlayerLive(
                player_id=p["player_id"],
                team_id=p["team_id"],
                number=p["number"],
                role=p["role"],
                name=p["name"],
            )
            for p in roster()
        }
        self.assist_by_goal: dict[str, str | None] = {}
        self._last_successful_pass: dict | None = None

    def _next_id(self) -> str:
        fid = f"f-{self.fact_n:04d}"
        self.fact_n += 1
        return fid

    def _emit_fact(self, **kw) -> dict:
        fact = {"fact_id": self._next_id(), "match_id": self.match_id, **kw}
        self.facts.append(fact)
        return fact

    def _tick_distance(self, t: float) -> None:
        dt = max(0.0, t - self.t)
        if dt == 0:
            return
        for p in self.players.values():
            if not p.on_pitch:
                continue
            p.distance_km += 7.0 * (dt / 3600.0) * ROLE_PACE.get(p.role, 1.0)

    def _prune_window(self, t: float, span: float = 600.0) -> None:
        while self.window and t - self.window[0]["t"] > span:
            self.window.popleft()

    def _counts(self, span: float, pred) -> int:
        cutoff = self.t - span
        return sum(1 for w in self.window if w["t"] >= cutoff and pred(w))

    def _recompute_metrics(self) -> None:
        for team in TEAMS:
            opp_passes = self._counts(600, lambda w, t=team: w["type"] == "pass" and w["team"] == opp(t))
            actions = self._counts(600, lambda w, t=team: w["type"] in ("tackle", "interception", "foul") and w["team"] == t)
            self.ppda[team] = round(opp_passes / max(actions, 1), 2)
        turnovers = self._counts(300, lambda w: w["type"] == "turnover")
        to_per_min = turnovers / 5.0
        to_norm = min(1.0, to_per_min / 4.0)
        mean_chain = (sum(self.chain_lengths) / len(self.chain_lengths)) if self.chain_lengths else 3.0
        chain_norm = min(1.0, mean_chain / 6.0)
        hom_passes = self._counts(300, lambda w: w["type"] == "pass" and w["team"] == "HOM")
        awy_passes = self._counts(300, lambda w: w["type"] == "pass" and w["team"] == "AWY")
        total = max(1, hom_passes + awy_passes)
        p = hom_passes / total
        entropy = 0.0 if p in (0, 1) else -p * math.log(p) - (1 - p) * math.log(1 - p)
        entropy_norm = entropy / math.log(2)
        self.control = round(0.4 * (1 - to_norm) + 0.35 * chain_norm + 0.25 * (1 - entropy_norm), 3)
        self.tempo = round(self._counts(300, lambda w: w["type"] == "pass") / 5.0, 2)
        self.wp = win_table(self.t / 60, self.score, self.men)

    def apply(self, event: dict) -> list[dict]:
        self._tick_distance(event["t"])
        self.t = event["t"]
        self.period = event.get("period") or self.period
        new_facts: list[dict] = []
        etype = event["type"]
        team = event.get("team_id")
        player_id = event.get("player_id")
        start = event.get("start")
        end = event.get("end")

        if start:
            self.ball = {**to_display(team, start["x"], start["y"]), "team_id": team}
            if player_id and player_id in self.players:
                self.players[player_id].last_x = self.ball["x"]
                self.players[player_id].last_y = self.ball["y"]
        if end and etype in ("pass", "carry", "shot"):
            self.ball = {**to_display(team, end["x"], end["y"]), "team_id": team}

        if etype in ("pass", "carry", "shot", "tackle", "interception", "foul", "turnover", "pressure"):
            self.window.append({"t": self.t, "type": etype, "team": team})
            self._prune_window(self.t)

        if etype == "pass":
            self.possession = team
            self.chain_len = self.chain_len + 1 if event.get("outcome") == "success" else 0
            if event.get("outcome") != "success":
                self.chain_lengths.append(self.chain_len if self.chain_len else 1)
            pl = self.players.get(player_id)
            if pl:
                pl.passes += 1
                if event.get("outcome") == "success":
                    pl.passes_ok += 1
            difficulty = self.pass_model.difficulty(event) if start and end else 0.4
            self.last_pass = {
                "start": to_display(team, start["x"], start["y"]) if start else None,
                "end": to_display(team, end["x"], end["y"]) if end else None,
                "difficulty": round(difficulty, 3),
                "success": event.get("outcome") == "success",
                "player_id": player_id,
                "recipient_id": event.get("recipient_id"),
                "speed_kmh": event.get("speed_kmh"),
                "tags": event.get("tags") or [],
            }
            if event.get("outcome") == "success":
                self._last_successful_pass = event
            if event.get("outcome") == "success" and difficulty > 0.5:
                new_facts.append(
                    self._emit_fact(
                        t=self.t,
                        kind="pass_of_note",
                        importance=round(min(1.0, 0.35 + difficulty), 2),
                        subject={"team_id": team, "player_id": player_id},
                        metrics={
                            "minute": int(self.t / 60) + 1,
                            "difficulty": round(difficulty, 3),
                            "distance_m": round(float(np_hypot(start, end)), 1) if start and end else 0,
                            "speed_kmh": round(float(event.get("speed_kmh") or 0), 1),
                            "line_breaking": "line_breaking" in (event.get("tags") or []),
                        },
                        why={"driver": "pass_difficulty", "before": 0.5, "after": round(difficulty, 3), "delta": round(difficulty - 0.5, 3), "window_s": 0},
                        evidence=[event["event_id"]],
                        audience_tags=["analyst", "stat"],
                    )
                )

        elif etype == "carry":
            self.possession = team
            if start and end:
                dist = math.hypot(end["x"] - start["x"], end["y"] - start["y"])
                dt = 1.2
                speed = dist / dt * 3.6
                pl = self.players.get(player_id)
                if pl:
                    pl.max_speed_kmh = max(pl.max_speed_kmh, speed)
                if speed >= 30:
                    new_facts.append(
                        self._emit_fact(
                            t=self.t,
                            kind="sprint",
                            importance=0.42,
                            subject={"team_id": team, "player_id": player_id},
                            metrics={"minute": int(self.t / 60) + 1, "speed_kmh": round(speed, 1), "distance_m": round(dist, 1)},
                            why={"driver": "speed", "before": 30, "after": round(speed, 1), "delta": round(speed - 30, 1), "window_s": 0},
                            evidence=[event["event_id"]],
                            audience_tags=["casual", "stat"],
                        )
                    )

        elif etype == "shot":
            self.shots[event["event_id"]] = event
            pl = self.players.get(player_id)
            if pl:
                pl.shots += 1
            xg = float(event.get("xg") or 0)
            speed = float(event.get("speed_kmh") or 0)
            if xg >= 0.25 and event.get("outcome") != "goal":
                new_facts.append(
                    self._emit_fact(
                        t=self.t,
                        kind="big_chance",
                        importance=round(min(1.0, 0.4 + xg), 2),
                        subject={"team_id": team, "player_id": player_id},
                        metrics={"minute": int(self.t / 60) + 1, "xg": round(xg, 3), "shot_speed_kmh": round(speed, 1), "outcome": event.get("outcome") or ""},
                        why={"driver": "xt", "before": 0.1, "after": round(xg, 3), "delta": round(xg - 0.1, 3), "window_s": 0},
                        evidence=[event["event_id"]],
                        audience_tags=["analyst", "story"],
                    )
                )
            if speed >= 100:
                new_facts.append(
                    self._emit_fact(
                        t=self.t,
                        kind="shot_speed",
                        importance=0.4,
                        subject={"team_id": team, "player_id": player_id},
                        metrics={"minute": int(self.t / 60) + 1, "shot_speed_kmh": round(speed, 1)},
                        why={"driver": "speed", "before": 100, "after": round(speed, 1), "delta": round(speed - 100, 1), "window_s": 0},
                        evidence=[event["event_id"]],
                        audience_tags=["casual", "stat"],
                    )
                )

        elif etype == "goal":
            before = win_prob(team, self.t / 60, self.score, self.men)
            self.score[team] += 1
            after = win_prob(team, self.t / 60, self.score, self.men)
            pl = self.players.get(player_id)
            if pl:
                pl.goals += 1
            shot_id = None
            for tag in event.get("tags") or []:
                if tag.startswith("shot:"):
                    shot_id = tag.split(":", 1)[1]
            shot = self.shots.get(shot_id or "", {})
            assist_id = None
            if self._last_successful_pass and self._last_successful_pass.get("team_id") == team:
                if self._last_successful_pass.get("recipient_id") == player_id:
                    assist_id = self._last_successful_pass.get("player_id")
            new_facts.append(
                self._emit_fact(
                    t=self.t,
                    kind="goal",
                    importance=round(min(1.0, abs(after - before) * 2), 2),
                    subject={"team_id": team, "player_id": player_id},
                    metrics={
                        "minute": int(self.t / 60) + 1,
                        "xg": float(shot.get("xg") or 0),
                        "shot_speed_kmh": float(shot.get("speed_kmh") or 0),
                        "score_home": self.score["HOM"],
                        "score_away": self.score["AWY"],
                        "assist_player_id": assist_id or "",
                    },
                    why={"driver": "win_probability", "before": round(before, 3), "after": round(after, 3), "delta": round(after - before, 3), "window_s": 0},
                    evidence=[eid for eid in (shot_id, event["event_id"]) if eid],
                    audience_tags=["casual", "analyst", "story"],
                )
            )
            self.chain_len = 0

        elif etype == "card" and event.get("outcome") == "red":
            before = win_prob(team, self.t / 60, self.score, self.men)
            self.men[team] = max(7, self.men[team] - 1)
            if player_id and player_id in self.players:
                self.players[player_id].on_pitch = False
            after = win_prob(team, self.t / 60, self.score, self.men)
            new_facts.append(
                self._emit_fact(
                    t=self.t,
                    kind="win_prob_swing",
                    importance=round(min(1.0, abs(after - before) * 2 + 0.3), 2),
                    subject={"team_id": team, "player_id": player_id},
                    metrics={"minute": int(self.t / 60) + 1, "players_on_pitch": self.men[team], "card": "red", "score_home": self.score["HOM"], "score_away": self.score["AWY"]},
                    why={"driver": "win_probability", "before": round(before, 3), "after": round(after, 3), "delta": round(after - before, 3), "window_s": 0},
                    evidence=[event["event_id"]],
                    audience_tags=["casual", "analyst", "story"],
                )
            )

        elif etype == "period_end":
            kind_label = "half_time" if self.period == 1 else "full_time"
            new_facts.append(
                self._emit_fact(
                    t=self.t,
                    kind="period_summary",
                    importance=0.85 if kind_label == "full_time" else 0.7,
                    subject={"team_id": None, "player_id": None},
                    metrics={
                        "minute": int(self.t / 60),
                        "score_home": self.score["HOM"],
                        "score_away": self.score["AWY"],
                        "period": self.period,
                        "label": kind_label,
                        "wp_home": round(self.wp["HOM"], 3),
                        "wp_away": round(self.wp["AWY"], 3),
                    },
                    why={"driver": "milestone", "before": 0, "after": self.period, "delta": 1, "window_s": self.t},
                    evidence=[event["event_id"]],
                    audience_tags=["casual", "analyst", "story"],
                )
            )

        self._recompute_metrics()

        for team_id in TEAMS:
            prev = self.last_ppda_emit[team_id]
            cur = self.ppda[team_id]
            if self.t > 600 and prev - cur >= 1.8:
                new_facts.append(
                    self._emit_fact(
                        t=self.t,
                        kind="pressing_shift",
                        importance=round(min(1.0, 0.35 + (prev - cur) / 10), 2),
                        subject={"team_id": team_id, "player_id": None},
                        metrics={"minute": int(self.t / 60) + 1, "ppda_before": round(prev, 2), "ppda_after": round(cur, 2)},
                        why={"driver": "ppda", "before": round(prev, 2), "after": round(cur, 2), "delta": round(cur - prev, 2), "window_s": 600},
                        evidence=[event["event_id"]],
                        audience_tags=["analyst", "story"],
                    )
                )
                self.last_ppda_emit[team_id] = cur
            elif cur > prev:
                self.last_ppda_emit[team_id] = cur * 0.3 + prev * 0.7

        if self.t > 300 and abs(self.control - self.last_control_emit) >= 0.12:
            new_facts.append(
                self._emit_fact(
                    t=self.t,
                    kind="control_chaos_shift",
                    importance=round(min(1.0, 0.3 + abs(self.control - self.last_control_emit)), 2),
                    subject={"team_id": self.possession, "player_id": None},
                    metrics={"minute": int(self.t / 60) + 1, "control": self.control, "tempo": self.tempo},
                    why={"driver": "control_index", "before": self.last_control_emit, "after": self.control, "delta": round(self.control - self.last_control_emit, 3), "window_s": 300},
                    evidence=[event["event_id"]],
                    audience_tags=["analyst", "story"],
                )
            )
            self.last_control_emit = self.control

        if self.t > 300 and abs(self.tempo - self.last_tempo_emit) >= 4:
            new_facts.append(
                self._emit_fact(
                    t=self.t,
                    kind="tempo_change",
                    importance=0.38,
                    subject={"team_id": self.possession, "player_id": None},
                    metrics={"minute": int(self.t / 60) + 1, "tempo": self.tempo},
                    why={"driver": "tempo", "before": self.last_tempo_emit, "after": self.tempo, "delta": round(self.tempo - self.last_tempo_emit, 2), "window_s": 300},
                    evidence=[event["event_id"]],
                    audience_tags=["analyst"],
                )
            )
            self.last_tempo_emit = self.tempo

        for pl in self.players.values():
            for mark in (5.0, 8.0, 10.0):
                key = (pl.player_id, mark)
                if mark not in pl.milestones and pl.distance_km >= mark:
                    pl.milestones.add(mark)
                    new_facts.append(
                        self._emit_fact(
                            t=self.t,
                            kind="distance_milestone",
                            importance=0.33 if mark < 10 else 0.5,
                            subject={"team_id": pl.team_id, "player_id": pl.player_id},
                            metrics={"minute": int(self.t / 60) + 1, "distance_km": round(pl.distance_km, 2), "milestone_km": mark},
                            why={"driver": "distance", "before": mark - 1, "after": mark, "delta": 1, "window_s": self.t},
                            evidence=[event["event_id"]],
                            audience_tags=["casual", "stat"],
                        )
                    )

        return new_facts

    def snapshot(self) -> dict:
        return {
            "t": round(self.t, 2),
            "period": self.period,
            "score": dict(self.score),
            "men": dict(self.men),
            "wp": {k: round(v, 3) for k, v in self.wp.items()},
            "ppda": dict(self.ppda),
            "control": self.control,
            "tempo": self.tempo,
            "possession": self.possession,
            "chain_len": self.chain_len,
            "ball": self.ball,
            "last_pass": self.last_pass,
            "players": {
                pid: {
                    "player_id": p.player_id,
                    "team_id": p.team_id,
                    "name": p.name,
                    "number": p.number,
                    "role": p.role,
                    "on_pitch": p.on_pitch,
                    "distance_km": round(p.distance_km, 2),
                    "max_speed_kmh": round(p.max_speed_kmh, 1),
                    "passes": p.passes,
                    "passes_ok": p.passes_ok,
                    "shots": p.shots,
                    "goals": p.goals,
                    "x": p.last_x,
                    "y": p.last_y,
                }
                for pid, p in self.players.items()
            },
        }


def np_hypot(start: dict, end: dict) -> float:
    return math.hypot(end["x"] - start["x"], end["y"] - start["y"])
