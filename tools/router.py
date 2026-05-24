from dataclasses import dataclass
import re

from mode import available_modes_snapshot, get_mode, set_mode
from planner import plan_request
from tools.approval_tool import approve_action, list_pending_actions, request_copy, request_delete, request_move
from tools.agenda_tool import answer_agenda_request
from tools.commands_tool import run_command
from tools.files_tool import (
    allowed_roots_snapshot,
    create_file,
    list_directory,
    read_file,
    recent_activity_snapshot,
    search_files,
)
from tools.notes_tool import search_knowledge, summarize_file
from tools.review_tool import build_operating_review
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


def _extract_search_target(text: str) -> str | None:
    patterns = (
        r"(?is).*?(?:find|look for|search for)\s+(?:that\s+|the\s+)?(?:file|document|doc|note)?\s*(.+)",
        r"(?is).*?(?:where is|where's)\s+(?:the\s+)?(.+)",
    )
    for pattern in patterns:
        match = re.match(pattern, text)
        if match:
            candidate = match.group(1).strip(" .?!")
            if candidate:
                return candidate
    return None


def _extract_read_target(text: str) -> str | None:
    patterns = (
        r"(?is).*?(?:open|read|show me|pull up)\s+(?:the\s+)?(?:file|document|doc|note)?\s*(.+)",
        r"(?is).*?what(?:'s| is)\s+in\s+(?:the\s+)?(.+)",
    )
    for pattern in patterns:
        match = re.match(pattern, text)
        if match:
            candidate = match.group(1).strip(" .?!")
            if candidate:
                return candidate
    return None


def _extract_topic_after_marker(text: str, markers: tuple[str, ...]) -> str | None:
    lowered = text.lower()
    for marker in markers:
        idx = lowered.find(marker)
        if idx >= 0:
            candidate = text[idx + len(marker):].strip(" .?!")
            if candidate:
                return candidate
    return None


def _infer_natural_request(text: str) -> ToolResult | None:
    planned = plan_request(text)
    if planned is not None:
        if planned.mode == "direct":
            return _direct_result(planned.payload)
        return _context_result(planned.payload, planned.instruction)

    lowered = text.lower().strip()

    if any(
        phrase in lowered
        for phrase in (
            "what should i be paying attention to",
            "what should i pay attention to",
            "what matters most right now",
            "give me a quick review",
            "give me a status review",
            "what needs my attention",
        )
    ):
        return _context_result(
            build_operating_review(),
            "Use this operating review to tell the user what deserves attention and why.",
        )

    if any(
        phrase in lowered
        for phrase in (
            "what have i been focused on",
            "what have i been doing lately",
            "what have i been up to lately",
            "what have i been touching lately",
            "what files have i been working on",
        )
    ):
        return _context_result(
            recent_activity_snapshot(),
            "Use this recent file activity to infer what the user has likely been working on lately. Be explicit that this is based on file modification traces.",
        )

    if any(
        phrase in lowered
        for phrase in (
            "what can you access",
            "what can you see on my machine",
            "what parts of my machine can you access",
            "where are you allowed to look",
        )
    ):
        return _context_result(
            allowed_roots_snapshot(),
            "Use this allowed-root list to answer where Voss can currently read and work.",
        )

    topic = _extract_topic_after_marker(
        text,
        (
            "what did i write about ",
            "what do my notes say about ",
            "what did i say about ",
            "what do i know about ",
        ),
    )
    if topic is not None:
        return _context_result(
            search_knowledge(topic),
            "Use these knowledge-search results from the workspace to answer the user's question.",
        )

    topic = _extract_topic_after_marker(
        text,
        (
            "look up ",
            "check on ",
            "find out about ",
            "search the web for ",
            "search online for ",
        ),
    )
    if topic is not None:
        return _context_result(
            search_web(topic),
            "Use these web search results to answer the user. Be explicit when you only have search-result snippets rather than full-page evidence.",
        )

    if any(signal in lowered for signal in ("pricing", "competitors", "competitor", "latest news on ")):
        if "http://" not in lowered and "https://" not in lowered:
            return _context_result(
                search_web(text),
                "Use these web search results to answer the user. Be explicit when you only have search-result snippets rather than full-page evidence.",
            )

    if "http://" in lowered or "https://" in lowered:
        if any(word in lowered for word in ("summarize", "summarise", "what's on", "what is on")):
            url_match = re.search(r"https?://\S+", text)
            if url_match:
                return _context_result(
                    summarize_page(url_match.group(0).rstrip(".,!?")),
                    "Summarize this webpage for the user using the extracted content below.",
                )
        if any(word in lowered for word in ("open", "read", "fetch", "check")):
            url_match = re.search(r"https?://\S+", text)
            if url_match:
                return _context_result(
                    fetch_page(url_match.group(0).rstrip(".,!?")),
                    "Use this fetched webpage content to answer the user's request. Distinguish page text from your own reasoning.",
                )

    if any(word in lowered for word in ("summarize", "summarise", "explain", "what's in", "what is in")):
        target = _extract_read_target(text)
        if target is not None and not target.lower().startswith(("http://", "https://")):
            return _context_result(
                summarize_file(target),
                "Summarize this file for the user using the extracted excerpts below.",
            )

    target = _extract_read_target(text)
    if target is not None and not any(word in lowered for word in ("pricing", "competitor", "competitors")):
        return _context_result(
            read_file(target),
            "Use this file content to answer the user's request. If they asked for explanation, explain it. If they asked to read it, summarize the important parts.",
        )

    target = _extract_search_target(text)
    if target is not None:
        return _context_result(
            search_files(target),
            "Use these file-search results to answer the user clearly. Do not invent files that were not found.",
        )

    return None


def handle_tool_request(user_input: str) -> ToolResult | None:
    text = user_input.strip()
    try:
        if text.lower().strip() in {
            "run self test",
            "run self-test",
            "self test",
            "self-test",
            "health check",
        }:
            from selftest import run_self_test

            return _context_result(
                run_self_test(),
                "Use this self-test output to explain the current health of Voss clearly and concretely.",
            )

        mode_match = re.match(r"(?is).*(?:switch to|use|enter)\s+(build|review|strategy|critical|quiet)\s+mode.*", text)
        if mode_match:
            return _direct_result(set_mode(mode_match.group(1)))

        if text.lower().strip() in {
            "what mode are you in",
            "current mode",
            "which mode are you in",
            "show mode",
        }:
            return _direct_result(f"Current mode: {get_mode()}.")

        if text.lower().strip() in {
            "show modes",
            "what modes do you have",
            "list modes",
        }:
            return _context_result(
                available_modes_snapshot(),
                "Use this mode list to answer the user's question about available operating modes.",
            )

        natural_reply = _infer_natural_request(text)
        if natural_reply is not None:
            return natural_reply

        agenda_reply = answer_agenda_request(text)
        if agenda_reply is not None:
            return _context_result(
                agenda_reply,
                "Use this agenda state to answer the user's scheduling or commitment question.",
            )

        if text.lower() in {
            "what matters right now",
            "what am i neglecting",
            "what looks urgent",
            "give me an operating review",
            "operating review",
            "what should i focus on next",
        }:
            return _context_result(
                build_operating_review(),
                "Use this operating review to tell the user what deserves attention and why.",
            )

        if text.lower() in {
            "show allowed roots",
            "what folders can you access",
            "what paths can you access",
            "where can you look",
        }:
            return _context_result(
                allowed_roots_snapshot(),
                "Use this allowed-root list to answer where Voss can currently read and work.",
            )

        if text.lower() in {
            "what have i been working on recently",
            "what looks active right now",
            "which project seems hottest",
            "show my recent activity",
            "recent activity",
        }:
            return _context_result(
                recent_activity_snapshot(),
                "Use this recent file activity to infer what the user has likely been working on lately. Be explicit that this is based on file modification traces.",
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
