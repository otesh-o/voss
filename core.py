from agenda import agenda_snapshot, get_agenda_items, maybe_capture_commitment
from context import get_full_context
from diagnostics import all_checks_passed, format_startup_report, run_startup_checks
from memory import add_to_history, get_history, get_history_snapshot, maybe_store_memory
from mode import available_modes_data, get_mode, get_mode_instruction
from notifications import send_notification, send_push_notification
from provider import generate_reply
from reminder import collect_due_reminders, get_due_reminder_items
from tools.notes_tool import get_relevant_knowledge
from tools.router import ToolResult, handle_tool_request


def build_system_prompt(user_input: str, tool_result: ToolResult | None = None) -> str:
    system_prompt = get_full_context()
    system_prompt = f"{system_prompt}\n\n{get_mode_instruction()}"

    knowledge = get_relevant_knowledge(user_input)
    if knowledge:
        system_prompt = f"{system_prompt}\n\nRELEVANT WORKSPACE KNOWLEDGE:\n{knowledge}"

    agenda_state = agenda_snapshot()
    if agenda_state:
        system_prompt = f"{system_prompt}\n\nAGENDA STATE:\n{agenda_state}"

    if tool_result and tool_result.mode == "context":
        system_prompt = (
            f"{system_prompt}\n\n"
            "TOOL MATERIAL:\n"
            f"{tool_result.payload}\n\n"
            "TOOL INSTRUCTION:\n"
            f"{tool_result.instruction}\n\n"
            "Use the tool material to answer the user. "
            "Treat the tool output as evidence, not as the final wording."
        )

    return system_prompt


def think(user_input: str) -> str:
    add_to_history("user", user_input)
    maybe_capture_commitment(user_input)

    tool_reply = handle_tool_request(user_input)
    if tool_reply is not None:
        if tool_reply.mode == "direct":
            add_to_history("assistant", tool_reply.payload)
            return tool_reply.payload

        reply = generate_reply(build_system_prompt(user_input, tool_reply), get_history())
        add_to_history("assistant", reply)
        maybe_store_memory(user_input, reply)
        return reply

    reply = generate_reply(build_system_prompt(user_input), get_history())
    add_to_history("assistant", reply)
    maybe_store_memory(user_input, reply)
    return reply


def chat_turn(user_input: str) -> dict:
    add_to_history("user", user_input)
    captured_commitment = maybe_capture_commitment(user_input)

    tool_reply = handle_tool_request(user_input)
    if tool_reply is not None and tool_reply.mode == "direct":
        add_to_history("assistant", tool_reply.payload)
        reminders = collect_and_notify_reminders()
        return {
            "reply": tool_reply.payload,
            "mode": get_mode(),
            "reminders": reminders,
            "captured_commitment": captured_commitment,
        }

    if tool_reply is not None:
        reply = generate_reply(build_system_prompt(user_input, tool_reply), get_history())
    else:
        reply = generate_reply(build_system_prompt(user_input), get_history())

    add_to_history("assistant", reply)
    maybe_store_memory(user_input, reply)
    reminders = collect_and_notify_reminders()
    return {
        "reply": reply,
        "mode": get_mode(),
        "reminders": reminders,
        "captured_commitment": captured_commitment,
    }


def startup_report() -> tuple[bool, str]:
    checks = run_startup_checks()
    return all_checks_passed(checks), format_startup_report(checks)


def collect_and_notify_reminders() -> list[str]:
    reminders = collect_due_reminders()
    for reminder_message in reminders:
        send_notification("Voss Reminder", reminder_message)
        send_push_notification("Voss Reminder", reminder_message)
    return reminders


def app_state() -> dict:
    agenda_items = get_agenda_items()
    reminder_items = get_due_reminder_items()
    history_items = get_history_snapshot()
    return {
        "mode": get_mode(),
        "modes": available_modes_data(),
        "agenda_count": len(agenda_items),
        "due_reminder_count": len(reminder_items),
        "history_count": len(history_items),
    }
