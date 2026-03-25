"""
Multiplayer Classroom Game – Magic Dungeon
==========================================
A Flask + Socket.IO multiplayer dungeon game.

Each round a random correct exit is chosen from [front, back, left, right].
All players pick a direction. Once everyone has answered, a results table is
shown. Correct answers advance the player one dungeon. First to clear all
dungeons wins!

Run:
    python game.py
Then open http://localhost:5000 in a browser.
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, emit
import secrets
import random

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)


# ---------------------------------------------------------------------------
# Reverse-proxy middleware – reads X-Script-Name header set by nginx so that
# url_for() automatically prepends the sub-path (e.g. /py_dungeon).
# ---------------------------------------------------------------------------
class ReverseProxied:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        script_name = environ.get("HTTP_X_SCRIPT_NAME", "")
        if script_name:
            environ["SCRIPT_NAME"] = script_name
            path_info = environ.get("PATH_INFO", "")
            if path_info.startswith(script_name):
                environ["PATH_INFO"] = path_info[len(script_name):]
        return self.wsgi_app(environ, start_response)


app.wsgi_app = ReverseProxied(app.wsgi_app)

socketio = SocketIO(app)

# ---------------------------------------------------------------------------
# Game settings
# ---------------------------------------------------------------------------
MIN_PLAYERS = 3
MAX_PLAYERS = 20
TOTAL_DUNGEONS = 5
DIRECTIONS = ["front", "back", "left", "right"]

# ---------------------------------------------------------------------------
# In-memory state  (resets every time the server restarts)
# ---------------------------------------------------------------------------
players: dict[str, dict] = {}          # sid -> {"name": str, "progress": int}
game = {
    "started": False,
    "current_round": 0,
    "correct_exit": None,
    "answers": {},                     # sid -> direction chosen
    "finished_players": [],            # names in finishing order
}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def welcome():
    return render_template("welcome.html")


@app.route("/api/status")
def api_status():
    return jsonify(
        count=len(players),
        min=MIN_PLAYERS,
        max=MAX_PLAYERS,
        full=len(players) >= MAX_PLAYERS,
        started=game["started"],
    )


@app.route("/join", methods=["POST"])
def join():
    name = request.form.get("name", "").strip()
    if not name:
        return redirect(url_for("welcome"))
    if len(players) >= MAX_PLAYERS:
        return redirect(url_for("welcome"))
    if game["started"]:
        return redirect(url_for("welcome"))
    session["player_name"] = name
    return redirect(url_for("lobby"))


@app.route("/lobby")
def lobby():
    name = session.get("player_name")
    if not name:
        return redirect(url_for("welcome"))
    return render_template("lobby.html", player_name=name,
                           min_players=MIN_PLAYERS, max_players=MAX_PLAYERS)


@app.route("/game")
def game_page():
    name = session.get("player_name")
    if not name:
        return redirect(url_for("welcome"))
    return render_template("game.html", player_name=name,
                           total_dungeons=TOTAL_DUNGEONS,
                           directions=DIRECTIONS)


# ---------------------------------------------------------------------------
# Socket.IO - Lobby events
# ---------------------------------------------------------------------------
@socketio.on("connect")
def handle_connect():
    pass


@socketio.on("player_join")
def handle_player_join(data):
    if game["started"]:
        emit("game_already_started")
        return
    if len(players) >= MAX_PLAYERS:
        emit("lobby_full")
        return

    name = data.get("name", "Anonymous")
    players[request.sid] = {"name": name, "progress": 0}
    emit("update_players", build_lobby_state(), broadcast=True)


@socketio.on("disconnect")
def handle_disconnect():
    was_in = request.sid in players
    players.pop(request.sid, None)
    game["answers"].pop(request.sid, None)

    if was_in and not game["started"]:
        emit("update_players", build_lobby_state(), broadcast=True)

    # If game is running, check if all remaining players answered
    if game["started"] and players:
        active = active_players()
        if active and all(sid in game["answers"] for sid in active):
            broadcast_round_results()


@socketio.on("start_game")
def handle_start_game():
    if game["started"]:
        return
    if len(players) < MIN_PLAYERS:
        return

    game["started"] = True
    game["current_round"] = 0
    game["finished_players"] = []

    for p in players.values():
        p["progress"] = 0

    start_new_round()
    emit("game_started", {}, broadcast=True)


# ---------------------------------------------------------------------------
# Socket.IO - Game events
# ---------------------------------------------------------------------------
@socketio.on("rejoin_game")
def handle_rejoin_game(data):
    """Player loads the game page (or reconnects)."""
    name = data.get("name", "Anonymous")

    # Find existing player with same name (reconnect scenario)
    existing_sid = None
    for sid, p in players.items():
        if p["name"] == name and sid != request.sid:
            existing_sid = sid
            break

    if existing_sid:
        players[request.sid] = players.pop(existing_sid)
        if existing_sid in game["answers"]:
            game["answers"][request.sid] = game["answers"].pop(existing_sid)
    elif request.sid not in players:
        players[request.sid] = {"name": name, "progress": 0}

    emit("round_start", build_round_state())
    emit("answer_status", build_answer_status())


@socketio.on("submit_answer")
def handle_submit_answer(data):
    if not game["started"]:
        return
    sid = request.sid
    if sid not in players:
        return
    if sid in game["answers"]:
        return
    if players[sid]["progress"] >= TOTAL_DUNGEONS:
        return

    direction = data.get("direction", "")
    if direction not in DIRECTIONS:
        return

    game["answers"][sid] = direction
    emit("answer_status", build_answer_status(), broadcast=True)

    # Check if all active players have answered
    active = active_players()
    if all(sid in game["answers"] for sid in active):
        broadcast_round_results()


# ---------------------------------------------------------------------------
# Game logic helpers
# ---------------------------------------------------------------------------
def active_players() -> list[str]:
    """SIDs of players who haven't cleared all dungeons yet."""
    return [sid for sid, p in players.items()
            if p["progress"] < TOTAL_DUNGEONS]


def start_new_round():
    game["current_round"] += 1
    game["correct_exit"] = random.choice(DIRECTIONS)
    game["answers"] = {}


def broadcast_round_results():
    correct = game["correct_exit"]
    results = []

    for sid, direction in game["answers"].items():
        if sid not in players:
            continue
        p = players[sid]
        is_correct = direction == correct
        if is_correct:
            p["progress"] += 1

        results.append({
            "name": p["name"],
            "choice": direction,
            "correct": is_correct,
            "progress": p["progress"],
        })

    # Track finishing order
    for sid, p in players.items():
        if (p["progress"] >= TOTAL_DUNGEONS
                and p["name"] not in game["finished_players"]):
            game["finished_players"].append(p["name"])

    results.sort(key=lambda r: (-r["correct"], -r["progress"]))

    leaderboard = sorted(
        [{"name": p["name"], "progress": p["progress"]}
         for p in players.values()],
        key=lambda x: -x["progress"]
    )

    game_over = all(p["progress"] >= TOTAL_DUNGEONS
                    for p in players.values())

    socketio.emit("round_results", {
        "round": game["current_round"],
        "correct_exit": correct,
        "results": results,
        "leaderboard": leaderboard,
        "total_dungeons": TOTAL_DUNGEONS,
        "finished": game["finished_players"],
        "game_over": game_over,
    })

    if not game_over:
        start_new_round()
        socketio.sleep(6)
        socketio.emit("round_start", build_round_state())


def build_round_state() -> dict:
    return {
        "round": game["current_round"],
        "total_dungeons": TOTAL_DUNGEONS,
        "directions": DIRECTIONS,
        "scores": {p["name"]: p["progress"] for p in players.values()},
    }


def build_answer_status() -> dict:
    answered, waiting = [], []
    for sid, p in players.items():
        if p["progress"] >= TOTAL_DUNGEONS:
            continue
        (answered if sid in game["answers"] else waiting).append(p["name"])
    return {
        "answered": answered,
        "waiting": waiting,
        "total_active": len(answered) + len(waiting),
        "total_answered": len(answered),
    }


def build_lobby_state() -> dict:
    return {
        "players": [{"name": p["name"]} for p in players.values()],
        "count": len(players),
        "min": MIN_PLAYERS,
        "max": MAX_PLAYERS,
        "ready": len(players) >= MIN_PLAYERS,
        "full": len(players) >= MAX_PLAYERS,
    }


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
