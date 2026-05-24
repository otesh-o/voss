from pathlib import Path

from config import MAX_FILE_READ_CHARS, MAX_SEARCH_RESULTS, WORKSPACE_ROOT, get_allowed_roots


def _label_for_path(path: Path) -> str:
    for root in get_allowed_roots():
        try:
            relative = path.resolve().relative_to(root.resolve())
            root_name = root.name or str(root)
            if str(relative):
                return f"{root_name}/{relative}".replace("\\", "/")
            return root_name
        except ValueError:
            continue
    return str(path)


def _resolve_workspace_path(user_path: str | None = None) -> Path:
    allowed_roots = get_allowed_roots()
    base_path = WORKSPACE_ROOT.resolve()
    if not user_path or user_path.strip() in {".", ""}:
        return base_path

    candidate = Path(user_path.strip().strip('"').strip("'"))
    if not candidate.is_absolute():
        candidate = base_path / candidate

    resolved = candidate.resolve()

    for root in allowed_roots:
        try:
            resolved.relative_to(root.resolve())
            return resolved
        except ValueError:
            continue

    raise ValueError("Path must stay inside an allowed Voss root.")


def allowed_roots_snapshot() -> str:
    roots = get_allowed_roots()
    if not roots:
        return "No allowed roots are configured."

    lines = ["Allowed roots:"]
    for root in roots:
        lines.append(str(root))
    return "\n".join(lines)



def search_files(query: str) -> str:
    if not query.strip():
        return "Search query is empty."

    matches: list[Path] = []
    query_lower = query.lower()

    for root in get_allowed_roots():
        for path in root.rglob("*"):
            if ".git" in path.parts:
                continue
            if query_lower in path.name.lower():
                matches.append(path)
            if len(matches) >= MAX_SEARCH_RESULTS:
                break
        if len(matches) >= MAX_SEARCH_RESULTS:
            break

    if not matches:
        return f"No files found matching '{query}'."

    lines = [f"Found {len(matches)} match(es):"]
    for match in matches:
        lines.append(_label_for_path(match))
    return "\n".join(lines)


def list_directory(user_path: str | None = None) -> str:
    target = _resolve_workspace_path(user_path)
    items = sorted(target.iterdir(), key=lambda item: (item.is_file(), item.name.lower()))
    label = _label_for_path(target)

    if not items:
        return f"{label} is empty."

    lines = [f"Contents of {label}:"]
    for item in items[:MAX_SEARCH_RESULTS]:
        suffix = "/" if item.is_dir() else ""
        lines.append(f"{item.name}{suffix}")

    if len(items) > MAX_SEARCH_RESULTS:
        lines.append(f"...and {len(items) - MAX_SEARCH_RESULTS} more")

    return "\n".join(lines)


def read_file(user_path: str) -> str:
    target = _resolve_workspace_path(user_path)

    if not target.exists():
        return f"File not found: {user_path}"
    if target.is_dir():
        return f"'{user_path}' is a directory, not a file."

    try:
        text = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"'{user_path}' is not a UTF-8 text file."
    if len(text) > MAX_FILE_READ_CHARS:
        text = text[:MAX_FILE_READ_CHARS] + "\n\n[truncated]"

    return f"Contents of {_label_for_path(target)}:\n{text}"


def create_file(user_path: str, content: str = "", overwrite: bool = False) -> str:
    target = _resolve_workspace_path(user_path)

    if target.exists() and not overwrite:
        return f"File already exists: {user_path}. Say overwrite if you want to replace it."

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    if content:
        return f"Created {_label_for_path(target)}."
    return f"Created empty file {_label_for_path(target)}."
