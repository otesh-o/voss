from agenda import list_open_commitments


URGENT_TIME_REFERENCES = {
    "today",
    "tonight",
    "tomorrow",
    "tomorrow morning",
    "tomorrow afternoon",
    "tomorrow evening",
}


def build_operating_review() -> str:
    items = list_open_commitments()
    if not items:
        return "Operating review:\nNo open commitments are currently stored."

    urgent = []
    in_progress = []
    neglected = []
    high_priority = []

    for item in items:
        time_reference = str(item.get("time_reference") or "").lower()
        status = str(item.get("status") or "").lower()
        priority = str(item.get("priority") or "").lower()

        if time_reference in URGENT_TIME_REFERENCES and status in {"pending", "in progress"}:
            urgent.append(item)
        if status == "in progress":
            in_progress.append(item)
        if status == "pending" and not time_reference:
            neglected.append(item)
        if priority == "high" and status != "done":
            high_priority.append(item)

    lines = ["Operating review:"]

    if urgent:
        lines.append("Urgent:")
        for item in urgent[:5]:
            lines.append(
                f"{item['id']} | {item['title']} | {item.get('time_reference') or 'unspecified'} | {item['status']}"
            )
    else:
        lines.append("Urgent: none explicitly time-bound for today or tomorrow.")

    if in_progress:
        lines.append("In progress:")
        for item in in_progress[:5]:
            lines.append(f"{item['id']} | {item['title']}")
    else:
        lines.append("In progress: none.")

    if neglected:
        lines.append("Unscheduled pending items:")
        for item in neglected[:5]:
            lines.append(f"{item['id']} | {item['title']} | priority={item['priority']}")
    else:
        lines.append("Unscheduled pending items: none.")

    if high_priority:
        lines.append("High priority:")
        for item in high_priority[:5]:
            lines.append(f"{item['id']} | {item['title']} | {item.get('time_reference') or 'unspecified'}")
    else:
        lines.append("High priority: none.")

    return "\n".join(lines)
