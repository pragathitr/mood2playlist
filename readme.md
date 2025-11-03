# Mood2Playlist

Turn a vibe into a playable, actually usable Spotify playlist.
Type “sitting by a fireplace while it snows” and get tracks that match the mood.

# What’s inside

- **Frontend:** React + Vite UI for prompts, presets, and results

- __Backend:__ FastAPI service that handles Spotify auth, search, recommendations, and the Agent DJ flow

- **Agent mode:** A tiny orchestration layer that parses natural language, maps it to audio features, and builds a track list that feels intentional

- **Presets:** Reusable mood tokens that map to audio features

**Repo layout:** `agentic_playlist/`, `backend/`, `frontend/`. 


# Quick start
### **1) Prereqs:**
   - Python 3.10+
   - Node 18+
   - A Spotify Developer app with Client ID and Secret

### **2) Backend setup:**
   - `cd backend`
   - `python -m venv .venv` 
   - `source .venv/bin/activate`   `# Windows: .venv\Scripts\activate`
   - `pip install -r requirements.txt`


**Create backend/ .env:**

`SPOTIFY_CLIENT_ID=your_client_id`
`SPOTIFY_CLIENT_SECRET=your_client_secret`

**Run it:**

`uvicorn app:app --reload --port 8000`

The API should be at: http://localhost:8000

### **3) Frontend setup:**

`cd ../frontend`

`npm i`

Create frontend/.env (Vite uses this at build time):

`VITE_API_BASE=http://localhost:8000`

**Run it:**

`npm run dev`

Vite will print a local URL, usually http://localhost:5173

# How it works

This is a small experimental project in which the agent parses your mood prompt into a small set of audio feature targets and seed artists/ genres.

Spotify calls are made by the backend. It uses Spotify APIs to search, pick seeds, and pull recommendations around those feature targets.

Curation occurs following this, where light filtering is done to avoid repeats and keep the vibe cohesive.

The tracks are then returned and the frontend renders a playable list with links.

### **At a high level:**

React UI  ->  `/api/agent` (FastAPI)

               ├─ vibe parser / presets
               ├─ seed search
               └─ recommendations -> curated track list

# Development notes

- Keep mood-to-features logic in a dedicated module so presets and parsing rules can evolve without touching API handlers.

- Add unit tests for the parser to keep agent behavior stable as you tweak heuristics.

- Consider caching Spotify responses during dev to avoid rate limits.

### Roadmap

- Optional user OAuth to create and save playlists directly

- Better seed selection via short-list reranking

- Per-mood diversity control and dedupe across sessions

- Shareable links for a generated playlist configuration