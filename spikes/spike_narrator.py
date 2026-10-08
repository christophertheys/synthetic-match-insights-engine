"""Spike 3: can captions be produced fast enough for live play, and can we stop the narrator inventing numbers?

Pipeline exercised: demo match events -> win probability -> InsightFacts -> persona x language captions -> verifier.

Gate:
  - template captions p95 < 5 ms (live path)
  - verifier passes every template caption and rejects a caption with an invented number
  - optional: if OPENAI_API_KEY is set, LLM caption p95 < 2 s
"""

from __future__ import annotations

import json
import math
import os
import re
import statistics as st
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "data/sample/demo_redcard_comeback.json"

TEAM_NAMES = {"HOM": "Northbridge", "AWY": "Riverside"}
FIRST = ["K.", "L.", "M.", "D.", "J.", "T.", "S.", "R.", "A.", "E.", "N."]
LAST = {
    "HOM": ["Adebayo", "Lindqvist", "Moreau", "Okafor", "Silva", "Tanaka", "Brennan", "Haddad", "Novak", "Ortega", "Whitfield"],
    "AWY": ["Achterberg", "Bianchi", "Castell", "Diallo", "Eriksen", "Fujita", "Gallagher", "Hakimi", "Ivanov", "Kovac", "Mensah"],
}


def player_name(player_id: str) -> str:
    team, num = player_id.split("-")
    i = int(num) - 1
    return f"{FIRST[(i + (0 if team == 'HOM' else 4)) % 11]} {LAST[team][i]}"


# ---- win probability: independent Poisson goals over remaining time ------

GOALS_PER_90 = 1.3


def win_prob(team: str, minute: float, score: dict, men: dict) -> float:
    opp = "AWY" if team == "HOM" else "HOM"
    rem = max(0.0, 90 - minute) / 90
    lam = {t: GOALS_PER_90 * rem * (men[t] / men["AWY" if t == "HOM" else "HOM"]) ** 2.5 for t in ("HOM", "AWY")}

    def pois(k: int, l: float) -> float:
        return math.exp(-l) * l**k / math.factorial(k)

    diff = score[team] - score[opp]
    return sum(pois(a, lam[team]) * pois(b, lam[opp]) for a in range(10) for b in range(10) if diff + a - b > 0)


def build_facts(events: list[dict]) -> list[dict]:
    score = {"HOM": 0, "AWY": 0}
    men = {"HOM": 11, "AWY": 11}
    shots = {e["event_id"]: e for e in events if e["type"] == "shot"}
    facts = []
    for e in events:
        minute = e["t"] / 60
        if e["type"] == "goal":
            team = e["team_id"]
            before = win_prob(team, minute, score, men)
            score[team] += 1
            after = win_prob(team, minute, score, men)
            shot_id = next(tag.split(":", 1)[1] for tag in e["tags"] if tag.startswith("shot:"))
            facts.append({
                "fact_id": f"f-{len(facts):04d}", "match_id": e["match_id"], "t": e["t"], "kind": "goal",
                "importance": round(min(1.0, abs(after - before) * 2), 2),
                "subject": {"team_id": team, "player_id": e["player_id"]},
                "metrics": {"minute": int(minute) + 1, "xg": shots[shot_id]["xg"], "shot_speed_kmh": shots[shot_id]["speed_kmh"],
                            "score_home": score["HOM"], "score_away": score["AWY"]},
                "why": {"driver": "win_probability", "before": round(before, 3), "after": round(after, 3),
                        "delta": round(after - before, 3), "window_s": 0},
                "evidence": [shot_id, e["event_id"]], "audience_tags": ["casual", "analyst", "story"],
            })
        elif e["type"] == "card" and e.get("outcome") == "red":
            team = e["team_id"]
            before = win_prob(team, minute, score, men)
            men[team] -= 1
            after = win_prob(team, minute, score, men)
            facts.append({
                "fact_id": f"f-{len(facts):04d}", "match_id": e["match_id"], "t": e["t"], "kind": "win_prob_swing",
                "importance": round(min(1.0, abs(after - before) * 2 + 0.3), 2),
                "subject": {"team_id": team, "player_id": e["player_id"]},
                "metrics": {"minute": int(minute) + 1, "players_on_pitch": men[team], "card": "red"},
                "why": {"driver": "win_probability", "before": round(before, 3), "after": round(after, 3),
                        "delta": round(after - before, 3), "window_s": 0},
                "evidence": [e["event_id"]], "audience_tags": ["casual", "analyst", "story"],
            })
    return facts


# ---- templates -----------------------------------------------------------

TEMPLATES = {
    ("goal", "casual"): {
        "en": "GOAL! {player} scores for {team}. {team} are now {after}% likely to win.",
        "es": "¡GOL! {player} marca para {team}. {team} tiene ahora un {after}% de probabilidad de ganar.",
        "ar": "هدف! {player} يسجل لـ{team}. فرصة فوز {team} الآن {after}%.",
        "ja": "ゴール！{player}が{team}に得点。{team}の勝利確率は{after}%に。",
    },
    ("goal", "analyst"): {
        "en": "Goal {player} ({team}) {minute}' | {home}-{away} | xG {xg} | {speed} km/h | Win prob {before}% -> {after}% ({delta} pts)",
        "es": "Gol de {player} ({team}) {minute}' | {home}-{away} | xG {xg} | {speed} km/h | Prob. de victoria {before}% -> {after}% ({delta} pts)",
        "ar": "هدف {player} ({team}) الدقيقة {minute} | {home}-{away} | xG {xg} | {speed} كم/س | احتمال الفوز {before}% ← {after}% ({delta} نقطة)",
        "ja": "ゴール {player}（{team}）{minute}分 | {home}-{away} | xG {xg} | {speed} km/h | 勝利確率 {before}% → {after}%（{delta}pt）",
    },
    ("win_prob_swing", "casual"): {
        "en": "Red card! {player} is sent off and {team} are down to {men} men.",
        "es": "¡Tarjeta roja! {player} es expulsado y {team} se queda con {men}.",
        "ar": "بطاقة حمراء! طرد {player} و{team} يلعب بـ{men} لاعبين.",
        "ja": "レッドカード！{player}が退場、{team}は{men}人に。",
    },
    ("win_prob_swing", "analyst"): {
        "en": "Red card {player} ({team}) {minute}' | {team} win prob {before}% -> {after}% ({delta} pts)",
        "es": "Roja a {player} ({team}) {minute}' | Prob. de victoria de {team} {before}% -> {after}% ({delta} pts)",
        "ar": "بطاقة حمراء {player} ({team}) الدقيقة {minute} | احتمال فوز {team} {before}% ← {after}% ({delta} نقطة)",
        "ja": "レッドカード {player}（{team}）{minute}分 | {team}勝利確率 {before}% → {after}%（{delta}pt）",
    },
}


def slots(fact: dict) -> dict:
    m, w = fact["metrics"], fact["why"]
    s = {
        "player": player_name(fact["subject"]["player_id"]),
        "team": TEAM_NAMES[fact["subject"]["team_id"]],
        "minute": m["minute"],
        "before": round(w["before"] * 100),
        "after": round(w["after"] * 100),
    }
    s["delta"] = f"{s['after'] - s['before']:+d}"
    if fact["kind"] == "goal":
        s |= {"xg": f"{m['xg']:.2f}", "speed": round(m["shot_speed_kmh"]), "home": m["score_home"], "away": m["score_away"]}
    else:
        s["men"] = m["players_on_pitch"]
    return s


def render(fact: dict, mode: str, lang: str) -> str:
    return TEMPLATES[(fact["kind"], mode)][lang].format(**slots(fact))


# ---- verifier ------------------------------------------------------------

NUM = re.compile(r"(?:(?<!\d)[+-])?\d+(?:\.\d+)?")


def verify(text: str, fact: dict) -> tuple[bool, list[str]]:
    """Every number in the caption must come from the fact's formatted slots."""
    allowed = {str(v).lstrip("+") for v in slots(fact).values() if NUM.fullmatch(str(v))}
    found = [n.lstrip("+") for n in NUM.findall(text)]
    bad = [n for n in found if n not in allowed]
    return not bad and bool(fact["evidence"]), bad


# ---- optional LLM path ---------------------------------------------------

def llm_caption(fact: dict, mode: str, lang: str) -> str:
    body = {
        "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "You are a football broadcast captioner. Use ONLY numbers present in the facts. "
                                          "Reply as JSON {\"caption\": str}. One sentence, under 20 words."},
            {"role": "user", "content": json.dumps({"lang": lang, "mode": mode, "facts": slots(fact)}, ensure_ascii=False)},
        ],
    }
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(json.loads(r.read())["choices"][0]["message"]["content"])["caption"]


def main() -> int:
    events = json.loads(DEMO.read_text())
    facts = build_facts(events)
    print(f"Demo match: {len(events):,} events -> {len(facts)} facts\n")

    modes, langs = ("casual", "analyst"), ("en", "es", "ar", "ja")
    timings, failures = [], []
    for fact in facts:
        print(f"[{fact['fact_id']}] {fact['kind']} t={fact['t'] / 60:.0f}'  why: {fact['why']['driver']} "
              f"{fact['why']['before']:.2f} -> {fact['why']['after']:.2f}  evidence={fact['evidence']}")
        for mode in modes:
            for lang in langs:
                t = time.perf_counter()
                text = render(fact, mode, lang)
                timings.append((time.perf_counter() - t) * 1000)
                ok, bad = verify(text, fact)
                if not ok:
                    failures.append((fact["fact_id"], mode, lang, bad))
                if lang in ("en", "ja") or mode == "casual" and lang == "es":
                    print(f"    {mode:<8}{lang}: {text}")
        print()

    p95 = sorted(timings)[int(0.95 * len(timings)) - 1]
    print(f"Template captions: {len(timings)}  p95 {p95:.3f} ms  verifier failures {len(failures)}")

    goal = next(f for f in facts if f["kind"] == "goal")
    forged = render(goal, "casual", "en").replace(f"{round(goal['why']['after'] * 100)}%", "91%")
    caught, bad = verify(forged, goal)
    print(f"Forged caption: {forged!r}\n  -> verifier {'REJECTED' if not caught else 'ACCEPTED'} (unsupported numbers: {bad})")

    ok = p95 < 5 and not failures and not caught

    if os.environ.get("OPENAI_API_KEY"):
        lat, rejected = [], 0
        for fact in facts:
            for lang in langs:
                t = time.perf_counter()
                try:
                    text = llm_caption(fact, "casual", lang)
                except Exception as exc:  # network or provider error: report, don't crash the spike
                    print(f"  LLM error: {exc}")
                    continue
                lat.append(time.perf_counter() - t)
                rejected += not verify(text, fact)[0]
        if lat:
            lp95 = sorted(lat)[max(0, int(0.95 * len(lat)) - 1)]
            print(f"LLM captions: {len(lat)}  p95 {lp95:.2f} s  verifier rejected {rejected}")
            ok &= lp95 < 2.0
    else:
        print("LLM path: skipped (OPENAI_API_KEY not set); live path uses templates, LLM upgrades captions asynchronously")

    print(f"\nGATE: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
