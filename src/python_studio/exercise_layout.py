from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .workspace import SubjectWorkspace, get_workspace


VALID_SCOPES = {"course", "workshop", "tutoring"}
SCOPE_DIRECTORIES = {
    "course": "",
    "workshop": "workshop",
    "tutoring": "ai",
}


@dataclass(frozen=True)
class ExerciseLocation:
    scope: str
    directory: Path
    relative_directory: str
    course_id: str
    course_slug: str
    course_title: str
    module_id: str
    module_number: int | None
    module_title: str
    level_index: int | None
    level_id: str


def normalize_scope(scope: str | None) -> str:
    value = str(scope or "").strip().lower()
    return value if value in VALID_SCOPES else "tutoring"


def scope_for_exercise(exercise: dict[str, Any]) -> str:
    explicit = str(exercise.get("scope") or "").strip().lower()
    if explicit in VALID_SCOPES:
        return explicit
    origin = str(exercise.get("origin") or "").strip().lower()
    stage = str(exercise.get("stage") or "").strip()
    if origin == "workshop" or stage == "workshop":
        return "workshop"
    if stage == "ai_practice":
        return "tutoring"
    return "course"


def scope_directory(
    scope: str,
    *,
    workspace: SubjectWorkspace | None = None,
) -> Path:
    resolved = workspace or get_workspace()
    relative = SCOPE_DIRECTORIES[normalize_scope(scope)]
    return resolved.exercises_dir / relative if relative else resolved.exercises_dir


def _read_roadmap(workspace: SubjectWorkspace) -> dict[str, Any]:
    path = workspace.curriculum_dir / "roadmap.json"
    if not path.exists():
        return {"stages": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"stages": []}
    return payload if isinstance(payload, dict) else {"stages": []}


def stage_metadata(
    stage_id: str,
    *,
    workspace: SubjectWorkspace | None = None,
) -> dict[str, Any]:
    resolved = workspace or get_workspace()
    for stage in _read_roadmap(resolved).get("stages", []):
        if str(stage.get("id")) != stage_id:
            continue
        try:
            module_number = int(stage.get("module"))
        except (TypeError, ValueError):
            module_number = None
        return {
            "module_id": stage_id,
            "module_number": module_number,
            "module_title": str(stage.get("title") or stage_id),
        }
    return {
        "module_id": stage_id,
        "module_number": None,
        "module_title": stage_id,
    }


def next_level_index(
    stage_id: str,
    *,
    workspace: SubjectWorkspace | None = None,
) -> int:
    from .catalog import load_exercises

    resolved = workspace or get_workspace()
    indexes = []
    for exercise in load_exercises(
        resolved.exercises_dir,
        include_inactive=True,
        origin="course",
    ):
        if str(exercise.get("stage")) != stage_id:
            continue
        try:
            indexes.append(int(exercise.get("level_index") or 0))
        except (TypeError, ValueError):
            indexes.append(0)
    return max(indexes, default=0) + 1


def build_level_id(
    scope: str,
    stage_id: str,
    level_index: int | None,
) -> str:
    normalized = normalize_scope(scope)
    if normalized == "course" and level_index is not None:
        return f"{stage_id}-L{level_index:02d}"
    if normalized == "course":
        return stage_id
    if normalized == "workshop":
        return "workshop"
    return "tutoring"


def resolve_exercise_location(
    *,
    scope: str,
    stage: str,
    workspace: SubjectWorkspace | None = None,
    level_index: int | None = None,
    compute_next_level: bool = True,
) -> ExerciseLocation:
    resolved = workspace or get_workspace()
    normalized = normalize_scope(scope)
    directory = scope_directory(normalized, workspace=resolved)
    relative_directory = (
        directory.relative_to(resolved.exercises_dir).as_posix()
        if directory != resolved.exercises_dir
        else ""
    )
    if normalized == "course":
        module = stage_metadata(stage, workspace=resolved)
        if level_index is None and compute_next_level:
            level_index = next_level_index(stage, workspace=resolved)
    else:
        module = {
            "module_id": stage or ("workshop" if normalized == "workshop" else "ai_practice"),
            "module_number": None,
            "module_title": (
                "创造工坊"
                if normalized == "workshop"
                else "AI 专属补练"
            ),
        }
    return ExerciseLocation(
        scope=normalized,
        directory=directory,
        relative_directory=relative_directory,
        course_id=resolved.id,
        course_slug=resolved.slug,
        course_title=resolved.title,
        module_id=str(module["module_id"]),
        module_number=module["module_number"],
        module_title=str(module["module_title"]),
        level_index=level_index,
        level_id=build_level_id(normalized, str(module["module_id"]), level_index),
    )


def enrich_exercise_metadata(
    exercise: dict[str, Any],
    *,
    workspace: SubjectWorkspace | None = None,
    relative_path: str = "",
) -> dict[str, Any]:
    resolved = workspace or get_workspace()
    scope = scope_for_exercise(exercise)
    stage = str(exercise.get("stage") or "")
    raw_level = exercise.get("level_index")
    if str(raw_level or "").isdigit():
        level_index = int(raw_level)
    else:
        level_index = None
    location = resolve_exercise_location(
        scope=scope,
        stage=stage,
        workspace=resolved,
        level_index=level_index,
        compute_next_level=False,
    )
    exercise["subject_id"] = location.course_id
    exercise["scope"] = location.scope
    exercise["storage_scope"] = location.scope
    exercise["origin"] = "workshop" if location.scope == "workshop" else "course"
    exercise["course_id"] = location.course_id
    exercise["course_slug"] = location.course_slug
    exercise["course_title"] = location.course_title
    exercise["module_id"] = location.module_id
    exercise["module_number"] = location.module_number
    exercise["module_title"] = location.module_title
    exercise["level_index"] = location.level_index
    exercise["level_id"] = location.level_id
    exercise["relative_path"] = relative_path
    exercise["storage_path"] = relative_path
    return exercise


def normalize_workspace_exercise_metadata(
    workspace: SubjectWorkspace | None = None,
) -> dict[str, int]:
    resolved = workspace or get_workspace()
    entries: list[tuple[Path, dict[str, Any], str]] = []
    for meta_path in sorted(resolved.exercises_dir.rglob("meta.json")):
        try:
            payload = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(payload, dict):
            continue
        relative = meta_path.parent.relative_to(resolved.exercises_dir).as_posix()
        entries.append((meta_path, payload, relative))

    course_groups: dict[str, list[tuple[Path, dict[str, Any], str]]] = {}
    for entry in entries:
        payload = entry[1]
        if scope_for_exercise(payload) != "course":
            continue
        if not payload.get("active", True):
            continue
        stage = str(payload.get("stage") or "unassigned")
        course_groups.setdefault(stage, []).append(entry)

    level_indexes: dict[Path, int | None] = {}
    for stage_entries in course_groups.values():
        ordered = sorted(
            stage_entries,
            key=lambda item: (
                int(item[1].get("order") or 0),
                str(item[1].get("id") or item[0].parent.name),
            ),
        )
        for index, (meta_path, _, _) in enumerate(ordered, start=1):
            level_indexes[meta_path] = index

    updated = 0
    for meta_path, payload, relative in entries:
        level_index = level_indexes.get(meta_path)
        enriched = enrich_exercise_metadata(
            payload,
            workspace=resolved,
            relative_path=relative,
        )
        enriched["level_index"] = (
            level_index if enriched.get("scope") == "course" else None
        )
        enriched["level_id"] = build_level_id(
            str(enriched.get("scope")),
            str(enriched.get("module_id")),
            enriched.get("level_index"),
        )
        serialized = json.dumps(enriched, ensure_ascii=False, indent=2) + "\n"
        if meta_path.read_text(encoding="utf-8") == serialized:
            continue
        temporary = meta_path.with_suffix(".json.tmp")
        temporary.write_text(serialized, encoding="utf-8")
        temporary.replace(meta_path)
        updated += 1
    return {"exercises": len(entries), "updated": updated}
