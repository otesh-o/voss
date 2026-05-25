import json
from datetime import datetime, timedelta
from pathlib import Path

from agenda import list_open_commitments
from config import REMINDER_COOLDOWN_MINUTES, current_local_datetime, current_timestamp


REMINDER_STATE_PATH = Path(__file__).with_name("reminders.json")


def _ensure_state():
    if not REMINDER_STATE_PATH.exists():
        REMINDER_STATE_PATH.write_text("{}\n", encoding="utf-8")


def _load_state() -> dict:
    _ensure_state()
    try:
        return json.loads(REMINDER_STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save_state(state: dict):
    REMINDER_STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _is_due(item: dict, now: datetime) -> bool:
    reference = str(item.get("time_reference") or "").lower()
    created_at = _parse_timestamp(item.get("created_at"))
    created_local = created_at.astimezone(now.tzinfo) if created_at else now

    if reference == "today":
        return now.date() >= created_local.date()
    if reference == "tonight":
        return now.date() >= created_local.date() and now.hour >= 17
    if reference == "tomorrow":
        return now.date() >= (created_local.date() + timedelta(days=1))
    if reference == "tomorrow morning":
        due_date = created_local.date() + timedelta(days=1)
        return now.date() > due_date or (now.date() == due_date and now.hour >= 8)
    if reference == "tomorrow afternoon":
        due_date = created_local.date() + timedelta(days=1)
        return now.date() > due_date or (now.date() == due_date and now.hour >= 12)
    if reference == "tomorrow evening":
        due_date = created_local.date() + timedelta(days=1)
        return now.date() > due_date or (now.date() == due_date and now.hour >= 17)
    if reference == "this week":
        return True
    if reference == "this weekend":
        return now.weekday() >= 5
    return False


def due_reminders_snapshot() -> str:
    now = current_local_datetime()
    due_items = [item for item in list_open_commitments() if _is_due(item, now)]
    if not due_items:
        return "No reminders are currently due."

    lines = ["Due reminders:"]
    for item in due_items[:8]:
        lines.append(
            f"{item['id']} | {item['title']} | {item.get('time_reference') or 'unspecified'} | {item['status']}"
        )
    return "\n".join(lines)


def get_due_reminder_items() -> list[dict]:
    now = current_local_datetime()
    due_items = [item for item in list_open_commitments() if _is_due(item, now)]
    return [dict(item) for item in due_items]


def collect_due_reminders() -> list[str]:
    now = current_local_datetime()
    state = _load_state()
    messages: list[str] = []
    changed = False

    for item in list_open_commitments():
        if not _is_due(item, now):
            continue

        item_id = item["id"]
        last_sent = _parse_timestamp(state.get(item_id))
        if last_sent and (now - last_sent.astimezone(now.tzinfo)) < timedelta(minutes=REMINDER_COOLDOWN_MINUTES):
            continue

        time_ref = item.get("time_reference") or "soon"
        messages.append(f"Reminder. {item['title']}. Time reference: {time_ref}.")
        state[item_id] = current_timestamp()
        changed = True

    if changed:
        _save_state(state)

    return messages
