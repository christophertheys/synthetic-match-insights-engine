# Phase 2: Concept Decision

Scale 1 to 5, equal weights.

| Concept | Impact | AI depth | Feasibility | Demo-ability | Total |
|---|---|---|---|---|---|
| A. Match Brain | 5 | 5 | 4 | 4 | **18** |
| B. Synthetic Football Lab | 3 | 4 | 4 | 3 | 14 |
| C. Agentic Studio Producer | 5 | 5 | 2 | 4 | 16 |
| **A + lightweight C (Producer ranker)** | 5 | 5 | 4 | 5 | **19** |

## Decision: Match Brain with a Producer ranker

**One-liner for the pitch:**
> Match Brain turns a stream of synthetic match events into explainable, broadcast-ready moments, and a Producer decides which moment each viewer sees, in their language, about the players they care about.

### What we take from each concept

- **From A:** event-sourced pipeline, metrics, win-probability, control/chaos explainability, grounded narrator, personas.
- **From B:** the generator is a first-class deliverable (open dataset, scenario injection, model card). It's also our training data.
- **From C:** only the decision step. The Producer is a deterministic, explainable ranking function, not an LLM agent:

```
score(fact, persona) =
    w_importance * fact.importance          # win-prob delta or regime-shift magnitude
  + w_novelty    * novelty(fact, recent)    # penalise repeating the same insight type
  + w_affinity   * affinity(fact, persona)  # favourite club/player, chosen metric
  + w_mode       * mode_fit(fact, persona)  # analyst likes dense metrics, casual likes stories
```

The Producer allocates overlay slots (`lower_third`, `corner_badge`, `side_panel`, `full_takeover`) with cooldowns so the screen never gets cluttered.

### Why not full C

Multi-agent orchestration adds latency, nondeterminism and debugging time, and is hard to evaluate in a weekend. The ranker gives the same "AI decides what's on screen" story, and every decision can be explained ("shown because importance 0.31, favourite player, not shown in last 4 min").

### Signature differentiator

**"Why this matters" on every overlay.** Each overlay carries a one-line, numeric reason:

- "Win probability for ARS: 41% -> 58% (+17 pts)"
- "Control -> Chaos: turnovers doubled in the last 5 minutes"
- "Pressing shift detected at 63': CHE PPDA 14.2 -> 6.8"

This hits the brief's most repeated ask directly and is visible in every frame of the demo.

### Risks accepted

| Risk | Mitigation |
|---|---|
| Synthetic data looks fake | Calibrate to public aggregate norms (about 1,000 passes and 25 shots per match, pass accuracy 80 to 85%) |
| Win-prob model trained on our own sim is circular | Be upfront: it's a pipeline demo; the model card states the training source |
| LLM latency in live mode | Live captions use templates + LLM only for top-ranked moments; recaps are batch |
