from __future__ import annotations

import json
import re
from contextvars import ContextVar, Token
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .paths import (
    CURRICULUM_DIR,
    DATA_DIR,
    DATABASE_FILE,
    EXERCISES_DIR,
    PROJECT_ROOT,
    PROJECTS_DIR,
    PROGRESS_FILE,
    SUBJECT_REGISTRY,
    SUBJECTS_DIR,
)


DEFAULT_SUBJECT_ID = "python"


@dataclass(frozen=True)
class SubjectWorkspace:
    id: str
    slug: str
    title: str
    mode: str
    root: Path
    curriculum_dir: Path
    exercises_dir: Path
    projects_dir: Path
    database_file: Path
    progress_file: Path
    journal_dir: Path
    is_default: bool = False


def _default_workspace() -> SubjectWorkspace:
    return SubjectWorkspace(
        id=DEFAULT_SUBJECT_ID,
        slug=DEFAULT_SUBJECT_ID,
        title="Python Studio",
        mode="programming",
        root=PROJECT_ROOT,
        curriculum_dir=CURRICULUM_DIR,
        exercises_dir=EXERCISES_DIR,
        projects_dir=PROJECTS_DIR,
        database_file=DATABASE_FILE,
        progress_file=PROGRESS_FILE,
        journal_dir=PROJECT_ROOT / "journal",
        is_default=True,
    )


_current_subject_id: ContextVar[str] = ContextVar(
    "current_subject_id",
    default=DEFAULT_SUBJECT_ID,
)


def _read_registry() -> list[dict[str, Any]]:
    if not SUBJECT_REGISTRY.exists():
        return []
    try:
        payload = json.loads(SUBJECT_REGISTRY.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return list(payload.get("subjects") or [])


def _write_registry(subjects: list[dict[str, Any]]) -> None:
    SUBJECTS_DIR.mkdir(parents=True, exist_ok=True)
    temporary = SUBJECT_REGISTRY.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps({"subjects": subjects}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(SUBJECT_REGISTRY)


def _slug(value: str, fallback: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug[:60] or fallback


def _workspace_from_record(record: dict[str, Any]) -> SubjectWorkspace:
    root = (SUBJECTS_DIR / str(record["slug"])).resolve()
    return SubjectWorkspace(
        id=str(record["id"]),
        slug=str(record["slug"]),
        title=str(record["title"]),
        mode=str(record.get("mode", "programming")),
        root=root,
        curriculum_dir=root / "curriculum",
        exercises_dir=root / "exercises",
        projects_dir=root / "projects",
        database_file=root / "data" / "study.db",
        progress_file=root / "progress.json",
        journal_dir=root / "journal",
    )


def list_workspaces() -> list[SubjectWorkspace]:
    return [_default_workspace(), *(_workspace_from_record(item) for item in _read_registry())]


def get_workspace(subject_id: str | None = None) -> SubjectWorkspace:
    resolved_id = subject_id or _current_subject_id.get()
    if resolved_id == DEFAULT_SUBJECT_ID:
        return _default_workspace()
    for record in _read_registry():
        if str(record.get("id")) == str(resolved_id) or str(record.get("slug")) == str(
            resolved_id
        ):
            return _workspace_from_record(record)
    raise KeyError(f"Unknown subject: {resolved_id}")


def set_current_subject(subject_id: str) -> Token[str]:
    get_workspace(subject_id)
    return _current_subject_id.set(str(subject_id))


def reset_current_subject(token: Token[str]) -> None:
    _current_subject_id.reset(token)


def create_subject_workspace(
    *,
    title: str,
    mode: str,
    blueprint: dict[str, Any],
    source_material: str,
) -> SubjectWorkspace:
    existing = _read_registry()
    next_number = len(existing) + 1
    subject_id = f"subject-{next_number}"
    while any(item["id"] == subject_id for item in existing):
        next_number += 1
        subject_id = f"subject-{next_number}"
    slug_base = _slug(title, subject_id)
    slug = slug_base
    suffix = 2
    while any(item["slug"] == slug for item in existing):
        slug = f"{slug_base}-{suffix}"
        suffix += 1

    root = (SUBJECTS_DIR / slug).resolve()
    for directory in (
        root / "curriculum",
        root / "exercises",
        root / "projects",
        root / "data",
        root / "journal",
    ):
        directory.mkdir(parents=True, exist_ok=True)
    (root / "progress.json").write_text(
        json.dumps(
            {
                "version": 1,
                "completed": [],
                "attempts": {},
                "last_exercise": None,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    subject_manifest = {
        "id": subject_id,
        "slug": slug,
        "title": title,
        "mode": mode,
        "blueprint": blueprint,
        "source_material": source_material[:50000],
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    (root / "subject.json").write_text(
        json.dumps(subject_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    existing.append(
        {
            "id": subject_id,
            "slug": slug,
            "title": title,
            "mode": mode,
            "created_at": subject_manifest["created_at"],
        }
    )
    _write_registry(existing)
    return _workspace_from_record(existing[-1])


def workspace_payload(workspace: SubjectWorkspace) -> dict[str, Any]:
    payload = asdict(workspace)
    for key in (
        "root",
        "curriculum_dir",
        "exercises_dir",
        "projects_dir",
        "database_file",
        "progress_file",
        "journal_dir",
    ):
        payload[key] = str(payload[key])
    return payload

