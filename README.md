# ChronoQuest

ChronoQuest is a lightweight Flask-based single-player web game where you travel between airports, collect ChronoShards and Fluxfire, avoid bandits and paradox traps, and race back to Helsinki-Vantaa (EFHK) with the right fuel to win. The backend stores users in a simple JSON file and keeps an authoritative game state in the user session. A small Leaflet map on the frontend displays airports and lets you click to travel.

This README explains how the project is organized, how the game works, how to run it locally, and the available API endpoints.

---

## Quick overview

- Backend: Flask (Python)
- Frontend: JS + Leaflet for map UI
- Persistence: `users.json` contains user records; session stores the current game state
- Airports: `airport-data.json` — distances are computed from EFHK using the Haversine formula at startup
- Badges: `BADGE_DATA` in `app.py` and full badge descriptions in `badges.json`
- Default start location: EFHK (Helsinki-Vantaa Airport)

---

## Features

- Register and login users (passwords hashed via Werkzeug).
- Per-session authoritative game state; session state is returned by `/api/main/state`.
- Game mechanics:
  - Travel (random energy cost 20–200).
  - Random events: ChronoShard, Fluxfire, Bandits, Credits, Range, Paradox, Nothing.
  - Paradox trap: collect 3 paradox coins to escape.
  - Exchange Fluxfire for Credits, and Credits for Range (energy).
  - Win by returning to EFHK with 5 shards and required Fluxfire.
  - Loss conditions based on credits and energy.
- Badges awarded for milestones (first win/loss, flux/credits thresholds, shard collection, etc.)
- Airport distances from EFHK are computed with the Haversine formula (km).

---

## What this README contains

We created this README to explain:
- How to install and run ChronoQuest locally.
- The main routes and API endpoints with examples.
- How game state and persistence behave.
- Where to look for data and asset files.
- Troubleshooting tips and known behaviors to be aware of.

---

## Requirements

- Python 3.9+ (3.11 recommended)
- See `requirements.txt` for pinned package versions:
  - Flask==3.1.2
  - Werkzeug==3.1.4
  - itsdangerous==2.2.0
  - Jinja2==3.1.6

Create and activate a venv, then:

```
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

---

## Run locally

Set an optional secret for sessions (recommended for non-dev use):

```
export CHRONOSECRET="a-strong-secret"   # macOS / Linux
# Windows (PowerShell)
$env:CHRONOSECRET="a-strong-secret"
```

Start the server:

```
python app.py
```

By default the app runs on `http://127.0.0.1:5000` in debug mode (see `if __name__ == '__main__'` in `app.py`).

Open your browser at `http://localhost:5000` to play.

---

## File structure (important files)

- app.py — The Flask server and game logic
- requirements.txt — Python dependencies
- users.json — runtime user store (created automatically if missing)
- airport-data.json — list of airports (lat/lon given; distances computed at startup)
- badges.json — full badge metadata and descriptions
- templates/
  - start.html, main.html, end.html, quit.html
- static/
  - js/main.js, js/start.js, js/end.js
  - css/*.css
  - img/* (icons, logos, shard images, etc.)

---

## Important implementation notes / game behavior

- On login, the server always starts a brand-new game state for that user (session). Any previously persisted in-progress save for that user is cleared on login. This enforces a fresh start.
- A "persisted" in-progress save is stored in the user's `game_state_save` field in `users.json`. The server may write this on logout/quit or when saving between travels, but logging in always clears it.
- The authoritative game state used by the UI is the session-held object returned by `/api/main/state`.
- Airport distances:
  - The server computes distances from EFHK (Helsinki-Vantaa) using the Haversine formula at app startup (see constants EFHK_LAT / EFHK_LON in `app.py`).
  - Some entries in `airport-data.json` have a `distance` prefilled; the server recalculates for entries where needed (and leaves EFHK as origin).
- Loss conditions handled by the server:
  - credits <= 20 and energy == 0, or
  - credits == 0 and 10 <= energy <= 20

---

## API Endpoints

All endpoints are relative to the server root. JSON is used for request and response bodies.

Public (no auth required):
- POST /api/user/check
  - Body: { "name": "<username>" }
  - Returns: { "exists": true|false }
- POST /api/user/register
  - Body: { "name": "<username>", "password": "<password>" }
  - Creates user (if not exists) and starts session.
  - Returns: { "ok": true } on success
- POST /api/user/login
  - Body: { "name": "<username>", "password": "<password>" }
  - On success creates a new session and a fresh game; clears saved game for the user.
  - Returns: { "ok": true } or { "ok": false, "error": "..." }

Authenticated (require session cookie; the frontend handles this):
- GET /api/main/state
  - Returns current session game state (or creates a fresh one if missing).
  - Example response: { "state": { ...game state... } }
- GET /api/main/airports
  - Returns the airport list with computed `distance` from EFHK.
- POST /api/main/travel
  - Body: { "ICAO": "EGLL" }
  - Applies random travel cost, runs random events, updates session state, persists state into `users.json` (user's `game_state_save`).
  - Response includes `events`, `state`, `win`, `lose`.
- POST /api/buy/credits
  - Body: { "fluxfire": <number> }
  - Exchange rate: 1 Fluxfire -> 10 Credits.
  - Returns updated state.
- POST /api/buy/range
  - Body: { "credits": <number> } (also accepts `amount` field)
  - Rate: 1 Credit -> 1 Energy (client UI shows 1 Credit = 2 Range but server uses 1:1; be aware — see Known Issues).
- GET /api/user/badges
  - Returns user's badges with friendly names and descriptions.
- POST /api/user/logout
  - Clears session (`username` and `game_state`).

Other web routes:
- GET / or /start — Login/register page.
- GET /main — Main game UI (requires login).
- GET /end — End screen (requires login); the client reads the final run result from localStorage.
- GET /quit and POST /quit — Quit handling: POST toggles a quit flag, GET displays quit page if flagged.

---

## Game details & balance notes

- Travel costs are randomized (20–200). If a travel cost exceeds available energy, energy drops to zero and an `insufficient_range` event is returned.
- Paradox trap mechanics:
  - When triggered you must collect 3 paradox coins (awarded on arrival events while trapped) to escape.
  - The frontend has a watchdog timer that, if trapped for too long (2 minutes), will present a loss screen. The server also persists paradox metadata into the session.
- Shards: there are 5 ChronoShards. Collecting all 5 and enough Fluxfire to match the `required_flux` allows a win when traveling to EFHK.

---

Thanks for checking out ChronoQuest — load it up, collect your ChronoShards, and race back to EFHK before the bandits, flux, and paradoxes stop you.
