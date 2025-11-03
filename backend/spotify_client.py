from __future__ import annotations
import os, time
from typing import Optional, Dict, Any, List
import httpx
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
if not CLIENT_ID or not CLIENT_SECRET:
    raise RuntimeError("Missing SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET")

_http: Optional[httpx.AsyncClient] = None
_token: Dict[str, Any] = {"access_token": None, "expires_at": 0}

async def _httpc() -> httpx.AsyncClient:
    global _http
    if _http is None:
        _http = httpx.AsyncClient(timeout=30)
    return _http

async def get_token() -> str:
    now = time.time()
    if _token["access_token"] and now < _token["expires_at"] - 30:
        return _token["access_token"]
    c = await _httpc()
    r = await c.post(
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
    tok = await get_token()
    headers = {"Authorization": f"Bearer {tok}", "Accept": "application/json"}
    c = await _httpc()
    url = f"https://api.spotify.com/v1/{path.strip('/')}"
    r = await c.get(url, headers=headers, params=params)
    if r.status_code != 200:
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise HTTPException(status_code=r.status_code, detail=f"Spotify error {r.status_code} @ {path}: {detail}")
    return r.json()

async def search_tracks_by_genres_only(seed_genres: List[str], limit: int, variant: int = 0) -> list[dict]:
    sg = [g for g in (seed_genres or [])][:3] or ["pop"]
    queries: List[str] = [f'genre:"{g}"' for g in sg]
    if len(sg) >= 2:
        queries.append("(" + " OR ".join([f'genre:"{g}"' for g in sg[:2]]) + ")")

    seen: set[str] = set()
    results: list[dict] = []
    per_call = min(max(limit, 1), 20)
    base_offset = (variant * 7) % 120

    for i, q in enumerate(queries):
        data = await spotify_get(
            "search",
            params={"q": q, "type": "track", "limit": per_call, "offset": base_offset + i * 5, "market": "US"},
        )
        for t in data.get("tracks", {}).get("items", []):
            tid = t.get("id")
            if not tid or tid in seen:
                continue
            seen.add(tid)
            results.append(t)
            if len(results) >= limit:
                return results
    return results

async def shutdown_http():
    global _http
    if _http is not None:
        await _http.aclose()
        _http = None
