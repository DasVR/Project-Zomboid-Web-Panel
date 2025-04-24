import eventlet
eventlet.monkey_patch()
import os
import threading
import time
import json
import requests
from player_map import get_player_locations
from utils.config_parser import parse_config_file
from datetime import timedelta
from config_editor import config_bp
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file, flash
from flask_socketio import SocketIO
from auth import login_user, logout_user, require_login
from server_control import start_server, stop_server, is_running, attach_socketio, maybe_start_log_stream, server_process
from logs_parser import tail_log, get_players
from utils.sysinfo import get_stats
from auth import load_users, save_user
from flask_openid import OpenID
from steam_openid import get_steam_openid_url, parse_steam_id
from utils.duckdns_updater import start_duckdns_loop

app = Flask(__name__)
app.secret_key = "supersecretkey"

oid = OpenID(app, os.path.join(os.getcwd(), 'openid-store'))
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
start_duckdns_loop()
attach_socketio(socketio)

app.register_blueprint(config_bp)

@app.route("/link-steam")
@require_login
def link_steam():
    return redirect(get_steam_openid_url(url_for("verify_steam", _external=True)))


@app.route("/verify-steam")
@require_login
def verify_steam():
    claimed_id = request.args.get("openid.claimed_id")
    if claimed_id:
        steam_id = parse_steam_id(claimed_id)
        user = session["user"]

        # Save the steam_id to steam_links.json
        try:
            with open("steam_links.json", "r") as f:
                links = json.load(f)
        except:
            links = {}

        links[user] = steam_id
        with open("steam_links.json", "w") as f:
            json.dump(links, f, indent=2)

        flash(f"✅ Linked Steam ID: {steam_id}")
    else:
        flash("⚠️ Failed to link Steam.")

    return redirect(url_for("dashboard"))

# Logging in the user
@app.route("/", methods=["GET", "POST"])
def login():
    return login_user()

# Logging out the user
@app.route("/logout")
def logout():
    return logout_user()

# Running the signup route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        users = load_users()
        if username in users:
            flash("Username already exists!", "error")
        else:
            save_user(username, password)
            flash("✅ Account created. You may now log in.")
            return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/api/player-locations")
def player_locations():
    return jsonify(get_player_locations())

# Rendering the dashboard and stats
@app.route("/dashboard")
@require_login
def dashboard():
    return render_template("dashboard.html", stats=get_stats(), running=is_running())

# Opens the player dashboard
@app.route("/players_dashboard")
@require_login
def players_dashboard():
    return render_template("players.html", players=get_players())

# Opens the config editor with all sections and global variable
@app.route("/config-editor")
def config_page():
    config_path = r"C:\Users\airfr\Zomboid\Server\servertest.ini"
    config, descriptions, ranges = parse_config_file(config_path)
    return render_template("server_config.html", config_values={
        "config": config,
        "descriptions": descriptions,
        "ranges": ranges
    })

# Gets the server control options and runs them
@app.route("/control", methods=["POST"])
@require_login
def control():
    action = request.form.get("action")
    print(f"[🧠] Action = {action}")

    if action == "start":
        print("Server is starting!")
        start_server()
    elif action == "stop":
        print("Server is stopping!")
        stop_server()
    elif action == "restart":
        stop_server()
        time.sleep(1)
        start_server()
    elif action == "force_stop":
        global server_process
        if server_process:
            print("[💣] FORCE STOP triggered!")
            server_process.kill()
            server_process.wait()
        server_process = None

    return redirect(url_for("dashboard"))

# Puts the stats into jsonify and outputs them
@app.route("/stats")
@require_login
def stats():
    return jsonify(get_stats())

# Jsonifies the players
@app.route("/players")
@require_login
def players():
    return jsonify({"players": get_players()})

# Gets the last known log
@app.route("/log_tail")
@require_login
def log_tail():
    return jsonify({"lines": tail_log()})

# Gets the server status
@app.route("/server-status")
def server_status():
    status = "running" if is_running() else "stopped"
    return jsonify({"status": status})

# A test websocket to show if a user connected to the log streaming
@socketio.on('connect')
def test_emit_to_browser():
    print("[SocketIO] Client connected.")
    socketio.emit("log_update", {"line": "[TEST] Hello from server\n"})

# Displays a display that starts the log streaming and debug line
@socketio.on('connect')
def client_connected():
    print("[SocketIO] Client connected.")
    socketio.emit("log_update", {"line": "[CLIENT] Connected to WebSocket ✅\n"})
    maybe_start_log_stream()

# Gets the stats... (again)
@app.route("/metrics")
@require_login
def metrics():
    return jsonify(get_stats())

def serialize_config(config):
    safe_config = {}
    for k, v in config.items():
        if isinstance(v, timedelta):
            safe_config[k] = str(v)  # or v.total_seconds() if preferred
        else:
            safe_config[k] = v
    return safe_config

# Gets the live players and displays them into the json
@app.route("/live_players")
@require_login
def live_players():
    return jsonify({"players": get_players()})

# Renders the map
@app.route("/map")
@require_login
def player_map():
    return render_template("player_map.html")

# Gets the logs and outputs them into the downloadable logs
@app.route("/logs-history")
@require_login
def logs_history():
    log_dir = "logs"
    try:
        logs = []
        for filename in sorted(os.listdir(log_dir), reverse=True):
            if filename.endswith((".log", ".txt")):
                filepath = os.path.join(log_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        line_count = sum(1 for _ in f)
                    logs.append({"filename": filename, "lines": line_count})
                except Exception as e:
                    logs.append({"filename": filename, "lines": f"Error: {e}"})
        return render_template("logs_history.html", logs=logs)
    except Exception as e:
        return f"Error loading logs: {e}"

# Getting the archived logs
@app.route("/logs/<filename>")
@require_login
def download_archived_log(filename):
    log_path = os.path.join("logs", filename)
    return send_file(log_path, as_attachment=True)

@app.route("/me")
@require_login
def personal_dashboard():
    user = session["user"]

    # Load Steam ID
    try:
        with open("steam_links.json", "r") as f:
            steam_links = json.load(f)
        steam_id = steam_links.get(user)
    except Exception:
        steam_id = None

    steam_data = {}
    if steam_id:
        key = os.getenv("STEAM_API_KEY")
        if key:
            url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={key}&steamids={steam_id}"
            try:
                res = requests.get(url).json()
                player = res["response"]["players"][0]
                steam_data = {
                    "steam_id": steam_id,
                    "avatar": player["avatarfull"],
                    "name": player["personaname"]
                }
            except:
                steam_data = {"steam_id": steam_id, "avatar": None, "name": "Unknown Steam User"}
        else:
            steam_data = {"steam_id": steam_id, "avatar": None, "name": "Steam key not set"}

    # Look for identity info in logs
    identity = None
    try:
        with open("logs/console.txt", "r", encoding="utf-8") as f:
            for line in reversed(f.readlines()):
                if "NAME:" in line and user in line:
                    identity = line.strip()
                    break
    except:
        identity = "No in-game identity found."

    return render_template("personal_dashboard.html",
                           username=user,
                           steam=steam_data,
                           identity=identity)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=16261, debug=True)