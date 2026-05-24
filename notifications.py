from config import NOTIFICATIONS_ENABLED


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
