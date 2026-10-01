from __future__ import annotations

import ast
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


def _function_names(path: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    return [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def _test_names(path: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []

    names: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith(
            "test_"
        ):
            names.append(node.name)
        elif isinstance(node, ast.ClassDef):
            names.extend(
                child.name
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                and child.name.startswith("test_")
            )
    return names


def _failed_test_names(output: str) -> set[str]:
    pattern = re.compile(
        r"FAILED\s+test_exercise\.py::(?:[\w.]+::)?(?P<test>\w+)",
        re.MULTILINE,
    )
    return {match.group("test") for match in pattern.finditer(output)}


def _normalize(value: str) -> str:
    value = re.sub(r"^test_\d+_?", "", value)
    value = value.replace("test_", "")
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _match_function(test_name: str, function_names: list[str]) -> str | None:
    normalized_test = _normalize(test_name)
    for function_name in function_names:
        normalized_function = _normalize(function_name)
        if normalized_function and normalized_function in normalized_test:
            return function_name

    ranked = sorted(
        (
            (
                SequenceMatcher(None, normalized_test, _normalize(function_name)).ratio(),
                function_name,
            )
            for function_name in function_names
        ),
        reverse=True,
    )
    if ranked and ranked[0][0] >= 0.45:
        return ranked[0][1]
    return None


def _infer_skill(function_name: str, exercise: dict[str, Any]) -> str:
    task_skills = exercise.get("task_skills", {})
    if function_name in task_skills:
        return str(task_skills[function_name])
    concepts = list(exercise.get("concepts") or [])
    if concepts:
        return str(concepts[0])
    return str(exercise.get("title") or exercise.get("id") or "当前知识点")


def analyze_test_results(
    exercise: dict[str, Any],
    output: str,
    *,
    passed_overall: bool,
    analysis_mode: str = "python_ast",
) -> list[dict[str, Any]]:
    if analysis_mode != "python_ast":
        return [
            {
                "task_name": exercise.get("id", "exercise"),
                "test_name": exercise.get("test_file", "check"),
                "passed": passed_overall,
                "knowledge_point": (
                    (exercise.get("concepts") or ["当前知识点"])[0]
                ),
            }
        ]

    exercise_dir = Path(exercise["directory"])
    from .domain_profiles import profile_for_exercise

    profile = profile_for_exercise(exercise)
    functions = _function_names(exercise_dir / profile.starter_file)
    tests = _test_names(exercise_dir / profile.test_file)
    failed = _failed_test_names(output)

    if passed_overall:
        failed = set()
    elif not failed and tests:
        failed = set(tests)

    results = []
    for test_name in tests:
        function_name = _match_function(test_name, functions)
        task_name = function_name or test_name.removeprefix("test_")
        results.append(
            {
                "task_name": task_name,
                "test_name": test_name,
                "passed": test_name not in failed,
                "knowledge_point": _infer_skill(task_name, exercise),
            }
        )
    return results
