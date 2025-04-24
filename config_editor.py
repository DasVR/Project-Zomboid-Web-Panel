import os
from flask import jsonify, request
from flask import Blueprint

config_bp = Blueprint("config_bp", __name__)

CONFIG_PATH = os.path.expanduser(r"C:\Users\airfr\Zomboid\Server\servertest.ini")

@config_bp.route("/config", methods=["GET"])
def get_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        config_data = {}
        for line in lines:
            if "=" in line and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                config_data[key] = value
        return jsonify(config_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@config_bp.route("/config", methods=["POST"])
def save_config():
    data = request.json
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            for key, value in data.items():
                f.write(f"{key}={value}\n")
        return jsonify({"message": "Config saved!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
