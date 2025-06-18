# utils/mod_parser.py

import os
import json
import time
import requests
from datetime import datetime, timedelta

INI_KEYS = ["Mods", "WorkshopItems"]
CACHE_FILE = "data/mod_cache.json"
STEAM_API = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
CACHE_TTL_HOURS = 24


def read_mods_from_ini(path):
    with open(path, "r", encoding="cp1252") as f:
        lines = f.readlines()

    mod_line = next((l for l in lines if l.startswith("Mods=")), "Mods=\n")
    work_line = next((l for l in lines if l.startswith("WorkshopItems=")), "WorkshopItems=\n")

    mods = [m.strip() for m in mod_line.strip().split("=")[-1].split(";") if m]
    ids = [w.strip() for w in work_line.strip().split("=")[-1].split(";") if w]

    return list(zip(mods, ids))  # [(mod_name, id), ...]


def write_mods_to_ini(path, enabled_mods):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    mods_line = "Mods=" + ";".join([m["mod"] for m in enabled_mods if m["enabled"]]) + "\n"
    ids_line = "WorkshopItems=" + ";".join([m["id"] for m in enabled_mods if m["enabled"]]) + "\n"

    def replace_line(key, new_line):
        for i, line in enumerate(lines):
            if line.startswith(key + "="):
                lines[i] = new_line
                return
        lines.append(new_line)

    replace_line("Mods", mods_line)
    replace_line("WorkshopItems", ids_line)

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_cache(data):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def fetch_steam_data(mod_id):
    try:
        r = requests.post(STEAM_API, data={"itemcount": 1, "publishedfileids[0]": mod_id})
        info = r.json()["response"]["publishedfiledetails"][0]
        return {
            "id": mod_id,
            "title": info.get("title", "[Unknown Mod]"),
            "preview": info.get("preview_url", ""),
            "description": info.get("description", ""),
            "author": info.get("creator", ""),
            "updated": datetime.utcfromtimestamp(info.get("time_updated", 0)).strftime("%Y-%m-%d"),
            "workshop_url": f"https://steamcommunity.com/sharedfiles/filedetails/?id={mod_id}"
        }
    except Exception as e:
        print(f"[ERROR] Steam API failed for {mod_id}: {e}")
        return {"id": mod_id, "title": "[Unknown]", "preview": "", "description": "", "author": "", "updated": "?", "workshop_url": ""}


def get_mod_info(mod_id, force_refresh=False):
    cache = load_cache()
    cached = cache.get(mod_id)

    if cached and not force_refresh:
        updated = datetime.strptime(cached["cache_time"], "%Y-%m-%dT%H:%M:%S")
        if datetime.utcnow() - updated < timedelta(hours=CACHE_TTL_HOURS):
            return cached

    info = fetch_steam_data(mod_id)
    info["cache_time"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

    cache[mod_id] = info
    save_cache(cache)
    return info
