export type FilmScene = {
  id: string;
  duration: number;
  view: "title" | "pipeline" | "live" | "insights" | "personas" | "verify" | "end";
  fromT?: number;
  personaB?: boolean;
  kicker?: string;
  title?: string;
  body?: string;
};

export const FILM_SCENES: FilmScene[] = [
  {
    id: "open",
    duration: 7000,
    view: "title",
    kicker: "Match Brain",
    title: "See the game. Read why it matters.",
    body: "Explainable match intelligence from synthetic football events.",
  },
  {
    id: "pipeline",
    duration: 8000,
    view: "pipeline",
    kicker: "One pipeline. Five stages.",
    title: "Ingest. Interpret. Explain. Render. Personalise.",
    body: "Every insight is a structured fact before it becomes a caption.",
  },
  {
    id: "live",
    duration: 11000,
    view: "live",
    fromT: 3300,
    kicker: "Minute 55 · Northbridge 2–1",
    title: "The scoreline is not the story.",
    body: "Northbridge lead. The engine is already watching the press.",
  },
  {
    id: "red",
    duration: 14000,
    view: "live",
    fromT: 3592,
    personaB: true,
    kicker: "61' · Red card",
    title: "Win probability 75% → 67%. Score unchanged.",
    body: "T. Tanaka is sent off. The same fact reaches an analyst and a casual fan as two different experiences.",
  },
  {
    id: "insights",
    duration: 12000,
    view: "insights",
    kicker: "Tactical studio",
    title: "Why this moment matters.",
    body: "Control, pressure and win probability — before the equaliser arrives.",
  },
  {
    id: "winner",
    duration: 14000,
    view: "live",
    fromT: 5302,
    kicker: "89' · The swing",
    title: "E. Fujita. 3% → 98%. +95 pts.",
    body: "A grounded caption. Every number cites a recorded fact.",
  },
  {
    id: "personas",
    duration: 11000,
    view: "personas",
    fromT: 5302,
    personaB: true,
    kicker: "Personalise",
    title: "Same moment. Two audiences.",
    body: "Analyst English. Casual Spanish. Player-focus Japanese. One fact stream.",
  },
  {
    id: "verify",
    duration: 10000,
    view: "verify",
    kicker: "Grounding",
    title: "The narrator cannot invent a number.",
    body: "A forged 91% is rejected. Unsupported figures never reach the overlay.",
  },
  {
    id: "end",
    duration: 8000,
    view: "end",
    kicker: "Match Brain",
    title: "Synthetic. Explainable. Personal.",
    body: "Broadcast-ready overlays from a match that never needed real footage.",
  },
];

export const PIPELINE = [
  { n: "01", name: "Ingest", copy: "Synthetic events stream as they happen." },
  { n: "02", name: "Interpret", copy: "Pass difficulty, speed, PPDA, control." },
  { n: "03", name: "Explain", copy: "A numeric why on every key moment." },
  { n: "04", name: "Render", copy: "Timed overlay cues a graphics desk can draw." },
  { n: "05", name: "Personalise", copy: "Analyst, casual, club, player, language." },
];

export const INSIGHT_CARDS = [
  {
    n: "01",
    title: "Start with the scoreline",
    copy: "Northbridge lead 2–1 after 26'. Win probability sits at 75%. That is what the graphic would show. It is not the whole match.",
  },
  {
    n: "02",
    title: "The game turns first",
    copy: "At 61' T. Tanaka is sent off. Riverside’s press tightens. PPDA falls. Win probability 75% → 67% while the score is still 2–1.",
  },
  {
    n: "03",
    title: "Then the swing",
    copy: "76' Mensah equalises. 89' E. Fujita wins it. Win probability 3% → 98% (+95 pts). The overlay states the why, not just the goal.",
  },
];

export const VERIFY_RULES = [
  { n: "01", title: "Facts first", copy: "Every caption is built from a structured InsightFact, not free prose." },
  { n: "02", title: "Slots only", copy: "The narrator may fill templates. It may not invent a statistic." },
  { n: "03", title: "Reject the rest", copy: "If a number is not already on the fact, the overlay never ships." },
];

export const PERSONA_MOMENTS = [
  {
    id: "analyst-en",
    eyebrow: "Analyst · EN",
    text: "Red card T. Tanaka (Northbridge) 61' | Northbridge win prob 75% → 67% (−8 pts)",
  },
  {
    id: "casual-es-home",
    eyebrow: "Casual · ES",
    text: "¡Tarjeta roja! T. Tanaka es expulsado y Northbridge se queda con 10.",
  },
  {
    id: "player-focus-ja",
    eyebrow: "Player focus · JA",
    text: "ゴール！E. FujitaがRiversideに得点。Riversideの勝利確率は98%に。",
  },
];
