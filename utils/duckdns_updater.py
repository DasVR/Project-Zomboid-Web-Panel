import requests
import time
import threading
import os

DUCKDNS_DOMAIN = os.getenv("DUCKDNS_DOMAIN")
DUCKDNS_TOKEN = os.getenv("DUCKDNS_TOKEN")

def update_duckdns():
    if not DUCKDNS_DOMAIN or not DUCKDNS_TOKEN:
        print("[❌] DUCKDNS_DOMAIN or DUCKDNS_TOKEN not set in .env!")
        return

    url = f"https://www.duckdns.org/update?domains={DUCKDNS_DOMAIN}&token={DUCKDNS_TOKEN}&ip="
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print(f"[🌐] DuckDNS update successful: {response.text}")
        else:
            print(f"[⚠️] DuckDNS update failed: {response.status_code}")
    except Exception as e:
        print(f"[🚫] Error updating DuckDNS: {e}")

def start_duckdns_loop(interval=600):
    def loop():
        while True:
            update_duckdns()
            time.sleep(interval)
    threading.Thread(target=loop, daemon=True).start()
