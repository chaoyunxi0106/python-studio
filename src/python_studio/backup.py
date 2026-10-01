from __future__ import annotations

import json
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

from .workspace import SubjectWorkspace, get_workspace


FORMAT_VERSION = 2
BACKUP_FORMAT = "python-studio-learning-backup"


def _timestamp() -> str:
    return datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")


def _resolved_workspace(workspace: SubjectWorkspace | None = None) -> SubjectWorkspace:
    return workspace or get_workspace()


def backup_dir(workspace: SubjectWorkspace | None = None) -> Path:
    return _resolved_workspace(workspace).root / "data" / "backups"


def _safe_backup_path(
    name: str,
    *,
    workspace: SubjectWorkspace | None = None,
) -> Path:
    root = backup_dir(workspace).resolve()
    candidate = (root / name).resolve()
    if not candidate.is_relative_to(root) or candidate == root:
        raise ValueError("Invalid backup name.")
    if candidate.suffix.lower() != ".zip":
        raise ValueError("Invalid backup file.")
    return candidate


def backup_file_path(
    name: str,
    *,
    workspace: SubjectWorkspace | None = None,
) -> Path:
    """Return a validated backup path for downloads and maintenance handlers."""
    path = _safe_backup_path(name, workspace=workspace)
    if not path.exists():
        raise KeyError("Backup not found.")
    return path


def _safe_label(label: str) -> str:
    return "".join(
        character
        for character in label
        if character.isalnum() or character in {"-", "_"}
    )[:40] or "manual"


def _archive_member_name(name: str) -> str:
    """Normalize and validate a ZIP member path before restoring it."""
    pure = PurePosixPath(name)
    if pure.is_absolute() or ".." in pure.parts:
        raise ValueError(f"Unsafe backup member: {name}")
    return pure.as_posix()


def _write_journal_files(
    archive: zipfile.ZipFile,
    names: set[str],
    journal_dir: Path,
) -> int:
    restored = 0
    journal_dir.mkdir(parents=True, exist_ok=True)
    for member in sorted(names):
        normalized = _archive_member_name(member)
        if not normalized.startswith("journal/") or member.endswith("/"):
            continue
        relative = PurePosixPath(normalized).relative_to("journal")
        target = (journal_dir / Path(*relative.parts)).resolve()
        if not target.is_relative_to(journal_dir.resolve()):
            raise ValueError(f"Unsafe journal member: {member}")
        target.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(member) as source, target.open("wb") as destination:
            shutil.copyfileobj(source, destination)
        restored += 1
    return restored


def create_learning_backup(
    label: str = "manual",
    *,
    workspace: SubjectWorkspace | None = None,
) -> dict[str, Any]:
    resolved = _resolved_workspace(workspace)
    target_dir = backup_dir(resolved)
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_label = _safe_label(label)
    prefix = (
        "python-studio"
        if resolved.is_default
        else f"python-studio-{_safe_label(resolved.slug)}"
    )
    backup_name = f"{prefix}-{_timestamp()}-{safe_label}.zip"
    backup_path = _safe_backup_path(backup_name, workspace=resolved)
    created_at = datetime.now().astimezone().isoformat(timespec="seconds")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db = Path(temp_dir) / "study.db"
        source = sqlite3.connect(resolved.database_file)
        target = sqlite3.connect(temp_db)
        try:
            source.backup(target)
        finally:
            target.close()
            source.close()

        contains = ["study.db", "progress.json", "journal"]
        subject_manifest = resolved.root / "subject.json"
        if subject_manifest.exists():
            contains.append("subject.json")
        manifest = {
            "format": BACKUP_FORMAT,
            "format_version": FORMAT_VERSION,
            "created_at": created_at,
            "label": safe_label,
            "workspace": {
                "id": resolved.id,
                "slug": resolved.slug,
                "title": resolved.title,
                "mode": resolved.mode,
            },
            "contains": contains,
        }
        with zipfile.ZipFile(
            backup_path,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as archive:
            archive.writestr(
                "manifest.json",
                json.dumps(manifest, ensure_ascii=False, indent=2),
            )
            archive.write(temp_db, "study.db")
            if resolved.progress_file.exists():
                archive.write(resolved.progress_file, "progress.json")
            if resolved.journal_dir.exists():
                for path in resolved.journal_dir.rglob("*"):
                    if path.is_file():
                        archive.write(
                            path,
                            str(path.relative_to(resolved.root)),
                        )
            if subject_manifest.exists():
                archive.write(subject_manifest, "subject.json")

    return {
        "name": backup_path.name,
        "path": str(backup_path),
        "created_at": created_at,
        "size_bytes": backup_path.stat().st_size,
        "workspace_id": resolved.id,
        "workspace_title": resolved.title,
    }


def list_learning_backups(
    *,
    workspace: SubjectWorkspace | None = None,
) -> list[dict[str, Any]]:
    target_dir = backup_dir(workspace)
    if not target_dir.exists():
        return []
    backups = []
    for path in sorted(target_dir.glob("*.zip"), reverse=True):
        backups.append(
            {
                "name": path.name,
                "created_at": datetime.fromtimestamp(
                    path.stat().st_mtime
                ).astimezone().isoformat(timespec="seconds"),
                "size_bytes": path.stat().st_size,
            }
        )
    return backups


def delete_learning_backup(
    name: str,
    *,
    workspace: SubjectWorkspace | None = None,
) -> bool:
    backup_path = _safe_backup_path(name, workspace=workspace)
    if not backup_path.exists():
        raise KeyError("Backup not found.")
    backup_path.unlink()
    return True


def restore_learning_backup(
    name: str,
    *,
    workspace: SubjectWorkspace | None = None,
) -> dict[str, Any]:
    resolved = _resolved_workspace(workspace)
    backup_path = _safe_backup_path(name, workspace=resolved)
    if not backup_path.exists():
        raise KeyError("Backup not found.")

    pre_restore = create_learning_backup("pre-restore", workspace=resolved)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        with zipfile.ZipFile(backup_path) as archive:
            names = {
                _archive_member_name(item)
                for item in archive.namelist()
                if item and not item.endswith("/")
            }
            if "manifest.json" not in names or "study.db" not in names:
                raise ValueError("Backup is missing required files.")
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
            if manifest.get("format") != BACKUP_FORMAT:
                raise ValueError("Unsupported backup format.")
            manifest_workspace = manifest.get("workspace") or {}
            if manifest_workspace.get("id") not in {None, resolved.id}:
                raise ValueError("Backup belongs to a different subject workspace.")

            extracted_db = temp_dir_path / "study.db"
            with archive.open("study.db") as source, extracted_db.open("wb") as target:
                shutil.copyfileobj(source, target)

            verification = sqlite3.connect(extracted_db)
            try:
                integrity = verification.execute("PRAGMA integrity_check").fetchone()[0]
            finally:
                verification.close()
            if integrity != "ok":
                raise ValueError("Backup database failed integrity check.")

            resolved.database_file.parent.mkdir(parents=True, exist_ok=True)
            for suffix in ("-wal", "-shm"):
                sidecar = resolved.database_file.with_name(
                    resolved.database_file.name + suffix
                )
                if sidecar.exists():
                    sidecar.unlink()
            shutil.copy2(
                resolved.database_file,
                resolved.database_file.with_suffix(".db.before-restore"),
            )
            shutil.copy2(extracted_db, resolved.database_file)

            if "progress.json" in names:
                with archive.open("progress.json") as source:
                    progress = json.loads(source.read().decode("utf-8"))
                resolved.progress_file.write_text(
                    json.dumps(progress, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )

            restored_journal = _write_journal_files(
                archive,
                names,
                resolved.journal_dir,
            )

            if "subject.json" in names:
                with archive.open("subject.json") as source:
                    subject = json.loads(source.read().decode("utf-8"))
                (resolved.root / "subject.json").write_text(
                    json.dumps(subject, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )

    return {
        "restored": backup_path.name,
        "pre_restore_backup": pre_restore["name"],
        "workspace_id": resolved.id,
        "journal_files": restored_journal,
    }
