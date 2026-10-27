"""Explainable Producer: ranks InsightFacts per viewer persona and assigns overlay slots."""

from __future__ import annotations

W_IMP, W_NOV, W_AFF, W_MODE = 0.40, 0.20, 0.25, 0.15

CASUAL_KINDS = {"goal", "win_prob_swing", "player_milestone", "period_summary", "sprint", "distance_milestone"}
ANALYST_KINDS = {
    "pass_of_note",
    "pressing_shift",
    "control_chaos_shift",
    "tempo_change",
    "shot_speed",
    "big_chance",
    "goal",
    "win_prob_swing",
    "period_summary",
}
FOCUS_KIND = {"pass_difficulty": "pass_of_note", "speed": "shot_speed"}
ALWAYS = {"goal", "win_prob_swing", "period_summary"}
SLOTS = ("lower_third", "corner_badge", "side_panel", "full_takeover", "player_tag")


def assign_slot(fact: dict, persona: dict) -> tuple[str, str, float]:
    kind = fact["kind"]
    if kind == "goal":
        return "full_takeover", "headline", 8.0
    if kind == "period_summary":
        return "full_takeover", "recap_card", 10.0
    if kind == "win_prob_swing":
        return "lower_third", "win_prob_bar", 8.0
    if kind == "pass_of_note":
        slot = "side_panel" if persona["mode"] == "analyst" else "corner_badge"
        return slot, "pass_card", 7.0
    if kind in ("pressing_shift", "control_chaos_shift", "tempo_change"):
        return "side_panel", "momentum_strip", 9.0
    if kind in ("sprint", "distance_milestone", "player_milestone"):
        return "player_tag", "player_tag", 5.0
    if kind in ("shot_speed", "big_chance"):
        return "corner_badge", "speed_gauge", 6.0
    return "lower_third", "stat_card", 6.0


class Producer:
    def __init__(self, persona: dict):
        self.persona = persona
        self.recent: list[dict] = []
        self.cue_times: list[float] = []
        self.slot_busy_until = {s: -1e9 for s in SLOTS}
        self.n = 0

    def score(self, fact: dict) -> dict:
        importance = float(fact.get("importance") or 0)
        novelty = self._novelty(fact)
        affinity = self._affinity(fact)
        mode_fit = self._mode_fit(fact)
        total = W_IMP * importance + W_NOV * novelty + W_AFF * affinity + W_MODE * mode_fit
        return {
            "importance": round(importance, 3),
            "novelty": round(novelty, 3),
            "affinity": round(affinity, 3),
            "mode_fit": round(mode_fit, 3),
            "score": round(total, 3),
        }

    def _novelty(self, fact: dict) -> float:
        same = [f for f in self.recent if f["kind"] == fact["kind"] and fact["t"] - f["t"] < 240]
        return max(0.0, 1.0 - 0.35 * len(same))

    def _affinity(self, fact: dict) -> float:
        subject = fact.get("subject") or {}
        s = 0.0
        focus = self.persona.get("focus_player_id")
        fav = self.persona.get("favorite_team_id")
        if focus and subject.get("player_id") == focus:
            s += 1.0
        if fav and subject.get("team_id") == fav:
            s += 0.6
        return min(1.0, s)

    def _mode_fit(self, fact: dict) -> float:
        kind = fact["kind"]
        metric = self.persona.get("metric_focus")
        if metric:
            want = FOCUS_KIND.get(metric, metric)
            if kind == want or kind in ALWAYS:
                return 1.0
            return 0.08
        if self.persona["mode"] == "casual":
            return 0.9 if kind in CASUAL_KINDS else 0.32
        return 0.9 if kind in ANALYST_KINDS else 0.5

    def try_emit(self, fact: dict, headline: str, why: str, snapshot: dict) -> dict | None:
        reason = self.score(fact)
        kind = fact["kind"]
        subject = fact.get("subject") or {}
        focus = self.persona.get("focus_player_id")
        is_focus = bool(focus and subject.get("player_id") == focus)
        metric = self.persona.get("metric_focus")
        if metric and kind not in ALWAYS:
            want = FOCUS_KIND.get(metric, metric)
            if kind != want:
                return None
        min_score = 0.26 if self.persona["mode"] == "analyst" else 0.36
        if kind in ALWAYS or is_focus:
            min_score = 0.0
        if reason["score"] < min_score:
            return None
        recent_min = [t for t in self.cue_times if fact["t"] - t < 60]
        if len(recent_min) >= self.persona["max_cues_per_min"] and kind not in ALWAYS and not is_focus:
            return None
        slot, template, ttl = assign_slot(fact, self.persona)
        if is_focus and kind not in ALWAYS:
            slot, template, ttl = "player_tag", "player_tag", 5.0
        if self.slot_busy_until[slot] > fact["t"] and kind not in ALWAYS:
            if slot != "corner_badge" and self.slot_busy_until["corner_badge"] <= fact["t"]:
                slot = "corner_badge"
                template = "stat_card"
            else:
                return None
        self.n += 1
        self.recent.append(fact)
        self.cue_times.append(fact["t"])
        self.slot_busy_until[slot] = fact["t"] + ttl
        values = {k: v for k, v in (fact.get("metrics") or {}).items() if isinstance(v, (int, float, str))}
        why_payload = fact.get("why") or {}
        if "before" in why_payload:
            values["why_before"] = why_payload["before"]
            values["why_after"] = why_payload.get("after")
            values["why_delta"] = why_payload.get("delta")
        ball = snapshot.get("ball") or {}
        cue = {
            "cue_id": f"c-{self.persona['persona_id']}-{fact['fact_id']}",
            "persona_id": self.persona["persona_id"],
            "t_start": fact["t"],
            "ttl": ttl,
            "slot": slot,
            "template": template,
            "priority": int(min(100, round(reason["score"] * 100))),
            "lang": self.persona["lang"],
            "fact_ids": [fact["fact_id"]],
            "data": {
                "headline": headline,
                "why": why,
                "values": values,
                "anchor": {
                    "x": ball.get("x"),
                    "y": ball.get("y"),
                    "player_id": subject.get("player_id"),
                },
            },
            "producer_reason": reason,
        }
        return cue
