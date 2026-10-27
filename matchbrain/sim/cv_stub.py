"""Noisy 'video detection' stub and cleaner.

Shows the architecture slot a real auto-eventing model would occupy:
detections are jittered, dropped, and occasionally invented, then cleaned
back toward ground-truth events with a reported precision/recall.
"""

from __future__ import annotations

from copy import deepcopy

import numpy as np


def noisify(events: list[dict], seed: int = 0, drop_p: float = 0.08, false_p: float = 0.02) -> list[dict]:
    rng = np.random.default_rng(seed)
    detections: list[dict] = []
    for e in events:
        if e["type"] in ("period_end", "kickoff"):
            continue
        if rng.random() < drop_p:
            continue
        det = deepcopy(e)
        det["source"] = "cv_cleaned"
        det["event_id"] = f"det-{e['event_id']}"
        for key in ("start", "end"):
            if key in det and isinstance(det[key], dict):
                det[key] = {
                    "x": float(np.clip(det[key]["x"] + rng.normal(0, 1.8), 0, 105)),
                    "y": float(np.clip(det[key]["y"] + rng.normal(0, 1.8), 0, 68)),
                }
        detections.append(det)
        if rng.random() < false_p:
            fake = deepcopy(det)
            fake["event_id"] = f"false-{e['event_id']}"
            fake["type"] = "pass"
            fake["t"] = float(e["t"] + rng.uniform(0.4, 1.6))
            fake["outcome"] = "fail"
            detections.append(fake)
    detections.sort(key=lambda d: d["t"])
    return detections


def clean(detections: list[dict], snap: float = 0.75) -> list[dict]:
    """Drop isolated false touches and lightly snap coordinates."""
    cleaned = []
    for i, det in enumerate(detections):
        if str(det["event_id"]).startswith("false-"):
            nearby = [
                o
                for o in detections[max(0, i - 3) : i + 4]
                if o is not det and abs(o["t"] - det["t"]) < 1.0 and o["type"] == det["type"]
            ]
            if not nearby:
                continue
        out = deepcopy(det)
        out["source"] = "cv_cleaned"
        for key in ("start", "end"):
            if key in out and isinstance(out[key], dict):
                out[key]["x"] = round(out[key]["x"] / snap) * snap
                out[key]["y"] = round(out[key]["y"] / snap) * snap
        cleaned.append(out)
    return cleaned


def evaluate(ground_truth: list[dict], cleaned: list[dict], tol_s: float = 2.0) -> dict:
    gt = [e for e in ground_truth if e["type"] not in ("period_end", "kickoff", "pressure")]
    used = set()
    tp = 0
    for e in gt:
        for i, c in enumerate(cleaned):
            if i in used:
                continue
            if c["type"] != e["type"] or c.get("team_id") != e.get("team_id"):
                continue
            if abs(c["t"] - e["t"]) <= tol_s:
                used.add(i)
                tp += 1
                break
    fp = len(cleaned) - len(used)
    fn = len(gt) - tp
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    return {
        "ground_truth": len(gt),
        "detections_kept": len(cleaned),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(2 * precision * recall / max(1e-9, precision + recall), 3),
    }


def run_stub(events: list[dict], seed: int = 0) -> dict:
    detections = noisify(events, seed=seed)
    cleaned = clean(detections)
    report = evaluate(events, cleaned)
    report["raw_detections"] = len(detections)
    return report
