import os
import re
import json

os.makedirs("logs", exist_ok=True)
LOG_DIR = "logs"
LINKS_FILE = "steam_links.json"

def get_latest_log_file():
    files = [f for f in os.listdir(LOG_DIR) if f.startswith("log_") and f.endswith(".txt")]
    files.sort(reverse=True)
    return os.path.join(LOG_DIR, files[0]) if files else None

def get_player_locations():
    locations = []
    steam_links = {}

    if os.path.exists(LINKS_FILE):
        with open(LINKS_FILE, "r", encoding="utf-8") as f:
            steam_links = json.load(f)

    if not os.path.exists(LOG_DIR):
        return []

    with open(LOG_DIR, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find the latest log entries with coordinates
    for line in reversed(lines):
        match = re.search(r"NAME:\s+(.*?)\s+\((.*?)\), POSITION: x=(\d+) Y=(\d+)", line)
        if match:
            steam_name = match.group(1).strip()
            username = match.group(2).strip()
            x = int(match.group(3))
            y = int(match.group(4))

            # Link steam ID
            steam_id = steam_links.get(username, None)

            locations.append({
                "steam_name": steam_name,
                "username": username,
                "x": x,
                "y": y,
                "steam_id": steam_id
            })

        if len(locations) >= 10:  # limit to 10 recent
            break

    return locations

    pattern = re.compile(r'(?P<timestamp>[\d\-T:Z]+), NAME: (?P<name>.+?) \((?P<username>.+?)\), POSITION: x=(?P<x>\d+) Y=(?P<y>\d+) Z=(?P<z>\d+), MOVEMENT: .*')

    players = {}
    with open(log_file, "r", encoding="utf-8", errors="ignore") as file:
        for line in reversed(file.readlines()):
            match = pattern.search(line)
            if match:
                name = match.group("name")
                if name not in players:  # Only latest per player
                    players[name] = {
                        "username": match.group("username"),
                        "x": int(match.group("x")),
                        "y": int(match.group("y")),
                        "z": int(match.group("z")),
                        "time": match.group("timestamp")
                    }

    return list(players.values())
