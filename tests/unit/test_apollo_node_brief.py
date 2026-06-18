from __future__ import annotations

from datetime import UTC, datetime

import pytest

from foxclaw.nodes.apollo import (
    ApolloNodeBrief,
    GitSnapshot,
    NodeAuthorityLocks,
    build_node_brief,
    dumps_json,
    render_markdown,
)


def _git(repo_path: str) -> GitSnapshot:
    return GitSnapshot(
        repo_path=repo_path,
        branch="master",
        head="abc1234",
        head_subject="Fixture node handoff",
        upstream="origin/master",
        ahead=1,
        behind=0,
        dirty=False,
        changed_files=(),
    )


def test_apollo_node_brief_renders_repo_truth_and_next_request(tmp_path):
    (tmp_path / "VERSION").write_text("9.9.9\n", encoding="utf-8")
    brief = build_node_brief(
        repo_path=tmp_path,
        node_id="A1",
        peer_node="A2",
        current_slice="node coordination",
        next_request="pull and run inventory",
        blockers=("none",),
        notes=("old repo is reference-only",),
        generated_at=datetime(2026, 6, 18, tzinfo=UTC),
        git=_git(str(tmp_path)),
    )
    markdown = render_markdown(brief)
    payload = dumps_json(brief)

    assert isinstance(brief, ApolloNodeBrief)
    assert brief.protocol == "apollo_node_brief_v1"
    assert brief.version == "9.9.9"
    assert brief.authority.can_submit_order is False
    assert "From: `A1`" in markdown
    assert "To: `A2`" in markdown
    assert "pull and run inventory" in markdown
    assert '"protocol": "apollo_node_brief_v1"' in payload


def test_apollo_brief_reports_dirty_files_without_granting_authority(tmp_path):
    dirty_git = GitSnapshot(
        repo_path=str(tmp_path),
        branch="master",
        head="abc1234",
        head_subject="Dirty fixture",
        upstream="origin/master",
        ahead=0,
        behind=1,
        dirty=True,
        changed_files=(" M docs/example.md", "?? scratch.txt"),
    )
    brief = build_node_brief(
        repo_path=tmp_path,
        node_id="A2",
        peer_node="A1",
        git=dirty_git,
    )
    markdown = render_markdown(brief)

    assert brief.git.dirty is True
    assert "Tree: `dirty`" in markdown
    assert "` M docs/example.md`" in markdown
    assert brief.authority.live_execution_allowed is False


def test_node_authority_locks_reject_any_true_flag():
    with pytest.raises(ValueError, match="cannot grant authority"):
        NodeAuthorityLocks(can_move_funds=True)
