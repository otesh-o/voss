import json
from pathlib import Path


DEVICE_STORE_PATH = Path(__file__).with_name("devices.json")


def _ensure_store():
    if not DEVICE_STORE_PATH.exists():
        DEVICE_STORE_PATH.write_text("[]\n", encoding="utf-8")


def load_devices() -> list[dict]:
    _ensure_store()
    try:
        return json.loads(DEVICE_STORE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save_devices(devices: list[dict]):
    DEVICE_STORE_PATH.write_text(json.dumps(devices, indent=2), encoding="utf-8")


def register_device(device: dict) -> dict:
    devices = load_devices()
    token = str(device.get("push_token", "")).strip()
    if not token:
        raise ValueError("Missing push token.")

    normalized = {
        "push_token": token,
        "platform": str(device.get("platform", "unknown")).strip().lower() or "unknown",
        "device_name": str(device.get("device_name", "unknown")).strip() or "unknown",
    }

    for index, existing in enumerate(devices):
        if str(existing.get("push_token", "")).strip() == token:
            devices[index] = {**existing, **normalized}
            save_devices(devices)
            return devices[index]

    devices.append(normalized)
    save_devices(devices)
    return normalized


def list_devices() -> list[dict]:
    return [dict(device) for device in load_devices()]
