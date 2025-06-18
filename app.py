import os
import re
import json
import time
import threading
import requests
from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file, flash
from flask_socketio import SocketIO
from flask_openid import OpenID
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

from options_loader import load_sandbox_options  # ✅ NEW
from config_editor import config_bp
from sandbox_parser import build_combined_sandbox, python_to_lua_table, get_all_sandbox_mod_options, prettify_keys
from server_control import start_server, stop_server, is_running, attach_socketio, maybe_start_log_stream, server_process
from logs_parser import tail_log, get_players
from utils.sysinfo import get_stats
from utils.config_parser import parse_config_file
from utils.duckdns_updater import start_duckdns_loop
from steam_openid import get_steam_openid_url, parse_steam_id
from auth import login_user, logout_user, require_login, load_users, save_user
from player_map import get_player_locations
from routes.mod_api import mod_api


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET", "supersecretkey")
app.permanent_session_lifetime = timedelta(minutes=30)

oid = OpenID(app, os.path.join(os.getcwd(), 'openid-store'))
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

attach_socketio(socketio)
start_duckdns_loop()
app.register_blueprint(config_bp)
app.register_blueprint(mod_api)


@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route("/sandbox-editor", methods=["GET", "POST"])
@require_login
def sandbox_editor():
    lua_path = os.getenv("SANDBOX_PATH")

    if request.method == "POST":
        try:
            new_data = request.json
            lua_str = f"SandboxVars = {python_to_lua_table(new_data)}\n\nreturn SandboxVars"
            with open(lua_path, "w", encoding="utf-8") as f:
                f.write(lua_str)
            return jsonify({"status": "✅ Saved SandboxVars!"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    try:
        parsed_vars = build_combined_sandbox(
            lua_path,
            os.getenv("BASE_SANDBOX_PATH"),
            os.getenv("MOD_SANDBOX_DIR"),
        )
        return render_template("sandbox_editor.html", sandbox=parsed_vars)
    except Exception as e:
        return f"Error rendering editor: {e}", 500


@app.route("/mods-ui")
@require_login
def mods_ui():
    return render_template("mods.html")

@app.route('/api/save-mods', methods=['POST'])
def save_mods():
    ini_path = os.getenv('CONFIG_PATH')
    if not ini_path or not os.path.exists(ini_path):
        return "❌ INI file not found or path is unset.", 404

    data = request.json or {}
    mods = data.get('mods', [])
    workshop_ids = data.get('workshopIds', [])

    try:
        content = open(ini_path, encoding='utf-8').read()

        mods_str = ';'.join(mods)
        workshop_str = ';'.join(map(str, workshop_ids))

        # Use ^ to target start-of-line, ensure long lines aren’t wrapped
        content = re.sub(r'^Mods=.*', f'Mods={mods_str}', content, flags=re.M)
        content = re.sub(r'^WorkshopItems=.*', f'WorkshopItems={workshop_str}', content, flags=re.M)

        with open(ini_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return "✅ Mods and WorkshopItems saved!"
    except Exception as e:
        app.logger.error("INI save error: %s", e)
        return "❌ Failed to update INI", 500

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
        try:
            links = {}
            if os.path.exists("steam_links.json"):
                with open("steam_links.json", "r") as f:
                    links = json.load(f)
            links[user] = steam_id
            with open("steam_links.json", "w") as f:
                json.dump(links, f, indent=2)
            flash(f"✅ Linked Steam ID: {steam_id}")
        except:
            flash("⚠️ Failed to save Steam ID.")
    else:
        flash("⚠️ Failed to link Steam.")
    return redirect(url_for("dashboard"))

@app.route("/", methods=["GET", "POST"])
def login():
    return login_user()

@app.route("/logout")
def logout():
    return logout_user()

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        if not username or not password:
            flash("Username and password required.", "error")
            return redirect(url_for("signup"))

        users = load_users()
        if username in users:
            flash("Username already exists!", "error")
        else:
            save_user(username, password)
            flash("✅ Account created. You may now log in.")
            return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/dashboard")
@require_login
def dashboard():
    return render_template("dashboard.html", stats=get_stats(), running=is_running())

@app.route("/players_dashboard")
@require_login
def players_dashboard():
    return render_template("players.html", players=get_players())

@app.route("/config-editor")
def config_page():
    config_path = os.getenv("CONFIG_PATH", r"C:\\Users\\airfr\\Zomboid\\Server\\servertest.ini")
    config, descriptions, ranges = parse_config_file(config_path)
    return render_template("server_config.html", config_values={
        "config": config,
        "descriptions": descriptions,
        "ranges": ranges
    })

@app.route("/control", methods=["POST"])
@require_login
def control():
    action = request.form.get("action")
    print(f"[🧠] Action = {action}")
    global server_process
    if action == "start":
        start_server()
    elif action == "stop":
        stop_server()
    elif action == "restart":
        stop_server()
        time.sleep(1)
        start_server()
    elif action == "force_stop" and server_process:
        print("[💣] FORCE STOP triggered!")
        server_process.kill()
        server_process.wait()
        server_process = None
    return redirect(url_for("dashboard"))

@app.route("/stats")
@require_login
def stats():
    return jsonify(get_stats())

@app.route("/players")
@require_login
def players():
    return jsonify({"players": get_players()})

@app.route("/log_tail")
@require_login
def log_tail():
    return jsonify({"lines": tail_log()})

@app.route("/server-status")
def server_status():
    status = "running" if is_running() else "stopped"
    return jsonify({"status": status})

@socketio.on('connect')
def client_connected():
    print("[SocketIO] Client connected.")
    socketio.emit("log_update", {"line": "[CLIENT] Connected to WebSocket ✅\n"})
    maybe_start_log_stream()

@app.route("/metrics")
@require_login
def metrics():
    return jsonify(get_stats())

@app.route("/live_players")
@require_login
def live_players():
    return jsonify({"players": get_players()})

@app.route("/map")
@require_login
def player_map():
    return render_template("player_map.html")

@app.route("/mods", methods=["GET", "POST"])
@require_login
def mod_manager():
    mods_dir = os.getenv("MODS_DIR", "mods")
    os.makedirs(mods_dir, exist_ok=True)

    if request.method == "POST":
        file = request.files.get("modfile")
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(mods_dir, filename))
            flash(f"✅ Uploaded mod: {filename}")
        return redirect(url_for("mod_manager"))

    mods = os.listdir(mods_dir)
    return render_template("mods.html", mods=mods)

@app.route("/logs-history")
@require_login
def logs_history():
    try:
        logs = []
        for filename in sorted(os.listdir("logs"), reverse=True):
            if filename.endswith((".log", ".txt")):
                filepath = os.path.join("logs", filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        line_count = sum(1 for _ in f)
                    logs.append({"filename": filename, "lines": line_count})
                except Exception as e:
                    logs.append({"filename": filename, "lines": f"Error: {e}"})
        return render_template("logs_history.html", logs=logs)
    except Exception as e:
        return f"Error loading logs: {e}"

@app.route("/logs/<filename>")
@require_login
def download_archived_log(filename):
    return send_file(os.path.join("logs", filename), as_attachment=True)

@app.route("/me")
@require_login
def personal_dashboard():
    user = session["user"]
    steam_data = {}
    identity = "No in-game identity found."
    try:
        with open("steam_links.json", "r") as f:
            steam_links = json.load(f)
        steam_id = steam_links.get(user)
        if steam_id:
            key = os.getenv("STEAM_API_KEY")
            if key:
                url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={key}&steamids={steam_id}"
                res = requests.get(url).json()
                player = res.get("response", {}).get("players", [{}])[0]
                steam_data = {
                    "steam_id": steam_id,
                    "avatar": player.get("avatarfull"),
                    "name": player.get("personaname", "Unknown")
                }
            else:
                steam_data = {"steam_id": steam_id, "avatar": None, "name": "Steam key not set"}
    except:
        steam_data = {"steam_id": None, "avatar": None, "name": "Unknown Steam User"}

    try:
        with open("logs/console.txt", "r", encoding="utf-8") as f:
            for line in reversed(f.readlines()):
                if "NAME:" in line and user in line:
                    identity = line.strip()
                    break
    except:
        pass

    return render_template("personal_dashboard.html", username=user, steam=steam_data, identity=identity)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.getenv("APP_PORT", 16261)), debug=True)
