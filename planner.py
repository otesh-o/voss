from dataclasses import dataclass
import re

from reminder import due_reminders_snapshot
from tools.approval_tool import request_copy, request_delete, request_move
from tools.agenda_tool import answer_agenda_request
from tools.files_tool import (
    allowed_roots_snapshot,
    create_directory,
    create_file,
    read_file,
    recent_activity_snapshot,
    search_files,
)
from tools.notes_tool import search_knowledge, summarize_file
from tools.review_tool import build_operating_review
from tools.web_tool import fetch_page, search_web, summarize_page


@dataclass
class PlanStep:
    title: str
    action: str
    argument: str = ""


@dataclass
class PlannedContext:
    mode: str
    payload: str
    instruction: str


def _direct_outcome(payload: str) -> PlannedContext:
    return PlannedContext(mode="direct", payload=payload, instruction="")


def _context_outcome(payload: str, instruction: str) -> PlannedContext:
    return PlannedContext(mode="context", payload=payload, instruction=instruction)


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


def _extract_move_targets(text: str) -> tuple[str, str] | None:
    match = re.match(r"(?is).*(?:move|put|organize)\s+(.+?)\s+(?:into|to)\s+(.+)", text)
    if match:
        source = match.group(1).strip(" .?!")
        target = match.group(2).strip(" .?!")
        if source and target:
            return source, target
    return None


def _extract_copy_targets(text: str) -> tuple[str, str] | None:
    match = re.match(r"(?is).*(?:copy|duplicate)\s+(.+?)\s+(?:into|to)\s+(.+)", text)
    if match:
        source = match.group(1).strip(" .?!")
        target = match.group(2).strip(" .?!")
        if source and target:
            return source, target
    return None


def _extract_delete_target(text: str) -> str | None:
    match = re.match(r"(?is).*(?:delete|remove|clean up)\s+(.+)", text)
    if match:
        target = match.group(1).strip(" .?!")
        if target:
            return target
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


def plan_request(user_input: str) -> PlannedContext | None:
    text = user_input.strip()
    lowered = text.lower().strip()
    steps: list[PlanStep] = []
    instruction = ""

    create_folder_match = re.match(
        r"(?is).*(?:create|make|set up)\s+(?:a\s+)?(?:folder|directory)\s+(?:for\s+)?(.+)",
        text,
    )
    if create_folder_match:
        target = create_folder_match.group(1).strip(" .?!")
        if target:
            return _direct_outcome(create_directory(target))

    create_note_match = re.match(
        r"(?is).*(?:create|make|draft)\s+(?:a\s+)?(?:note|file)\s+(?:for\s+)?(.+)",
        text,
    )
    if create_note_match and "with content" not in lowered:
        target = create_note_match.group(1).strip(" .?!")
        if target:
            safe_name = target.replace(" ", "_")
            if "." not in safe_name:
                safe_name = f"{safe_name}.md"
            content = f"# {target}\n\n"
            return _direct_outcome(create_file(safe_name, content))

    move_targets = _extract_move_targets(text)
    if move_targets and any(word in lowered for word in ("move", "put", "organize")):
        source, target = move_targets
        return _direct_outcome(request_move(source, target))

    copy_targets = _extract_copy_targets(text)
    if copy_targets:
        source, target = copy_targets
        return _direct_outcome(request_copy(source, target))

    delete_target = _extract_delete_target(text)
    if delete_target and any(word in lowered for word in ("delete", "remove", "clean up")):
        return _direct_outcome(request_delete(delete_target))

    if any(phrase in lowered for phrase in ("create a folder", "make a folder", "set up a folder")) and any(
        phrase in lowered for phrase in ("find related", "find anything related", "summarize", "summarise")
    ):
        folder_match = re.search(r"(?is)(?:create|make|set up)\s+(?:a\s+)?(?:folder|directory)\s+(?:for\s+)?(.+?)(?:\s+and\s+|\s*,\s*|$)", text)
        if folder_match:
            target = folder_match.group(1).strip(" .?!")
            if target:
                folder_result = create_directory(target)
                steps = [
                    PlanStep("Directory creation result", "literal", folder_result),
                    PlanStep("File search results", "file_search", target),
                    PlanStep("Knowledge matches", "knowledge_search", target),
                ]
                instruction = "Use the created-folder confirmation, file search results, and knowledge matches to tell the user what was set up and what related material exists."

    if any(
        phrase in lowered
        for phrase in (
            "what matters most",
            "what should i focus on",
            "what deserves my attention",
            "give me the big picture",
        )
    ):
        steps = [
            PlanStep("Operating review", "operating_review"),
            PlanStep("Due reminders", "due_reminders"),
            PlanStep("Recent activity", "recent_activity", "8"),
        ]
        instruction = "Use the combined operating review, reminders, and recent activity to tell the user what matters most right now. Prioritize signal over completeness."

    elif any(phrase in lowered for phrase in ("what am i neglecting", "what am i missing", "what am i overlooking")):
        steps = [
            PlanStep("Operating review", "operating_review"),
            PlanStep("Agenda state", "agenda_state", "show agenda"),
            PlanStep("Recent activity", "recent_activity", "8"),
        ]
        instruction = "Use the operating review, agenda state, and recent activity together to identify neglected or overlooked work."

    elif "find" in lowered and any(word in lowered for word in ("summarize", "summarise", "explain")):
        target = _extract_search_target(text)
        if target:
            steps = [
                PlanStep("File search results", "file_search", target),
                PlanStep("Knowledge matches", "knowledge_search", target),
            ]
            instruction = "Use the file search results and knowledge matches together. Identify the most relevant material and summarize what it likely contains."

    elif any(phrase in lowered for phrase in ("compare", "difference between", "vs ", "versus ")) and any(
        signal in lowered for signal in ("pricing", "competitor", "competitors", "plan", "plans")
    ):
        steps = [PlanStep("Web search results", "web_search", text)]
        instruction = "Use these web search results to compare the things the user asked about. Be explicit that the comparison is based on retrieved results, not full manual browsing."

    elif any(
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
        steps = [PlanStep("Operating review", "operating_review")]
        instruction = "Use this operating review to tell the user what deserves attention and why."

    elif any(
        phrase in lowered
        for phrase in (
            "what have i been focused on",
            "what have i been doing lately",
            "what have i been up to lately",
            "what have i been touching lately",
            "what files have i been working on",
        )
    ):
        steps = [PlanStep("Recent activity", "recent_activity", "12")]
        instruction = "Use this recent file activity to infer what the user has likely been working on lately. Be explicit that this is based on file modification traces."

    elif any(
        phrase in lowered
        for phrase in (
            "what can you access",
            "what can you see on my machine",
            "what parts of my machine can you access",
            "where are you allowed to look",
        )
    ):
        steps = [PlanStep("Allowed roots", "allowed_roots")]
        instruction = "Use this allowed-root list to answer where Voss can currently read and work."

    else:
        topic = _extract_topic_after_marker(
            text,
            (
                "what did i write about ",
                "what do my notes say about ",
                "what did i say about ",
                "what do i know about ",
            ),
        )
        if topic:
            steps = [PlanStep("Knowledge matches", "knowledge_search", topic)]
            instruction = "Use these knowledge-search results from the workspace to answer the user's question."

        else:
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
            if topic:
                steps = [PlanStep("Web search results", "web_search", topic)]
                instruction = "Use these web search results to answer the user. Be explicit when you only have search-result snippets rather than full-page evidence."

            elif any(signal in lowered for signal in ("pricing", "competitors", "competitor", "latest news on ")) and "http://" not in lowered and "https://" not in lowered:
                steps = [PlanStep("Web search results", "web_search", text)]
                instruction = "Use these web search results to answer the user. Be explicit when you only have search-result snippets rather than full-page evidence."

            elif "http://" in lowered or "https://" in lowered:
                url_match = re.search(r"https?://\S+", text)
                if url_match:
                    url = url_match.group(0).rstrip(".,!?")
                    if any(word in lowered for word in ("summarize", "summarise", "what's on", "what is on")):
                        steps = [PlanStep("Web page summary material", "page_summary", url)]
                        instruction = "Summarize this webpage for the user using the extracted content below."
                    elif any(word in lowered for word in ("open", "read", "fetch", "check")):
                        steps = [PlanStep("Web page content", "page_fetch", url)]
                        instruction = "Use this fetched webpage content to answer the user's request. Distinguish page text from your own reasoning."

            elif any(word in lowered for word in ("summarize", "summarise", "explain", "what's in", "what is in")):
                target = _extract_read_target(text)
                if target and not target.lower().startswith(("http://", "https://")):
                    steps = [PlanStep("File excerpt", "file_summary", target)]
                    instruction = "Summarize this file for the user using the extracted excerpts below."

            else:
                target = _extract_read_target(text)
                if target and not any(word in lowered for word in ("pricing", "competitor", "competitors")):
                    steps = [PlanStep("File content", "file_read", target)]
                    instruction = "Use this file content to answer the user's request. If they asked for explanation, explain it. If they asked to read it, summarize the important parts."
                else:
                    target = _extract_search_target(text)
                    if target:
                        steps = [PlanStep("File search results", "file_search", target)]
                        instruction = "Use these file-search results to answer the user clearly. Do not invent files that were not found."

    if not steps:
        return None

    payload_parts = []
    for step in steps:
        payload_parts.append(f"{step.title}:\n{_run_step(step)}")

    return _context_outcome("\n\n".join(payload_parts), instruction)


def _run_step(step: PlanStep) -> str:
    if step.action == "literal":
        return step.argument
    if step.action == "operating_review":
        return build_operating_review()
    if step.action == "due_reminders":
        return due_reminders_snapshot()
    if step.action == "recent_activity":
        limit = int(step.argument) if step.argument else 12
        return recent_activity_snapshot(limit=limit)
    if step.action == "agenda_state":
        return answer_agenda_request(step.argument) or "No agenda state."
    if step.action == "allowed_roots":
        return allowed_roots_snapshot()
    if step.action == "file_search":
        return search_files(step.argument)
    if step.action == "knowledge_search":
        return search_knowledge(step.argument)
    if step.action == "web_search":
        return search_web(step.argument)
    if step.action == "page_fetch":
        return fetch_page(step.argument)
    if step.action == "page_summary":
        return summarize_page(step.argument)
    if step.action == "file_summary":
        return summarize_file(step.argument)
    if step.action == "file_read":
        return read_file(step.argument)
    return f"Unsupported plan step: {step.action}"
