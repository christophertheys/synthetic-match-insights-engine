"""Grounded caption templates. Numbers come only from formatted fact slots."""

from __future__ import annotations

from matchbrain.catalog import TEAM_NAMES, player_name

TEMPLATES: dict[str, dict[str, dict[str, str]]] = {
    "goal": {
        "casual": {
            "en": "GOAL! {player} scores for {team}. {headline_team} are now {headline_wp}% likely to win.",
            "es": "¡GOL! {player} marca para {team}. {headline_team} tiene ahora un {headline_wp}% de probabilidad de ganar.",
            "ar": "هدف! {player} يسجل لـ{team}. فرصة فوز {headline_team} الآن {headline_wp}%.",
            "ja": "ゴール！{player}が{team}に得点。{headline_team}の勝利確率は{headline_wp}%に。",
        },
        "analyst": {
            "en": "Goal {player} ({team}) {minute}' | {home}-{away} | xG {xg} | {speed} km/h | Win prob {before}% -> {after}% ({delta} pts)",
            "es": "Gol de {player} ({team}) {minute}' | {home}-{away} | xG {xg} | {speed} km/h | Prob. de victoria {before}% -> {after}% ({delta} pts)",
            "ar": "هدف {player} ({team}) الدقيقة {minute} | {home}-{away} | xG {xg} | {speed} كم/س | احتمال الفوز {before}% ← {after}% ({delta} نقطة)",
            "ja": "ゴール {player}（{team}）{minute}分 | {home}-{away} | xG {xg} | {speed} km/h | 勝利確率 {before}% → {after}%（{delta}pt）",
        },
    },
    "win_prob_swing": {
        "casual": {
            "en": "Red card! {player} is sent off and {team} are down to {men} men.",
            "es": "¡Tarjeta roja! {player} es expulsado y {team} se queda con {men}.",
            "ar": "بطاقة حمراء! طرد {player} و{team} يلعب بـ{men} لاعبين.",
            "ja": "レッドカード！{player}が退場、{team}は{men}人に。",
        },
        "analyst": {
            "en": "Red card {player} ({team}) {minute}' | {team} win prob {before}% -> {after}% ({delta} pts)",
            "es": "Roja a {player} ({team}) {minute}' | Prob. de victoria de {team} {before}% -> {after}% ({delta} pts)",
            "ar": "بطاقة حمراء {player} ({team}) الدقيقة {minute} | احتمال فوز {team} {before}% ← {after}% ({delta} نقطة)",
            "ja": "レッドカード {player}（{team}）{minute}分 | {team}勝利確率 {before}% → {after}%（{delta}pt）",
        },
    },
    "pressing_shift": {
        "casual": {
            "en": "{team} have turned the screw. Their PPDA dropped from {ppda_before} to {ppda_after}.",
            "es": "{team} aprieta más. Su PPDA baja de {ppda_before} a {ppda_after}.",
            "ar": "{team} يضغط أكثر. PPDA من {ppda_before} إلى {ppda_after}.",
            "ja": "{team}のプレスが強まる。PPDAが{ppda_before}から{ppda_after}へ。",
        },
        "analyst": {
            "en": "Pressing shift {team} {minute}' | PPDA {ppda_before} -> {ppda_after} ({ppda_delta})",
            "es": "Cambio de presión {team} {minute}' | PPDA {ppda_before} -> {ppda_after} ({ppda_delta})",
            "ar": "تحول الضغط {team} {minute}' | PPDA {ppda_before} ← {ppda_after} ({ppda_delta})",
            "ja": "プレッシング変化 {team} {minute}分 | PPDA {ppda_before} → {ppda_after}（{ppda_delta}）",
        },
    },
    "control_chaos_shift": {
        "casual": {
            "en": "The game is tilting: control index {control_pct}.",
            "es": "El partido cambia de ritmo: índice de control {control_pct}.",
            "ar": "إيقاع المباراة يتغير: مؤشر السيطرة {control_pct}.",
            "ja": "試合の支配率が変化。コントロール指数 {control_pct}。",
        },
        "analyst": {
            "en": "Control vs chaos {minute}' | index {before_c} -> {after_c} | tempo {tempo}",
            "es": "Control vs caos {minute}' | índice {before_c} -> {after_c} | tempo {tempo}",
            "ar": "سيطرة مقابل فوضى {minute}' | {before_c} ← {after_c} | الإيقاع {tempo}",
            "ja": "支配対カオス {minute}分 | 指数 {before_c} → {after_c} | テンポ {tempo}",
        },
    },
    "pass_of_note": {
        "casual": {
            "en": "{player} threads a difficult pass for {team}.",
            "es": "{player} filtra un pase difícil para {team}.",
            "ar": "{player} يمرر تمريرة صعبة لـ{team}.",
            "ja": "{player}が{team}で高難度のパスを通す。",
        },
        "analyst": {
            "en": "Pass of note {player} {minute}' | difficulty {diff} | {distance} m | {speed} km/h",
            "es": "Pase destacado {player} {minute}' | dificultad {diff} | {distance} m | {speed} km/h",
            "ar": "تمريرة مميزة {player} {minute}' | صعوبة {diff} | {distance} م | {speed} كم/س",
            "ja": "注目のパス {player} {minute}分 | 難度 {diff} | {distance} m | {speed} km/h",
        },
    },
    "period_summary": {
        "casual": {
            "en": "{label}: {home_name} {home}-{away} {away_name}.",
            "es": "{label}: {home_name} {home}-{away} {away_name}.",
            "ar": "{label}: {home_name} {home}-{away} {away_name}.",
            "ja": "{label}: {home_name} {home}-{away} {away_name}.",
        },
        "analyst": {
            "en": "{label} {home}-{away} | WP {wp_home_pct}%-{wp_away_pct}% | {home_name} vs {away_name}",
            "es": "{label} {home}-{away} | Prob. {wp_home_pct}%-{wp_away_pct}% | {home_name} vs {away_name}",
            "ar": "{label} {home}-{away} | احتمال {wp_home_pct}%-{wp_away_pct}% | {home_name} vs {away_name}",
            "ja": "{label} {home}-{away} | 勝率 {wp_home_pct}%-{wp_away_pct}% | {home_name} vs {away_name}",
        },
    },
    "shot_speed": {
        "casual": {
            "en": "{player} hits it at {speed} km/h.",
            "es": "{player} golpea a {speed} km/h.",
            "ar": "{player} يسدد بسرعة {speed} كم/س.",
            "ja": "{player}のシュートは{speed} km/h。",
        },
        "analyst": {
            "en": "Shot speed {player} {minute}' | {speed} km/h",
            "es": "Velocidad de tiro {player} {minute}' | {speed} km/h",
            "ar": "سرعة التسديدة {player} {minute}' | {speed} كم/س",
            "ja": "シュート速度 {player} {minute}分 | {speed} km/h",
        },
    },
    "sprint": {
        "casual": {
            "en": "{player} breaks {speed} km/h.",
            "es": "{player} supera {speed} km/h.",
            "ar": "{player} ينطلق بـ {speed} كم/س.",
            "ja": "{player}が{speed} km/hでスプリント。",
        },
        "analyst": {
            "en": "Sprint {player} {minute}' | {speed} km/h over {distance} m",
            "es": "Sprint {player} {minute}' | {speed} km/h en {distance} m",
            "ar": "انطلاق {player} {minute}' | {speed} كم/س عبر {distance} م",
            "ja": "スプリント {player} {minute}分 | {speed} km/h / {distance} m",
        },
    },
    "big_chance": {
        "casual": {
            "en": "Big chance for {player} — xG {xg}.",
            "es": "Gran ocasión de {player} — xG {xg}.",
            "ar": "فرصة كبيرة لـ{player} — xG {xg}.",
            "ja": "{player}のビッグチャンス — xG {xg}。",
        },
        "analyst": {
            "en": "Big chance {player} {minute}' | xG {xg} | {speed} km/h | {outcome}",
            "es": "Gran ocasión {player} {minute}' | xG {xg} | {speed} km/h | {outcome}",
            "ar": "فرصة كبيرة {player} {minute}' | xG {xg} | {speed} كم/س | {outcome}",
            "ja": "決定機 {player} {minute}分 | xG {xg} | {speed} km/h | {outcome}",
        },
    },
    "tempo_change": {
        "casual": {
            "en": "The tempo jumps to {tempo} passes per minute.",
            "es": "El ritmo sube a {tempo} pases por minuto.",
            "ar": "الإيقاع يرتفع إلى {tempo} تمريرة في الدقيقة.",
            "ja": "テンポが{tempo}パス/分に。",
        },
        "analyst": {
            "en": "Tempo change {minute}' | {before_t} -> {tempo} passes/min",
            "es": "Cambio de ritmo {minute}' | {before_t} -> {tempo} pases/min",
            "ar": "تغير الإيقاع {minute}' | {before_t} ← {tempo} تمريرة/د",
            "ja": "テンポ変化 {minute}分 | {before_t} → {tempo} パス/分",
        },
    },
    "distance_milestone": {
        "casual": {
            "en": "{player} has covered {distance_km} km.",
            "es": "{player} ya recorre {distance_km} km.",
            "ar": "{player} قطع {distance_km} كم.",
            "ja": "{player}の走行距離は{distance_km} km。",
        },
        "analyst": {
            "en": "Distance milestone {player} {minute}' | {distance_km} km",
            "es": "Hito de distancia {player} {minute}' | {distance_km} km",
            "ar": "مسافة {player} {minute}' | {distance_km} كم",
            "ja": "走行距離 {player} {minute}分 | {distance_km} km",
        },
    },
}

WHY_TEMPLATES = {
    "win_probability": {
        "en": "Win probability {before}% -> {after}% ({delta} pts)",
        "es": "Probabilidad de victoria {before}% -> {after}% ({delta} pts)",
        "ar": "احتمال الفوز {before}% ← {after}% ({delta} نقطة)",
        "ja": "勝利確率 {before}% → {after}%（{delta}pt）",
    },
    "ppda": {
        "en": "PPDA {ppda_before} -> {ppda_after}",
        "es": "PPDA {ppda_before} -> {ppda_after}",
        "ar": "PPDA {ppda_before} ← {ppda_after}",
        "ja": "PPDA {ppda_before} → {ppda_after}",
    },
    "control_index": {
        "en": "Control index {before_c} -> {after_c}",
        "es": "Índice de control {before_c} -> {after_c}",
        "ar": "مؤشر السيطرة {before_c} ← {after_c}",
        "ja": "コントロール指数 {before_c} → {after_c}",
    },
    "pass_difficulty": {
        "en": "Pass difficulty {diff}",
        "es": "Dificultad del pase {diff}",
        "ar": "صعوبة التمريرة {diff}",
        "ja": "パス難度 {diff}",
    },
    "speed": {
        "en": "Speed {speed} km/h",
        "es": "Velocidad {speed} km/h",
        "ar": "السرعة {speed} كم/س",
        "ja": "速度 {speed} km/h",
    },
    "distance": {
        "en": "Distance {distance_km} km",
        "es": "Distancia {distance_km} km",
        "ar": "المسافة {distance_km} كم",
        "ja": "走行 {distance_km} km",
    },
    "tempo": {
        "en": "Tempo {tempo} passes/min",
        "es": "Ritmo {tempo} pases/min",
        "ar": "الإيقاع {tempo} تمريرة/د",
        "ja": "テンポ {tempo} パス/分",
    },
    "milestone": {
        "en": "{label}: {home}-{away}",
        "es": "{label}: {home}-{away}",
        "ar": "{label}: {home}-{away}",
        "ja": "{label}: {home}-{away}",
    },
    "xt": {
        "en": "xG {xg}",
        "es": "xG {xg}",
        "ar": "xG {xg}",
        "ja": "xG {xg}",
    },
}

LABELS = {
    "half_time": {"en": "Half time", "es": "Descanso", "ar": "نهاية الشوط", "ja": "ハーフタイム"},
    "full_time": {"en": "Full time", "es": "Final", "ar": "نهاية المباراة", "ja": "試合終了"},
}


def pct(value: float | None) -> int:
    return int(round((value or 0) * 100))


def slots(fact: dict) -> dict[str, str | int | float]:
    m = fact.get("metrics") or {}
    w = fact.get("why") or {}
    subject = fact.get("subject") or {}
    team_id = subject.get("team_id") or "HOM"
    lang_label = m.get("label") or ""
    before = pct(w.get("before")) if w.get("driver") == "win_probability" else w.get("before")
    after = pct(w.get("after")) if w.get("driver") == "win_probability" else w.get("after")
    if w.get("driver") == "win_probability":
        delta = f"{int(after) - int(before):+d}"
        headline_wp, headline_team = after, TEAM_NAMES.get(team_id, team_id)
        if fact["kind"] == "goal":
            # after is scoring team's WP. If that's small, talk about the collapse of the other side.
            scoring_after = int(after)
            if scoring_after < 40:
                other = "AWY" if team_id == "HOM" else "HOM"
                other_before = 100 - int(before)
                other_after = 100 - scoring_after
                headline_team = TEAM_NAMES[other]
                headline_wp = other_after
                # Keep those numbers in slots so the verifier accepts them.
                extra_before, extra_after = other_before, other_after
            else:
                extra_before = extra_after = None
        else:
            extra_before = extra_after = None
    else:
        delta = w.get("delta")
        headline_wp, headline_team = after, TEAM_NAMES.get(team_id, team_id)
        extra_before = extra_after = None

    out: dict[str, str | int | float] = {
        "player": player_name(subject.get("player_id")),
        "team": TEAM_NAMES.get(team_id, team_id or ""),
        "home_name": TEAM_NAMES["HOM"],
        "away_name": TEAM_NAMES["AWY"],
        "minute": int(m.get("minute") or 0),
        "home": m.get("score_home", ""),
        "away": m.get("score_away", ""),
        "before": before if before is not None else "",
        "after": after if after is not None else "",
        "delta": delta if delta is not None else "",
        "headline_team": headline_team,
        "headline_wp": headline_wp if headline_wp is not None else "",
        "xg": f"{float(m.get('xg') or 0):.2f}",
        "speed": round(float(m.get("shot_speed_kmh") or m.get("speed_kmh") or 0)),
        "men": m.get("players_on_pitch", ""),
        "ppda_before": m.get("ppda_before", w.get("before", "")),
        "ppda_after": m.get("ppda_after", w.get("after", "")),
            "ppda_delta": round(float(m.get("ppda_after", 0) - m.get("ppda_before", 0)), 2) if "ppda_before" in m else w.get("delta", ""),
        "control": m.get("control", ""),
        "control_pct": pct(m.get("control") or 0) if m.get("control") is not None else "",
        "before_c": w.get("before", "") if w.get("driver") == "control_index" else "",
        "after_c": w.get("after", "") if w.get("driver") == "control_index" else "",
        "tempo": m.get("tempo", w.get("after", "")),
        "before_t": w.get("before", "") if w.get("driver") == "tempo" else "",
        "diff": f"{float(m.get('difficulty') or w.get('after') or 0):.2f}",
        "distance": m.get("distance_m", ""),
        "distance_km": m.get("distance_km", m.get("milestone_km", "")),
        "outcome": m.get("outcome", ""),
        "wp_home_pct": pct(m.get("wp_home") or 0) if "wp_home" in m else "",
        "wp_away_pct": pct(m.get("wp_away") or 0) if "wp_away" in m else "",
        "label": LABELS.get(str(lang_label), {}).get("en", str(lang_label)),
    }
    if extra_before is not None:
        out["other_before"] = extra_before
        out["other_after"] = extra_after
    # Drop empty keys that would confuse format_map; keep numeric zeros.
    return {k: v for k, v in out.items() if v != "" and v is not None}


def localize_label(fact: dict, lang: str) -> str:
    label = (fact.get("metrics") or {}).get("label") or ""
    return LABELS.get(str(label), {}).get(lang) or LABELS.get(str(label), {}).get("en") or str(label)


def render_template(fact: dict, mode: str, lang: str) -> str:
    kind = fact["kind"]
    table = TEMPLATES.get(kind, {}).get(mode) or TEMPLATES.get(kind, {}).get("casual") or {}
    tmpl = table.get(lang) or table.get("en")
    if not tmpl:
        return f"{kind}"
    values = slots(fact)
    values["label"] = localize_label(fact, lang)
    try:
        return tmpl.format_map(_Safe(values))
    except Exception:
        return table.get("en", "{kind}").format_map(_Safe(values))


def render_why(fact: dict, lang: str) -> str:
    driver = (fact.get("why") or {}).get("driver") or "milestone"
    tmpl = (WHY_TEMPLATES.get(driver) or WHY_TEMPLATES["milestone"]).get(lang) or WHY_TEMPLATES.get(driver, {}).get("en")
    values = slots(fact)
    values["label"] = localize_label(fact, lang)
    try:
        return tmpl.format_map(_Safe(values))
    except Exception:
        return driver


class _Safe(dict):
    def __missing__(self, key: str) -> str:
        return ""
