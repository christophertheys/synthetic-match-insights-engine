"""Explainable remaining-time Poisson win probability with a man-advantage term."""

from __future__ import annotations

import math

GOALS_PER_90 = 1.3
TEAMS = ("HOM", "AWY")


def poisson_pmf(k: int, lam: float) -> float:
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * lam**k / math.factorial(k)


def win_prob(team: str, minute: float, score: dict[str, int], men: dict[str, int]) -> float:
    opp = "AWY" if team == "HOM" else "HOM"
    rem = max(0.0, 90 - minute) / 90
    lam = {}
    for t in TEAMS:
        other = "AWY" if t == "HOM" else "HOM"
        lam[t] = GOALS_PER_90 * rem * (men[t] / max(1, men[other])) ** 2.5
    diff = score[team] - score[opp]
    total = 0.0
    for a in range(10):
        pa = poisson_pmf(a, lam[team])
        for b in range(10):
            if diff + a - b > 0:
                total += pa * poisson_pmf(b, lam[opp])
    return float(total)


def table(minute: float, score: dict[str, int], men: dict[str, int]) -> dict[str, float]:
    home = win_prob("HOM", minute, score, men)
    away = win_prob("AWY", minute, score, men)
    draw = max(0.0, 1.0 - home - away)
    return {"HOM": home, "AWY": away, "DRAW": draw}
