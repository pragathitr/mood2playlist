from __future__ import annotations
from typing import List, Dict, Any
from agentic_playlist.tools.filters import dedupe_by_artist, ensure_diversity

class Critic:
    def __init__(self, max_calls: int, tracer):
        self.max_calls = max_calls
        self.calls = 0
        self.tracer = tracer

    def review(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if self.calls >= self.max_calls:
            self.tracer.span(agent='critic', tool='filters.review', status='budget_exceeded')
            return candidates
        step1 = dedupe_by_artist(candidates, tracer=self.tracer)
        step2 = ensure_diversity(step1, tracer=self.tracer)
        self.calls += 1
        return step2
