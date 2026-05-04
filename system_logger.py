import os
from datetime import datetime

LOG_FILE = "logs/camera_events.log"

os.makedirs("logs", exist_ok=True)

def log(message):
    time = datetime.now().strftime("%H:%M:%S")
    line = f"[{time}] {message}"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")