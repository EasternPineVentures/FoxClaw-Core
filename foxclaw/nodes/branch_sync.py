"""Safe branch-position helper for Apollo founder nodes."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class BranchSyncState:
    repo_path: str
    current_branch: str
    head: str
    head_subject: str
    upstream: str | None
    ahead: int
    behind: int
    dirty: bool
    changed_files: tuple[str, ...]
    target_branch: str | None
    target_local_exists: bool
    target_remote_exists: bool
    remote: str


@dataclass(frozen=True)
class BranchSyncPlan:
    state: BranchSyncState
    action: str
    safe_to_apply: bool
    commands: tuple[tuple[str, ...], ...]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class BranchSyncResult:
    before: BranchSyncState
    plan: BranchSyncPlan
    applied: bool
    after: BranchSyncState | None
    executed: tuple[tuple[str, ...], ...]


def inspect_branch_sync(
    repo_path: str | Path,
    *,
    target_branch: str | None = None,
    remote: str = "origin",
) -> BranchSyncState:
    repo = Path(repo_path).resolve()
    current = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    upstream = _optional_git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    ahead = behind = 0
    if upstream:
        behind_text, ahead_text = _git(repo, "rev-list", "--left-right", "--count", f"{upstream}...HEAD").split()
        ahead = int(ahead_text)
        behind = int(behind_text)
    changed = tuple(line for line in _git(repo, "status", "--short").splitlines() if line.strip())
    return BranchSyncState(
        repo_path=str(repo),
        current_branch=current,
        head=_git(repo, "rev-parse", "--short", "HEAD"),
        head_subject=_git(repo, "log", "-1", "--pretty=%s"),
        upstream=upstream,
        ahead=ahead,
        behind=behind,
        dirty=bool(changed),
        changed_files=changed,
        target_branch=target_branch,
        target_local_exists=_branch_exists(repo, target_branch) if target_branch else False,
        target_remote_exists=_remote_branch_exists(repo, remote, target_branch) if target_branch else False,
        remote=remote,
    )


def plan_branch_sync(state: BranchSyncState) -> BranchSyncPlan:
    target = state.target_branch
    if not target:
        return BranchSyncPlan(
            state=state,
            action="inspect_current_branch",
            safe_to_apply=False,
            commands=(),
            notes=("pass --target-branch to plan a sync",),
        )
    if state.dirty:
        return BranchSyncPlan(
            state=state,
            action="stop_dirty_tree",
            safe_to_apply=False,
            commands=(),
            notes=("commit or intentionally set aside local changes before switching branches",),
        )

    commands: list[tuple[str, ...]] = []
    notes: list[str] = []
    if state.current_branch != target:
        if state.target_local_exists:
            commands.append(("git", "switch", target))
        elif state.target_remote_exists:
            commands.append(("git", "switch", "-c", target, "--track", f"{state.remote}/{target}"))
        else:
            return BranchSyncPlan(
                state=state,
                action="stop_missing_target_branch",
                safe_to_apply=False,
                commands=(),
                notes=(f"{state.remote}/{target} was not found; run with --fetch or verify the branch name",),
            )
        commands.append(("git", "pull", "--ff-only"))
        return BranchSyncPlan(
            state=state,
            action="switch_then_fast_forward",
            safe_to_apply=True,
            commands=tuple(commands),
            notes=("no push, reset, rebase, or checkout overwrite will be performed",),
        )

    if not state.upstream and state.target_remote_exists:
        commands.append(("git", "branch", "--set-upstream-to", f"{state.remote}/{target}", target))
        commands.append(("git", "pull", "--ff-only"))
        return BranchSyncPlan(
            state=state,
            action="attach_upstream_then_fast_forward",
            safe_to_apply=True,
            commands=tuple(commands),
            notes=("local branch exists but is not tracking the remote branch",),
        )
    if state.behind > 0 and state.ahead > 0:
        return BranchSyncPlan(
            state=state,
            action="stop_diverged",
            safe_to_apply=False,
            commands=(),
            notes=("branch has both local and remote commits; human review required",),
        )
    if state.behind > 0:
        commands.append(("git", "pull", "--ff-only"))
        return BranchSyncPlan(
            state=state,
            action="fast_forward_current_branch",
            safe_to_apply=True,
            commands=tuple(commands),
            notes=("remote has commits this node can fast-forward to",),
        )
    if state.ahead > 0:
        return BranchSyncPlan(
            state=state,
            action="local_commits_not_pushed",
            safe_to_apply=False,
            commands=(),
            notes=("local branch is ahead; Courier will not push automatically",),
        )
    return BranchSyncPlan(
        state=state,
        action="already_synced",
        safe_to_apply=False,
        commands=(),
        notes=("branch is clean and aligned with its upstream",),
    )


def apply_branch_sync(
    repo_path: str | Path,
    *,
    target_branch: str,
    remote: str = "origin",
    fetch: bool = True,
) -> BranchSyncResult:
    repo = Path(repo_path).resolve()
    executed: list[tuple[str, ...]] = []
    initial = inspect_branch_sync(repo, target_branch=target_branch, remote=remote)
    initial_plan = plan_branch_sync(initial)
    if initial.dirty:
        return BranchSyncResult(
            before=initial,
            plan=initial_plan,
            applied=False,
            after=None,
            executed=(),
        )
    if fetch:
        fetch_cmd = ("git", "fetch", "--prune", remote)
        _run(repo, fetch_cmd)
        executed.append(fetch_cmd)
    before = inspect_branch_sync(repo, target_branch=target_branch, remote=remote)
    plan = plan_branch_sync(before)
    if not plan.safe_to_apply:
        return BranchSyncResult(before=before, plan=plan, applied=False, after=None, executed=tuple(executed))
    for command in plan.commands:
        _run(repo, command)
        executed.append(command)
    after = inspect_branch_sync(repo, target_branch=target_branch, remote=remote)
    return BranchSyncResult(before=before, plan=plan, applied=True, after=after, executed=tuple(executed))


def fetch_remote(repo_path: str | Path, *, remote: str = "origin") -> None:
    _run(Path(repo_path).resolve(), ("git", "fetch", "--prune", remote))


def dumps_json(value: Any) -> str:
    return json.dumps(to_jsonable(value), indent=2, sort_keys=True) + "\n"


def to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {field.name: to_jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in sorted(value.items())}
    if isinstance(value, tuple | list):
        return [to_jsonable(item) for item in value]
    return value


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def _run(repo: Path, command: Iterable[str]) -> None:
    subprocess.run(
        list(command),
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )


def _optional_git(repo: Path, *args: str) -> str | None:
    try:
        out = _git(repo, *args)
    except subprocess.CalledProcessError:
        return None
    return out or None


def _branch_exists(repo: Path, branch: str | None) -> bool:
    if not branch:
        return False
    return subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
        cwd=repo,
    ).returncode == 0


def _remote_branch_exists(repo: Path, remote: str, branch: str | None) -> bool:
    if not branch:
        return False
    return subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/remotes/{remote}/{branch}"],
        cwd=repo,
    ).returncode == 0
