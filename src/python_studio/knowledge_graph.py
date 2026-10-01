from __future__ import annotations

import json
from typing import Any

from .catalog import load_exercises
from .store import _connect, _now, skill_summary


def sync_knowledge_graph() -> dict[str, int]:
    exercises = load_exercises(include_inactive=True)
    skills: dict[str, str] = {}
    links: list[tuple[str, str, float]] = []
    exercise_skill_ids: dict[str, list[str]] = {}
    for exercise in exercises:
        concepts = list(exercise.get("concepts") or [])
        task_skills = exercise.get("task_skills") or {}
        concepts.extend(task_skills.values())
        for concept in dict.fromkeys(str(item).strip() for item in concepts):
            if not concept:
                continue
            skills[concept] = exercise.get("summary", "")
            links.append((str(exercise["id"]), concept, 1.0))
            exercise_skill_ids.setdefault(str(exercise["id"]), []).append(concept)

    prerequisite_links: set[tuple[str, str]] = set()
    by_stage: dict[str, list[dict[str, Any]]] = {}
    for exercise in exercises:
        by_stage.setdefault(str(exercise.get("stage", "")), []).append(exercise)
    for stage_exercises in by_stage.values():
        ordered = sorted(
            stage_exercises,
            key=lambda item: int(item.get("order", 0)),
        )
        for previous, current in zip(ordered, ordered[1:]):
            previous_skills = exercise_skill_ids.get(str(previous["id"]), [])
            current_skills = exercise_skill_ids.get(str(current["id"]), [])
            for current_skill in current_skills:
                for prerequisite in previous_skills:
                    if current_skill != prerequisite:
                        prerequisite_links.add((current_skill, prerequisite))

    now = _now()
    with _connect() as connection:
        for skill_id, description in skills.items():
            connection.execute(
                """
                INSERT INTO skills (id, title, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    description = excluded.description,
                    updated_at = excluded.updated_at
                """,
                (skill_id, skill_id, description, now, now),
            )
        for exercise_id, skill_id, weight in links:
            connection.execute(
                """
                INSERT INTO exercise_skills (exercise_id, skill_id, weight)
                VALUES (?, ?, ?)
                ON CONFLICT(exercise_id, skill_id) DO UPDATE SET
                    weight = excluded.weight
                """,
                (exercise_id, skill_id, weight),
            )
        for skill_id, prerequisite_id in sorted(prerequisite_links):
            connection.execute(
                """
                INSERT OR IGNORE INTO skill_prerequisites (
                    skill_id, prerequisite_id
                )
                VALUES (?, ?)
                """,
                (skill_id, prerequisite_id),
            )
    return {
        "skills": len(skills),
        "links": len(links),
        "prerequisites": len(prerequisite_links),
    }


def refresh_student_skill_state() -> int:
    summary = skill_summary()
    now = _now()
    with _connect() as connection:
        for item in summary:
            connection.execute(
                """
                INSERT INTO student_skill_state (
                    skill_id, mastery, checks, failures, trend,
                    recent_results, last_seen, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(skill_id) DO UPDATE SET
                    mastery = excluded.mastery,
                    checks = excluded.checks,
                    failures = excluded.failures,
                    trend = excluded.trend,
                    recent_results = excluded.recent_results,
                    last_seen = excluded.last_seen,
                    updated_at = excluded.updated_at
                """,
                (
                    item["knowledge_point"],
                    item["mastery"],
                    item["checks"],
                    item["failures"],
                    item["trend"],
                    json.dumps(item["recent_results"]),
                    item["last_seen"],
                    now,
                ),
            )
    return len(summary)


def knowledge_graph_summary() -> dict[str, Any]:
    with _connect() as connection:
        skills = connection.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
        links = connection.execute(
            "SELECT COUNT(*) FROM exercise_skills"
        ).fetchone()[0]
        prerequisites = connection.execute(
            "SELECT COUNT(*) FROM skill_prerequisites"
        ).fetchone()[0]
        states = connection.execute(
            "SELECT COUNT(*) FROM student_skill_state"
        ).fetchone()[0]
    return {
        "skills": int(skills),
        "exercise_links": int(links),
        "prerequisites": int(prerequisites),
        "student_states": int(states),
    }
