from __future__ import annotations

from foxclaw.nodes.branch_sync import BranchSyncState, plan_branch_sync


def _state(**overrides):
    values = {
        "repo_path": "C:/repo",
        "current_branch": "master",
        "head": "abc123",
        "head_subject": "test",
        "upstream": "origin/master",
        "ahead": 0,
        "behind": 0,
        "dirty": False,
        "changed_files": (),
        "target_branch": "feature/demo",
        "target_local_exists": False,
        "target_remote_exists": True,
        "remote": "origin",
    }
    values.update(overrides)
    return BranchSyncState(**values)


def test_branch_sync_plan_refuses_dirty_tree():
    plan = plan_branch_sync(
        _state(
            dirty=True,
            changed_files=(" M tools/apollo_mesh.py",),
        )
    )

    assert plan.action == "stop_dirty_tree"
    assert plan.safe_to_apply is False
    assert plan.commands == ()


def test_branch_sync_plan_tracks_remote_target_branch():
    plan = plan_branch_sync(_state())

    assert plan.action == "switch_then_fast_forward"
    assert plan.safe_to_apply is True
    assert plan.commands == (
        ("git", "switch", "-c", "feature/demo", "--track", "origin/feature/demo"),
        ("git", "pull", "--ff-only"),
    )


def test_branch_sync_plan_never_pushes_or_rebases():
    plan = plan_branch_sync(_state(current_branch="feature/demo", target_local_exists=True, ahead=2))

    assert plan.action == "local_commits_not_pushed"
    assert plan.safe_to_apply is False
    assert plan.commands == ()
