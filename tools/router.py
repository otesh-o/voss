import re

from tools.approval_tool import approve_action, list_pending_actions, request_copy, request_delete, request_move
from tools.commands_tool import run_command
from tools.files_tool import create_file, list_directory, read_file, search_files
from tools.notes_tool import search_knowledge, summarize_file


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

        knowledge_target = _extract_after_prefix(
            text,
            ("search knowledge for ", "search notes for ", "find in notes ", "find in knowledge "),
        )
        if knowledge_target is not None:
            return search_knowledge(knowledge_target)

        summary_target = _extract_after_prefix(
            text,
            ("summarize file ", "summarise file ", "summarize note ", "summarise note "),
        )
        if summary_target is not None:
            return summarize_file(summary_target)

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

        delete_target = _extract_after_prefix(text, ("delete file ", "delete folder ", "remove file ", "remove folder "))
        if delete_target is not None:
            return request_delete(delete_target)

        move_match = re.match(r"(?is)^(?:move|rename)\s+(.+?)\s+to\s+(.+)$", text)
        if move_match:
            source = move_match.group(1).strip()
            target = move_match.group(2).strip()
            return request_move(source, target)

        copy_match = re.match(r"(?is)^copy\s+(.+?)\s+to\s+(.+)$", text)
        if copy_match:
            source = copy_match.group(1).strip()
            target = copy_match.group(2).strip()
            return request_copy(source, target)

        approve_target = _extract_after_prefix(text, ("approve action ",))
        if approve_target is not None:
            return approve_action(approve_target)

        pending_target = _extract_after_prefix(text, ("list pending actions", "show pending actions"))
        if pending_target is not None or text.lower() in {"pending actions", "list pending", "show pending"}:
            return list_pending_actions()

        command_text = _extract_after_prefix(
            text,
            ("run command ", "command ", "run "),
        )
        if command_text is not None:
            return run_command(command_text)
    except ValueError as exc:
        return str(exc)

    return None
