# url=
import os, json, random, time
from pathlib import Path
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
# NEW: Import math functions for distance calculation
from math import radians, sin, cos, sqrt, atan2

# --- Configuration and Setup ---
BASE = Path(__file__).parent
USERS_FILE = BASE / 'users.json'
AIRPORTS_FILE = BASE / 'airport-data.json'

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)
# NOTE: Use a secure secret key in production; environment variable recommended
app.secret_key = os.environ.get('CHRONOSECRET', 'dev-secret-please-change')

# --- Constants for Distance Calculation ---
# Coordinates for Helsinki-Vantaa Airport (EFHK)
EFHK_LAT = 60.317222
EFHK_LON = 24.963333
R = 6371  # Earth radius in kilometers

BADGE_DATA = {
    "FIRST_WIN": {"name": "Time Traveler", "desc": "Achieved your first ChronoQuest victory."},
    "FIRST_LOSS": {"name": "Temporal Blip", "desc": "Experienced your first journey ending in defeat."},
    "FLUX_MASTER": {"name": "Fluxfire Collector", "desc": "Reached 20 Fluxfire in a single game."},
    "CREDIT_KING": {"name": "Credit King", "desc": "Reached 5000 Credits in a single game."},
    "FULL_SHARDS": {"name": "Shard Hoarder", "desc": "Collected all 5 ChronoShards."},
}


# --- Haversine Distance Helper ---

def calculate_distance(lat2, lon2):
    """Return the great-circle distance (km) from EFHK to the given lat/lon using the Haversine formula."""
    lat1 = radians(EFHK_LAT)
    lon1 = radians(EFHK_LON)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    # Return distance rounded down to the nearest whole kilometer
    distance = int(R * c)
    return distance


# --- User Management Helpers ---

def load_users():
    """Load users.json and return the parsed list. Create the file if it doesn't exist."""
    if not USERS_FILE.exists():
        USERS_FILE.write_text('[]', encoding='utf-8')
    return json.loads(USERS_FILE.read_text(encoding='utf-8'))


def save_users(users):
    """Write the provided users list back to users.json with indentation."""
    USERS_FILE.write_text(json.dumps(users, indent=2), encoding='utf-8')


def find_user(username):
    """Return the user dict for the given username (case-insensitive), or None if not found."""
    users = load_users()
    for u in users:
        if u['playerName'].lower() == username.lower():
            return u
    return None


def get_user_index(username):
    """Return the index of the user in the users list or -1 if not found."""
    users = load_users()
    for i, u in enumerate(users):
        if u['playerName'].lower() == username.lower():
            return i
    return -1


# --- Airport Loading (MODIFIED to calculate distances) ---

def load_all_airports():
    """Load airports from AIRPORTS_FILE and compute distance from EFHK for each entry.

    Returns a list of airport dicts. If the file is missing or invalid JSON, returns an empty list.
    """
    airports_list = []

    # Load all airports from the primary file
    try:
        with open(AIRPORTS_FILE, 'r', encoding='utf-8') as f:
            airports_list.extend(json.load(f))
    except FileNotFoundError:
        print(f"Error: Airport data file not found at {AIRPORTS_FILE}")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {AIRPORTS_FILE}")
        return []

    # Calculate distance for all loaded airports (skip EFHK which is the origin)
    for airport in airports_list:
        if airport['ICAO'] != 'EFHK':
            try:
                # Use Haversine formula helper to compute km distance
                airport['distance'] = calculate_distance(airport['lat'], airport['lon'])
            except KeyError:
                # If lat/lon missing, set a sentinel high value and warn
                print(f"Warning: Missing lat/lon data for {airport['ICAO']}. Setting distance to a default high value.")
                airport['distance'] = 9999

    return airports_list


# Assign the combined list to AIRPORTS
AIRPORTS = load_all_airports()


def get_airport_by_icao(icao):
    """Return an airport dict from AIRPORTS matching the ICAO code, or None."""
    return next((a for a in AIRPORTS if a['ICAO'] == icao), None)


# --- Game State Helpers ---

def new_game_state(username):
    """Create and return a fresh game state for a given username.

    Randomly selects a fuel type and required flux to vary each new game.
    """
    # Determine random fuel requirements
    fuel_types = {"Aetherite": [8, 12], "Lumorin": [14, 18], "Voltash": [5, 8], "Noxalite": [11, 15], "Inferno": [1, 5]}
    chosen_fuel = random.choice(list(fuel_types.keys()))
    required_flux = random.randint(fuel_types[chosen_fuel][0], fuel_types[chosen_fuel][1])

    return {
        'playerName': username,
        'credits': 1000,
        'energy': 1000,
        'shards': {},
        'countShards': 0,
        'currentLocation': 'EFHK',  # Helsinki-Vantaa Airport
        'fluxfire': 0,
        'paradox': {'active': False, 'coins': 0, 'startTime': 0},
        'fuel_to_make': chosen_fuel,
        'required_flux': required_flux
    }


def get_game_state():
    """Retrieve the game state stored in the session (or None)."""
    return session.get('game_state')


def save_game_state(gs):
    """Store the provided game state into the session."""
    session['game_state'] = gs


def persist_game_state(username, gs):
    """Persist the provided game state into the user's profile in users.json.

    This saves an in-progress game so it can be resumed later (unless intentionally cleared).
    """
    users = load_users()
    idx = get_user_index(username)
    if idx != -1:
        # Use a shallow copy to avoid accidental references; set None to clear save
        users[idx]['game_state_save'] = gs.copy() if gs else None
        save_users(users)


# --- Decorator and Persistent Stats Logic ---

def login_required(f):
    """Flask decorator that enforces a logged-in session for routes."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            # API routes should return 401 on missing auth; page routes redirect to start page.
            if request.path.startswith('/api/'):
                return jsonify({'error': 'not logged in'}), 401
            return redirect(url_for('start_page'))
        return f(*args, **kwargs)

    return decorated_function


def award_badge(username, badge_id):
    """Add a badge to a user's profile if they don't already have it.

    Returns the badge metadata when newly awarded, otherwise None.
    """
    users = load_users()
    idx = get_user_index(username)

    if idx != -1:
        user = users[idx]
        if badge_id not in user.get('playerBadges', []):
            user.setdefault('playerBadges', []).append(badge_id)
            save_users(users)
            return BADGE_DATA.get(badge_id, {"name": badge_id, "desc": "New Badge!"})
    return None


def update_user_stats(username, win=False, clear_game=True):
    """Increment play/win/loss counters for a user and award first-win/loss badges.

    If clear_game is True, the saved in-progress game is removed from the user's profile.
    """
    users = load_users()
    idx = get_user_index(username)

    if idx != -1:
        user = users[idx]
        # Ensure counters exist
        user.setdefault('playerHowManyTimesPlayed', 0)
        user.setdefault('playerHowManyWins', 0)
        user.setdefault('playerHowManyLoses', 0)

        user['playerHowManyTimesPlayed'] += 1

        if win:
            user['playerHowManyWins'] += 1
            award_badge(username, 'FIRST_WIN')
        else:
            user['playerHowManyLoses'] += 1
            award_badge(username, 'FIRST_LOSS')

        if clear_game:
            # Clear any persisted in-progress save when the game is finalized
            user['game_state_save'] = None

        save_users(users)


# --- HTML Page Routes ---

@app.route('/')
@app.route('/start')
def start_page():
    """Render the login/register start page.

    Always shows start.html; successful login is handled by the API which then navigates to /main.
    """
    return render_template('start.html')


@app.route('/main')
@login_required
def main_page():
    """Render the main game UI.

    Important: Do NOT create a fresh game state here. The client requests the session state via /api/main/state.
    Clearing persisted save here prevents resurrecting an old in-progress game on page load.
    """
    # Ensure any persisted save is cleared so reloads/logins won't resurrect an old in-progress game
    persist_game_state(session['username'], None)

    return render_template('main.html')


@app.route('/end')
@login_required
def end_page():
    """Render the game over page (win or lose). The client reads the result (win/lose) from localStorage."""
    return render_template('end.html')

@app.route('/quit', methods=['GET', 'POST'])
@login_required
def quit_page():
    """Handle quitting: POST sets a quit flag; GET renders the quit page if flagged, otherwise redirects."""
    username = session.get('username')

    # If POST (from button click), set a quit flag
    if request.method == 'POST':
        session['player_quit'] = True
        return '', 204

    # GET: render quit page if the player quit
    if session.pop('player_quit', False):
        # Optionally persist and clear the current session game state
        gs = get_game_state()
        if gs:
            persist_game_state(username, gs)  # save current state if desired
            session.pop('game_state', None)

        return render_template('quit.html', message="You quit the game. 👋")
    else:
        # If no quit flag, redirect back to the main game
        return redirect(url_for('main_page'))

# --- API Routes - Authentication ---

@app.route('/api/user/check', methods=['POST'])
def api_user_check():
    """API: Check if a username exists (used during the login flow)."""
    data = request.get_json()
    name = data.get('name')
    if find_user(name):
        return jsonify({'exists': True})
    return jsonify({'exists': False})


@app.route('/api/user/login', methods=['POST'])
def api_user_login():
    """API: Authenticate an existing user.

    Behavior: Always start a brand-new game on login and clear any persisted saved game to enforce a fresh start.
    """
    data = request.get_json()
    name = data.get('name')
    password = data.get('password')
    user = find_user(name)

    if user and check_password_hash(user['playerPasswordHash'], password):
        session['username'] = name

        # Always start a brand-new game on login (option C)
        new_gs = new_game_state(name)
        session['game_state'] = new_gs

        # Clear persisted save for this user to enforce "start new on login/page load"
        persist_game_state(name, None)

        return jsonify({'ok': True})
    return jsonify({'ok': False, 'error': 'Wrong password'})


@app.route('/api/user/register', methods=['POST'])
def api_user_register():
    """API: Create a new user account and start a fresh session.

    New users get default counters and no saved in-progress game.
    """
    data = request.get_json()
    name = data.get('name')
    password = data.get('password')

    if find_user(name):
        return jsonify({'ok': False, 'error': 'User already exists'})

    users = load_users()

    # Initialize game state but do NOT persist it (we will always start new on login/page load)
    initial_gs = new_game_state(name)

    new_user = {
        'playerName': name,
        'playerPasswordHash': generate_password_hash(password),
        'playerBadges': [],
        'playerLoseBadges': [],
        'playerHowManyWins': 0,
        'playerHowManyLoses': 0,
        'playerHowManyTimesPlayed': 0,
        'jetstream_uses': 0,
        'game_state_save': None  # Do not save an initial in-progress game
    }
    users.append(new_user)
    save_users(users)

    session['username'] = name
    # session gets a fresh game for this login
    session['game_state'] = initial_gs

    return jsonify({'ok': True})


# FIX: Add an API to fetch the current game state when main.js loads
@app.route('/api/main/state', methods=['GET'])
@login_required
def api_get_state():
    """Return the current game state stored in the session.

    If the session is missing a state, create a fresh one (consistent with login behavior) and persist the cleared save.
    """
    gs = get_game_state()
    if gs:
        return jsonify({'state': gs})

    # If somehow session state is missing, create a fresh one (option C behavior)
    username = session.get('username')
    if username:
        fresh = new_game_state(username)
        save_game_state(fresh)
        # Clear persisted save to be consistent with option C
        persist_game_state(username, None)
        return jsonify({'state': fresh})

    return jsonify({'error': 'Game state not found'}), 404


@app.route('/api/user/logout', methods=['POST'])
def api_user_logout():
    """API: Log out the current user and clear session game state."""
    session.pop('username', None)
    session.pop('game_state', None)
    return jsonify({'ok': True})


# --- API Routes - Game Flow ---


def weighted_sample_without_replacement(population, weights, k):
    """Select up to k unique items from population according to given weights (without replacement)."""
    items = population[:]
    w = weights[:]
    picked = []
    k = min(k, len(items))
    for _ in range(k):
        total = sum(w)
        if total <= 0:
            break
        r = random.uniform(0, total)
        cumulative = 0
        for i, wt in enumerate(w):
            cumulative += wt
            if r <= cumulative:
                picked.append(items.pop(i))
                w.pop(i)
                break
    return picked


def check_loss_conditions(gs):
    """Return True when the game's special loss conditions are met.

    Loss occurs when:
      - credits <= 20 and energy == 0
      OR
      - credits == 0 and 10 <= energy <= 20
    """
    credits = gs.get('credits', 0)
    energy = gs.get('energy', 0)
    if credits <= 20 and energy == 0:
        return True
    if credits == 0 and 10 <= energy <= 20:
        return True
    return False


@app.route('/api/main/airports', methods=['GET'])
@login_required
def api_get_airports():
    """Return the preloaded list of airports including computed distance from EFHK."""
    # The AIRPORTS list is now loaded with calculated distances
    return jsonify(AIRPORTS)


@app.route('/api/main/travel', methods=['POST'])
@login_required
def api_travel():
    """Handle travel to another airport, apply energy cost, random events, and win/lose logic.

    This endpoint updates the session game state and persists it to the user's profile.
    """
    gs = get_game_state()
    username = session['username']
    data = request.get_json()
    icao = data.get('ICAO')
    events = []
    lose = False
    win = False

    # Prevent travel if the player has no energy (cannot move)
    if gs['energy'] <= 0:
        return jsonify({
            'events': [{'type': 'no_energy', 'message': 'Cannot travel with 0 Energy. Must refuel.'}],
            'state': gs,
            'win': False,
            'lose': False,
            'ok': False,
            'error': 'Insufficient Energy'
        }), 400

    # Check for EFHK (home) win condition: all shards and enough fluxfire
    if icao == 'EFHK':
        if gs['countShards'] == 5 and gs['fluxfire'] >= gs['required_flux']:
            win = True
            update_user_stats(username, win=True, clear_game=True)
            return jsonify(
                {'events': [{'type': 'win', 'fuel': gs['fuel_to_make'], 'required_flux': gs['required_flux']}],
                 'state': gs, 'win': True, 'lose': False})
        else:
            events.append({'type': 'efhk_requirements_not_met', 'required_flux': gs['required_flux']})
            save_game_state(gs)
            persist_game_state(username, gs)
            return jsonify({'events': events, 'state': gs, 'win': False, 'lose': False})

    # --- Standard Travel Logic (applies whether or not trapped in a paradox) ---

    cost = random.randint(20, 200)

    # Deduct energy cost; if not enough, deplete energy to 0 and notify
    if gs['energy'] < cost:
        gs['energy'] = 0
        events.append({'type': 'insufficient_range', 'message': 'Not enough range for full travel; range set to 0.'})
    else:
        gs['energy'] -= cost

    # Update the player's current location
    gs['currentLocation'] = icao

    # --- Handle random events on arrival ---

    is_trapped = gs['paradox']['active']
    num_events = random.randint(1, 3)

    if is_trapped:
        # When trapped in a paradox, events are limited: either nothing happens or a paradox coin is awarded.
        base_events = events[:]
        events = base_events

        # 50% chance to grant a paradox coin, 50% chance nothing
        if random.random() < 0.5:
            gs['paradox']['coins'] += 1
            events.append({'type': 'paradox_coin', 'coins': gs['paradox']['coins']})

            if gs['paradox']['coins'] >= 3:
                # Escape trap after collecting 3 coins
                gs['paradox']['active'] = False
                gs['paradox']['coins'] = 0
                events.append({'type': 'paradox_escaped'})
        else:
            events.append({'type': 'nothing'})

    else:
        # Normal event pool when not trapped
        event_population = ['bandit', 'credits', 'range', 'fluxfire', 'paradox', 'shard', 'nothing']
        event_weights = [1, 1, 1, 1, 1, 1, 1]  # equal chance for each event

        chosen = weighted_sample_without_replacement(event_population, event_weights, num_events)

        for ev in chosen:
            if ev == 'bandit':
                # Bandit steals either credits or range (randomly chosen)
                steal_type = random.choice(['credits', 'range'])
                if steal_type == 'credits':
                    loss_amount = random.randint(20, 100)
                    gs['credits'] = max(0, gs['credits'] - loss_amount)
                    events.append({'type': 'bandit', 'subtype': 'credits', 'amount': loss_amount})
                else:
                    loss_amount = random.randint(10, 100)
                    gs['energy'] = max(0, gs['energy'] - loss_amount)
                    events.append({'type': 'bandit', 'subtype': 'range', 'amount': loss_amount})

            elif ev == 'credits':
                # Player gains credits; award CREDIT_KING badge at threshold
                gain = random.randint(10, 100)
                gs['credits'] += gain
                events.append({'type': 'credits', 'amount': gain})
                if gs['credits'] >= 5000:
                    award_badge(username, 'CREDIT_KING')

            elif ev == 'range':
                # Player gains energy (range)
                gain = random.randint(10, 100)
                gs['energy'] += gain
                events.append({'type': 'range', 'amount': gain})

            elif ev == 'fluxfire':
                # Increment fluxfire and award FLUX_MASTER badge at 20
                gs['fluxfire'] += 1
                events.append({'type': 'fluxfire'})
                if gs['fluxfire'] >= 20:
                    award_badge(username, 'FLUX_MASTER')

            elif ev == 'paradox':
                # Activate paradox trap if not already active
                if not gs['paradox'].get('active', False):
                    gs['paradox']['active'] = True
                    gs['paradox']['coins'] = 0
                    gs['paradox']['startTime'] = int(time.time() * 1000)
                    events.append({'type': 'paradox'})
                else:
                    # If already trapped, treat as nothing
                    events.append({'type': 'nothing'})

            elif ev == 'shard':
                # Give the next uncollected shard (1..5) if available
                shard_id = next((i for i in range(1, 6) if str(i) not in gs['shards']), None)
                if shard_id is not None:
                    gs['shards'][str(shard_id)] = True
                    events.append({'type': 'shard', 'shard': shard_id})
                    if len(gs['shards']) == 5:
                        award_badge(username, 'FULL_SHARDS')
                else:
                    # No shards left to collect
                    events.append({'type': 'nothing'})

            elif ev == 'nothing':
                events.append({'type': 'nothing'})

    # Update the shard count based on collected shards
    gs['countShards'] = sum(1 for v in gs['shards'].values() if v)

    # Check for loss after processing events; if lost, finalize and persist
    if check_loss_conditions(gs):
        lose = True
        update_user_stats(username, win=False, clear_game=True)
        save_game_state(gs)
        persist_game_state(username, gs)
        return jsonify(
            {'events': events + [{'type': 'lose', 'message': 'You have lost the game.'}], 'state': gs, 'win': False,
             'lose': True})

    # No loss: persist state and return current events and state
    save_game_state(gs)
    persist_game_state(username, gs)
    return jsonify({'events': events, 'state': gs, 'win': win, 'lose': lose})


@app.route('/api/buy/credits', methods=['POST'])
@login_required
def api_buy_credits():
    """Exchange fluxfire for credits at a fixed rate (1 Fluxfire = 10 Credits)."""
    gs = get_game_state()
    username = session['username']
    data = request.get_json()
    flux_spend = data.get('fluxfire', 0)

    if not flux_spend or flux_spend <= 0:
        return jsonify({'ok': False, 'error': 'Invalid amount of Fluxfire.'})

    if gs['fluxfire'] < flux_spend:
        return jsonify({'ok': False, 'error': 'Not enough Fluxfire.'})

    # Exchange rate: 1 Fluxfire = 10 Credits (as per client-side)
    credit_gain = flux_spend * 10

    gs['fluxfire'] -= flux_spend
    gs['credits'] += credit_gain
    save_game_state(gs)
    persist_game_state(username, gs)

    return jsonify({'ok': True, 'state': gs})


# NEW ROUTE: Buy Range/Energy using Credits
@app.route('/api/buy/range', methods=['POST'])
@login_required
def api_buy_range():
    """Exchange credits for energy (range). Accepts either 'credits' or 'amount' fields.

    Rate: 1 Credit = 1 Energy.
    """
    gs = get_game_state()
    username = session['username']
    data = request.get_json()

    # Accept either 'credits' or 'amount' for robustness
    credits_spend = data.get('credits', data.get('amount', 0))

    if not credits_spend or credits_spend <= 0:
        return jsonify({'ok': False, 'error': 'Invalid amount of Credits.'})

    if gs['credits'] < credits_spend:
        return jsonify({'ok': False, 'error': 'Not enough Credits.'})

    # 1:1 exchange rate
    range_gain = credits_spend

    gs['credits'] -= credits_spend
    gs['energy'] += range_gain

    save_game_state(gs)
    persist_game_state(username, gs)

    return jsonify({'ok': True, 'state': gs})


@app.route('/api/user/badges', methods=['GET'])
@login_required
def api_get_badges():
    """Return the current user's badges with friendly names and descriptions."""
    user = find_user(session['username'])

    player_badges = []
    for badge_id in user.get('playerBadges', []):
        badge_info = BADGE_DATA.get(badge_id, {"name": badge_id, "desc": "Unknown Badge"})
        player_badges.append(f"{badge_info['name']} ({badge_info['desc']})")

    return jsonify({'playerBadges': player_badges})


# --- Server Run Block ---

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
