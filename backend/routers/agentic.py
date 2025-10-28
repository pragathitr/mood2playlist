from __future__ import annotations
from typing import List, Dict, Any
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from backend.mood_map import MOOD_PRESETS
from agentic_playlist.agents.orchestrator import Orchestrator
from agentic_playlist.tracing.tracer import Tracer
from agentic_playlist.tools.music_catalog import MusicCatalog
import pathlib

router = APIRouter()

class AgentTrack(BaseModel):
    title: str
    artist: str
    genre: str | None = None
    region: str | None = None
    spotify_url: str | None = None
    image: str | None = None

class AgenticResponse(BaseModel):
    mood: str
    seed: int
    count: int
    playlist: List[AgentTrack] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    trace_url: str | None = None  # NEW

@router.get("/recommend", response_model=AgenticResponse)
async def agentic_recommend(
    mood: str = Query(...),
    limit: int = Query(10, ge=1, le=50),
    seed: int = Query(42, ge=0),
    variant: int = Query(0, ge=0),
):
    key = (mood or "").strip().lower()
    preset = MOOD_PRESETS.get(key)
    seed_genres = (preset or {}).get("seed_genres") or []

    traces_dir = pathlib.Path("agentic_playlist/traces")
    traces_dir.mkdir(parents=True, exist_ok=True)
    trace_path = traces_dir / f"agent-run-{key}-seed{seed}-v{variant}.jsonl"
    tracer = Tracer(trace_path)

    catalog = MusicCatalog(tracer=tracer, limit=limit, variant=variant, seed_genres=seed_genres)
    orch = Orchestrator(
        cfg={"seed": seed, "playlist_size": limit, "budgets": {
            "curator_max_calls": 8, "critic_max_calls": 3, "compliance_max_calls": 3
        }},
        tracer=tracer,
        catalog=catalog,
    )
    result = await orch.arun()
    trace_rel = f"/traces/{trace_path.name}"  # <-- URL that maps to the static mount
    return AgenticResponse(
        mood=key,
        seed=result["seed"],
        count=len(result["playlist"]),
        playlist=[AgentTrack(**t) for t in result["playlist"]],
        metrics=result["metrics"],
        trace_url=trace_rel,
    )
