import os
import time
import platform
import subprocess
import threading
import traceback
import shutil
from datetime import datetime
from flask_socketio import SocketIO
from dotenv import load_dotenv
from flask import g

load_dotenv()

server_process = None
socketio: SocketIO = None
stream_started = False
start_time = None

def attach_socketio(sio):
    global socketio
    socketio = sio

def is_running():
    global server_process
    if server_process is None:
        return False
    if server_process.poll() is not None:
        print("[🧯] Detected crashed server. Cleaning up reference.")
        server_process = None
        return False
    return True

def stream_logs():
    global stream_started, server_process
    print("[~] Log stream thread running...")

    try:
        while True:
            if server_process.poll() is not None:
                break

            line = server_process.stdout.readline()
            if not line:
                continue

            if line.strip():
                print(f"[stream] {line.strip()}")
                socketio.emit("log_update", {"line": line})

            socketio.sleep(0.1)

    except Exception as e:
        print("[!] Stream error:")
        traceback.print_exc()
        socketio.emit("log_update", {"line": f"[STREAM ERROR] {str(e)}\n"})

    finally:
        stream_started = False
        print("[x] Log stream ended.")

        if server_process and server_process.poll() is not None:
            print("[💥] Crash detected. Server Shutting Down")
            socketio.emit("log_update", {"line": "[CRASH] Server stopped unexpectedly. Confirming Shutdown\n"})
            time.sleep(2)
            stop_server()
            archive_current_log()
            start_time = 0

def maybe_start_log_stream():
    global stream_started
    if not stream_started and server_process:
        threading.Thread(target=stream_logs, daemon=True).start()
        stream_started = True
        print("[🧠] Live log stream attached to server.")

def start_server():
    global server_process, stream_started, start_time

    if server_process is None:
        try:
            base_dir = r"C:\dedic_pz_serverone"
            bat_file = os.path.join(base_dir, "StartServer64.bat")

            if not os.path.exists(bat_file):
                raise FileNotFoundError(f"Missing BAT file at {bat_file}")

            command = [bat_file]
            print("[🧪] Launching using BAT file:", command)

            server_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=base_dir,
                shell=True
            )

            socketio.emit("log_update", {"line": "[LAUNCHED] Using StartServer64.bat ✅\n"})
            stream_started = False
            start_time = time.time()
            return True

        except Exception as e:
            print(f"[❌] Failed to launch from BAT: {e}")
            socketio.emit("log_update", {"line": f"[ERROR] {e}\n"})
            return False

    print("[⚠️] Server already running.")
    return False

def stop_server():
    global server_process

    if server_process and server_process.poll() is None:
        try:
            print("[🛑] Sending graceful shutdown command: 'quit'")
            server_process.stdin.write("quit\n")
            server_process.stdin.flush()
            archive_current_log()
            return True
        except Exception as e:
            print(f"[⚠️] Failed to send quit: {e}. Terminating forcefully.")
            server_process.terminate()
            server_process.wait()
            server_process = None
            archive_current_log()
            start_time = 0
            return False
    else:
        print("[ℹ️] No server process to stop.")
    return False

def archive_current_log():
    log_src = r"C:\Users\airfr\Zomboid\server-console.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archive_name = f"logs/log_{timestamp}.txt"
    try:
        os.makedirs("logs", exist_ok=True)
        shutil.copy(log_src, archive_name)
        socketio.emit("log_update", {"line": "[🗃️] Log archived to {archive_name}\n"})
                      
    except Exception as e:
        print(f"[❌] Failed to archive log: {e}")

def get_uptime():
    if start_time and server_process is None:
        return int(time.time()) - start_time
    return 0