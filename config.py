import os


ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "your key here")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

AI_PROVIDER = os.getenv("VOSS_PROVIDER", "anthropic").lower()

VOICE_SPEED = 175
VOICE_VOLUME = 1.0
LISTENING_TIMEOUT = 10
MODEL = "claude-sonnet-4-20250514"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-5-mini")
