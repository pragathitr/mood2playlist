import json, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def run(seed: int):
    cmd = ["python", str(ROOT / "main.py"), "--seed", str(seed)]
    subprocess.run(cmd, check=True)
    out = ROOT / "outputs" / f"playlist-seed{seed}.json"
    return json.loads(out.read_text())

def test_unique_artists_nonzero():
    r = run(9)
    assert r['metrics']['unique_artists'] > 0
