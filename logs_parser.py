import os

LOG_FILE = os.path.expanduser(r"C:\Users\airfr\Zomboid\console.txt")

def tail_log(n=50):
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as file:
            lines = file.readlines()
            return lines[-n:] if len(lines) > n else lines
    except Exception as e:
        return [f"[ERROR] {e}"]

def get_players():
    players = set()
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as file:
            for line in file:
                if "Player connected:" in line:
                    name = line.split("Player connected:")[-1].strip()
                    players.add(name)
    except:
        pass
    return list(players)
