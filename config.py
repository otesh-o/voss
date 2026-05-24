import os
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


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

WORKSPACE_ROOT = Path(os.getenv("VOSS_WORKSPACE_ROOT", Path(__file__).resolve().parent))
DEFAULT_ALLOWED_ROOTS = [
    WORKSPACE_ROOT,
    Path.home() / "Documents",
    Path.home() / "Downloads",
    Path.home() / "Desktop",
]
MAX_FILE_READ_CHARS = 8000
MAX_SEARCH_RESULTS = 10
MAX_KNOWLEDGE_RESULTS = 5
KNOWLEDGE_PREVIEW_CHARS = 700
MAX_MEMORY_ENTRIES = 200
MAX_WEB_RESULTS = 5
MAX_WEB_TEXT_CHARS = 5000
MAX_AGENDA_ITEMS = 200
MAX_RECENT_ACTIVITY_RESULTS = 12
REMINDER_COOLDOWN_MINUTES = 120
VOSS_TIMEZONE = os.getenv("VOSS_TIMEZONE", "Africa/Lagos")
NOTIFICATIONS_ENABLED = os.getenv("VOSS_NOTIFICATIONS_ENABLED", "1").strip() not in {"0", "false", "False"}
TEXT_FILE_SUFFIXES = {
    ".txt",
    ".md",
    ".py",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".csv",
}


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def current_local_datetime() -> datetime:
    try:
        tz = ZoneInfo(VOSS_TIMEZONE)
    except Exception:
        tz = timezone.utc
    return datetime.now(tz)


def get_allowed_roots() -> list[Path]:
    env_value = os.getenv("VOSS_ALLOWED_ROOTS", "").strip()
    if env_value:
        roots = [Path(part.strip()) for part in env_value.split(";") if part.strip()]
    else:
        roots = DEFAULT_ALLOWED_ROOTS

    unique_roots: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        resolved = root.resolve()
        key = str(resolved).lower()
        if key not in seen and resolved.exists():
            seen.add(key)
            unique_roots.append(resolved)
    return unique_roots
