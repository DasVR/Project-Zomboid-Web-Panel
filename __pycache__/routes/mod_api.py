# routes/mod_api.py

from flask import Blueprint, request, jsonify
from utils.mod_parser import read_mods_from_ini, write_mods_to_ini, get_mod_info
import os

mod_api = Blueprint("mod_api", __name__)
INI_PATH = os.getenv("CONFIG_PATH", "Project_ZED.ini")


@mod_api.route("/api/mods", methods=["GET"])
def list_mods():
    parsed = read_mods_from_ini(INI_PATH)
    result = []

    for mod_name, mod_id in parsed:
        info = get_mod_info(mod_id)
        info.update({
            "enabled": True,  # since it's in INI
            "mod": mod_name
        })
        result.append(info)

    return jsonify(result)


@mod_api.route("/api/mods/enable", methods=["POST"])
def enable_mod():
    mod_id = request.json.get("id")
    mod_name = request.json.get("mod")

    current = read_mods_from_ini(INI_PATH)
    if (mod_name, mod_id) not in current:
        current.append((mod_name, mod_id))

    mod_list = [{"mod": m, "id": i, "enabled": True} for m, i in current]
    write_mods_to_ini(INI_PATH, mod_list)
    return jsonify({"status": "enabled", "id": mod_id})


@mod_api.route("/api/mods/disable", methods=["POST"])
def disable_mod():
    mod_id = request.json.get("id")
    mod_name = request.json.get("mod")

    current = read_mods_from_ini(INI_PATH)
    mod_list = [{"mod": m, "id": i, "enabled": not (m == mod_name and i == mod_id)} for m, i in current]
    write_mods_to_ini(INI_PATH, mod_list)
    return jsonify({"status": "disabled", "id": mod_id})


@mod_api.route("/api/mods/<mod_id>", methods=["DELETE"])
def delete_mod(mod_id):
    current = read_mods_from_ini(INI_PATH)
    mod_list = [{"mod": m, "id": i, "enabled": False} for m, i in current if i != mod_id]
    write_mods_to_ini(INI_PATH, mod_list)
    return jsonify({"status": "deleted", "id": mod_id})
