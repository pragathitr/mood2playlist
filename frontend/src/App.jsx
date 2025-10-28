import { useState } from 'react'
import { motion } from 'framer-motion'
import { fetchRecommendations } from './api'
import { fetchAgenticPlaylist } from "./api";

const MOODS = ["hype","cozy","focus","sad-girl","romantic","study","rage-run","party","dark"]

function TrackCard({ t }) {
  return (
    <motion.a
      href={t.spotify_url}
      target="_blank"
      rel="noreferrer"
      className="block rounded-2xl bg-neutral-900/60 p-4 hover:bg-neutral-800/60 border border-neutral-800"
      whileHover={{ scale: 1.02 }}
    >
      <div className="flex gap-4">
        <img src={t.image} alt={t.name} className="w-20 h-20 rounded-xl object-cover" />
        <div className="flex-1">
          <div className="text-lg font-semibold">{t.name}</div>
          <div className="text-sm text-neutral-400">{t.artists}</div>
          {t.preview_url && (
            <audio controls src={t.preview_url} className="mt-2 w-full" />
          )}
        </div>
      </div>
    </motion.a>
  )
}

export default function App() {
  const [mood, setMood] = useState('cozy')
  const [custom, setCustom] = useState('')
  const [loading, setLoading] = useState(false)
  const [tracks, setTracks] = useState([])
  const [error, setError] = useState('')
  const [variant, setVariant] = useState(0)           // NEW
  const [clicks, setClicks] = useState(0)             // NEW
  const refreshEveryTwo = true                        // toggle behavior here
  const [agentMood, setAgentMood] = useState("cozy");
  const [agentSeed, setAgentSeed] = useState(42);
  const [agentVariant, setAgentVariant] = useState(0);
  const [agentData, setAgentData] = useState(null);
  const [agentLoading, setAgentLoading] = useState(false);
  const [agentError, setAgentError] = useState("");


  async function handleAgentRun() {
    setAgentLoading(true);
    setAgentError("");
    setAgentData(null);
    try {
      const data = await fetchAgenticPlaylist({
        mood: agentMood,
        limit: 10,
        seed: Number(agentSeed) || 42,
        variant: Number(agentVariant) || 0,
      });
      setAgentData(data);
    } catch (e) {
      setAgentError(String(e?.message || e));
    } finally {
      setAgentLoading(false);
   }
  }

  async function go() {
    setLoading(true); setError('')
    try {
      const m = custom.trim() || mood
       // compute next variant: every click or every 2 clicks
      const nextClicks = clicks + 1
      const nextVariant = refreshEveryTwo ? Math.floor(nextClicks / 2) : nextClicks

      const data = await fetchRecommendations(m, 12, nextVariant)
      setTracks(data.tracks)

      // update counters after success
      setClicks(nextClicks)
      setVariant(nextVariant)

      const url = new URL(window.location.href)
      url.searchParams.set('mood', m)
      window.history.replaceState({}, '', url)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold tracking-tight">Mood2Playlist</h1>
      <p className="text-neutral-400 mt-1">Type a vibe or pick one and get instant recommendations.</p>

      <div className="mt-6 flex flex-wrap gap-2">
        {MOODS.map(m => (
          <button
            key={m}
            onClick={() => { setMood(m); setCustom('') }}
            className={`px-3 py-1.5 rounded-full border ${mood===m? 'bg-neutral-100 text-neutral-900 border-neutral-100':'bg-neutral-900/60 border-neutral-800'}`}
          >{m}</button>
        ))}
      </div>

      <div className="mt-4 flex gap-2">
        <input
          value={custom}
          onChange={e=>setCustom(e.target.value)}
          placeholder="or… type your own vibe (e.g., cozy fireplace, rainy study)"
          className="flex-1 rounded-xl bg-neutral-900/60 border border-neutral-800 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-neutral-600"
        />
        <button
          onClick={go}
          disabled={loading}
          className="rounded-xl px-5 py-3 bg-white text-black font-semibold disabled:opacity-60"
        >{loading? 'Finding…':'Generate'}</button>
      </div>

      {error && <div className="mt-4 text-red-400 whitespace-pre-wrap">{error}</div>}

      <div className="grid md:grid-cols-2 gap-4 mt-6">
        {tracks.map(t => <TrackCard key={t.id} t={t} />)}
      </div>

      {!tracks.length && (
        <div className="mt-10 text-neutral-500">No tracks yet — pick a mood and hit Generate.</div>
      )}

      {/* Agent Mode (Multi-Agent, Traced) */}
<div className="mt-8 rounded-xl border border-neutral-700/40 p-4">
  <h3 className="text-lg font-semibold">Agent Mode (2026-ready)</h3>

  <div className="mt-3 grid grid-cols-1 sm:grid-cols-4 gap-3">
    <div>
      <label className="block text-sm opacity-80 mb-1">Mood</label>
      <input
        className="w-full rounded-md border border-neutral-700/50 bg-transparent px-3 py-2"
        value={agentMood}
        onChange={(e) => setAgentMood(e.target.value)}
        placeholder="cozy"
      />
    </div>

    <div>
      <label className="block text-sm opacity-80 mb-1">Seed</label>
      <input
        type="number"
        className="w-full rounded-md border border-neutral-700/50 bg-transparent px-3 py-2"
        value={agentSeed}
        onChange={(e) => setAgentSeed(e.target.value)}
      />
    </div>

    <div>
      <label className="block text-sm opacity-80 mb-1">Variant</label>
      <input
        type="number"
        className="w-full rounded-md border border-neutral-700/50 bg-transparent px-3 py-2"
        value={agentVariant}
        onChange={(e) => setAgentVariant(e.target.value)}
      />
    </div>

    <div className="flex items-end">
      <button
        onClick={handleAgentRun}
        className="w-full rounded-md bg-indigo-600 hover:bg-indigo-500 px-4 py-2 font-medium"
      >
        Try Agent Mode
      </button>
    </div>
  </div>

  {agentLoading && <p className="mt-3 text-sm opacity-80">Generating…</p>}
  {agentError && <p className="mt-3 text-sm text-red-400">{agentError}</p>}

  {agentData && (
    <div className="mt-4">
      <p className="text-sm opacity-75">
        mood <span className="font-mono">{agentData.mood}</span> •
        seed <span className="font-mono">{agentData.seed}</span> •
        size <span className="font-mono">{agentData.count}</span> •
        dup_rate <span className="font-mono">{Number(agentData?.metrics?.dup_rate ?? 0).toFixed(2)}</span> •
        unique_artists <span className="font-mono">{agentData?.metrics?.unique_artists}</span>
      </p>
      <a
        href={`http://localhost:8000${agentData.trace_url}`}
        target="_blank"
        rel="noreferrer"
        className="text-xs underline opacity-70"
      >
        view trace
      </a>

      <ul className="mt-3 space-y-2">
        {agentData.playlist.map((t, i) => (
          <li key={i} className="flex items-center gap-3">
            {t.image ? (
              <img src={t.image} alt="" className="w-12 h-12 rounded-md object-cover" />
            ) : (
              <div className="w-12 h-12 rounded-md bg-neutral-800" />
            )}
            <div>
              <a
                href={t.spotify_url || "#"}
                target="_blank"
                rel="noreferrer"
                className="hover:underline"
              >
                {i + 1}. {t.artist} — {t.title}
              </a>
              {t.genre && (
                <div className="text-xs opacity-60">genre: {t.genre}</div>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )}
</div>

    </div>

  )
}