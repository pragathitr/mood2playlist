from __future__ import annotations

import os, time, re
from typing import Optional, Dict, Any, List
import random
import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from fastapi import FastAPI
#from backend.spotify_client import spotify_get, shutdown_http  # NEW shared client
from backend.mood_map import MOOD_PRESETS
#from mood_map import MOOD_PRESETS
from pathlib import Path
from pathlib import Path
from fastapi.staticfiles import StaticFiles

# --- env ---
load_dotenv()
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=False)
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
if not CLIENT_ID or not CLIENT_SECRET:
    raise RuntimeError("Missing SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET")

# --- app ---
app = FastAPI(title="Mood2Playlist API (Search+Vibe)", version="2.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount(
    "/traces",
    StaticFiles(directory="agentic_playlist/traces"),
    name="traces",
)
# --- Agent Mode routes ---
from backend.routers.agentic import router as agentic_router
app.include_router(agentic_router, prefix="/api/agentic", tags=["agentic"])


# --- models ---
class Track(BaseModel):
    id: str
    name: str
    artists: str
    album: str = ""
    image: str = ""
    preview_url: Optional[str] = None
    spotify_url: Optional[str] = None

class RecommendResponse(BaseModel):
    mood: str
    count: int
    tracks: List[Track] = Field(default_factory=list)

# --- http + token cache ---
_http: Optional[httpx.AsyncClient] = None
_token: Dict[str, Any] = {"access_token": None, "expires_at": 0}

async def http() -> httpx.AsyncClient:
    global _http
    if _http is None:
        _http = httpx.AsyncClient(timeout=30)
    return _http

async def get_token() -> str:
    now = time.time()
    if _token["access_token"] and now < _token["expires_at"] - 30:
        return _token["access_token"]
    client = await http()
    r = await client.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(CLIENT_ID, CLIENT_SECRET),
    )
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Spotify auth failed: {r.text}")
    data = r.json()
    _token["access_token"] = data["access_token"]
    _token["expires_at"] = now + int(data.get("expires_in", 3600))
    return _token["access_token"]

async def spotify_get(path: str, params: dict | None = None) -> dict:
    token = await get_token()
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    client = await http()
    url = f"https://api.spotify.com/v1/{path.strip('/')}"
    r = await client.get(url, headers=headers, params=params)
    if r.status_code != 200:
        body = r.text
        try:
            j = r.json()
            body = j if j else body
        except Exception:
            pass
        raise HTTPException(status_code=r.status_code, detail=f"Spotify error {r.status_code} @ {path}: {body}")
    return r.json()

# --- Vibe Parser ---
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

# --- Query builder & search ---

def build_queries_from_genres(seed_genres: List[str]) -> List[str]:
    sg = [g for g in (seed_genres or [])][:3] or ["pop"]
    # Build 2–4 queries using only genre filters; avoid title keyword bias entirely
    queries: List[str] = []
    for g in sg:
        queries.append(f'genre:"{g}"')
    if len(sg) >= 2:
        queries.append("(" + " OR ".join([f'genre:"{g}"' for g in sg[:2]]) + ")")
    return queries
'''
async def search_tracks_by_genre_only(seed_genres: List[str], limit: int) -> List[Track]:
    queries = build_queries_from_genres(seed_genres)
    seen: set[str] = set()
    results: List[Track] = []
    per_call = min(max(limit, 1), 20)
    for q in queries:
        data = await spotify_get(
            "search",
            params={
                "q": q,
                "type": "track",
                "limit": per_call,
                "market": "US",
            },
        )
        for t in data.get("tracks", {}).get("items", []):
            tid = t.get("id")
            if not tid or tid in seen:
                continue
            seen.add(tid)
            images = (t.get("album", {}).get("images") or [])
            img = images[0]["url"] if images else ""
            results.append(
                Track(
                    id=tid,
                    name=t.get("name", ""),
                    artists=", ".join(a.get("name", "") for a in t.get("artists", [])),
                    album=t.get("album", {}).get("name", ""),
                    image=img,
                    preview_url=t.get("preview_url"),
                    spotify_url=t.get("external_urls", {}).get("spotify"),
                )
            )
            if len(results) >= limit:
                return results
    return results
'''
async def search_tracks_by_genre_only(seed_genres: List[str], limit: int, variant: int = 0) -> List[Track]:
    # deterministic RNG based on variant so the same variant -> same set (debuggable)
    rng = random.Random(variant)

    queries = build_queries_from_genres(seed_genres)
    if queries:
        # rotate query order based on variant, so different starting genre each time
        r = variant % len(queries)
        queries = queries[r:] + queries[:r]

    seen: set[str] = set()
    results: List[Track] = []
    per_call = min(max(limit, 1), 20)

    # use offset to paginate within Spotify search results without changing query
    # keep it modest; most searches have useful results within first few hundred
    base_offset = (variant * 7) % 120  # 0..119, step of 7 to jump pages

    for i, q in enumerate(queries):
        data = await spotify_get(
            "search",
            params={
                "q": q,
                "type": "track",
                "limit": per_call,
                "offset": base_offset + i * 5,  # nudge each query differently
                "market": "US",
            },
        )
        for t in data.get("tracks", {}).get("items", []):
            tid = t.get("id")
            if not tid or tid in seen:
                continue
            seen.add(tid)
            images = (t.get("album", {}).get("images") or [])
            img = images[0]["url"] if images else ""
            results.append(
                Track(
                    id=tid,
                    name=t.get("name", ""),
                    artists=", ".join(a.get("name", "") for a in t.get("artists", [])),
                    album=t.get("album", {}).get("name", ""),
                    image=img,
                    preview_url=t.get("preview_url"),
                    spotify_url=t.get("external_urls", {}).get("spotify"),
                )
            )
            if len(results) >= limit:
                return results
    return results

# --- routes ---
@app.get("/api/health")
async def health():
    token_ok = True
    try:
        await get_token()
    except HTTPException:
        token_ok = False
    return {"ok": True, "token": token_ok, "moods": len(MOOD_PRESETS)}

@app.get("/api/moods")
async def moods():
    return sorted(MOOD_PRESETS.keys())

@app.get("/api/recommend", response_model=RecommendResponse)
async def recommend(
    mood: str = Query(...),
    limit: int = Query(12, ge=1, le=50),
    variant: int = Query(0, ge=0),  # NEW
):
    key = (mood or "").strip().lower()
    preset = MOOD_PRESETS.get(key)
    if preset:
        seed_genres = preset.get("seed_genres", [])
        parsed_from = "preset"
    else:
        seed_genres = parse_vibe(key)
        parsed_from = "vibe"

    tracks = await search_tracks_by_genre_only(seed_genres, limit, variant=variant)  # pass variant
    return RecommendResponse(mood=f"{key} ({parsed_from})", count=len(tracks), tracks=tracks)

'''
@app.get("/api/recommend", response_model=RecommendResponse)
async def recommend(mood: str = Query(...), limit: int = Query(12, ge=1, le=50)):
    key = (mood or "").strip().lower()
    preset = MOOD_PRESETS.get(key)

    if preset:
        seed_genres = preset.get("seed_genres", [])
        parsed_from = "preset"
    else:
        # Treat as free text → vibe parser → genres
        seed_genres = parse_vibe(key)
        parsed_from = "vibe"

    tracks = await search_tracks_by_genre_only(seed_genres, limit)
    return RecommendResponse(mood=f"{key} ({parsed_from})", count=len(tracks), tracks=tracks)
'''

@app.on_event("shutdown")
async def _shutdown():
    global _http
    if _http is not None:
        await _http.aclose()
        _http = None