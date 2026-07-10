import subprocess
import sys
import time
import webbrowser
from pathlib import Path

# Project folder
BASE = Path(__file__).resolve().parent

python = sys.executable

# 1. Sync database
subprocess.run(
    [python, str(BASE / "scripts" / "sync_database.py")],
    check=True
)

# 2. Start website server
server = subprocess.Popen(
    [python, "-m", "http.server", "8000"],
    cwd=BASE
)

# Give the server a moment to start
time.sleep(2)

# 3. Open documentation page
webbrowser.open("http://localhost:8000/docs/")

print("Website running at http://localhost:8000/docs/")
print("Close this window to stop the server.")

# Keep launcher alive so the server stays open
try:
    server.wait()
except KeyboardInterrupt:
    server.terminate()