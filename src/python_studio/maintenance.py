from __future__ import annotations

import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .ai_jobs import ai_usage_summary
from .backup import list_learning_backups
from .catalog import find_exercise, load_exercises
from .knowledge_graph import (
    knowledge_graph_summary,
    refresh_student_skill_state,
    sync_knowledge_graph,
)
from .store import (
    attempt_counts_for_exercises,
    cleanup_attempts_before,
    cleanup_mastered_mistakes,
    learning_history_summary,
    list_mistakes,
)
from .workspace import SubjectWorkspace, get_workspace


def _resolved_workspace(workspace: SubjectWorkspace | None = None) -> SubjectWorkspace:
    return workspace or get_workspace()


def _generated_exercises(
    workspace: SubjectWorkspace | None = None,
) -> list[dict[str, Any]]:
    resolved = _resolved_workspace(workspace)
    attempt_counts = attempt_counts_for_exercises()
    exercises = []
    for meta in load_exercises(
        resolved.exercises_dir,
        include_inactive=True,
    ):
        if not meta.get("generated"):
            continue
        directory = Path(meta["directory"])
        exercises.append(
            {
                "id": meta.get("id", directory.name),
                "title": meta.get("title", directory.name),
                "knowledge_point": (meta.get("concepts") or [""])[0],
                "active": bool(meta.get("active", True)),
                "archived": bool(meta.get("archived", False)),
                "scope": meta.get("scope", "tutoring"),
                "stage": meta.get("stage", ""),
                "level_id": meta.get("level_id", ""),
                "relative_path": meta.get("relative_path", ""),
                "created_at": datetime.fromtimestamp(
                    (directory / "meta.json").stat().st_mtime
                ).astimezone().isoformat(timespec="seconds"),
                "attempts": attempt_counts.get(meta.get("id"), 0),
                "directory": str(directory),
            }
        )
    return exercises


def maintenance_summary(
    workspace: SubjectWorkspace | None = None,
) -> dict[str, Any]:
    resolved = _resolved_workspace(workspace)
    sync_knowledge_graph()
    refresh_student_skill_state()
    graph = knowledge_graph_summary()
    history = learning_history_summary()
    mistakes = list_mistakes(active_only=False)
    generated = _generated_exercises(resolved)
    database_size = (
        resolved.database_file.stat().st_size
        if resolved.database_file.exists()
        else 0
    )
    cutoff_30_days = (
        datetime.now().astimezone() - timedelta(days=30)
    ).isoformat(timespec="seconds")
    return {
        "history": history,
        "mistakes": {
            "active": sum(1 for item in mistakes if item["status"] == "active"),
            "mastered": sum(1 for item in mistakes if item["status"] == "mastered"),
        },
        "generated_exercises": {
            "total": len(generated),
            "active": sum(1 for item in generated if item["active"]),
            "archived": sum(1 for item in generated if item["archived"]),
        },
        "database_size_bytes": database_size,
        "cleanup_policy": {
            "records_before": cutoff_30_days,
            "retention_days": 30,
        },
        "generated_items": generated,
        "backups": list_learning_backups(workspace=resolved),
        "ai_usage": ai_usage_summary(),
        "knowledge_graph": graph,
        "workspace": {
            "id": resolved.id,
            "title": resolved.title,
        },
    }


def cleanup_data(scope: str) -> dict[str, Any]:
    if scope == "records_30d":
        cutoff = (
            datetime.now().astimezone() - timedelta(days=30)
        ).isoformat(timespec="seconds")
        deleted = cleanup_attempts_before(cutoff)
        return {"scope": scope, "deleted": deleted, "cutoff": cutoff}
    if scope == "mastered_mistakes":
        deleted = cleanup_mastered_mistakes()
        return {"scope": scope, "deleted": deleted}
    raise ValueError("Unsupported cleanup scope.")


def update_generated_exercise(
    exercise_id: str,
    action: str,
    *,
    workspace: SubjectWorkspace | None = None,
) -> dict[str, Any]:
    resolved = _resolved_workspace(workspace)
    root = resolved.exercises_dir.resolve()
    exercise = find_exercise(
        exercise_id,
        resolved.exercises_dir,
        include_inactive=True,
    )
    candidate = Path(exercise["directory"]).resolve()
    if not candidate.is_relative_to(root) or candidate == root:
        raise ValueError("Invalid generated exercise id.")
    if not exercise.get("generated"):
        raise ValueError("Only generated exercises can be managed here.")
    meta_path = candidate / "meta.json"
    if not meta_path.exists():
        raise KeyError("Generated exercise not found.")

    if action in {"archive", "restore"}:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["active"] = action == "restore"
        meta["archived"] = action == "archive"
        meta_path.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return {"id": exercise_id, "action": action}
    if action == "delete":
        shutil.rmtree(candidate)
        return {"id": exercise_id, "action": action}
    raise ValueError("Unsupported generated exercise action.")


def archive_practiced_generated_exercises(
    *,
    workspace: SubjectWorkspace | None = None,
) -> int:
    resolved = _resolved_workspace(workspace)
    attempt_counts = attempt_counts_for_exercises()
    archived = 0
    for item in _generated_exercises(resolved):
        if not item["active"] or item["attempts"] <= 0:
            continue
        update_generated_exercise(item["id"], "archive", workspace=resolved)
        archived += 1
    return archived
