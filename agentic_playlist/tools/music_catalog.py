from __future__ import annotations
from typing import Dict, Any, List
from agentic_playlist.tracing.tracer import Tracer
from backend.spotify_client import search_tracks_by_genres_only  # bridge

class MusicCatalog:
    def __init__(self, tracer: Tracer, limit: int, variant: int, seed_genres: List[str] | None = None):
        self.tracer = tracer
        self.limit = limit
        self.variant = variant
        self.seed_genres = seed_genres or ["pop"]

    async def acurate(self, n: int = 30, seed: int = 42) -> List[Dict[str, Any]]:
        raw = await search_tracks_by_genres_only(self.seed_genres, limit=max(self.limit * 2, 20), variant=self.variant)
        out: List[Dict[str, Any]] = []
        for t in raw:
            artists = ", ".join(a.get("name", "") for a in t.get("artists", []))
            self.tracer.span(agent="curator", tool="spotify.search", details={"name": t.get("name", "")})
            out.append({
                "title": t.get("name", ""),
                "artist": artists,
                "genre": None,
                "region": "US",
                "spotify_url": t.get("external_urls", {}).get("spotify"),
                "image": (t.get("album", {}).get("images") or [{}])[0].get("url"),
            })
            if len(out) >= n:
                break
        return out
