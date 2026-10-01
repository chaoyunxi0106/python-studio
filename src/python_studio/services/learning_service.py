from __future__ import annotations

from typing import Any

from ..ai_jobs import run_ai_operation
from ..catalog import (
    find_exercise,
    read_exercise_documentation,
    read_exercise_solution,
)
from ..companion import (
    analyze_attempt_code,
    analyze_learning,
    companion_status,
    generate_ai_solution,
)
from ..config import get_deepseek_config
from ..domain_profiles import profile_for_exercise
from ..knowledge import knowledge_for_exercise
from ..store import (
    get_learning_attempt,
    learning_history_summary,
    list_learning_attempts,
    list_mistakes,
    replace_mistakes,
    save_attempt_analysis,
    save_analysis,
    skill_summary,
)


def _enrich_attempt(attempt: dict[str, Any]) -> dict[str, Any]:
    try:
        exercise = find_exercise(
            str(attempt.get("exercise_id")),
            include_inactive=True,
        )
    except KeyError:
        return attempt
    enriched = dict(attempt)
    enriched["requirements"] = read_exercise_documentation(exercise)
    enriched["knowledge"] = knowledge_for_exercise(exercise)
    profile = profile_for_exercise(exercise)
    enriched["domain_name"] = profile.name
    enriched["domain_context"] = profile.ai_context
    return enriched


def history_payload(origin: str | None = None) -> dict[str, Any]:
    attempts = list_learning_attempts(limit=100, origin=origin)
    for attempt in attempts:
        try:
            exercise = find_exercise(
                str(attempt["exercise_id"]),
                include_inactive=True,
            )
        except KeyError:
            attempt["standard_solution"] = None
            continue
        attempt["standard_solution"] = read_exercise_solution(exercise)
    return {
        "summary": learning_history_summary(origin=origin),
        "attempts": attempts,
    }


def analyze_attempt(attempt_id: int, *, use_cache: bool = False) -> dict[str, Any]:
    attempt = get_learning_attempt(attempt_id)
    if attempt is None:
        raise KeyError("Attempt not found.")
    enriched = _enrich_attempt(attempt)
    analysis = run_ai_operation(
        "attempt_analysis",
        {
            "exercise_id": enriched.get("exercise_id"),
            "code": enriched.get("code_snapshot"),
            "output": enriched.get("output"),
            "task_results": enriched.get("task_results"),
        },
        lambda: analyze_attempt_code(
            enriched,
            config=get_deepseek_config(),
        ),
        use_cache=use_cache,
    )
    save_attempt_analysis(attempt_id, analysis)
    return {"attempt_id": attempt_id, "analysis": analysis}


def analyze_failures(limit: int = 5, origin: str | None = None) -> int:
    attempts = list_learning_attempts(limit=100, origin=origin)
    analyzed = 0
    config = get_deepseek_config()
    for attempt in attempts:
        if analyzed >= limit:
            break
        if attempt.get("passed") or attempt.get("ai_analysis"):
            continue
        enriched = _enrich_attempt(attempt)
        analysis = run_ai_operation(
            "attempt_analysis",
            {
                "exercise_id": enriched.get("exercise_id"),
                "code": enriched.get("code_snapshot"),
                "output": enriched.get("output"),
                "task_results": enriched.get("task_results"),
            },
            lambda: analyze_attempt_code(enriched, config=config),
            use_cache=True,
        )
        save_attempt_analysis(int(attempt["id"]), analysis)
        analyzed += 1
    return analyzed


def generate_solution(attempt_id: int) -> dict[str, Any]:
    attempt = get_learning_attempt(attempt_id)
    if attempt is None:
        raise KeyError("Attempt not found.")
    try:
        exercise = find_exercise(
            str(attempt["exercise_id"]),
            include_inactive=True,
        )
    except KeyError as error:
        raise KeyError("Exercise not found.") from error
    solution = run_ai_operation(
        "standard_solution",
        {
            "exercise_id": exercise["id"],
            "title": exercise["title"],
        },
        lambda: generate_ai_solution(
            exercise,
            config=get_deepseek_config(),
        ),
        use_cache=True,
    )
    return {
        "attempt_id": attempt_id,
        **solution,
    }


def run_learning_diagnosis(
    *,
    origin: str | None = None,
    failure_limit: int = 3,
) -> dict[str, Any]:
    from ..maintenance import archive_practiced_generated_exercises

    config = get_deepseek_config()
    analyze_failures(limit=failure_limit, origin=origin)
    attempts = list_learning_attempts(
        limit=config.history_limit,
        origin=origin,
    )
    mistakes = list_mistakes(origin=origin)
    analysis = run_ai_operation(
        "learning_diagnosis",
        {
            "attempt_ids": [attempt["id"] for attempt in attempts],
            "analyses": [attempt.get("ai_analysis") for attempt in attempts],
            "mistakes": mistakes,
        },
        lambda: analyze_learning(attempts, mistakes, config=config),
        use_cache=True,
    )
    replace_mistakes(
        analysis.get("practice_items", [])[:2],
        source=str(analysis.get("source", "local")),
        origin=origin or "course",
    )
    save_analysis(analysis, origin=origin or "course")
    archived = archive_practiced_generated_exercises()
    return {
        "status": companion_status(config),
        "analysis": analysis,
        "history": learning_history_summary(origin=origin),
        "skills": skill_summary(origin=origin),
        "mistakes": list_mistakes(origin=origin),
        "archived_practiced": archived,
    }
