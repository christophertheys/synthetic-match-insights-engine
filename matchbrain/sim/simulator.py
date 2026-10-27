"""Seeded possession-chain match simulator.

Coordinates are team-relative metres on a 105 x 68 pitch: the team in possession
always attacks towards x = 105. Possession changes mirror the ball position.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from matchbrain.catalog import ROLE_BY_NUMBER

PITCH_X, PITCH_Y = 105.0, 68.0
HALF_S = 45 * 60
TEAMS = ("HOM", "AWY")
ROLE_X_RANGE = {"GK": (0, 12), "DF": (10, 50), "MF": (30, 80), "FW": (55, 100)}


@dataclass
class Player:
    player_id: str
    team_id: str
    number: int
    role: str
    passing: float
    finishing: float
    on_pitch: bool = True


@dataclass
class Scenario:
    """Scripted match beats that make demos repeatable."""

    red_card: tuple[str, int] | None = None
    momentum_shift: tuple[str, int, float] | None = None
    high_press: str | None = None


DEMO_SEED = 49
DEMO_SCENARIO = Scenario(red_card=("HOM", 60), momentum_shift=("AWY", 60, 1.25), high_press="AWY")


@dataclass
class MatchSim:
    seed: int
    match_id: str = "m001"
    scenario: Scenario = field(default_factory=Scenario)

    def __post_init__(self) -> None:
        self.rng = np.random.default_rng(self.seed)
        self.players: dict[str, list[Player]] = {}
        for team in TEAMS:
            squad = []
            for n in range(1, 12):
                role = ROLE_BY_NUMBER[n]
                squad.append(
                    Player(
                        player_id=f"{team}-{n}",
                        team_id=team,
                        number=n,
                        role=role,
                        passing=float(np.clip(self.rng.normal(0.78 if role != "GK" else 0.65, 0.07), 0.45, 0.97)),
                        finishing=float(np.clip(self.rng.normal(1.15 if role == "FW" else 0.8, 0.15), 0.3, 1.6)),
                    )
                )
            self.players[team] = squad
        self.strength = {t: 1.0 for t in TEAMS}
        self.events: list[dict] = []
        self.seq = 0
        self.score = {t: 0 for t in TEAMS}

    def _emit(self, **kw) -> dict:
        ev = {"event_id": f"{self.match_id}-{self.seq:06d}", "match_id": self.match_id, "seq": self.seq, "source": "sim", **kw}
        ev["t"] = round(ev["t"], 2)
        self.events.append(ev)
        self.seq += 1
        return ev

    def _active(self, team: str) -> list[Player]:
        return [p for p in self.players[team] if p.on_pitch]

    def _pick_player_near(self, team: str, x: float, exclude: str | None = None) -> Player:
        cands = [p for p in self._active(team) if p.player_id != exclude]
        centres = np.array([sum(ROLE_X_RANGE[p.role]) / 2 for p in cands])
        w = np.exp(-np.abs(centres - x) / 15.0)
        return cands[int(self.rng.choice(len(cands), p=w / w.sum()))]

    @staticmethod
    def _flip(x: float, y: float) -> tuple[float, float]:
        return PITCH_X - x, PITCH_Y - y

    def _opp(self, team: str) -> str:
        return TEAMS[1] if team == TEAMS[0] else TEAMS[0]

    def _pressure_lambda(self, defending: str, x: float) -> float:
        base = 0.35 + 0.9 * (x / PITCH_X) ** 2
        if self.scenario.high_press == defending:
            base *= 1.0 + 0.8 * (1 - x / PITCH_X)
        men = len(self._active(defending)) / 11
        return base * men * self.strength[defending] ** 0.5

    def _xg(self, x: float, y: float) -> float:
        dx, dy = PITCH_X - x, abs(PITCH_Y / 2 - y)
        dist = math.hypot(dx, dy)
        angle = math.atan2(7.32 * dx, dx**2 + dy**2 - (7.32 / 2) ** 2)
        if angle < 0:
            angle += math.pi
        z = -0.7 - 0.12 * dist + 1.2 * angle
        return float(1 / (1 + math.exp(-z)))

    def _apply_scenario(self, t: float) -> None:
        minute = t / 60
        sc = self.scenario
        if sc.red_card and not getattr(self, "_red_done", False) and minute >= sc.red_card[1]:
            team = sc.red_card[0]
            victim = next(p for p in self._active(team) if p.role == "MF")
            victim.on_pitch = False
            self.strength[team] *= 0.85
            self._red_done = True
            self._emit(t=t, period=self._period(t), type="card", team_id=team, player_id=victim.player_id, outcome="red")
        if sc.momentum_shift and not getattr(self, "_shift_done", False) and minute >= sc.momentum_shift[1]:
            self.strength[sc.momentum_shift[0]] *= sc.momentum_shift[2]
            self._shift_done = True

    @staticmethod
    def _period(t: float) -> int:
        return 1 if t < HALF_S else 2

    def run(self) -> list[dict]:
        rng = self.rng
        t = 0.0
        team = TEAMS[0]
        x, y = PITCH_X / 2, PITCH_Y / 2
        carrier = self._pick_player_near(team, x)
        self._emit(t=t, period=1, type="kickoff", team_id=team, player_id=carrier.player_id, start={"x": x, "y": y})
        half_two_started = False

        while t < 2 * HALF_S:
            if not half_two_started and t >= HALF_S:
                self._emit(t=HALF_S, period=1, type="period_end", team_id=team)
                t, team, x, y = HALF_S, TEAMS[1], PITCH_X / 2, PITCH_Y / 2
                carrier = self._pick_player_near(team, x)
                self._emit(t=t, period=2, type="kickoff", team_id=team, player_id=carrier.player_id, start={"x": x, "y": y})
                half_two_started = True

            self._apply_scenario(t)
            period = self._period(t)
            opp = self._opp(team)
            pressure = int(rng.poisson(self._pressure_lambda(opp, x)))
            xg_here = self._xg(x, y)

            if pressure > 0 and rng.random() < 0.55:
                presser = self._pick_player_near(opp, PITCH_X - x)
                px, py = self._flip(x, y)
                self._emit(
                    t=t,
                    period=period,
                    type="pressure",
                    team_id=opp,
                    player_id=presser.player_id,
                    start={"x": round(px, 1), "y": round(py, 1)},
                    pressure_count=pressure,
                )

            shoot_p = 0.0 if x < 80 else min(0.6, 0.05 + 2.4 * xg_here)
            if rng.random() < shoot_p:
                t += rng.uniform(1.0, 3.0)
                xg = xg_here * (0.85 ** pressure)
                p_goal = min(0.95, xg * carrier.finishing * self.strength[team] / self.strength[opp] ** 0.5)
                roll = rng.random()
                if roll < p_goal:
                    outcome = "goal"
                elif roll < p_goal + 0.25:
                    outcome = "on_target"
                elif roll < p_goal + 0.45:
                    outcome = "blocked"
                else:
                    outcome = "off_target"
                ev = self._emit(
                    t=t,
                    period=period,
                    type="shot",
                    team_id=team,
                    player_id=carrier.player_id,
                    start={"x": round(x, 1), "y": round(y, 1)},
                    end={"x": PITCH_X, "y": round(rng.uniform(30.3, 37.7), 1)},
                    outcome=outcome,
                    xg=round(xg, 3),
                    speed_kmh=round(float(rng.normal(92, 14)), 1),
                    under_pressure=pressure > 0,
                    pressure_count=pressure,
                )
                if outcome == "goal":
                    self.score[team] += 1
                    self._emit(
                        t=t,
                        period=period,
                        type="goal",
                        team_id=team,
                        player_id=carrier.player_id,
                        tags=[f"score_{self.score['HOM']}-{self.score['AWY']}", f"shot:{ev['event_id']}"],
                    )
                    t += rng.uniform(45, 75)
                    team, x, y = opp, PITCH_X / 2, PITCH_Y / 2
                    carrier = self._pick_player_near(team, x)
                    self._emit(
                        t=t,
                        period=self._period(t),
                        type="kickoff",
                        team_id=team,
                        player_id=carrier.player_id,
                        start={"x": x, "y": y},
                    )
                else:
                    t += rng.uniform(8, 20)
                    team, x, y = opp, 6.0, PITCH_Y / 2
                    carrier = next(p for p in self._active(team) if p.role == "GK")
                continue

            if rng.random() < 0.12:
                dist = float(rng.gamma(2.0, 4.0))
                ang = float(rng.normal(0, 0.7))
                nx = float(np.clip(x + dist * math.cos(ang), 1, 99))
                ny = float(np.clip(y + dist * math.sin(ang), 1, 67))
                t += dist / 5.5
                lost = rng.random() < 0.06 + 0.07 * pressure
                self._emit(
                    t=t,
                    period=period,
                    type="carry",
                    team_id=team,
                    player_id=carrier.player_id,
                    start={"x": round(x, 1), "y": round(y, 1)},
                    end={"x": round(nx, 1), "y": round(ny, 1)},
                    outcome="fail" if lost else "success",
                    under_pressure=pressure > 0,
                    pressure_count=pressure,
                )
                x, y = nx, ny
                if lost:
                    team, carrier, x, y = self._turnover(t, period, team, x, y, "tackle")
                continue

            dist = float(np.clip(rng.lognormal(math.log(15), 0.55), 3, 65))
            ang = float(rng.normal(0.25 if x < 80 else 0.0, 1.1))
            nx = float(np.clip(x + dist * math.cos(ang), 1, 101))
            ny = float(np.clip(y + dist * math.sin(ang), 1, 67))
            dist = math.hypot(nx - x, ny - y)
            dx = nx - x
            box_crowding = max(nx - 92, 0) * 0.35
            line_breaking = dx > 15 and nx > 50
            through = line_breaking and nx > 80
            receiver = self._pick_player_near(team, nx, exclude=carrier.player_id)

            z = (
                3.55
                - 0.055 * dist
                - 0.42 * pressure
                - 0.75 * line_breaking
                - 0.02 * max(dx, 0)
                - 0.024 * max(nx - 70, 0)
                - box_crowding
                + 3.0 * (carrier.passing - 0.78)
                + 0.6 * (self.strength[team] - self.strength[opp])
            )
            success = rng.random() < 1 / (1 + math.exp(-z))
            speed = float(np.clip(28 + 1.6 * dist + rng.normal(0, 6), 15, 120))
            t += max(1.5, dist / (speed / 3.6) + rng.uniform(1.8, 5.0))

            tags = [tag for tag, on in (("line_breaking", line_breaking), ("through_ball", through), ("switch", abs(ny - y) > 30)) if on]
            self._emit(
                t=t,
                period=period,
                type="pass",
                team_id=team,
                player_id=carrier.player_id,
                start={"x": round(x, 1), "y": round(y, 1)},
                end={"x": round(nx, 1), "y": round(ny, 1)},
                outcome="success" if success else "fail",
                recipient_id=receiver.player_id if success else None,
                speed_kmh=round(speed, 1),
                under_pressure=pressure > 0,
                pressure_count=pressure,
                tags=tags,
            )
            x, y = nx, ny
            if success:
                carrier = receiver
            else:
                team, carrier, x, y = self._turnover(t, period, team, x, y, "interception")

        self._emit(t=2 * HALF_S, period=2, type="period_end", team_id=team)
        return self.events

    def _turnover(self, t: float, period: int, team: str, x: float, y: float, kind: str):
        opp = self._opp(team)
        fx, fy = self._flip(x, y)
        winner = self._pick_player_near(opp, fx)
        if self.rng.random() < 0.08:
            self._emit(t=t, period=period, type="foul", team_id=opp, player_id=winner.player_id, start={"x": round(fx, 1), "y": round(fy, 1)})
            return team, self._pick_player_near(team, x), x, y
        self._emit(t=t, period=period, type=kind, team_id=opp, player_id=winner.player_id, start={"x": round(fx, 1), "y": round(fy, 1)}, outcome="success")
        self._emit(t=t, period=period, type="turnover", team_id=team, start={"x": round(x, 1), "y": round(y, 1)})
        return opp, winner, fx, fy
