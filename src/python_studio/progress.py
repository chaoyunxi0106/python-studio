from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any


def default_progress() -> dict[str, Any]:
    return {
        "version": 1,
        "completed": [],
        "attempts": {},
        "last_exercise": None,
    }


def load_progress(path: Path) -> dict[str, Any]:
    if not path.exists():
        return default_progress()

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default_progress()

    progress = default_progress()
    if isinstance(payload, dict):
        progress.update(payload)
    if not isinstance(progress.get("completed"), list):
        progress["completed"] = []
    if not isinstance(progress.get("attempts"), dict):
        progress["attempts"] = {}
    return progress


def save_progress(path: Path, progress: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(progress, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(path)


def record_attempt(
    progress: dict[str, Any],
    exercise_id: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    attempts = progress.setdefault("attempts", {})
    current = attempts.setdefault(
        exercise_id,
        {
            "attempts": 0,
            "passed": False,
            "last_checked": None,
            "duration_seconds": 0,
            "last_output": "",
        },
    )

    current["attempts"] = int(current.get("attempts", 0)) + 1
    current["passed"] = bool(result.get("passed"))
    current["last_checked"] = result.get("checked_at")
    current["duration_seconds"] = result.get("duration_seconds", 0)
    current["last_output"] = result.get("output", "")

    if current["passed"] and exercise_id not in progress["completed"]:
        progress["completed"].append(exercise_id)

    progress["last_exercise"] = exercise_id
    return progress


def set_last_exercise(progress: dict[str, Any], exercise_id: str) -> None:
    progress["last_exercise"] = exercise_id


def progress_stats(
    progress: dict[str, Any],
    exercises: list[dict[str, Any]],
) -> dict[str, Any]:
    completed = set(progress.get("completed", []))
    completed_exercises = [item for item in exercises if item["id"] in completed]
    practice_minutes = sum(int(item.get("minutes", 0)) for item in completed_exercises)
    total_minutes = sum(int(item.get("minutes", 0)) for item in exercises)
    today = date.today().isoformat()
    visible_ids = {item["id"] for item in exercises}
    today_passed = sum(
        1
        for exercise_id, attempt in progress.get("attempts", {}).items()
        if exercise_id in visible_ids
        and attempt.get("passed")
        and str(attempt.get("last_checked", "")).startswith(today)
    )
    total = len(exercises)
    return {
        "completed": len(completed_exercises),
        "total": total,
        "percent": round((len(completed_exercises) / total) * 100) if total else 0,
        "practice_minutes": practice_minutes,
        "total_minutes": total_minutes,
        "today_passed": today_passed,
    }
