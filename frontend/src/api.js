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