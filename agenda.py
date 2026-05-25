import json
import re
from pathlib import Path

from config import MAX_AGENDA_ITEMS, current_timestamp


AGENDA_PATH = Path(__file__).with_name("agenda.json")

COMMITMENT_PATTERNS = (
    r"\bi need to\s+(?P<title>.+)",
    r"\bi have to\s+(?P<title>.+)",
    r"\bi should\s+(?P<title>.+)",
    r"\bremind me to\s+(?P<title>.+)",
    r"\bi want to finish\s+(?P<title>.+)",
    r"\bi plan to\s+(?P<title>.+)",
)

TIME_REFERENCES = (
    "today",
    "tonight",
    "tomorrow",
    "tomorrow morning",
    "tomorrow afternoon",
    "tomorrow evening",
    "this week",
    "next week",
    "this weekend",
    "by monday",
    "by tuesday",
    "by wednesday",
    "by thursday",
    "by friday",
    "by saturday",
    "by sunday",
)


def _ensure_store():
    if not AGENDA_PATH.exists():
        AGENDA_PATH.write_text("[]\n", encoding="utf-8")


def load_agenda() -> list[dict]:
    _ensure_store()
    try:
        return json.loads(AGENDA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save_agenda(items: list[dict]):
    AGENDA_PATH.write_text(json.dumps(items, indent=2), encoding="utf-8")


def _next_agenda_id(items: list[dict]) -> str:
    numbers = []
    for item in items:
        match = re.match(r"^A(\d+)$", str(item.get("id", "")))
        if match:
            numbers.append(int(match.group(1)))
    next_number = max(numbers, default=0) + 1
    return f"A{next_number:03d}"


def _extract_time_reference(text: str) -> str | None:
    lowered = text.lower()
    for marker in TIME_REFERENCES:
        if marker in lowered:
            return marker
    return None


def detect_commitment(user_input: str) -> dict | None:
    text = user_input.strip()
    lowered = text.lower()

    for pattern in COMMITMENT_PATTERNS:
        match = re.search(pattern, lowered, flags=re.IGNORECASE)
        if not match:
            continue

        title = match.group("title").strip(" .")
        if len(title) < 4:
            return None

        return {
            "title": title[:160],
            "source": text,
            "time_reference": _extract_time_reference(text),
            "status": "pending",
            "priority": "high" if any(token in lowered for token in ("need to", "have to", "by ")) else "normal",
        }

    return None


def maybe_capture_commitment(user_input: str) -> dict | None:
    candidate = detect_commitment(user_input)
    if candidate is None:
        return None

    items = load_agenda()
    for item in items:
        if item.get("source", "").strip().lower() == candidate["source"].strip().lower():
            return None

    if len(items) >= MAX_AGENDA_ITEMS:
        return None

    candidate["id"] = _next_agenda_id(items)
    candidate["created_at"] = current_timestamp()
    items.append(candidate)
    save_agenda(items)
    return candidate


def list_open_commitments() -> list[dict]:
    return [item for item in load_agenda() if item.get("status") != "done"]


def get_agenda_items(status: str | None = None, include_done: bool = False) -> list[dict]:
    items = load_agenda()
    if not include_done:
        items = [item for item in items if item.get("status") != "done"]
    if status:
        normalized = status.strip().lower()
        items = [item for item in items if str(item.get("status", "")).lower() == normalized]
    return [dict(item) for item in items]


def agenda_snapshot(limit: int = 8) -> str:
    items = list_open_commitments()
    if not items:
        return "No open agenda items."

    lines = ["Open agenda items:"]
    for item in items[:limit]:
        time_ref = item.get("time_reference") or "unspecified"
        lines.append(
            f"{item['id']} | {item['title']} | time={time_ref} | status={item['status']} | priority={item['priority']}"
        )
    return "\n".join(lines)


def update_agenda_status(item_id: str, status: str) -> str:
    items = load_agenda()
    normalized = status.strip().lower()
    if normalized not in {"pending", "in progress", "done", "dropped"}:
        return f"Unsupported status: {status}"

    for item in items:
        if str(item.get("id", "")).upper() == item_id.upper():
            item["status"] = normalized
            item["updated_at"] = current_timestamp()
            save_agenda(items)
            return f"Updated {item['id']} to status '{normalized}'."

    return f"Agenda item not found: {item_id}"


def filter_agenda_by_time(label: str) -> str:
    target = label.strip().lower()
    items = [
        item for item in list_open_commitments()
        if str(item.get("time_reference") or "").lower() == target
    ]
    if not items:
        return f"No agenda items found for '{label}'."

    lines = [f"Agenda items for '{label}':"]
    for item in items:
        lines.append(f"{item['id']} | {item['title']} | status={item['status']} | priority={item['priority']}")
    return "\n".join(lines)
