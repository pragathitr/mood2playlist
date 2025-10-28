from __future__ import annotations
import random
from dataclasses import dataclass
from typing import Dict, Any, List
from agentic_playlist.tracing.tracer import Tracer
from agentic_playlist.agents.critic import Critic
from agentic_playlist.agents.compliance import Compliance

@dataclass
class Orchestrator:
    cfg: Dict[str, Any]
    tracer: Tracer
    catalog: Any  # injected

    async def arun(self) -> Dict[str, Any]:
        seed = int(self.cfg.get("seed", 42))
        random.seed(seed)
        budgets = self.cfg.get("budgets", {})
        critic = Critic(max_calls=budgets.get("critic_max_calls", 3), tracer=self.tracer)
        compliance = Compliance(max_calls=budgets.get("compliance_max_calls", 3), tracer=self.tracer)

        candidates = await self.catalog.acurate(n=30, seed=seed)
        reviewed = critic.review(candidates)
        compliant = compliance.enforce(reviewed)
        k = int(self.cfg.get("playlist_size", 10))
        final = compliant[:k]
        metrics = {
            "dup_rate": self._dup_rate(final),
            "unique_artists": len({t["artist"] for t in final}),
            "size": len(final),
        }
        return {"playlist": final, "metrics": metrics, "seed": seed}

    @staticmethod
    def _dup_rate(tracks: List[Dict[str, Any]]) -> float:
        by_artist, dup = {}, 0
        for t in tracks:
            a = t.get("artist")
            by_artist[a] = by_artist.get(a, 0) + 1
        for c in by_artist.values():
            dup += max(0, c - 1)
        return 0.0 if not tracks else dup / len(tracks)
