from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from .catalog import load_exercises
from .domain_profiles import profile_for_exercise


REQUIRED_META = {
    "id",
    "title",
    "stage",
    "order",
    "minutes",
    "summary",
    "concepts",
}


def _python_parse(path: Path) -> tuple[bool, str | None]:
    try:
        ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError as error:
        return False, f"{path.name}:{error.lineno}: {error.msg}"
    return True, None


def validate_exercises() -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    exercises = load_exercises(include_inactive=True)
    identifiers: set[str] = set()

    for exercise in exercises:
        exercise_id = str(exercise.get("id", ""))
        directory = Path(exercise["directory"])
        if exercise_id in identifiers:
            errors.append(f"{exercise_id}: duplicate exercise id")
        identifiers.add(exercise_id)

        missing_meta = REQUIRED_META.difference(exercise)
        if missing_meta:
            errors.append(
                f"{exercise_id}: missing meta fields {sorted(missing_meta)}"
            )
        try:
            profile = profile_for_exercise(exercise)
        except (KeyError, ValueError) as error:
            errors.append(f"{exercise_id}: invalid domain profile: {error}")
            continue
        required_files = {
            "README.md",
            "meta.json",
            profile.starter_file,
            profile.test_file,
        }
        missing_files = [
            name for name in required_files if not (directory / name).exists()
        ]
        if missing_files:
            errors.append(
                f"{exercise_id}: missing files {sorted(missing_files)}"
            )
        if not profile.primary_command:
            errors.append(f"{exercise_id}: primary test command is empty")
        for filename in (profile.starter_file, profile.test_file):
            path = directory / filename
            if path.exists() and path.suffix == ".py":
                valid, error = _python_parse(path)
                if not valid:
                    message = f"{exercise_id}: {error}"
                    if exercise.get("generated"):
                        warnings.append(f"generated learner code: {message}")
                    else:
                        errors.append(message)
        if not (directory / profile.solution_file).exists():
            warnings.append(
                f"{exercise_id}: {profile.solution_file} is not available"
            )

    return {
        "ok": not errors,
        "exercises": len(exercises),
        "errors": errors,
        "warnings": warnings,
    }
