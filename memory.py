from pathlib import Path

from config import MAX_MEMORY_ENTRIES

conversation_history = []


def add_to_history(role: str, content: str):
    conversation_history.append({"role": role, "content": content})


def get_history():
    return conversation_history


def get_history_snapshot(limit: int | None = None) -> list[dict]:
    if limit is None or limit <= 0:
        return [dict(entry) for entry in conversation_history]
    return [dict(entry) for entry in conversation_history[-limit:]]


def update_living_context(new_information: str):
    living_context_path = Path(__file__).with_name("living_context.txt")
    with living_context_path.open("a", encoding="utf-8") as file:
        file.write(f"\n{new_information.strip()}\n")


def should_store_permanently(text: str) -> bool:
    lowered = text.lower()
    signals = (
        "i am ",
        "i'm ",
        "my name is ",
        "i built ",
        "i'm building ",
        "i am building ",
        "i founded ",
        "my goal is ",
        "i want to ",
        "i plan to ",
        "remember that ",
        "important: ",
    )
    return any(signal in lowered for signal in signals)


def maybe_store_memory(user_input: str, assistant_reply: str | None = None) -> str | None:
    if not should_store_permanently(user_input):
        return None

    candidate = user_input.strip()
    if len(candidate) < 12:
        return None

    living_context_path = Path(__file__).with_name("living_context.txt")
    existing = ""
    if living_context_path.exists():
        existing = living_context_path.read_text(encoding="utf-8")
        if candidate in existing:
            return None

    lines = [line for line in existing.splitlines() if line.strip()]
    if len(lines) >= MAX_MEMORY_ENTRIES:
        return None

    update_living_context(candidate)
    return candidate


def clear_history():
    conversation_history.clear()
