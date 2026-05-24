import pyttsx3

from config import VOICE_SPEED, VOICE_VOLUME


def _build_engine():
    engine = pyttsx3.init()
    engine.setProperty("rate", VOICE_SPEED)
    engine.setProperty("volume", VOICE_VOLUME)
    return engine


engine = _build_engine()

# If you want a different voice, uncomment these lines and change the index.
# voices = engine.getProperty("voices")
# engine.setProperty("voice", voices[0].id)


def check_voice_output() -> tuple[bool, str]:
    try:
        voices = engine.getProperty("voices")
        if not voices:
            return False, "No TTS voices available."
        return True, f"Voice ready: {voices[0].name}"
    except Exception as exc:
        return False, f"Voice engine check failed: {exc}"


def speak(text: str):
    print(f"Voss: {text}")
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as exc:
        print(f"Mouth error: {exc}")
