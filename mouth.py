import pyttsx3

from config import VOICE_SPEED, VOICE_VOLUME


engine = pyttsx3.init()
engine.setProperty("rate", VOICE_SPEED)
engine.setProperty("volume", VOICE_VOLUME)

# If you want a different voice, uncomment these lines and change the index.
# voices = engine.getProperty("voices")
# engine.setProperty("voice", voices[0].id)


def speak(text: str):
    print(f"Voss: {text}")
    engine.say(text)
    engine.runAndWait()
