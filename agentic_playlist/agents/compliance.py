from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict, Any

SECURITY_DIR = Path(__file__).resolve().parent.parent / 'security'

class Compliance:
    def __init__(self, max_calls: int, tracer):
        self.max_calls = max_calls
        self.calls = 0
        self.tracer = tracer
        with open(SECURITY_DIR / 'denylist.json', 'r', encoding='utf-8') as f:
            self.deny = set(json.load(f).get('explicit_artists', []))
        with open(SECURITY_DIR / 'allowlist.json', 'r', encoding='utf-8') as f:
            self.allow = set(json.load(f).get('allowed_regions', ['US']))

    def enforce(self, tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if self.calls >= self.max_calls:
            self.tracer.span(agent='compliance', tool='policy.enforce', status='budget_exceeded')
            return tracks
        out = []
        for t in tracks:
            artist = t.get('artist', '')
            if artist in self.deny:
                self.tracer.span(agent='compliance', tool='policy.block', details={'artist': artist}, status='deny')
                continue
            region = t.get('region', 'US')
            if region not in self.allow:
                self.tracer.span(agent='compliance', tool='policy.region_block', details={'region': region}, status='deny')
                continue
            out.append(t)
        self.calls += 1
        return out
