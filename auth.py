import os
import time
import json
from flask import session, redirect, url_for, request, render_template, flash
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

USERS_FILE = "users.json"
MAX_ATTEMPTS = 5
LOCKOUT_TIME = 60
LOGIN_ATTEMPTS = {}

# 📦 Load all users from JSON
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# 💾 Save all users to JSON
def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

# ➕ Register a new user
def save_user(username, password_plaintext, steam_id=None):
    users = load_users()
    users[username] = {
        "password": generate_password_hash(password_plaintext),
        "steam_id": steam_id,
        "pz_username": username,  # default, editable later
        "role": "user"
    }
    save_users(users)

# 🔒 Require login decorator
def require_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            flash("You must be logged in to view this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

# 🔑 Login user handler
def login_user():
    ip = request.remote_addr
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        users = load_users()
        user = users.get(username)

        attempt = LOGIN_ATTEMPTS.get(ip, {"count": 0, "last_try": 0})
        if attempt["count"] >= MAX_ATTEMPTS and time.time() - attempt["last_try"] < LOCKOUT_TIME:
            flash("Too many failed attempts. Try again in 60 seconds.", "error")
            return render_template("login.html")

        if user and check_password_hash(user["password"], password):
            session["user"] = username
            LOGIN_ATTEMPTS[ip] = {"count": 0, "last_try": 0}
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials", "error")
            LOGIN_ATTEMPTS[ip] = {"count": attempt["count"] + 1, "last_try": time.time()}

    return render_template("login.html")

# 🚪 Logout

def logout_user():
    session.pop("user", None)
    return redirect(url_for("login"))