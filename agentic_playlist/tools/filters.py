from __future__ import annotations
from typing import List, Dict, Any

def dedupe_by_artist(tracks: List[Dict[str, Any]], tracer=None) -> List[Dict[str, Any]]:
    seen = set(); out = []
    for t in tracks:
        a = t.get('artist')
        if a in seen:
            if tracer: tracer.span(agent='critic', tool='filters.dedupe', details={'artist': a}, status='drop')
            continue
        seen.add(a); out.append(t)
    return out

def ensure_diversity(tracks: List[Dict[str, Any]], tracer=None) -> List[Dict[str, Any]]:
    # toy: max 3 per (inferred) genre field (often None in Spotify track payloads)
    count = {}; out = []
    for t in tracks:
        g = t.get('genre') or 'na'
        n = count.get(g, 0)
        if n >= 3:
            if tracer: tracer.span(agent='critic', tool='filters.diversity', details={'genre': g}, status='drop')
            continue
        count[g] = n + 1
        out.append(t)
    return out
