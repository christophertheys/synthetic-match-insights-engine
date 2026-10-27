# Model card: win probability

**Task.** After every goal or red card, estimate each side's chance of winning from the current score, minute, and number of players.

**Method.** Independent Poisson remaining-goals model. Each team’s expected remaining goals is `1.3 × remaining_fraction × (men / opponent_men)^2.5`. Win probability is the sum of outcome probabilities where the team finishes ahead.

**Why this form.** It is cheap (microseconds), fully inspectable, and needs no training data. The man-advantage exponent is what makes the 61' red card move Northbridge from about 75% to 67% before the scoreline changes.

**Demo check.** Riverside's 89th-minute winner moves win probability from about 3% to 98% (+95 pts). That delta is the overlay's "why".

**Limits.** The model ignores xG, style, and fatigue. It is an explainability instrument, not a betting model.
