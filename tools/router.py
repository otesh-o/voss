import re

from tools.commands_tool import run_command
from tools.files_tool import create_file, list_directory, read_file, search_files


def _extract_after_prefix(text: str, prefixes: tuple[str, ...]) -> str | None:
    lowered = text.lower()
    for prefix in prefixes:
        if lowered.startswith(prefix):
            return text[len(prefix):].strip()
    return None


def handle_tool_request(user_input: str) -> str | None:
    text = user_input.strip()
    try:
        search_term = _extract_after_prefix(
            text,
            ("search files for ", "find file ", "find files ", "search for file "),
        )
        if search_term is not None:
            return search_files(search_term)

        list_target = _extract_after_prefix(
            text,
            ("list files", "list folder", "show files", "show folder"),
        )
        if list_target is not None:
            cleaned = re.sub(r"^in\s+", "", list_target, flags=re.IGNORECASE).strip() or "."
            return list_directory(cleaned)

        read_target = _extract_after_prefix(
            text,
            ("read file ", "open file ", "show file "),
        )
        if read_target is not None:
            return read_file(read_target)

        create_match = re.match(
            r"(?is)^(?:create|make)\s+file\s+(.+?)(?:\s+with\s+content\s*:\s*(.+))?$",
            text,
        )
        if create_match:
            path = create_match.group(1).strip()
            content = (create_match.group(2) or "").strip()
            return create_file(path, content)

        overwrite_match = re.match(
            r"(?is)^overwrite\s+file\s+(.+?)\s+with\s+content\s*:\s*(.+)$",
            text,
        )
        if overwrite_match:
            path = overwrite_match.group(1).strip()
            content = overwrite_match.group(2).strip()
            return create_file(path, content, overwrite=True)

        command_text = _extract_after_prefix(
            text,
            ("run command ", "command ", "run "),
        )
        if command_text is not None:
            return run_command(command_text)
    except ValueError as exc:
        return str(exc)

    return None
