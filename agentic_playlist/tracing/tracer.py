from __future__ import annotations
import json, time
from pathlib import Path
from typing import Optional, Dict, Any

class Tracer:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._span_id = 0

    def span(self, agent: str, tool: str, details: Optional[Dict[str, Any]] = None, status: str = 'ok') -> None:
        self._span_id += 1
        rec = {
            'span_id': self._span_id,
            'ts': time.time(),
            'agent': agent,
            'tool': tool,
            'status': status,
            'details': details or {},
        }
        with open(self.path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(rec) + '\n')
