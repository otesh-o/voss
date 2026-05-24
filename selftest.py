from agenda import agenda_snapshot
from config import get_allowed_roots
from diagnostics import format_startup_report, run_startup_checks
from mode import available_modes_snapshot, get_mode
from reminder import due_reminders_snapshot


def run_self_test() -> str:
    sections = [format_startup_report(run_startup_checks())]

    roots = get_allowed_roots()
    sections.append(
        "Allowed roots:\n" + ("\n".join(str(root) for root in roots) if roots else "None configured.")
    )
    sections.append(f"Current mode:\n{get_mode()}")
    sections.append("Mode list:\n" + available_modes_snapshot())
    sections.append("Agenda snapshot:\n" + agenda_snapshot())
    sections.append("Reminder snapshot:\n" + due_reminders_snapshot())

    return "\n\n".join(sections)
