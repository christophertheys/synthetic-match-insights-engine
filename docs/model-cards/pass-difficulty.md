# Model card: pass difficulty

**Task.** Estimate how hard a completed pass was: `difficulty = 1 - P(success | observables)`.

**Training data.** Synthetic matches from `matchbrain.sim.MatchSim` (no real Premier League data). Passer skill and team strength are hidden from the model so it cannot simply invert the generator.

**Features.** Distance, forward displacement, lateral displacement, pressure count, line-breaking flag, start x, end x, end-in-box.

**Model.** Histogram gradient boosting (`sklearn.ensemble.HistGradientBoostingClassifier`). Logistic regression is the fallback for a fully linear explanation.

**Spike result.** Held-out AUC **0.82**, Brier **0.108**. Distance, pressure, line-breaking and end-in-box all make passes harder, as expected.

**Threshold.** `pass_of_note` fires on completed passes with difficulty > 0.5 (about 2–3% of passes). The Producer then ranks which ones reach the overlay.

**Limits.** The model is only as realistic as the simulator. Treat it as a pipeline demonstration, not a production scouting tool.
