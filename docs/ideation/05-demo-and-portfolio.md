# Phase 5: Demo Script, Scenario and Portfolio Assets

## The demo match (locked)

`MatchSim(seed=49, scenario=Scenario(red_card=("HOM", 60), momentum_shift=("AWY", 60, 1.25), high_press="AWY"))`
Stored at [`data/sample/demo_redcard_comeback.json`](../../data/sample/demo_redcard_comeback.json) (1,968 events).

**Northbridge 2-3 Riverside**

| Minute | Moment | Win-prob "why" (from the spike) |
|---|---|---|
| 18' | L. Ivanov (Riverside), assisted by N. Gallagher | Riverside 35% -> 65% |
| 21' | S. Brennan (Northbridge) equalises | Northbridge 13% -> 35% |
| 26' | S. Brennan again, 2-1 | Northbridge 34% -> 66% |
| 61' | **Red card**, T. Tanaka (Northbridge) | Northbridge 75% -> 67% |
| 60'-75' | Riverside press harder (scripted surge + high press) | Measured vs 45'-60': Riverside PPDA 9.9 -> 7.6, turnovers 2.1 -> 2.6 per min, Riverside pass share 51% -> 55% |
| 76' | D. Mensah equalises from a **line-breaking through ball** by T. Bianchi | Riverside 3% -> 20%; Northbridge 79% -> 12% |
| 89' | **E. Fujita winner**, assisted by K. Hakimi | Riverside 3% -> 98% (+95 pts) |

The story fits the brief exactly: the scoreline at 60' says Northbridge are winning, but the engine can *explain* the shift in control before the goals arrive.

**Build item:** the post-red-card shift is real but modest, and it fades after 75' (PPDA back to 11.2). Before recording, strengthen the scripted surge (for example, momentum boost 1.25 -> 1.4 and making the high press scale with man advantage), then re-run `spike_simulator.py` and confirm seed 49 still produces this scoreline. If it doesn't, re-run the seed search in Phase 5 with the same filter.

## 3-minute demo script

| Time | On screen | What the presenter says | Brief pillar |
|---|---|---|---|
| 0:00-0:20 | Title card, architecture diagram | "Football stories don't end with the scoreline. Match Brain explains *why* moments matter, for every fan." | Framing |
| 0:20-0:45 | Simulator generating a match in 31 ms; norms table | "All data is synthetic. Our generator is calibrated against real aggregates: 1,063 passes, 80% accuracy, 26 shots and 2.5 goals per match." | (v) data innovation, (a) ingest |
| 0:45-1:15 | Replay at 10x speed from 55'. Analyst view: PPDA strip, control index, pass-difficulty cards | "At 60' Northbridge lead 2-1. Then the red card. Watch the pressing line: Riverside's PPDA drops from 9.9 to 7.6 and turnovers jump. The scoreline hasn't changed yet; the game has." | (b) interpret, (iv) explain |
| 1:15-1:45 | Pause on the 76' equaliser. Split screen: Analyst (en) and Casual (es) for the **same fact** | "Same insight, two experiences. The analyst gets pass difficulty, xG and the probability swing. The casual fan gets the story." | (e) personalize, (vi) language |
| 1:45-2:15 | Player-focus mode (ja) following E. Fujita; persistent player tag, then the 89' winner | "A fan in Tokyo follows one player all match. Every cue is ranked by the Producer for *their* profile." | (e) player focus, (ii) player tagging |
| 2:15-2:35 | Overlay JSON cue next to the rendered graphic; `producer_reason` breakdown | "Every overlay is a timed, machine-readable cue a rendering partner can consume, and every decision is explainable." | (d) render |
| 2:35-2:50 | Verifier rejecting a forged "91%" caption | "The narrator can't invent numbers. Every claim cites event IDs, and the verifier blocks anything unsupported." | (iii) narrative, trust |
| 2:50-3:00 | Full-time recap card in 4 languages | "Explainable, broadcast-ready and personal. That's Match Brain." | (iii) recap |

**Backup plan:** record the full run as a screen capture on Saturday night. If the live demo fails, play the video and narrate over it.

## Portfolio assets checklist

| Asset | Source | Status |
|---|---|---|
| Open synthetic dataset + generator | `spikes/sim.py` -> `sim/` package, plus `data/sample/` | Spike done; promote to a package during the build |
| Calibration report (norms vs generated) | `spike_simulator.py` output | Done; turn into a chart |
| Model card: pass difficulty | `spike_pass_difficulty.py` (AUC 0.822, features, hidden-variable caveat) | Numbers ready; write the card |
| Model card: win probability (Poisson + man advantage) | `spike_narrator.py` | Numbers ready; write the card |
| Schema docs: event, fact, overlay | `docs/ideation/schemas/` | Done |
| Architecture diagram | `docs/ideation/03-architecture.md` | Done |
| Grounding write-up ("structured facts first" + verifier) | Phase 0 rule + Phase 4 results | Outline ready |
| 3-minute demo video | Demo script above | Record Saturday night |
| README with one-command run (`docker compose up`) | Build phase | To do |

## Portfolio framing (for CV or LinkedIn)

> Built Match Brain, a real-time football intelligence engine: a calibrated synthetic event generator (about 2,000 events per match in 31 ms), a pass-difficulty model (AUC 0.82), a Poisson win-probability model, and a grounded multilingual narrator with a numeric verifier. A persona-aware ranker then produces timed overlay cues for analyst, casual and player-focus audiences.
