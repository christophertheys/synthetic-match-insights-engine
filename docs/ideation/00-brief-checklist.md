# Phase 0: Brief Decoded into a Judging Checklist

Use this as the definition of done. Every item maps to a sentence in the brief, so a judge reading the brief can tick it off against the demo.

## Hard requirements (missing any of these is a disqualifier-level gap)

| # | Brief requirement | What "done" looks like in our demo | Owner |
|---|---|---|---|
| R1 | Synthetic, football-realistic data only | Every event comes from our seeded simulator; no real PL data in repo | Data |
| R2 | (a) Ingest events as they happen | Events stream over a WebSocket at match speed (or Nx speed) | Data |
| R3 | (b) Interpret into stats, patterns, context | Live match state: possession, pass accuracy, PPDA, xT, pass difficulty | ML |
| R4 | (c) Explain why a moment matters | Every highlighted moment carries a numeric "why" (win-prob delta, regime shift) | ML |
| R5 | (d) Render alongside the match | Overlay JSON spec with timing; web replay renders it on a pitch | Frontend |
| R6 | (e) Personalize: analyst vs casual as genuinely different experiences | Same moment shown in Analyst and Casual mode side by side, visibly different | AI / Frontend |
| R7 | Favorite club, favorite player, player-focus mode | Persona config drives filtering and ranking; player-focus follows one player all match | AI |
| R8 | Multi-language storytelling | Same recap in at least 3 languages, consistent terminology | AI |
| R9 | Responsive enough for live play | Event-to-overlay latency measured and shown (target under 500 ms without LLM, under 2 s with) | All |

## Feature checklist from section (ii) to (vi)

| Brief feature | Decision | Notes |
|---|---|---|
| Player name tagging + speed/distance thresholds | Build | Trigger overlay when sprint > 30 km/h or distance milestone (e.g. 10 km) |
| Pass distance, accuracy, difficulty rating | Build | Difficulty is a trained model, not a formula (portfolio point) |
| Ball speed, shot speed | Build | Derived from simulated ball trajectory |
| Auto-eventing from video | Stub | Noisy "detections" stream + cleaner shows the architecture slot |
| Key narratives, milestones, recaps | Build | Grounded LLM with event-ID citations |
| Control vs chaos, pressure changes, rhythm | Build (signature) | Control/Chaos index, PPDA changepoints, tempo |
| Extend synthetic datasets | Build | Publish generator + sample matches as an open dataset |
| Multi-language | Build | Native generation per language with a football glossary |

## What judges will likely weight most

1. **Explainability** (the brief repeats "why it matters" in four places). This is our signature.
2. **Personalization that is genuinely different**, not the same text with fewer numbers.
3. **Broadcast-readiness**: timed, machine-readable output, not just a chatbot.
4. **Data innovation**: a credible synthetic generator is rare in hackathons and easy to show off.

## Team rule: structured facts first

> Every insight is a structured, timestamped fact before it becomes text.

Concretely:

- The analytics layer emits `InsightFact` objects (see `docs/ideation/schemas/insight_fact.schema.json`). It never writes prose.
- The narrator only receives facts. It must cite `fact_id`s for every claim; the verifier drops any sentence that cites nothing or cites a fact that doesn't support it.
- The overlay layer renders facts directly. Text is an optional field on an overlay, not the overlay itself.

Why this rule pays off three times:

1. **Grounding**: the LLM cannot invent a stat that isn't in a fact.
2. **Broadcast**: facts are already machine-readable and timed, so the rendering partner path is trivial.
3. **Personalization and language**: one fact feeds N personas times M languages without re-running analytics.
