export type Persona = {
  persona_id: string;
  label: string;
  mode: "analyst" | "casual";
  lang: string;
  favorite_team_id: string | null;
  focus_player_id: string | null;
  metric_focus: string | null;
  max_cues_per_min: number;
};

export type Cue = {
  cue_id: string;
  persona_id: string;
  t_start: number;
  ttl: number;
  slot: string;
  template: string;
  priority: number;
  lang: string;
  fact_ids: string[];
  data: {
    headline: string;
    why: string;
    values: Record<string, string | number>;
    anchor?: { x?: number; y?: number; player_id?: string | null };
  };
  producer_reason: {
    importance: number;
    novelty: number;
    affinity: number;
    mode_fit: number;
    score: number;
  };
};

export type Snapshot = {
  t: number;
  period: number;
  score: { HOM: number; AWY: number };
  men: { HOM: number; AWY: number };
  wp: { HOM: number; AWY: number; DRAW: number };
  ppda: { HOM: number; AWY: number };
  control: number;
  tempo: number;
  possession: string;
  chain_len: number;
  ball: { x: number; y: number; team_id: string };
  last_pass: {
    start: { x: number; y: number } | null;
    end: { x: number; y: number } | null;
    difficulty: number;
    success: boolean;
    player_id: string;
    recipient_id?: string | null;
    speed_kmh?: number;
    tags: string[];
  } | null;
  players: Record<
    string,
    {
      player_id: string;
      team_id: string;
      name: string;
      number: number;
      role: string;
      on_pitch: boolean;
      distance_km: number;
      max_speed_kmh: number;
      passes: number;
      passes_ok: number;
      shots: number;
      goals: number;
      x: number | null;
      y: number | null;
    }
  >;
};

export type MatchMeta = {
  match_id: string;
  teams: Record<string, { id: string; name: string; abbr: string; color: string }>;
  roster: { player_id: string; team_id: string; number: number; role: string; name: string }[];
  personas: Persona[];
  key_moments: { t: number; minute: number; id: string; label: string }[];
  final: { HOM: number; AWY: number };
  events: number;
  facts: number;
  timeline: number;
  narrator: string;
  warm_ms: number;
  cv_stub: Record<string, number>;
  agents: { id: string; role: string }[];
};

export type Tick = {
  type: "tick";
  t: number;
  event: { type: string; team_id?: string; player_id?: string; t: number };
  facts: { fact_id: string; kind: string; importance: number; why: { driver: string; before?: number; after?: number; delta?: number } }[];
  cues: Record<string, Cue[]>;
  snapshot: Snapshot;
  latency_ms: number;
};
