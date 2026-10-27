import Pitch from "./Pitch";
import type { Cue, MatchMeta, Snapshot } from "../types";

type Props = {
  meta: MatchMeta | null;
  snapshot: Snapshot | null;
  tags: Cue[];
  inspector: Cue | null;
};

function pct(n: number | undefined): string {
  return `${Math.round((n || 0) * 100)}%`;
}

export default function Sidecar({ meta, snapshot, tags, inspector }: Props) {
  const home = meta?.teams.HOM;
  const away = meta?.teams.AWY;
  const wp = snapshot?.wp || { HOM: 0.5, AWY: 0.5, DRAW: 0 };

  return (
    <aside className="sidecar">
      <header>
        <div className="mark sm">MB</div>
        <div>
          <p className="kicker">Match intelligence</p>
          <strong>Northbridge × Riverside</strong>
        </div>
      </header>

      <div className="mini">
        <div className="mini-head">
          <span>Tactical snapshot</span>
          <span>Editorial view</span>
        </div>
        <Pitch
          snapshot={snapshot}
          tags={tags}
          homeColor={home?.color || "#6ea0ff"}
          awayColor={away?.color || "#ff7a59"}
          theme="schematic"
          compact
          uid="mini"
        />
        <p className="mini-foot">Positions from the event stream · not broadcast tracking</p>
      </div>

      <div className="intel">
        <Metric label="Northbridge WP" value={pct(wp.HOM)} fill={wp.HOM} color="#6ea0ff" />
        <Metric label="Riverside WP" value={pct(wp.AWY)} fill={wp.AWY} color="#ff7a59" />
        <Metric label="Control" value={snapshot ? snapshot.control.toFixed(2) : "—"} fill={snapshot?.control || 0.5} color="#3ee0c4" />
        <div className="stats">
          <div>
            <span>PPDA NOR</span>
            <b>{snapshot?.ppda.HOM ?? "—"}</b>
          </div>
          <div>
            <span>PPDA RIV</span>
            <b>{snapshot?.ppda.AWY ?? "—"}</b>
          </div>
          <div>
            <span>Tempo</span>
            <b>{snapshot?.tempo ?? "—"}</b>
          </div>
          <div>
            <span>Men</span>
            <b>
              {snapshot?.men.HOM ?? 11}–{snapshot?.men.AWY ?? 11}
            </b>
          </div>
        </div>
      </div>

      {inspector && (
        <div className="why-card">
          <p className="kicker">Why it matters</p>
          <p>{inspector.data.why}</p>
          <div className="reasons">
            {Object.entries(inspector.producer_reason).map(([k, v]) => (
              <div key={k}>
                <span>{k}</span>
                <i>
                  <em style={{ width: `${Math.round(Number(v) * 100)}%` }} />
                </i>
              </div>
            ))}
          </div>
        </div>
      )}
    </aside>
  );
}

function Metric({ label, value, fill, color }: { label: string; value: string; fill: number; color: string }) {
  return (
    <div className="metric">
      <div className="metric-top">
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
      <div className="meter">
        <i style={{ width: `${Math.max(6, Math.min(100, fill * 100))}%`, background: color }} />
      </div>
    </div>
  );
}
