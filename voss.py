from diagnostics import all_checks_passed, format_startup_report, run_startup_checks
from context import get_full_context
from ear import listen
from memory import add_to_history, get_history, maybe_store_memory
from mouth import speak
from provider import generate_reply
from tools.notes_tool import get_relevant_knowledge
from tools.router import handle_tool_request


def think(user_input: str) -> str:
    add_to_history("user", user_input)

    tool_reply = handle_tool_request(user_input)
    if tool_reply is not None:
        add_to_history("assistant", tool_reply)
        return tool_reply

    knowledge = get_relevant_knowledge(user_input)
    system_prompt = get_full_context()
    if knowledge:
        system_prompt = f"{system_prompt}\n\nRELEVANT WORKSPACE KNOWLEDGE:\n{knowledge}"

    reply = generate_reply(system_prompt, get_history())
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
