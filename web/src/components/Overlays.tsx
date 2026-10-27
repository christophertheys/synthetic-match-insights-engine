import type { Cue, Persona } from "../types";

type Props = {
  cues: Cue[];
  persona: Persona;
  quiet?: boolean;
};

function pick(cues: Cue[], slot: string): Cue | undefined {
  return cues.filter((c) => c.slot === slot).sort((a, b) => b.priority - a.priority)[0];
}

export default function Overlays({ cues, persona, quiet }: Props) {
  const takeover = pick(cues, "full_takeover");
  const lower = pick(cues, "lower_third") || (!takeover ? pick(cues, "side_panel") : undefined);
  const side = !takeover ? pick(cues, "side_panel") : undefined;
  const featured = takeover || lower;

  return (
    <div className={`overlay-stack ${persona.lang === "ar" ? "rtl" : ""} ${quiet ? "quiet" : ""}`}>
      {!quiet && (
        <div className="persona-chip">
          <i />
          {persona.label}
          <span>{persona.lang.toUpperCase()}</span>
        </div>
      )}

      {featured && (
        <div className={`banner ${takeover ? "hero" : ""}`}>
          <p className="kicker">{featured.data.why}</p>
          <h2>{featured.data.headline}</h2>
        </div>
      )}

      {side && side !== featured && !quiet && (
        <aside className="note">
          <p className="kicker">{side.template.replaceAll("_", " ")}</p>
          <h3>{side.data.headline}</h3>
        </aside>
      )}
    </div>
  );
}
