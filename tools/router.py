from dataclasses import dataclass
import re

from tools.approval_tool import approve_action, list_pending_actions, request_copy, request_delete, request_move
from tools.agenda_tool import answer_agenda_request, get_agenda_context
from tools.commands_tool import run_command
from tools.files_tool import create_file, list_directory, read_file, search_files
from tools.notes_tool import search_knowledge, summarize_file
from tools.web_tool import fetch_page, search_web, summarize_page


@dataclass
class ToolResult:
    mode: str
    payload: str
    instruction: str = ""


def _extract_after_prefix(text: str, prefixes: tuple[str, ...]) -> str | None:
    lowered = text.lower()
    for prefix in prefixes:
        if lowered.startswith(prefix):
            return text[len(prefix):].strip()
    return None


def _context_result(payload: str, instruction: str) -> ToolResult:
    return ToolResult(mode="context", payload=payload, instruction=instruction)


def _direct_result(payload: str) -> ToolResult:
    return ToolResult(mode="direct", payload=payload)


def handle_tool_request(user_input: str) -> ToolResult | None:
    text = user_input.strip()
    try:
        agenda_reply = answer_agenda_request(text)
        if agenda_reply is not None:
            return _context_result(
                agenda_reply,
                "Use this agenda state to answer the user's scheduling or commitment question.",
            )

        search_term = _extract_after_prefix(
            text,
            ("search files for ", "find file ", "find files ", "search for file "),
        )
        if search_term is not None:
            return _context_result(
                search_files(search_term),
                "Use these file-search results to answer the user clearly. Do not invent files that were not found.",
            )

        list_target = _extract_after_prefix(
            text,
            ("list files", "list folder", "show files", "show folder"),
        )
        if list_target is not None:
            cleaned = re.sub(r"^in\s+", "", list_target, flags=re.IGNORECASE).strip() or "."
            return _context_result(
                list_directory(cleaned),
                "Use this directory listing to answer the user's request. Keep it concrete.",
            )

        read_target = _extract_after_prefix(
            text,
            ("read file ", "open file ", "show file "),
        )
        if read_target is not None:
            return _context_result(
                read_file(read_target),
                "Use this file content to answer the user's request. If they asked for explanation, explain it. If they asked to read it, summarize the important parts.",
            )

        knowledge_target = _extract_after_prefix(
            text,
            ("search knowledge for ", "search notes for ", "find in notes ", "find in knowledge "),
        )
        if knowledge_target is not None:
            return _context_result(
                search_knowledge(knowledge_target),
                "Use these knowledge-search results from the workspace to answer the user's question.",
            )

        web_search_target = _extract_after_prefix(
            text,
            ("search web for ", "look up ", "search online for ", "web search for "),
        )
        if web_search_target is not None:
            return _context_result(
                search_web(web_search_target),
                "Use these web search results to answer the user. Be explicit when you only have search-result snippets rather than full-page evidence.",
            )

        summary_target = _extract_after_prefix(
            text,
            ("summarize file ", "summarise file ", "summarize note ", "summarise note "),
        )
        if summary_target is not None:
            return _context_result(
                summarize_file(summary_target),
                "Summarize this file for the user using the extracted excerpts below.",
            )

        page_target = _extract_after_prefix(
            text,
            ("open url ", "open page ", "fetch page ", "read webpage ", "read web page "),
        )
        if page_target is not None:
            return _context_result(
                fetch_page(page_target),
                "Use this fetched webpage content to answer the user's request. Distinguish page text from your own reasoning.",
            )

        page_summary_target = _extract_after_prefix(
            text,
            ("summarize page ", "summarise page ", "summarize webpage ", "summarise webpage "),
        )
        if page_summary_target is not None:
            return _context_result(
                summarize_page(page_summary_target),
                "Summarize this webpage for the user using the extracted content below.",
            )

        create_match = re.match(
            r"(?is)^(?:create|make)\s+file\s+(.+?)(?:\s+with\s+content\s*:\s*(.+))?$",
            text,
        )
        if create_match:
            path = create_match.group(1).strip()
            content = (create_match.group(2) or "").strip()
            return _direct_result(create_file(path, content))

        overwrite_match = re.match(
            r"(?is)^overwrite\s+file\s+(.+?)\s+with\s+content\s*:\s*(.+)$",
            text,
        )
        if overwrite_match:
            path = overwrite_match.group(1).strip()
            content = overwrite_match.group(2).strip()
            return _direct_result(create_file(path, content, overwrite=True))

        delete_target = _extract_after_prefix(text, ("delete file ", "delete folder ", "remove file ", "remove folder "))
        if delete_target is not None:
            return _direct_result(request_delete(delete_target))

        move_match = re.match(r"(?is)^(?:move|rename)\s+(.+?)\s+to\s+(.+)$", text)
        if move_match:
            source = move_match.group(1).strip()
            target = move_match.group(2).strip()
            return _direct_result(request_move(source, target))

        copy_match = re.match(r"(?is)^copy\s+(.+?)\s+to\s+(.+)$", text)
        if copy_match:
            source = copy_match.group(1).strip()
            target = copy_match.group(2).strip()
            return _direct_result(request_copy(source, target))

        approve_target = _extract_after_prefix(text, ("approve action ",))
        if approve_target is not None:
            return _direct_result(approve_action(approve_target))

        pending_target = _extract_after_prefix(text, ("list pending actions", "show pending actions"))
        if pending_target is not None or text.lower() in {"pending actions", "list pending", "show pending"}:
            return _context_result(
                list_pending_actions(),
                "Use this pending-action list to answer the user's question or confirm the queue state.",
            )

        command_text = _extract_after_prefix(
            text,
            ("run command ", "command ", "run "),
        )
        if command_text is not None:
            return _context_result(
                run_command(command_text),
                "Use this safe command output to answer the user's request.",
            )
    except ValueError as exc:
        return _direct_result(str(exc))

    return None
