from pathlib import Path
import argparse, json
from agentic_playlist.agents.orchestrator import Orchestrator
from agentic_playlist.tracing.tracer import Tracer
from agentic_playlist.tools.music_catalog import MusicCatalog

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--mood", type=str, default="cozy")
    p.add_argument("--variant", type=int, default=0)
    args = p.parse_args()

    traces = Path(__file__).parent / "traces"
    traces.mkdir(parents=True, exist_ok=True)
    trace_path = traces / f"cli-run-{args.mood}-seed{args.seed}-v{args.variant}.jsonl"
    tracer = Tracer(trace_path)

    # seed genres is mock here; API path uses mood_map
    catalog = MusicCatalog(tracer=tracer, limit=args.limit, variant=args.variant, seed_genres=["pop","indie","chill"])
    orch = Orchestrator(cfg={"seed": args.seed, "playlist_size": args.limit, "budgets": {
        "curator_max_calls": 8, "critic_max_calls": 3, "compliance_max_calls": 3
    }}, tracer=tracer, catalog=catalog)

    import asyncio
    result = asyncio.run(orch.arun())

    out = Path(__file__).parent / "outputs" / f"playlist-seed{args.seed}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2))
    print("Wrote:", out, "\nTrace:", trace_path)

if __name__ == "__main__":
    main()
