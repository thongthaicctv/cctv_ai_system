import json
import os

CONFIG_FILE = "config.json"


def _default_config():
    return {
        "alert_enabled": True,
        "storage_path": "videos",
        "record_auto_stop_seconds": 300,
        "record_mapping": {},
        "cameras": [],
    }


def _normalize_config(data):
    merged = _default_config()
    merged.update(data or {})

    cameras = merged.get("cameras", [])
    camera_ids = [str(cam.get("id", "")).strip() for cam in cameras if cam.get("id")]
    valid_ids = set(camera_ids)

    raw_mapping = merged.get("record_mapping", {}) or {}
    normalized = {}

    for cam_id in camera_ids:
        if cam_id in raw_mapping:
            targets = [
                str(target)
                for target in raw_mapping.get(cam_id, [])
                if str(target) in valid_ids
            ]
            normalized[cam_id] = targets
        else:
            normalized[cam_id] = [cam_id]

    merged["record_mapping"] = normalized
    return merged


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return _default_config()

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return _normalize_config(json.load(f))


def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(_normalize_config(data), f, indent=4, ensure_ascii=False)
