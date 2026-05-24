from pathlib import Path

from config import MAX_SEARCH_RESULTS, WORKSPACE_ROOT
from tools.files_tool import _resolve_workspace_path


def _tree_lines(root: Path, prefix: str = "") -> list[str]:
    entries = sorted(
        [entry for entry in root.iterdir() if ".git" not in entry.parts],
        key=lambda item: (item.is_file(), item.name.lower()),
    )
    lines: list[str] = []

    for index, entry in enumerate(entries[:MAX_SEARCH_RESULTS]):
        connector = "`-- " if index == len(entries[:MAX_SEARCH_RESULTS]) - 1 else "|-- "
        lines.append(f"{prefix}{connector}{entry.name}")
        if entry.is_dir():
            extension = "    " if connector == "`-- " else "|   "
            lines.extend(_tree_lines(entry, prefix + extension))

    if len(entries) > MAX_SEARCH_RESULTS:
        lines.append(f"{prefix}`-- ...")

    return lines


def run_command(command_text: str) -> str:
    raw = command_text.strip()
    if not raw:
        return "Command is empty."

    parts = raw.split(maxsplit=1)
    command = parts[0].lower()
    argument = parts[1] if len(parts) > 1 else ""

    if command in {"pwd", "whereami"}:
        return str(WORKSPACE_ROOT)

    if command in {"ls", "dir"}:
        target = _resolve_workspace_path(argument or ".")
        items = sorted(target.iterdir(), key=lambda item: (item.is_file(), item.name.lower()))
        relative = target.relative_to(WORKSPACE_ROOT)
        label = str(relative) if str(relative) else "."
        lines = [f"Listing for {label}:"]
        for item in items[:MAX_SEARCH_RESULTS]:
            marker = "[DIR]" if item.is_dir() else "[FILE]"
            lines.append(f"{marker} {item.name}")
        if len(items) > MAX_SEARCH_RESULTS:
            lines.append(f"...and {len(items) - MAX_SEARCH_RESULTS} more")
        return "\n".join(lines)

    if command == "tree":
        target = _resolve_workspace_path(argument or ".")
        relative = target.relative_to(WORKSPACE_ROOT)
        label = str(relative) if str(relative) else "."
        lines = [f"Tree for {label}:"]
        lines.extend(_tree_lines(target))
        return "\n".join(lines)

    if command == "mkdir":
        if not argument:
            return "mkdir needs a target path."
        target = _resolve_workspace_path(argument)
        target.mkdir(parents=True, exist_ok=True)
        return f"Created directory {target.relative_to(WORKSPACE_ROOT)}."

    if command == "whoami":
        return "You are Bukunmi Otesile. On this machine, Voss is operating inside your workspace."

    return (
        f"Command '{command}' is not allowed. "
        "Safe commands are: pwd, ls, dir, tree, mkdir, whoami."
    )
