# Phase 1: Topic Scoring

Scale: 1 (low) to 5 (high). **Cost is inverted** so that a higher number always means better (5 = cheapest to build in a weekend).

Weights reflect the team's goals: winning matters, but the portfolio angle is AI and data engineering.

- Win potential: 40%
- Portfolio value (AI / data engineering): 35%
- Weekend cost (inverted): 25%

| Topic | Win | Portfolio | Cost (inv.) | Weighted | Decision |
|---|---|---|---|---|---|
| (iv) Explainability: control vs chaos, pressure shifts, win-prob delta | 5 | 5 | 3 | **4.50** | Build, signature feature |
| (ii) Pass difficulty model + pass distance/accuracy | 4 | 5 | 4 | **4.35** | Build |
| (v) Synthetic data generator with scenario injection | 4 | 5 | 3 | **4.10** | Build, core |
| (e) Personalization: personas, club, player-focus | 5 | 3 | 4 | **4.05** | Build |
| (iii) Grounded narrative + recap + verifier | 4 | 4 | 3 | **3.75** | Build |
| (ii) Auto-eventing from real video | 4 | 5 | 1 | **3.60** | **Stub** (see below) |
| (ii) Ball/shot speed, sprint and distance tagging | 3 | 3 | 5 | **3.50** | Build (cheap from coordinates) |
| (vi) Multi-language | 3 | 2 | 5 | **3.15** | Build at narrative layer |
| (d) Overlay spec + web replay | 4 | 2 | 3 | **3.05** | Build, minimal |

## Why auto-eventing is stubbed despite a decent score

Its weighted score hides a fatal property: cost of 1 means it can eat the whole weekend and still produce nothing demoable. Instead, the simulator emits a second stream of noisy "detections" (jittered positions, missed frames, occasional false touches). A small cleaner turns them back into events and reports precision/recall against ground truth. That shows:

- the architecture slot where a real computer-vision model would plug in,
- a measurable evaluation loop (a strong data-engineering portfolio point),
- zero dependence on video, GPUs or licensing.

Cut entirely if the core pipeline isn't end-to-end by Saturday midday (Phase 4 gate).

## Ideas considered and parked

| Idea | Why parked |
|---|---|
| Full tracking data (22 players at 25 Hz) | Too heavy; event-level coordinates + sparse player positions are enough |
| Voice commentary (TTS) | High wow, low engineering signal; a stretch goal only if Sunday has slack |
| Fantasy-points mode | Good fan hook but adds a scoring system to design; reuse as a "single metric" persona instead |
| Betting-style odds overlay | Regulatory optics for a PL brief; win probability covers the same insight |

## Final build / stub / cut list

- **Build:** generator, match state, pass difficulty, speeds and thresholds, control/chaos, PPDA changepoints, win probability, insight facts, producer ranker, grounded narrator, verifier, personas, 3 languages, overlay spec, web replay.
- **Stub:** auto-eventing via noisy detections.
- **Cut / stretch:** TTS, fantasy mode, full tracking.
