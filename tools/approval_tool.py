from dataclasses import dataclass
from pathlib import Path
import shutil

from config import WORKSPACE_ROOT
from tools.files_tool import _resolve_workspace_path


@dataclass
class PendingAction:
    action_id: str
    action_type: str
    source: Path
    target: Path | None = None


_pending_actions: dict[str, PendingAction] = {}
_action_counter = 0


def _protected_path(path: Path) -> bool:
    resolved = path.resolve()
    workspace = WORKSPACE_ROOT.resolve()
    git_dir = (workspace / ".git").resolve()
    return resolved == workspace or resolved == git_dir or git_dir in resolved.parents


def _next_action_id() -> str:
    global _action_counter
    _action_counter += 1
    return f"A{_action_counter:03d}"


def request_delete(user_path: str) -> str:
    target = _resolve_workspace_path(user_path)
    if not target.exists():
        return f"Path not found: {user_path}"
    if _protected_path(target):
        return "That path is protected."

    action_id = _next_action_id()
    _pending_actions[action_id] = PendingAction(action_id, "delete", target)
    relative = target.relative_to(WORKSPACE_ROOT)
    return f"Pending delete {action_id}: {relative}. Say 'approve action {action_id}' to proceed."


def request_move(source_path: str, target_path: str) -> str:
    source = _resolve_workspace_path(source_path)
    if not source.exists():
        return f"Path not found: {source_path}"
    if _protected_path(source):
        return "That source path is protected."

    target = _resolve_workspace_path(target_path)
    if _protected_path(target):
        return "That target path is protected."
    action_id = _next_action_id()
    _pending_actions[action_id] = PendingAction(action_id, "move", source, target)
    return (
        f"Pending move {action_id}: {source.relative_to(WORKSPACE_ROOT)} -> "
        f"{target.relative_to(WORKSPACE_ROOT)}. Say 'approve action {action_id}' to proceed."
    )


def request_copy(source_path: str, target_path: str) -> str:
    source = _resolve_workspace_path(source_path)
    if not source.exists():
        return f"Path not found: {source_path}"
    if _protected_path(source):
        return "That source path is protected."

    target = _resolve_workspace_path(target_path)
    if _protected_path(target):
        return "That target path is protected."
    action_id = _next_action_id()
    _pending_actions[action_id] = PendingAction(action_id, "copy", source, target)
    return (
        f"Pending copy {action_id}: {source.relative_to(WORKSPACE_ROOT)} -> "
        f"{target.relative_to(WORKSPACE_ROOT)}. Say 'approve action {action_id}' to proceed."
    )


def list_pending_actions() -> str:
    if not _pending_actions:
        return "No pending actions."

    lines = ["Pending actions:"]
    for action in _pending_actions.values():
        if action.target is None:
            lines.append(f"{action.action_id}: {action.action_type} {action.source.relative_to(WORKSPACE_ROOT)}")
        else:
            lines.append(
                f"{action.action_id}: {action.action_type} "
                f"{action.source.relative_to(WORKSPACE_ROOT)} -> {action.target.relative_to(WORKSPACE_ROOT)}"
            )
    return "\n".join(lines)


def approve_action(action_id: str) -> str:
    action = _pending_actions.pop(action_id.upper(), None)
    if action is None:
        return f"No pending action with id {action_id}."

    if action.action_type == "delete":
        if action.source.is_dir():
            shutil.rmtree(action.source)
        else:
            action.source.unlink()
        return f"Deleted {action.source.relative_to(WORKSPACE_ROOT)}."

    if action.action_type == "move":
        assert action.target is not None
        action.target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(action.source), str(action.target))
        return (
            f"Moved {action.source.relative_to(WORKSPACE_ROOT)} "
            f"to {action.target.relative_to(WORKSPACE_ROOT)}."
        )

    if action.action_type == "copy":
        assert action.target is not None
        action.target.parent.mkdir(parents=True, exist_ok=True)
        if action.source.is_dir():
            shutil.copytree(action.source, action.target, dirs_exist_ok=True)
        else:
            shutil.copy2(action.source, action.target)
        return (
            f"Copied {action.source.relative_to(WORKSPACE_ROOT)} "
            f"to {action.target.relative_to(WORKSPACE_ROOT)}."
        )

    return f"Unsupported action type: {action.action_type}"
