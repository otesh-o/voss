from agenda import agenda_snapshot, maybe_capture_commitment
from diagnostics import all_checks_passed, format_startup_report, run_startup_checks
from context import get_full_context
from ear import listen
from memory import add_to_history, get_history, maybe_store_memory
from mouth import speak
from provider import generate_reply
from tools.notes_tool import get_relevant_knowledge
from tools.router import ToolResult, handle_tool_request


def _build_system_prompt(user_input: str, tool_result: ToolResult | None = None) -> str:
    system_prompt = get_full_context()

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

        reply = generate_reply(_build_system_prompt(user_input, tool_reply), get_history())
        add_to_history("assistant", reply)
        maybe_store_memory(user_input, reply)
        return reply

    reply = generate_reply(_build_system_prompt(user_input), get_history())
    add_to_history("assistant", reply)
    maybe_store_memory(user_input, reply)
    return reply


def main():
    checks = run_startup_checks()
    print(format_startup_report(checks))
    if not all_checks_passed(checks):
        print("Voss cannot start until the failed checks are fixed.")
        return

    print("Voss is online.")
    speak("Online.")

    while True:
        user_input = listen()

        if user_input is None:
            continue

        if "shut down" in user_input.lower():
            speak("Shutting down.")
            break

        try:
            response = think(user_input)
        except Exception as exc:
            response = f"I hit an error while thinking: {exc}"

        speak(response)


if __name__ == "__main__":
    main()
