import speech_recognition as sr

from config import LISTENING_TIMEOUT


def listen():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Voss is listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)

        try:
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
