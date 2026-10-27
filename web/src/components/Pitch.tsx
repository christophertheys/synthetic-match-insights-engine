import type { Cue, Snapshot } from "../types";

type Props = {
  snapshot: Snapshot | null;
  tags: Cue[];
  homeColor: string;
  awayColor: string;
  theme?: "live" | "schematic";
  compact?: boolean;
  uid?: string;
};

export default function Pitch({ snapshot, tags, homeColor, awayColor, theme = "live", compact = false, uid = "p" }: Props) {
  const ball = snapshot?.ball ?? { x: 52.5, y: 34, team_id: "HOM" };
  const last = snapshot?.last_pass;
  const players = snapshot ? Object.values(snapshot.players).filter((p) => p.x != null && p.y != null && p.on_pitch) : [];
  const schematic = theme === "schematic";
  const ghosts =
    players.length === 0
      ? [
          [8, 34],
          [22, 18],
          [22, 50],
          [38, 12],
          [38, 34],
          [38, 56],
          [58, 22],
          [58, 46],
          [78, 16],
          [78, 34],
          [78, 52],
        ]
      : [];

  return (
    <svg className={`pitch ${schematic ? "schematic" : ""} ${compact ? "compact" : ""}`} viewBox="0 0 105 68" preserveAspectRatio="none">
      <defs>
        <linearGradient id={`${uid}-turf`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={schematic ? "#1b2c48" : "#1b7d62"} />
          <stop offset="100%" stopColor={schematic ? "#121c32" : "#146850"} />
        </linearGradient>
        <pattern id={`${uid}-shade`} width="10.5" height="68" patternUnits="userSpaceOnUse">
          <rect width="5.25" height="68" fill="rgba(255,255,255,0.045)" />
        </pattern>
        <filter id={`${uid}-glow`}>
          <feGaussianBlur stdDeviation="1.1" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <rect width="105" height="68" fill={`url(#${uid}-turf)`} rx="1.2" />
      <rect width="105" height="68" fill={`url(#${uid}-shade)`} rx="1.2" />
      <g className="markings" fill="none" stroke="rgba(255,255,255,0.55)" strokeWidth="0.38">
        <rect x="1.2" y="1.2" width="102.6" height="65.6" rx="0.4" />
        <line x1="52.5" y1="1.2" x2="52.5" y2="66.8" />
        <circle cx="52.5" cy="34" r="9.15" />
        <rect x="1.2" y="13.84" width="16.5" height="40.32" />
        <rect x="87.3" y="13.84" width="16.5" height="40.32" />
        <rect x="1.2" y="24.84" width="5.5" height="18.32" />
        <rect x="98.3" y="24.84" width="5.5" height="18.32" />
      </g>
      <circle cx="52.5" cy="34" r="0.42" fill="rgba(255,255,255,0.7)" />
      {!compact && (
        <text x="52.5" y="6.2" textAnchor="middle" fill="rgba(255,255,255,0.35)" fontSize="2.1" fontFamily="Plus Jakarta Sans, sans-serif" letterSpacing="0.3">
          ATTACK →
        </text>
      )}

      {last?.start && last.end && (
        <g filter={`url(#${uid}-glow)`}>
          <line
            x1={last.start.x}
            y1={last.start.y}
            x2={last.end.x}
            y2={last.end.y}
            className={last.success ? "pass-ok" : "pass-broken"}
            stroke={last.success ? "#3ee0c4" : "#ff7a59"}
            strokeWidth="0.42"
            strokeDasharray={last.success ? "0" : "1.4 0.9"}
            opacity="0.9"
          />
        </g>
      )}

      {ghosts.map(([x, y], i) => (
        <circle key={`g${i}`} cx={x} cy={y} r={compact ? 0.85 : 1.15} fill={i < 6 ? homeColor : awayColor} opacity="0.35" />
      ))}

      {players.map((p) => (
        <circle
          key={p.player_id}
          cx={p.x as number}
          cy={p.y as number}
          r={compact ? 0.7 : 0.95}
          fill={p.team_id === "HOM" ? homeColor : awayColor}
          opacity="0.85"
        />
      ))}

      {tags.map((cue) => {
        const x = cue.data.anchor?.x ?? ball?.x ?? 52;
        const y = cue.data.anchor?.y ?? ball?.y ?? 34;
        return (
          <g key={cue.cue_id} className="tag-ring">
            <circle cx={x} cy={y} r="3.1" fill="none" stroke="#3ee0c4" strokeWidth="0.28" opacity="0.35" />
            <circle cx={x} cy={y} r="2.15" fill="none" stroke="#3ee0c4" strokeWidth="0.38" />
          </g>
        );
      })}

      {ball && (
        <g filter={`url(#${uid}-glow)`} className="ball-wrap">
          <circle className="pulse" cx={ball.x} cy={ball.y} r="2.6" fill="none" stroke={ball.team_id === "HOM" ? homeColor : awayColor} strokeWidth="0.28" />
          <circle cx={ball.x} cy={ball.y} r="1.05" fill="#f4f7fb" />
          <circle cx={ball.x} cy={ball.y} r="1.05" fill="none" stroke={ball.team_id === "HOM" ? homeColor : awayColor} strokeWidth="0.32" />
        </g>
      )}
    </svg>
  );
}
