"""Spike 2: does a pass-difficulty model train with sensible behaviour on simulated data?

difficulty = 1 - P(pass success | observable features)

Passer skill and team strength are hidden from the model on purpose, so it cannot
simply read back the generator's formula.

Gate:
  - held-out AUC >= 0.65 (matches split by match, not by row)
  - distance, pressure and line-breaking all make passes harder
"""

from __future__ import annotations

import sys
import time

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from sim import MatchSim

FEATURES = ["distance", "forward_dx", "abs_dy", "pressure_count", "line_breaking", "start_x", "end_x", "end_in_box"]


def featurise(events: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    rows, ys = [], []
    for e in events:
        if e["type"] != "pass":
            continue
        sx, sy, ex, ey = e["start"]["x"], e["start"]["y"], e["end"]["x"], e["end"]["y"]
        rows.append([
            float(np.hypot(ex - sx, ey - sy)),
            ex - sx,
            abs(ey - sy),
            e["pressure_count"],
            float("line_breaking" in e["tags"]),
            sx,
            ex,
            float(ex > 88.5 and 13.8 < ey < 54.2),
        ])
        ys.append(e["outcome"] == "success")
    return np.array(rows), np.array(ys, dtype=int)


def build(seeds: range) -> tuple[np.ndarray, np.ndarray]:
    xs, ys = zip(*(featurise(MatchSim(seed=s).run()) for s in seeds))
    return np.vstack(xs), np.concatenate(ys)


def main() -> int:
    t0 = time.perf_counter()
    X_tr, y_tr = build(range(1000, 1150))
    X_te, y_te = build(range(2000, 2050))
    print(f"Train passes: {len(y_tr):,}  Test passes: {len(y_te):,}  (built in {time.perf_counter() - t0:.1f}s)")
    print(f"Base success rate: {y_tr.mean():.3f}")

    lr = make_pipeline(StandardScaler(), LogisticRegression(max_iter=500)).fit(X_tr, y_tr)
    gb = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1).fit(X_tr, y_tr)

    results = {}
    for name, model in (("logistic", lr), ("grad_boost", gb)):
        t = time.perf_counter()
        p = model.predict_proba(X_te)[:, 1]
        infer_us = (time.perf_counter() - t) / len(y_te) * 1e6
        results[name] = roc_auc_score(y_te, p)
        print(f"{name:<11} AUC {results[name]:.3f}  Brier {brier_score_loss(y_te, p):.4f}  inference {infer_us:.2f} us/pass")

    coefs = dict(zip(FEATURES, lr[-1].coef_[0]))
    print("\nLogistic coefficients (standardised; negative = makes success less likely = harder):")
    for f, c in sorted(coefs.items(), key=lambda kv: kv[1]):
        print(f"  {f:<15} {c:+.3f}")

    p_te = gb.predict_proba(X_te)[:, 1]
    diff = 1 - p_te
    hard_success = ((diff > 0.5) & (y_te == 1)).mean()
    print(f"\nDifficulty distribution: p10 {np.percentile(diff, 10):.2f}  median {np.median(diff):.2f}  p90 {np.percentile(diff, 90):.2f}")
    print(f"Completed passes with difficulty > 0.5 ('pass of note' candidates): {hard_success:.1%} of all passes")

    sensible = coefs["distance"] < 0 and coefs["pressure_count"] < 0 and coefs["line_breaking"] < 0
    ok = max(results.values()) >= 0.65 and sensible
    print(f"\nSigns sensible: {sensible}")
    print(f"GATE: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
