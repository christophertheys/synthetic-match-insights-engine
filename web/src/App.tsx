import { useEffect, useMemo, useRef, useState } from "react";
import Insights from "./components/Insights";
import Overlays from "./components/Overlays";
import Pitch from "./components/Pitch";
import Sidecar from "./components/Sidecar";
import { FILM_SCENES, PERSONA_MOMENTS, PIPELINE, VERIFY_RULES } from "./story";
import type { Cue, MatchMeta, Snapshot, Tick } from "./types";

type LiveCue = Cue & { receivedAt: number };
type View = "live" | "insights" | "personas" | "verify";

const FILM = new URLSearchParams(location.search).get("film") === "1";

function clock(t: number): string {
  const m = Math.floor(t / 60);
  const s = Math.floor(t % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export default function App() {
  const [meta, setMeta] = useState<MatchMeta | null>(null);
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [playing, setPlaying] = useState(false);
  const [speed] = useState(FILM ? 14 : 12);
  const [fromT, setFromT] = useState(3300);
  const [personaA, setPersonaA] = useState("analyst-en");
  const [personaB, setPersonaB] = useState<string | null>(FILM ? "casual-es-home" : "casual-es-home");
  const [cues, setCues] = useState<Record<string, LiveCue[]>>({});
  const [latency, setLatency] = useState(0);
  const [inspector, setInspector] = useState<Cue | null>(null);
  const [verify, setVerify] = useState<Record<string, unknown> | null>(null);
  const [view, setView] = useState<View>("live");
  const [sceneId, setSceneId] = useState(FILM ? FILM_SCENES[0].id : "");
  const [inspectOpen, setInspectOpen] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const playRef = useRef<(startAt: number, split?: boolean) => void>(() => {});

  useEffect(() => {
    fetch("/api/match")
      .then((r) => r.json())
      .then(setMeta)
      .catch(() => setMeta(null));
  }, []);

  useEffect(() => {
    const id = window.setInterval(() => {
      const now = Date.now();
      setCues((prev) => {
        const next: Record<string, LiveCue[]> = {};
        for (const [k, list] of Object.entries(prev)) next[k] = list.filter((c) => now - c.receivedAt < 9000);
        return next;
      });
    }, 400);
    return () => window.clearInterval(id);
  }, []);

  function stop() {
    wsRef.current?.close();
    wsRef.current = null;
    setPlaying(false);
  }

  function play(startAt = fromT, split = Boolean(personaB)) {
    stop();
    const ids = [personaA, split ? personaB : null].filter(Boolean).join(",");
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${location.host}/ws/replay?speed=${speed}&from_t=${startAt}&mode=story&personas=${ids}`);
    wsRef.current = ws;
    setPlaying(true);
    setFromT(startAt);
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.type === "state" || msg.type === "hello") {
        if (msg.snapshot) setSnapshot(msg.snapshot);
        if (msg.meta) setMeta(msg.meta);
        return;
      }
      if (msg.type === "done") {
        if (msg.snapshot) setSnapshot(msg.snapshot);
        setPlaying(false);
        return;
      }
      if (msg.type !== "tick") return;
      const tick = msg as Tick;
      setSnapshot(tick.snapshot);
      setLatency(tick.latency_ms);
      const now = Date.now();
      setCues((prev) => {
        const next = { ...prev };
        for (const [pid, incoming] of Object.entries(tick.cues || {})) {
          if (!incoming.length) continue;
          const merged = [...(next[pid] || [])];
          for (const cue of incoming) {
            merged.push({ ...cue, receivedAt: now });
            setInspector(cue);
          }
          next[pid] = merged;
        }
        return next;
      });
    };
    ws.onclose = () => {
      if (wsRef.current === ws) setPlaying(false);
    };
  }

  playRef.current = (startAt, split) => play(startAt, split ?? Boolean(personaB));

  useEffect(() => () => stop(), []);

  useEffect(() => {
    if (!FILM) return;
    let cancelled = false;
    let timer: number | undefined;
    const run = async () => {
      try {
        await document.fonts.ready;
      } catch {
        /* continue with fallbacks */
      }
      await new Promise((res) => {
        timer = window.setTimeout(res, 500);
      });
      for (const scene of FILM_SCENES) {
        if (cancelled) return;
        setSceneId(scene.id);
        if (scene.view === "live" || scene.view === "personas" || scene.view === "insights") {
          setView(scene.view === "insights" ? "insights" : scene.view === "personas" ? "personas" : "live");
          setPersonaB(scene.personaB ? "casual-es-home" : null);
          if (scene.fromT != null) playRef.current(scene.fromT, Boolean(scene.personaB));
        }
        if (scene.view === "verify") {
          setView("verify");
          stop();
          try {
            const r = await fetch("/api/verify-demo");
            setVerify(await r.json());
          } catch {
            /* still show the panel */
          }
        }
        await new Promise((res) => {
          timer = window.setTimeout(res, scene.duration);
        });
      }
    };
    run();
    return () => {
      cancelled = true;
      if (timer) window.clearTimeout(timer);
    };
  }, []);

  useEffect(() => {
    if (view === "verify" && !verify) {
      fetch("/api/verify-demo")
        .then((r) => r.json())
        .then(setVerify)
        .catch(() => null);
    }
  }, [view, verify]);

  const personas = meta?.personas || [];
  const pa = personas.find((p) => p.persona_id === personaA) || personas[0];
  const pb = personaB ? personas.find((p) => p.persona_id === personaB) : null;
  const home = meta?.teams.HOM;
  const away = meta?.teams.AWY;
  const score = snapshot?.score || { HOM: 0, AWY: 0 };
  const tags = useMemo(() => (cues[personaA] || []).filter((c) => c.slot === "player_tag"), [cues, personaA]);
  const scene = FILM_SCENES.find((s) => s.id === sceneId);
  const cinematic = FILM && scene && (scene.view === "title" || scene.view === "pipeline" || scene.view === "end");
  const showSuper = FILM && scene && (scene.view === "live" || scene.view === "personas");
  const t = snapshot?.t || fromT;
  const unsupported = Array.isArray(verify?.unsupported) ? (verify?.unsupported as string[]) : [];

  const moments = [
    { id: "red", t: 3592, label: "01  Red card", clock: "61:00" },
    { id: "eq", t: 4516, label: "02  Equaliser", clock: "76:00" },
    { id: "win", t: 5302, label: "03  Winner", clock: "89:00" },
  ];

  return (
    <div className={`app ${FILM ? "film" : ""} ${cinematic ? "cinema" : ""}`} data-scene={sceneId || undefined}>
      {cinematic && scene && (
        <section className={`cinema-layer ${scene.view}`}>
          <div className="cinema-copy">
            <div className="brand-row">
              <span className="mark">MB</span>
              <em>Match Brain</em>
            </div>
            {scene.kicker && <p className="kicker">{scene.kicker}</p>}
            {scene.title && <h1>{scene.title}</h1>}
            {scene.body && <p className="cinema-body">{scene.body}</p>}
          </div>
          {scene.view === "pipeline" && (
            <ol className="pipeline">
              {PIPELINE.map((step) => (
                <li key={step.n}>
                  <span>{step.n}</span>
                  <div>
                    <strong>{step.name}</strong>
                    <em>{step.copy}</em>
                  </div>
                </li>
              ))}
            </ol>
          )}
        </section>
      )}

      <header className="top">
        <div className="brand">
          <span className="mark">MB</span>
          <div>
            <strong>Match Brain</strong>
            <em>See the game. Read why it matters.</em>
          </div>
        </div>
        <div className="scoreboard">
          <span className="team home">{home?.abbr || "NOR"}</span>
          <b>
            {score.HOM} <span>–</span> {score.AWY}
          </b>
          <span className="team away">{away?.abbr || "RIV"}</span>
          <time>{clock(t)}</time>
        </div>
        <div className="views">
          {(
            [
              ["live", "Immersive"],
              ["insights", "Tactical studio"],
              ["personas", "Personas"],
              ["verify", "Grounding"],
            ] as const
          ).map(([id, label]) => (
            <button key={id} className={view === id ? "on" : ""} onClick={() => setView(id)}>
              {label}
            </button>
          ))}
        </div>
        <div className="latency">{latency ? `${latency.toFixed(1)} ms` : "live"}</div>
      </header>

      <div className="moments">
        {moments.map((m) => (
          <button
            key={m.id}
            className={Math.abs(fromT - m.t) < 30 ? "on" : ""}
            onClick={() => {
              setView("live");
              play(m.t, true);
            }}
          >
            <span>{m.label}</span>
            <time>{m.clock}</time>
          </button>
        ))}
      </div>

      <main className={`stage view-${view}`}>
        {(view === "live" || view === "personas") && (
          <>
            <section className="pitch-wrap">
              <Pitch
                snapshot={snapshot}
                tags={tags}
                homeColor={home?.color || "#6ea0ff"}
                awayColor={away?.color || "#ff7a59"}
                uid="main"
              />
              {pa && <Overlays cues={cues[pa.persona_id] || []} persona={pa} />}
            </section>
            {view === "personas" && pb ? (
              <section className="persona-col">
                {PERSONA_MOMENTS.map((m) => (
                  <article key={m.id}>
                    <p className="kicker">{m.eyebrow}</p>
                    <p>{m.text}</p>
                  </article>
                ))}
                {pb && <Overlays cues={cues[pb.persona_id] || []} persona={pb} quiet />}
              </section>
            ) : (
              <Sidecar meta={meta} snapshot={snapshot} tags={tags} inspector={inspector} />
            )}
          </>
        )}

        {view === "insights" && <Insights meta={meta} snapshot={snapshot} tags={tags} />}

        {view === "verify" && (
          <section className="verify-view">
            <div className="verify-copy">
              <p className="kicker">Grounding verifier</p>
              <h2>Every number must already exist as a fact.</h2>
              <p className="lede">The narrator may only use formatted slots. Invented statistics never reach the overlay.</p>
              <ol className="verify-rules">
                {VERIFY_RULES.map((rule) => (
                  <li key={rule.n}>
                    <span>{rule.n}</span>
                    <div>
                      <h3>{rule.title}</h3>
                      <p>{rule.copy}</p>
                    </div>
                  </li>
                ))}
              </ol>
            </div>
            {verify && (
              <div className="verify-cards">
                <article>
                  <p className="kicker">Grounded caption</p>
                  <p>{String(verify.real)}</p>
                </article>
                <article className="forged">
                  <p className="kicker">Forged caption</p>
                  <p>{String(verify.forged)}</p>
                </article>
                <article className={verify.forged_ok ? "bad" : "good"}>
                  <p className="kicker">Verdict</p>
                  <h3>{verify.forged_ok ? "Accepted" : "Rejected"}</h3>
                  <p>{verify.forged_ok ? "The number was already on the fact." : "Unsupported figures never reach the overlay."}</p>
                  {unsupported.length > 0 && (
                    <p className="pills">{unsupported.map((n) => (n.includes("%") ? n : `${n}%`)).join(" · ")}</p>
                  )}
                </article>
              </div>
            )}
          </section>
        )}
      </main>

      {showSuper && scene && (
        <div className="film-super">
          <p className="kicker">{scene.kicker}</p>
          <div>
            <h2>{scene.title}</h2>
            {scene.body && <p>{scene.body}</p>}
          </div>
        </div>
      )}

      <footer className="transport">
        <button className="play" onClick={() => (playing ? stop() : play(fromT))} aria-label={playing ? "Pause" : "Play"}>
          {playing ? "❚❚" : "▶"}
        </button>
        <div className="scrub">
          <i style={{ width: `${Math.min(100, (t / 5400) * 100)}%` }} />
        </div>
        <span className="clock">{clock(t)}</span>
        <span className="muted">{playing ? "Story" : "Still"} · 12×</span>
        {!FILM && (
          <button className="ghost" onClick={() => setInspectOpen((v) => !v)}>
            Inspect
          </button>
        )}
      </footer>

      {inspectOpen && !FILM && (
        <div className="inspect">
          <pre>{inspector ? JSON.stringify(inspector, null, 2) : "Play to emit a timed OverlayCue."}</pre>
          <p className="muted">
            Narrator {meta?.narrator} · {meta?.facts} facts · CV F1 {meta?.cv_stub?.f1 ?? "—"}
          </p>
        </div>
      )}
    </div>
  );
}
