# Voss Next Steps

## Planned Voice Upgrade

Voss is currently using `pyttsx3` for offline text-to-speech.

The planned upgrade is to move Voss voice output to **ElevenLabs** for more natural, human-sounding speech.

### Why

- `pyttsx3` is simple and offline, but sounds robotic.
- ElevenLabs will give Voss a much more natural and premium voice.
- The long-term design is:
  - AI provider for reasoning
  - ElevenLabs for voice output

### What will be needed

- An ElevenLabs account
- An `ELEVENLABS_API_KEY`
- A chosen ElevenLabs voice ID

### Implementation plan

1. Add ElevenLabs config values
2. Update `mouth.py` to call ElevenLabs TTS
3. Play returned audio locally
4. Keep `pyttsx3` as fallback if ElevenLabs is unavailable

### Status

Not implemented yet.
This is the next major voice upgrade for Voss.
