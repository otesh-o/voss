import sys

from core import collect_and_notify_reminders, startup_report, think
from ear import listen
from mouth import speak
from selftest import run_self_test


def main():
    if "--self-test" in sys.argv:
        print(run_self_test())
        return

    ok, report = startup_report()
    print(report)
    if not ok:
        print("Voss cannot start until the failed checks are fixed.")
        return

    print("Voss is online.")
    speak("Online.")

    for reminder_message in collect_and_notify_reminders():
        print(f"Voss reminder: {reminder_message}")
        speak(reminder_message)

    while True:
        for reminder_message in collect_and_notify_reminders():
            print(f"Voss reminder: {reminder_message}")
            speak(reminder_message)

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
