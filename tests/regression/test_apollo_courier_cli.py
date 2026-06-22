from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
COURIER_TOOL = REPO / "tools" / "apollo_courier.py"


def _git(cwd: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def _run_courier(*args: str, cwd: Path = REPO) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(COURIER_TOOL), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
    )


def _commit_file(repo: Path, relative: str, text: str, message: str) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    _git(repo, "add", relative)
    _git(repo, "commit", "-m", message)


def _seed_remote(tmp_path: Path) -> Path:
    remote = tmp_path / "remote.git"
    seed = tmp_path / "seed"
    _git(tmp_path, "init", "--bare", str(remote))
    _git(tmp_path, "clone", str(remote), str(seed))
    _git(seed, "config", "user.email", "apollo@example.test")
    _git(seed, "config", "user.name", "Apollo Test")
    _commit_file(seed, "README.md", "master\n", "seed master")
    _git(seed, "push", "origin", "HEAD:master")
    _git(seed, "switch", "-c", "feature/demo")
    _commit_file(seed, "demo.txt", "demo\n", "seed feature branch")
    _git(seed, "push", "-u", "origin", "feature/demo")
    return remote


def test_apollo_courier_branch_sync_tracks_remote_branch(tmp_path: Path):
    remote = _seed_remote(tmp_path)
    node = tmp_path / "node"
    _git(tmp_path, "clone", str(remote), str(node))

    completed = _run_courier(
        "branch-sync",
        "--repo",
        str(node),
        "--target-branch",
        "feature/demo",
        "--apply",
        "--json",
    )
    payload = json.loads(completed.stdout)

    assert payload["applied"] is True
    assert payload["before"]["current_branch"] == "master"
    assert payload["plan"]["action"] == "switch_then_fast_forward"
    assert payload["after"]["current_branch"] == "feature/demo"
    assert payload["after"]["upstream"] == "origin/feature/demo"
    assert _git(node, "status", "--short") == ""


def test_apollo_courier_branch_sync_refuses_dirty_tree(tmp_path: Path):
    remote = _seed_remote(tmp_path)
    node = tmp_path / "node"
    _git(tmp_path, "clone", str(remote), str(node))
    (node / "local.txt").write_text("dirty\n", encoding="utf-8")

    completed = _run_courier(
        "branch-sync",
        "--repo",
        str(node),
        "--target-branch",
        "feature/demo",
        "--apply",
        "--json",
    )
    payload = json.loads(completed.stdout)

    assert payload["applied"] is False
    assert payload["plan"]["action"] == "stop_dirty_tree"
    assert payload["after"] is None
    assert payload["executed"] == []
    assert _git(node, "branch", "--show-current") == "master"
