import json, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def run(seed: int):
    cmd = ["python", str(ROOT / "main.py"), "--seed", str(seed)]
    subprocess.run(cmd, check=True)
    out = ROOT / "outputs" / f"playlist-seed{seed}.json"
    return json.loads(out.read_text())

def test_same_seed_same_output(tmp_path):
    a = run(7); b = run(7)
    assert a['playlist'] == b['playlist']
