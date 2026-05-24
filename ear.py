import speech_recognition as sr

from config import LISTENING_TIMEOUT


def check_microphone() -> tuple[bool, str]:
    try:
        names = sr.Microphone.list_microphone_names()
    except Exception as exc:
        return False, f"Microphone check failed: {exc}"

    if not names:
        return False, "No microphone detected."

    return True, f"Microphone ready: {names[0]}"


def listen():
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            print("Voss is listening...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=LISTENING_TIMEOUT)
            text = recognizer.recognize_google(audio)
            print(f"You: {text}")
            return text
    except sr.WaitTimeoutError:
        return None
    except sr.UnknownValueError:
        return None
    except Exception as exc:
        print(f"Ear error: {exc}")
        return None
