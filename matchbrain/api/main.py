"""Match Brain API: REST + WebSocket replay of the live insight pipeline."""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from matchbrain.agents.studio import Studio
from matchbrain.catalog import ROOT
from matchbrain.narrator.llm import provider_name

load_dotenv()

WEB_DIST = ROOT / "web" / "dist"
WEB_SRC = ROOT / "web"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.studio = Studio.load(train_model=os.getenv("MATCHBRAIN_SKIP_TRAIN") != "1")
    yield


app = FastAPI(title="Match Brain", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def studio() -> Studio:
    return app.state.studio


@app.get("/api/health")
def health():
    s = studio()
    return {
        "ok": True,
        "narrator": provider_name(),
        "events": len(s.events),
        "facts": len(s.state.facts),
        "warm_ms": s.warm_ms,
    }


@app.get("/api/match")
def match():
    return studio().meta()


@app.get("/api/facts")
def facts(kind: str | None = None):
    items = studio().state.facts
    if kind:
        items = [f for f in items if f["kind"] == kind]
    return {"count": len(items), "facts": items}


@app.get("/api/cues")
def cues(persona_id: str = "analyst-en"):
    out = []
    for tick in studio().timeline:
        out.extend(tick["cues"].get(persona_id, []))
    return {"persona_id": persona_id, "count": len(out), "cues": out}


@app.get("/api/recap")
def recap(persona_id: str = "analyst-en"):
    return studio().recap(persona_id)


@app.get("/api/cv-stub")
def cv_stub():
    return studio().cv_report


@app.get("/api/verify-demo")
def verify_demo():
    return studio().forge_demo()


@app.websocket("/ws/replay")
async def replay(
    ws: WebSocket,
    speed: float = Query(12.0),
    from_t: float = Query(0.0),
    mode: str = Query("story"),
    personas: str = Query(""),
):
    await ws.accept()
    s = studio()
    persona_ids = [p for p in personas.split(",") if p] or [p["persona_id"] for p in s.personas]
    try:
        await ws.send_json({"type": "hello", "meta": s.meta()})
        # Catch-up snapshot just before from_t.
        prior = [tick for tick in s.timeline if tick["t"] <= from_t]
        if prior:
            await ws.send_json({"type": "state", "snapshot": prior[-1]["snapshot"], "t": prior[-1]["t"]})
        last_t = from_t
        for tick in s.timeline:
            if tick["t"] < from_t:
                continue
            dt = max(0.0, tick["t"] - last_t)
            if mode == "story":
                has_cue = any(tick["cues"].get(pid) for pid in persona_ids)
                is_goal = tick["event"]["type"] in ("goal", "card", "period_end")
                if is_goal:
                    delay = 2.8 / max(speed / 12, 0.4)
                elif has_cue:
                    delay = 1.5 / max(speed / 12, 0.4)
                elif tick["facts"]:
                    delay = 0.12
                else:
                    delay = min(0.04, dt / max(speed, 1) / 8)
            else:
                delay = min(dt / max(speed, 0.1), 1.5)
            if delay:
                await asyncio.sleep(delay)
            payload = {
                "type": "tick",
                "t": tick["t"],
                "event": tick["event"],
                "facts": tick["facts"],
                "cues": {pid: tick["cues"].get(pid, []) for pid in persona_ids},
                "snapshot": tick["snapshot"],
                "latency_ms": tick["latency_ms"],
            }
            await ws.send_json(payload)
            last_t = tick["t"]
        await ws.send_json({"type": "done", "snapshot": s.state.snapshot()})
    except WebSocketDisconnect:
        return


if WEB_DIST.exists():
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="web")
else:

    @app.get("/")
    def missing_web():
        return {
            "error": "Frontend not built. From the repo root run: cd web && npm install && npm run build",
        }


def run() -> None:
    import uvicorn

    uvicorn.run(
        "matchbrain.api.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("RELOAD") == "1",
    )


if __name__ == "__main__":
    run()
