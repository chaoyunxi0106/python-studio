from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from ..assessment import evaluate_assessment
from ..catalog import catalog_payload, find_exercise
from ..knowledge_graph import refresh_student_skill_state
from ..progress import load_progress, record_attempt, save_progress
from ..store import record_learning_attempt
from ..workspace import get_workspace


def submit_assessment(
    exercise_id: str,
    answers: dict[str, Any],
    *,
    origin: str | None = None,
) -> dict[str, Any]:
    exercise = find_exercise(exercise_id)
    evaluation = evaluate_assessment(exercise, answers)
    now = datetime.now().astimezone().isoformat(timespec="seconds")

    output_lines = []
    task_results = []
    for item in evaluation["results"]:
        status = "通过" if item["passed"] else "未通过"
        output_lines.append(
            f"{item['item_id']}: {status} · {item.get('feedback', '')}"
        )
        task_results.append(
            {
                "task_name": item["item_id"],
                "test_name": f"assessment::{item['item_id']}",
                "knowledge_point": exercise["title"],
                "passed": bool(item["passed"]),
            }
        )

    result = {
        "exercise_id": exercise_id,
        "passed": evaluation["passed"],
        "returncode": 0 if evaluation["passed"] else 1,
        "duration_seconds": 0,
        "output": "\n".join(output_lines),
        "code_snapshot": json.dumps(answers, ensure_ascii=False, indent=2),
        "checked_at": now,
        "domain": "command",
        "analysis_mode": "generic",
        "task_results": task_results,
        "assessment": evaluation,
    }
    progress_path = get_workspace().progress_file
    progress = load_progress(progress_path)
    progress = record_attempt(progress, exercise_id, result)
    save_progress(progress_path, progress)
    record_learning_attempt(result, exercise)
    refresh_student_skill_state()
    result["stats"] = catalog_payload(progress, origin=origin)["stats"]
    return result
