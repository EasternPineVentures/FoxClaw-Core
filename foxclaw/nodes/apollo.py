"""Apollo node coordination receipts.

These receipts are for human/agent coordination across FoxClaw workstations. They do not
grant runtime authority and they deliberately avoid secret/env inspection.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

PROTOCOL = "apollo_node_brief_v1"
DEFAULT_RAILS = (
    "pull_before_start",
    "commit_each_slice",
    "clean_tree_before_handoff",
    "do_not_overlap_dirty_files",
    "old_repo_reference_only",
    "no_secret_printing",
    "no_live_orders",
    "no_funds_movement",
)


@dataclass(frozen=True)
class NodeAuthorityLocks:
    can_submit_order: bool = False
    can_move_funds: bool = False
    live_execution_allowed: bool = False
    can_publish: bool = False
    can_set_probability: bool = False

    def __post_init__(self) -> None:
        if any(
            (
                self.can_submit_order,
                self.can_move_funds,
                self.live_execution_allowed,
                self.can_publish,
                self.can_set_probability,
            )
        ):
            raise ValueError("Apollo node briefs cannot grant authority")


@dataclass(frozen=True)
class GitSnapshot:
    repo_path: str
    branch: str
    head: str
    head_subject: str
    upstream: str | None
    ahead: int
    behind: int
    dirty: bool
    changed_files: tuple[str, ...]
    available: bool = True
    error: str | None = None

    def __post_init__(self) -> None:
        if not self.repo_path:
            raise ValueError("repo_path is required")
        if self.ahead < 0 or self.behind < 0:
            raise ValueError("ahead/behind counts must be non-negative")
        if not isinstance(self.changed_files, tuple):
            raise TypeError("changed_files must be a tuple")
        if not self.available and not self.error:
            raise ValueError("unavailable git snapshots must carry an error")


@dataclass(frozen=True)
class ApolloNodeBrief:
    protocol: str
    node_id: str
    peer_node: str
    role: str
    generated_at: datetime
    version: str
    git: GitSnapshot
    current_slice: str
    next_request: str
    blockers: tuple[str, ...]
    notes: tuple[str, ...]
    rails: tuple[str, ...]
    authority: NodeAuthorityLocks
    old_reference_path: str | None = None

    def __post_init__(self) -> None:
        if self.protocol != PROTOCOL:
            raise ValueError(f"unsupported Apollo node protocol: {self.protocol}")
        for label in ("node_id", "peer_node", "role", "version", "current_slice", "next_request"):
            if not _text(getattr(self, label)):
                raise ValueError(f"{label} is required")
        if self.generated_at.tzinfo is None or self.generated_at.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")
        if not isinstance(self.git, GitSnapshot):
            raise TypeError("git must be a GitSnapshot")
        if not isinstance(self.authority, NodeAuthorityLocks):
            raise TypeError("authority must be NodeAuthorityLocks")


def build_node_brief(
    *,
    repo_path: str | Path,
    node_id: str | None = None,
    peer_node: str = "peer",
    role: str = "operator",
    current_slice: str = "status handoff",
    next_request: str = "pull, inspect status, and continue the smallest safe slice",
    blockers: tuple[str, ...] = (),
    notes: tuple[str, ...] = (),
    old_reference_path: str | Path | None = None,
    generated_at: datetime | None = None,
    git: GitSnapshot | None = None,
) -> ApolloNodeBrief:
    repo = Path(repo_path).resolve()
    snapshot = git if git is not None else git_snapshot(repo)
    return ApolloNodeBrief(
        protocol=PROTOCOL,
        node_id=_node_id(node_id),
        peer_node=peer_node,
        role=role,
        generated_at=(generated_at or datetime.now(UTC)).astimezone(UTC).replace(microsecond=0),
        version=_read_version(repo),
        git=snapshot,
        current_slice=current_slice,
        next_request=next_request,
        blockers=tuple(_text(item) for item in blockers if _text(item)),
        notes=tuple(_text(item) for item in notes if _text(item)),
        rails=DEFAULT_RAILS,
        authority=NodeAuthorityLocks(),
        old_reference_path=str(Path(old_reference_path).resolve()) if old_reference_path else None,
    )


def git_snapshot(repo_path: str | Path) -> GitSnapshot:
    repo = Path(repo_path).resolve()
    try:
        branch = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
        head = _git(repo, "rev-parse", "--short", "HEAD")
        subject = _git(repo, "log", "-1", "--pretty=%s")
        upstream = _optional_git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
        ahead = behind = 0
        if upstream:
            counts = _git(repo, "rev-list", "--left-right", "--count", f"{upstream}...HEAD")
            behind_text, ahead_text = counts.split()
            behind = int(behind_text)
            ahead = int(ahead_text)
        changed = tuple(
            line for line in _git(repo, "status", "--short").splitlines() if line.strip()
        )
        return GitSnapshot(
            repo_path=str(repo),
            branch=branch,
            head=head,
            head_subject=subject,
            upstream=upstream,
            ahead=ahead,
            behind=behind,
            dirty=bool(changed),
            changed_files=changed,
        )
    except (OSError, subprocess.CalledProcessError, ValueError) as exc:
        return GitSnapshot(
            repo_path=str(repo),
            branch="unknown",
            head="unknown",
            head_subject="unknown",
            upstream=None,
            ahead=0,
            behind=0,
            dirty=True,
            changed_files=(),
            available=False,
            error=str(exc),
        )


def render_markdown(brief: ApolloNodeBrief) -> str:
    clean = "dirty" if brief.git.dirty else "clean"
    lines = [
        "# FoxClaw Apollo Node Brief",
        "",
        f"From: `{brief.node_id}`",
        f"To: `{brief.peer_node}`",
        f"Role: `{brief.role}`",
        f"Generated: `{_iso(brief.generated_at)}`",
        "",
        "## Repo",
        "",
        f"- Path: `{brief.git.repo_path}`",
        f"- Version: `{brief.version}`",
        f"- Branch: `{brief.git.branch}`",
        f"- Head: `{brief.git.head}` - {brief.git.head_subject}",
        f"- Upstream: `{brief.git.upstream or 'none'}`",
        f"- Ahead/behind: `{brief.git.ahead}/{brief.git.behind}`",
        f"- Tree: `{clean}`",
    ]
    if brief.git.changed_files:
        lines.append("- Changed files:")
        lines.extend(f"  - `{item}`" for item in brief.git.changed_files)
    if brief.git.error:
        lines.append(f"- Git error: `{brief.git.error}`")
    if brief.old_reference_path:
        lines.append(f"- Old reference path: `{brief.old_reference_path}`")

    lines.extend(
        [
            "",
            "## Work",
            "",
            f"- Current slice: {brief.current_slice}",
            f"- Next request: {brief.next_request}",
        ]
    )
    lines.append("- Blockers: " + (", ".join(brief.blockers) if brief.blockers else "none"))
    if brief.notes:
        lines.append("- Notes:")
        lines.extend(f"  - {note}" for note in brief.notes)

    lines.extend(
        [
            "",
            "## Rails",
            "",
        ]
    )
    lines.extend(f"- `{rail}`" for rail in brief.rails)
    lines.extend(
        [
            "",
            "## Authority",
            "",
            "- `can_submit_order=false`",
            "- `can_move_funds=false`",
            "- `live_execution_allowed=false`",
            "- `can_publish=false`",
            "- `can_set_probability=false`",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def to_jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return _iso(value)
    if is_dataclass(value):
        return {field.name: to_jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): to_jsonable(item) for key, item in sorted(value.items())}
    if isinstance(value, (tuple, list)):
        return [to_jsonable(item) for item in value]
    return value


def dumps_json(value: Any) -> str:
    return json.dumps(to_jsonable(value), indent=2, sort_keys=True) + "\n"


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def _optional_git(repo: Path, *args: str) -> str | None:
    try:
        out = _git(repo, *args)
    except subprocess.CalledProcessError:
        return None
    return out or None


def _read_version(repo: Path) -> str:
    version_file = repo / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "unknown"


def _node_id(value: str | None) -> str:
    return _text(value or os.environ.get("FOXCLAW_NODE_ID") or socket.gethostname())


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _text(value: Any) -> str:
    return str(value or "").strip()
