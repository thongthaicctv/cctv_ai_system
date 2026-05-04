import os
from datetime import datetime

LOG_FILE = "logs/camera_events.log"


def write_log(camera_name, status):
    os.makedirs("logs", exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{now} | {camera_name} | {status}\n"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)