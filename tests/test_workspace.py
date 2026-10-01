from __future__ import annotations

from python_studio import workspace
from python_studio.store import list_learning_attempts, record_learning_attempt


def test_subject_workspaces_are_parallel(tmp_path, monkeypatch) -> None:
    subjects_dir = tmp_path / "subjects"
    registry = subjects_dir / "registry.json"
    monkeypatch.setattr(workspace, "SUBJECTS_DIR", subjects_dir)
    monkeypatch.setattr(workspace, "SUBJECT_REGISTRY", registry)

    first = workspace.create_subject_workspace(
        title="Data Structures",
        mode="programming",
        blueprint={"mode": "programming", "modules": []},
        source_material="stack queue",
    )
    second = workspace.create_subject_workspace(
        title="Optimization",
        mode="conceptual",
        blueprint={"mode": "conceptual", "modules": []},
        source_material="KKT",
    )

    assert first.root != second.root
    assert first.database_file != second.database_file
    assert first.root.exists()
    assert second.root.exists()
    assert len(workspace.list_workspaces()) == 3

    attempt = {
        "exercise_id": "example",
        "checked_at": "2026-10-01T12:00:00+08:00",
        "passed": True,
        "duration_seconds": 1,
        "output": "ok",
        "code_snapshot": "answer",
    }
    exercise = {"title": "Example", "concepts": ["concept"]}
    token = workspace.set_current_subject(first.id)
    try:
        record_learning_attempt(attempt, exercise)
        assert len(list_learning_attempts()) == 1
    finally:
        workspace.reset_current_subject(token)
    token = workspace.set_current_subject(second.id)
    try:
        assert list_learning_attempts() == []
    finally:
        workspace.reset_current_subject(token)
