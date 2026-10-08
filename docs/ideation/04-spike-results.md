# Phase 4: Feasibility Spikes and Go/No-Go Gates

All spikes are in [`spikes/`](../../spikes/) and need only Python 3.12+ with numpy and scikit-learn.

```bash
cd spikes
python3 spike_simulator.py        # writes data/sample/demo_redcard_comeback.json
python3 spike_pass_difficulty.py
python3 spike_narrator.py         # reads the demo match; set OPENAI_API_KEY to also time the LLM path
```

## Results

| Spike | Gate | Measured | Verdict |
|---|---|---|---|
| Simulator speed | < 5 s per 90-min match | **31 ms mean, 39 ms max** (200 matches, ~400k events in 6.5 s) | GO |
| Simulator realism | Per-match averages inside public norms | passes 1063, accuracy 79.7%, shots 25.7, goals 2.5, turnovers 212 | GO |
| Event schema | 0 validation errors | 0 errors over 20 matches (~40k events) | GO |
| Pass difficulty | Held-out AUC >= 0.65, sensible feature signs | Gradient boosting **AUC 0.822**, Brier 0.108; logistic AUC 0.791. Distance, pressure, line-breaking, end-in-box all make passes harder | GO |
| Live caption latency | Template p95 < 5 ms | **p95 0.004 ms** across 4 languages x 2 modes | GO |
| Grounding | Verifier passes real captions, rejects invented numbers | 32/32 template captions pass; forged "91%" caption rejected | GO |
| LLM latency | p95 < 2 s | **Not measured**: no API key in this environment | Deferred; run with `OPENAI_API_KEY` set on Saturday morning |
| Video auto-eventing stub | Core pipeline end-to-end by Saturday midday | Schedule gate, not a code spike | Decide on the day |

## What the spikes taught us

1. **The simulator needed calibration, and that is a story worth telling.** The first version produced 71 shots and 9 goals per match. The cause: pass end-points were clipped at the goal line, so a third of all shots came from inside 5 m. Capping pass depth and adding box crowding produced a realistic shot-distance distribution (median 18.5 m). This became a calibration loop that checks against aggregate norms, and it belongs in the model card.
2. **Hidden variables keep the model honest.** Passer skill and team strength are invisible to the pass-difficulty model, so AUC tops out around 0.82 rather than near 1.0. That is the realistic regime, and it means the model is not simply reading back the generator's formula.
3. **Threshold reality check.** Difficulty p90 is 0.61, so a 0.7 threshold would almost never fire. We moved `pass_of_note` to > 0.5 on completed passes (about 28 per match), and the Producer ranks them.
4. **Verifier edge cases matter.** The first verifier read the score "1-0" as the numbers "1" and "-0". Scores, minutes (61') and "10 men" all need to be explicit fact slots. Lesson for the build: the verifier works on *formatted slots*, not raw metrics.
5. **Win probability needs red cards.** A Poisson model with a man-advantage exponent gives sensible swings (Northbridge 2-1 up at 60', then a red card: 75% -> 67%; Riverside's 89' winner: 3% -> 98%). It's cheap, explainable and needs no training data.
6. **Casual copy needs framing logic.** After Riverside's 75' equaliser, the casual caption says "Riverside are now 20% likely to win", which is accurate but reads like bad news. In the build, casual goal templates should headline whichever side's probability moved most (here: "Northbridge's win chance falls from 79% to 12%").

## Fallbacks kept in reserve

| If this breaks during the build | Fall back to |
|---|---|
| Live simulator in the API | Replay a pre-generated JSON match file at 1x to 10x speed |
| Gradient-boosted pass model | Logistic model (AUC 0.79, coefficients are directly explainable on screen) |
| LLM latency or availability | Template captions (already in 4 languages); LLM only for half-time and full-time recaps |
| Changepoint detection | Fixed-threshold crossings on the rolling PPDA and control indices |

## Open item carried into the build

Measure LLM caption latency and verifier rejection rate with a real key. If more than 10% of LLM captions are rejected, constrain the LLM to choose between template variants plus a free-text "colour" clause that contains no numbers.
