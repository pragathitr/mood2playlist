import { useState } from 'react'
import { motion } from 'framer-motion'
import { fetchRecommendations } from './api'

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
    </div>
  )
}