from pathlib import Path

from config import KNOWLEDGE_PREVIEW_CHARS, MAX_KNOWLEDGE_RESULTS, TEXT_FILE_SUFFIXES, WORKSPACE_ROOT
from tools.files_tool import _resolve_workspace_path


def _iter_text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        if path.suffix.lower() not in TEXT_FILE_SUFFIXES:
            continue
        yield path


def _safe_read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def search_knowledge(query: str, user_path: str | None = None) -> str:
    query = query.strip()
    if not query:
        return "Knowledge query is empty."

    root = _resolve_workspace_path(user_path or ".")
    query_terms = [term for term in query.lower().split() if term]
    results: list[tuple[int, Path, str]] = []

    for path in _iter_text_files(root):
        content = _safe_read(path)
        if not content:
            continue

        content_lower = content.lower()
        score = sum(content_lower.count(term) for term in query_terms)
        if score <= 0 and query.lower() not in path.name.lower():
            continue

        preview_index = max(content_lower.find(query_terms[0]), 0) if query_terms else 0
        preview = content[preview_index:preview_index + KNOWLEDGE_PREVIEW_CHARS].strip()
        results.append((score, path, preview))

    if not results:
        return f"No knowledge results found for '{query}'."

    results.sort(key=lambda item: (-item[0], str(item[1])))
    lines = [f"Top knowledge matches for '{query}':"]
    for score, path, preview in results[:MAX_KNOWLEDGE_RESULTS]:
        relative = path.relative_to(WORKSPACE_ROOT)
        lines.append(f"[score={score}] {relative}")
        if preview:
            lines.append(preview.replace("\n", " ")[:KNOWLEDGE_PREVIEW_CHARS])
    return "\n".join(lines)


def get_relevant_knowledge(query: str, limit: int = 3) -> str:
    query = query.strip()
    if not query:
        return ""

    query_terms = [term for term in query.lower().split() if term]
    ranked: list[tuple[int, Path, str]] = []

    for path in _iter_text_files(WORKSPACE_ROOT):
        content = _safe_read(path)
        if not content:
            continue
        content_lower = content.lower()
        score = sum(content_lower.count(term) for term in query_terms)
        if score <= 0:
            continue
        preview_index = max(content_lower.find(query_terms[0]), 0)
        preview = content[preview_index:preview_index + 500].strip().replace("\n", " ")
        ranked.append((score, path, preview))

    if not ranked:
        return ""

    ranked.sort(key=lambda item: (-item[0], str(item[1])))
    sections = []
    for score, path, preview in ranked[:limit]:
        sections.append(
            f"Source: {path.relative_to(WORKSPACE_ROOT)}\nRelevance: {score}\nExcerpt: {preview}"
        )
    return "\n\n".join(sections)


def summarize_file(user_path: str) -> str:
    target = _resolve_workspace_path(user_path)
    if not target.exists() or not target.is_file():
        return f"File not found: {user_path}"

    content = _safe_read(target)
    if content is None:
        return f"Could not read {user_path} as text."

    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if not lines:
        return f"{user_path} is empty."

    head = lines[:5]
    tail = lines[-3:] if len(lines) > 6 else []
    summary_lines = [f"Summary of {target.relative_to(WORKSPACE_ROOT)}:"]
    summary_lines.append("Opening lines:")
    summary_lines.extend(head)
    if tail:
        summary_lines.append("Closing lines:")
        summary_lines.extend(tail)
    summary_lines.append(f"Approximate size: {len(content)} characters.")
    return "\n".join(summary_lines)
