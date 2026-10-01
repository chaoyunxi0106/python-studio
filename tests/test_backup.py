from __future__ import annotations

import json
import sqlite3
import zipfile
from pathlib import Path

from python_studio import backup
from python_studio.workspace import SubjectWorkspace


def make_workspace(root: Path, subject_id: str = "python") -> SubjectWorkspace:
    root.mkdir(parents=True, exist_ok=True)
    for directory in (
        root / "curriculum",
        root / "exercises",
        root / "projects",
        root / "data",
        root / "journal",
    ):
        directory.mkdir(parents=True, exist_ok=True)
    workspace = SubjectWorkspace(
        id=subject_id,
        slug=subject_id,
        title=subject_id,
        mode="programming",
        root=root,
        curriculum_dir=root / "curriculum",
        exercises_dir=root / "exercises",
        projects_dir=root / "projects",
        database_file=root / "data" / "study.db",
        progress_file=root / "progress.json",
        journal_dir=root / "journal",
        is_default=subject_id == "python",
    )
    workspace.progress_file.write_text("{}\n", encoding="utf-8")
    return workspace


def test_backup_and_restore_round_trip(tmp_path) -> None:
    workspace = make_workspace(tmp_path / "project")
    connection = sqlite3.connect(workspace.database_file)
    connection.execute("CREATE TABLE sample (value TEXT)")
    connection.execute("INSERT INTO sample VALUES ('before')")
    connection.commit()
    connection.close()
    (workspace.journal_dir / "2026-10-01.md").write_text(
        "before journal\n",
        encoding="utf-8",
    )

    created = backup.create_learning_backup("test", workspace=workspace)
    assert created["size_bytes"] > 0

    connection = sqlite3.connect(workspace.database_file)
    connection.execute("UPDATE sample SET value = 'after'")
    connection.commit()
    connection.close()
    (workspace.journal_dir / "2026-10-01.md").write_text(
        "after journal\n",
        encoding="utf-8",
    )

    restored = backup.restore_learning_backup(created["name"], workspace=workspace)
    assert restored["restored"] == created["name"]
    assert restored["journal_files"] == 1
    connection = sqlite3.connect(workspace.database_file)
    try:
        value = connection.execute("SELECT value FROM sample").fetchone()[0]
    finally:
        connection.close()
    assert value == "before"
    assert (workspace.journal_dir / "2026-10-01.md").read_text(
        encoding="utf-8"
    ) == "before journal\n"


def test_backup_manifest_excludes_secrets(tmp_path) -> None:
    workspace = make_workspace(tmp_path / "project", "subject-1")
    workspace.root.joinpath(".env").write_text("SECRET=value", encoding="utf-8")
    connection = sqlite3.connect(workspace.database_file)
    connection.execute("CREATE TABLE example (id INTEGER)")
    connection.commit()
    connection.close()

    created = backup.create_learning_backup("manifest", workspace=workspace)

    with zipfile.ZipFile(created["path"]) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert ".env" not in archive.namelist()
        assert "study.db" in manifest["contains"]
        assert manifest["workspace"]["id"] == "subject-1"


def test_backup_is_scoped_to_workspace(tmp_path) -> None:
    first = make_workspace(tmp_path / "first", "subject-1")
    second = make_workspace(tmp_path / "second", "subject-2")
    sqlite3.connect(first.database_file).close()
    sqlite3.connect(second.database_file).close()

    created = backup.create_learning_backup("first", workspace=first)

    assert backup.list_learning_backups(workspace=first)
    assert backup.list_learning_backups(workspace=second) == []
    try:
        backup.restore_learning_backup(created["name"], workspace=second)
    except KeyError:
        pass
    else:
        raise AssertionError("Backups must not leak across subject workspaces")


def test_restore_rejects_workspace_mismatch(tmp_path) -> None:
    first = make_workspace(tmp_path / "first", "subject-1")
    second = make_workspace(tmp_path / "second", "subject-2")
    sqlite3.connect(first.database_file).close()
    sqlite3.connect(second.database_file).close()
    created = backup.create_learning_backup("first", workspace=first)

    # Copy the archive into the second workspace's backup directory to test
    # manifest validation rather than path validation.
    target_dir = backup.backup_dir(second)
    target_dir.mkdir(parents=True, exist_ok=True)
    archive_path = backup.backup_file_path(created["name"], workspace=first)
    (target_dir / archive_path.name).write_bytes(archive_path.read_bytes())

    try:
        backup.restore_learning_backup(created["name"], workspace=second)
    except ValueError:
        pass
    else:
        raise AssertionError("A backup from another workspace must be rejected")


def test_delete_backup_rejects_path_traversal(tmp_path) -> None:
    workspace = make_workspace(tmp_path / "project")
    backup_dir = backup.backup_dir(workspace)
    backup_dir.mkdir(parents=True, exist_ok=True)

    try:
        backup.delete_learning_backup("../outside.zip", workspace=workspace)
    except ValueError:
        pass
    else:
        raise AssertionError("Path traversal must be rejected")

    sample = backup_dir / "sample.zip"
    sample.write_bytes(b"zip")
    assert backup.delete_learning_backup("sample.zip", workspace=workspace)
    assert not sample.exists()
