from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .exercise_layout import enrich_exercise_metadata
from .paths import CURRICULUM_DIR, EXERCISES_DIR
from .progress import progress_stats
from .store import exercise_origin
from .workspace import get_workspace


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_roadmap(root: Path | None = None) -> dict[str, Any]:
    resolved_root = root or get_workspace().curriculum_dir
    return _read_json(resolved_root / "roadmap.json")


def load_exercises(
    root: Path | None = None,
    *,
    include_inactive: bool = False,
    origin: str | None = None,
) -> list[dict[str, Any]]:
    workspace = get_workspace()
    resolved_root = root or workspace.exercises_dir
    exercises: list[dict[str, Any]] = []
    for meta_path in sorted(resolved_root.rglob("meta.json")):
        meta = _read_json(meta_path)
        if not include_inactive and not meta.get("active", True):
            continue
        required = {"id", "title", "stage", "order", "minutes", "summary"}
        missing = required.difference(meta)
        if missing:
            raise ValueError(f"{meta_path} is missing: {', '.join(sorted(missing))}")
        meta["path"] = meta_path.parent.relative_to(resolved_root).as_posix()
        meta["directory"] = str(meta_path.parent)
        meta["origin"] = exercise_origin(meta)
        enrich_exercise_metadata(
            meta,
            workspace=workspace,
            relative_path=str(meta["path"]),
        )
        if origin and meta["origin"] != origin:
            continue
        exercises.append(meta)
    return sorted(exercises, key=lambda item: (int(item["order"]), item["title"]))


def find_exercise(
    exercise_id: str,
    root: Path | None = None,
    *,
    include_inactive: bool = False,
    origin: str | None = None,
) -> dict[str, Any]:
    for exercise in load_exercises(
        root,
        include_inactive=include_inactive,
        origin=origin,
    ):
        if exercise["id"] == exercise_id:
            return exercise
    raise KeyError(f"Unknown exercise: {exercise_id}")


def read_exercise_documentation(exercise: dict[str, Any]) -> str:
    path = Path(exercise["directory"]) / "README.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def read_exercise_solution(exercise: dict[str, Any]) -> str | None:
    from .domain_profiles import profile_for_exercise

    profile = profile_for_exercise(exercise)
    path = Path(exercise["directory"]) / profile.solution_file
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def catalog_payload(
    progress: dict[str, Any],
    *,
    curriculum_root: Path | None = None,
    exercises_root: Path | None = None,
    origin: str | None = None,
) -> dict[str, Any]:
    # Course mode and workshop mode use separate catalogs. AI practice created
    # by the learning companion stays in the course catalog; only exercises
    # explicitly marked as workshop content are hidden from course mode.
    exercises = load_exercises(exercises_root, origin=origin)
    completed = set(progress.get("completed", []))
    attempts = progress.get("attempts", {})
    roadmap = load_roadmap(curriculum_root)
    roadmap_stage_ids = {
        str(stage.get("id"))
        for stage in roadmap.get("stages", [])
        if stage.get("id")
    }
    enriched = []
    for exercise in exercises:
        item = dict(exercise)
        item.pop("directory", None)
        item["completed"] = item["id"] in completed
        item["attempts"] = int(attempts.get(item["id"], {}).get("attempts", 0))
        item["last_passed"] = bool(attempts.get(item["id"], {}).get("passed"))
        enriched.append(item)

    unknown_stage_ids = sorted(
        {
            str(item.get("stage") or "unassigned")
            for item in enriched
            if str(item.get("stage") or "unassigned") not in roadmap_stage_ids
        }
    )
    for index, stage_id in enumerate(unknown_stage_ids, start=1):
        roadmap["stages"].append(
            {
                "id": stage_id,
                "module": 900 + index,
                "title": f"未归类 · {stage_id}",
                "description": (
                    "该练习引用了当前路线中不存在的 stage。"
                    "请重新归入正确模块。"
                ),
                "availability": "active",
                "accent": "#8b949e",
            }
        )

    visible_stages = []
    for stage in roadmap["stages"]:
        stage_exercises = [item for item in enriched if item["stage"] == stage["id"]]
        stage["exercise_count"] = len(stage_exercises)
        stage["completed_count"] = sum(
            1 for item in stage_exercises if item["completed"]
        )
        stage["status"] = stage.get("availability", "planned")
        visible_stages.append(stage)
    roadmap["stages"] = visible_stages

    return {
        "roadmap": roadmap,
        "exercises": enriched,
        "stats": progress_stats(progress, exercises),
        "progress": progress,
    }
