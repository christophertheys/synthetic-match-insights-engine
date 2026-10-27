import { INSIGHT_CARDS } from "../story";
import Pitch from "./Pitch";
import type { Cue, MatchMeta, Snapshot } from "../types";

type Props = {
  meta: MatchMeta | null;
  snapshot: Snapshot | null;
  tags: Cue[];
};

export default function Insights({ meta, snapshot, tags }: Props) {
  return (
    <section className="insights">
      <div className="insight-copy">
        <p className="kicker">Match Brain / Tactical studio</p>
        <h2>Read why it turned.</h2>
        <p className="lede">Spot the scoreline. Find the shift. The equaliser is a consequence, not the start.</p>
        <ol>
          {INSIGHT_CARDS.map((card) => (
            <li key={card.n}>
              <span>{card.n}</span>
              <div>
                <h3>{card.title}</h3>
                <p>{card.copy}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>
      <div className="insight-pitch">
        <div className="mini-head">
          <span>Tactical view / schematic</span>
          <span>Attack to goal →</span>
        </div>
        <div className="pitch-frame">
          <Pitch
            snapshot={snapshot}
            tags={tags}
            homeColor={meta?.teams.HOM.color || "#6ea0ff"}
            awayColor={meta?.teams.AWY.color || "#ff7a59"}
            theme="schematic"
            uid="insight"
          />
        </div>
      </div>
    </section>
  );
}
