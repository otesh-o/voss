import re

from agenda import agenda_snapshot, filter_agenda_by_time, list_open_commitments, update_agenda_status
from reminder import due_reminders_snapshot


def answer_agenda_request(user_input: str) -> str | None:
    text = user_input.strip()
    lowered = text.lower()

    if lowered in {
        "what am i supposed to be doing",
        "what am i supposed to be doing today",
        "what should i be doing",
        "what are my commitments",
        "what are my open commitments",
        "what is urgent right now",
    }:
        return agenda_snapshot()

    if lowered in {"show my agenda", "show agenda", "list agenda", "what is on my agenda"}:
        return agenda_snapshot()

    if lowered in {"show reminders", "list reminders", "what reminders are due", "what should you remind me about"}:
        return due_reminders_snapshot()

    time_match = re.match(r"(?is)^what did i say i would finish (.+)$", text)
    if time_match:
        return filter_agenda_by_time(time_match.group(1).strip())

    done_match = re.match(r"(?is)^(?:mark|set)\s+(A\d+)\s+(?:as\s+)?done$", text)
    if done_match:
        return update_agenda_status(done_match.group(1), "done")

    progress_match = re.match(r"(?is)^(?:mark|set)\s+(A\d+)\s+(?:as\s+)?in progress$", text)
    if progress_match:
        return update_agenda_status(progress_match.group(1), "in progress")

    drop_match = re.match(r"(?is)^(?:mark|set)\s+(A\d+)\s+(?:as\s+)?dropped$", text)
    if drop_match:
        return update_agenda_status(drop_match.group(1), "dropped")

    pending_match = re.match(r"(?is)^(?:mark|set)\s+(A\d+)\s+(?:as\s+)?pending$", text)
    if pending_match:
        return update_agenda_status(pending_match.group(1), "pending")

    if lowered == "list open commitments":
        items = list_open_commitments()
        if not items:
            return "No open commitments."
        lines = ["Open commitments:"]
        for item in items[:10]:
            lines.append(f"{item['id']} | {item['title']} | {item.get('time_reference') or 'unspecified'}")
        return "\n".join(lines)

    return None
