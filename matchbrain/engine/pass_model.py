"""Pass-difficulty model: 1 - P(success | observable features).

Passer skill and team strength are hidden, matching the spike design.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

from matchbrain.sim.simulator import MatchSim

FEATURES = ["distance", "forward_dx", "abs_dy", "pressure_count", "line_breaking", "start_x", "end_x", "end_in_box"]


def featurise_pass(event: dict) -> np.ndarray:
    start, end = event["start"], event["end"]
    sx, sy, ex, ey = start["x"], start["y"], end["x"], end["y"]
    return np.array(
        [
            float(np.hypot(ex - sx, ey - sy)),
            ex - sx,
            abs(ey - sy),
            float(event.get("pressure_count") or 0),
            float("line_breaking" in (event.get("tags") or [])),
            sx,
            ex,
            float(ex > 88.5 and 13.8 < ey < 54.2),
        ],
        dtype=float,
    )


def heuristic_difficulty(features: np.ndarray) -> float:
    """Fast fallback used before a trained model is available."""
    distance, forward_dx, _abs_dy, pressure, line_breaking, _sx, _ex, end_in_box = features
    z = 2.15 - 0.045 * distance - 0.38 * pressure - 0.7 * line_breaking - 0.012 * max(forward_dx, 0) - 0.45 * end_in_box
    p_success = 1 / (1 + np.exp(-z))
    return float(np.clip(1 - p_success, 0.02, 0.98))


class PassDifficultyModel:
    def __init__(self, sklearn_model=None):
        self.model = sklearn_model

    def difficulty(self, event: dict) -> float:
        x = featurise_pass(event).reshape(1, -1)
        if self.model is None:
            return heuristic_difficulty(x[0])
        p_success = float(self.model.predict_proba(x)[0, 1])
        return float(np.clip(1 - p_success, 0.02, 0.98))

    @classmethod
    def load_or_train(cls, path: Path, n_train: int = 60, n_test: int = 15) -> "PassDifficultyModel":
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            return cls(joblib.load(path))
        model = cls.train(n_train=n_train, n_test=n_test)
        joblib.dump(model.model, path)
        return model

    @classmethod
    def train(cls, n_train: int = 60, n_test: int = 15) -> "PassDifficultyModel":
        xs, ys = [], []
        for seed in range(3000, 3000 + n_train + n_test):
            for event in MatchSim(seed=seed, match_id=f"tr{seed}").run():
                if event["type"] != "pass":
                    continue
                xs.append(featurise_pass(event))
                ys.append(int(event["outcome"] == "success"))
        x = np.vstack(xs)
        y = np.array(ys)
        cut = int(len(y) * n_train / (n_train + n_test))
        gb = HistGradientBoostingClassifier(max_iter=120, learning_rate=0.1, max_depth=6, random_state=0)
        gb.fit(x[:cut], y[:cut])
        return cls(gb)


def train_cli(path: Path, n_train: int = 80, n_test: int = 20) -> dict:
    from sklearn.metrics import roc_auc_score

    xs, ys = [], []
    n = n_train + n_test
    for i, seed in enumerate(range(4000, 4000 + n)):
        for event in MatchSim(seed=seed, match_id=f"tr{seed}").run():
            if event["type"] != "pass":
                continue
            xs.append(featurise_pass(event))
            ys.append((i < n_train, int(event["outcome"] == "success")))
    x = np.vstack(xs)
    train_mask = np.array([m for m, _ in ys])
    y = np.array([v for _, v in ys])
    gb = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1, random_state=0)
    gb.fit(x[train_mask], y[train_mask])
    p = gb.predict_proba(x[~train_mask])[:, 1]
    auc = float(roc_auc_score(y[~train_mask], p))
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(gb, path)
    return {"auc": round(auc, 3), "train_passes": int(train_mask.sum()), "test_passes": int((~train_mask).sum()), "path": str(path)}
