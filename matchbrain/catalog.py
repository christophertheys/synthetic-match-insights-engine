"""Display names, locked demo metadata, and viewer personas."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO_PATH = ROOT / "data" / "sample" / "demo_redcard_comeback.json"
PERSONAS_PATH = ROOT / "docs" / "ideation" / "schemas" / "personas.example.json"
MODEL_PATH = ROOT / "data" / "models" / "pass_difficulty.joblib"

TEAM_NAMES = {"HOM": "Northbridge", "AWY": "Riverside"}
TEAM_ABBR = {"HOM": "NOR", "AWY": "RIV"}
TEAM_COLORS = {"HOM": "#6ea0ff", "AWY": "#ff7a59"}

ROLE_BY_NUMBER = {
    1: "GK",
    2: "DF",
    3: "DF",
    4: "DF",
    5: "DF",
    6: "MF",
    7: "FW",
    8: "MF",
    9: "FW",
    10: "MF",
    11: "FW",
}

FIRST = ["K.", "L.", "M.", "D.", "J.", "T.", "S.", "R.", "A.", "E.", "N."]
LAST = {
    "HOM": ["Adebayo", "Lindqvist", "Moreau", "Okafor", "Silva", "Tanaka", "Brennan", "Haddad", "Novak", "Ortega", "Whitfield"],
    "AWY": ["Achterberg", "Bianchi", "Castell", "Diallo", "Eriksen", "Fujita", "Gallagher", "Hakimi", "Ivanov", "Kovac", "Mensah"],
}

PERSONAS = [
    {
        "persona_id": "analyst-en",
        "label": "Analyst · English",
        "mode": "analyst",
        "lang": "en",
        "favorite_team_id": None,
        "focus_player_id": None,
        "metric_focus": None,
        "max_cues_per_min": 4.0,
    },
    {
        "persona_id": "casual-es-home",
        "label": "Casual · Spanish · Northbridge",
        "mode": "casual",
        "lang": "es",
        "favorite_team_id": "HOM",
        "focus_player_id": None,
        "metric_focus": None,
        "max_cues_per_min": 1.5,
    },
    {
        "persona_id": "player-focus-ja",
        "label": "Player focus · Japanese · E. Fujita",
        "mode": "casual",
        "lang": "ja",
        "favorite_team_id": "AWY",
        "focus_player_id": "AWY-6",
        "metric_focus": None,
        "max_cues_per_min": 2.0,
    },
    {
        "persona_id": "pass-nerd-ar",
        "label": "Pass metric · Arabic",
        "mode": "analyst",
        "lang": "ar",
        "favorite_team_id": None,
        "focus_player_id": None,
        "metric_focus": "pass_difficulty",
        "max_cues_per_min": 3.0,
    },
]

KEY_MOMENTS = [
    {"t": 1062.0, "minute": 18, "id": "opener", "label": "18' Riverside opener"},
    {"t": 1236.0, "minute": 21, "id": "equaliser", "label": "21' Brennan equaliser"},
    {"t": 1536.0, "minute": 26, "id": "lead", "label": "26' Northbridge 2-1"},
    {"t": 3300.0, "minute": 55, "id": "pre-red", "label": "55' before the red"},
    {"t": 3600.0, "minute": 60, "id": "red", "label": "60' Tanaka sent off"},
    {"t": 4524.0, "minute": 76, "id": "equaliser2", "label": "76' Mensah equaliser"},
    {"t": 5310.0, "minute": 89, "id": "winner", "label": "89' Fujita winner"},
    {"t": 5400.0, "minute": 90, "id": "ft", "label": "Full time"},
]


def player_name(player_id: str | None) -> str:
    if not player_id or "-" not in player_id:
        return "Unknown"
    team, num = player_id.split("-", 1)
    try:
        i = int(num) - 1
    except ValueError:
        return player_id
    if team not in LAST or not (0 <= i < 11):
        return player_id
    first = FIRST[(i + (0 if team == "HOM" else 4)) % 11]
    return f"{first} {LAST[team][i]}"


def roster() -> list[dict]:
    players = []
    for team in ("HOM", "AWY"):
        for n in range(1, 12):
            pid = f"{team}-{n}"
            players.append(
                {
                    "player_id": pid,
                    "team_id": team,
                    "number": n,
                    "role": ROLE_BY_NUMBER[n],
                    "name": player_name(pid),
                }
            )
    return players
