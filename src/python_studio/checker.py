from __future__ import annotations

import importlib.util
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from .catalog import find_exercise
from .domain_profiles import profile_for_exercise, resolve_command
from .execution import run_process
from .test_analysis import analyze_test_results
from .workspace import get_workspace


def _test_command(profile, exercise_dir: Path) -> list[str]:
    if (
        profile.analysis_mode == "python_ast"
        and importlib.util.find_spec("pytest") is None
    ):
        return resolve_command(profile, use_fallback=True)
    return resolve_command(profile)


def run_exercise_check(
    exercise_id: str,
    *,
    exercises_root: Path | None = None,
    timeout_seconds: int = 20,
) -> dict[str, Any]:
    resolved_root = exercises_root or get_workspace().exercises_dir
    exercise = find_exercise(exercise_id, resolved_root)
    exercise_dir = Path(exercise["directory"])
    profile = profile_for_exercise(exercise)
    starter_path = exercise_dir / profile.starter_file
    code_snapshot = (
        starter_path.read_text(encoding="utf-8", errors="replace")
        if starter_path.exists()
        else ""
    )
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONNOUSERSITE"] = "1"

    completed = run_process(
        _test_command(profile, exercise_dir),
        cwd=exercise_dir,
        env=environment,
        timeout_seconds=timeout_seconds,
    )
    output = "\n".join(
        part.strip() for part in (completed.stdout, completed.stderr) if part.strip()
    )
    if completed.timed_out:
        output = f"Check timed out after {timeout_seconds} seconds.\n{output}".strip()
    result = {
        "exercise_id": exercise_id,
        "passed": not completed.timed_out and completed.returncode == 0,
        "returncode": completed.returncode,
        "duration_seconds": completed.duration_seconds,
        "output": output or "No test output.",
        "code_snapshot": code_snapshot,
        "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "domain": profile.id,
        "analysis_mode": profile.analysis_mode,
    }
    result["task_results"] = analyze_test_results(
        exercise,
        result["output"],
        passed_overall=result["passed"],
        analysis_mode=profile.analysis_mode,
    )
    return result
