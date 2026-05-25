import json
from pathlib import Path


MODE_STATE_PATH = Path(__file__).with_name("mode.json")
DEFAULT_MODE = "build"

MODE_INSTRUCTIONS = {
    "build": "Build mode. Prioritize creation, execution, and momentum. Be concise and action-oriented.",
    "review": "Review mode. Prioritize critique, debugging, failure modes, regressions, and structural weakness.",
    "strategy": "Strategy mode. Prioritize long-range thinking, leverage, sequencing, and tradeoffs.",
    "critical": "Critical mode. Apply maximum rigor. Be unforgiving about weak logic and fragile plans.",
    "quiet": "Quiet mode. Minimize output. Only surface high-value signal.",
}


def _ensure_state():
    if not MODE_STATE_PATH.exists():
        MODE_STATE_PATH.write_text(json.dumps({"mode": DEFAULT_MODE}, indent=2), encoding="utf-8")


def get_mode() -> str:
    _ensure_state()
    try:
        data = json.loads(MODE_STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return DEFAULT_MODE
    mode = str(data.get("mode", DEFAULT_MODE)).lower()
    return mode if mode in MODE_INSTRUCTIONS else DEFAULT_MODE


def set_mode(mode: str) -> str:
    normalized = mode.strip().lower()
    if normalized not in MODE_INSTRUCTIONS:
        return f"Unsupported mode: {mode}. Available modes: {', '.join(MODE_INSTRUCTIONS)}."
    MODE_STATE_PATH.write_text(json.dumps({"mode": normalized}, indent=2), encoding="utf-8")
    return f"Mode set to {normalized}."


def get_mode_instruction() -> str:
    mode = get_mode()
    return f"CURRENT MODE: {mode}\n{MODE_INSTRUCTIONS[mode]}"


def available_modes_snapshot() -> str:
    lines = ["Available modes:"]
    for name, instruction in MODE_INSTRUCTIONS.items():
        lines.append(f"{name}: {instruction}")
    return "\n".join(lines)


def available_modes_data() -> list[dict]:
    return [{"name": name, "instruction": instruction} for name, instruction in MODE_INSTRUCTIONS.items()]
