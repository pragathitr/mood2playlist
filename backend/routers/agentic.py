from __future__ import annotations
from typing import List, Dict, Any
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from backend.mood_map import MOOD_PRESETS
from agentic_playlist.agents.orchestrator import Orchestrator
from agentic_playlist.tracing.tracer import Tracer
from agentic_playlist.tools.music_catalog import MusicCatalog
import pathlib

# Rule-based scoring: map free-text to a vibe profile, then to seed genres.
LEX = {
    "cozy": {"words": {"fireplace","blanket","candle","warm","cocoa","snow","reading","rain","chai"}, "genres": ["acoustic","singer-songwriter","indie","folk","chill","lo-fi","piano"]},
    "focus": {"words": {"study","focus","deep work","flow","concentrate","essay","reading"}, "genres": ["lo-fi","ambient","piano","classical","chill"]},
    "party": {"words": {"club","dancefloor","party","friday","dj","festival","rave", "dance"}, "genres": ["dance","edm","house","pop","hip-hop"]},
    "hype": {"words": {"gym","workout","max","pr","anthem","hype","run"}, "genres": ["edm","electro","dance","hip-hop","pop"]},
    "sad": {"words": {"heartbreak","alone","cry","melancholy","nostalgic","blue", "sad"}, "genres": ["indie","indie-pop","singer-songwriter","alt-rock","pop"]},
    "romantic": {"words": {"date","romantic","kiss","slow","candlelight","valentine", "love"}, "genres": ["r-n-b","soul","latin","pop","indie-pop"]},
    "dark": {"words": {"noir","brooding","night","storm","industrial"}, "genres": ["industrial","electro","rock","trap","alt-rock"]},
    "rage": {"words": {"rage","sprint","angry","angry gym","metal","mosh", "rock", "hard rock"}, "genres": ["rock","metal","trap","alt-rock","edm"]},
}

DEFAULT_GENRES = ["pop","indie","singer-songwriter","chill"]

def parse_vibe(text: str) -> List[str]:
    """Return a list of seed genres inferred from free-text."""
    s = (text or "").lower()
    # Shortcut seasonal/scene cues
    if any(w in s for w in ["fireplace","snow","blanket","cocoa","candle","knit","sweater","winter"]):
        return ["acoustic","singer-songwriter","indie","folk","chill","piano"][:3]
    if any(w in s for w in ["rain","rainy","monsoon"]):
        return ["lo-fi","indie","chill","ambient","piano"][:3]
    if any(w in s for w in ["gym","lift","sprint","pr","max","preworkout"]):
        return ["edm","electro","hip-hop","dance","pop"][:3]
    if any(w in s for w in ["club","night out","party","rave","dj"]):
        return ["dance","edm","house","pop","hip-hop"][:3]

    # Score-based: count lexicon hits
    scores: Dict[str,int] = {}
    for label, conf in LEX.items():
        hits = sum(1 for w in conf["words"] if w in s)
        if hits:
            scores[label] = hits
    if scores:
        # pick top label
        label = max(scores, key=scores.get)
        return LEX[label]["genres"][:3]

    # Fallback
    return DEFAULT_GENRES[:3]

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
    if preset:
        seed_genres = preset.get("seed_genres", [])
        parsed_from = "preset"
    else:
        seed_genres = parse_vibe(key)
        parsed_from = "vibe"

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
    #    mood=key,
        mood=f"{key} ({parsed_from})",
        seed=result["seed"],
        count=len(result["playlist"]),
        playlist=[AgentTrack(**t) for t in result["playlist"]],
        metrics=result["metrics"],
        trace_url=trace_rel,
    )
