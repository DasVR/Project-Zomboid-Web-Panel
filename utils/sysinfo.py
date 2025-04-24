import psutil
import time
from server_control import get_uptime

time_since = 0

def get_stats():
    return {
        "cpu": psutil.cpu_percent(interval=1),
        "ram": psutil.virtual_memory().percent,
        "uptime": get_uptime()
    }


