from context import get_full_context
from ear import listen
from memory import add_to_history, get_history
from mouth import speak
from provider import generate_reply


def think(user_input: str) -> str:
    add_to_history("user", user_input)

    reply = generate_reply(get_full_context(), get_history())
    add_to_history("assistant", reply)
    return reply


def main():
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
