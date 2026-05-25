import requests

from config import EXPO_PUSH_ENABLED, NOTIFICATIONS_ENABLED
from devices import list_devices


EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


def send_notification(title: str, message: str) -> str:
    if not NOTIFICATIONS_ENABLED:
        return "Notifications are disabled."

    try:
        from plyer import notification

        notification.notify(
            title=title,
            message=message,
            app_name="Voss",
            timeout=10,
        )
        return "Notification sent."
    except Exception as exc:
        return f"Notification fallback only: {exc}"


def send_push_notification(title: str, message: str) -> str:
    if not EXPO_PUSH_ENABLED:
        return "Expo push notifications are disabled."

    devices = list_devices()
    tokens = [device["push_token"] for device in devices if str(device.get("push_token", "")).startswith("ExponentPushToken[")]
    if not tokens:
        return "No registered push devices."

    payload = [
        {
            "to": token,
            "title": title,
            "body": message,
            "sound": "default",
        }
        for token in tokens
    ]

    try:
        response = requests.post(
            EXPO_PUSH_URL,
            json=payload,
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
                "Content-Type": "application/json",
            },
            timeout=10,
        )
        response.raise_for_status()
        return "Push notification sent."
    except Exception as exc:
        return f"Push delivery failed: {exc}"
