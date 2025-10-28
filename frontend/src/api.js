const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export async function fetchRecommendations(mood, limit = 12, variant = 0) {
  const ts = Date.now(); // avoid any intermediary caching
  const url = `${API_BASE}/api/recommend?mood=${encodeURIComponent(mood)}&limit=${limit}&variant=${variant}&_=${ts}`;
  const res = await fetch(url);
  if (!res.ok) {
    let msg = `API error: ${res.status}`;
    try {
      const j = await res.json();
      if (j?.detail) msg += ` — ${typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail)}`;
    } catch {}
    throw new Error(msg);
  }
  return res.json();
}
// Agent Mode: fetch multi-agent playlist
export async function fetchAgenticPlaylist({ mood, limit = 10, seed = 42, variant = 0 }) {
  const params = new URLSearchParams({ mood, limit, seed, variant });
  const res = await fetch(`/api/agentic/recommend?${params.toString()}`);
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Agentic API failed: ${res.status} ${txt}`);
  }
  return await res.json();
}
