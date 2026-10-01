from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Sequence

from .catalog import catalog_payload, find_exercise, load_exercises
from .checker import run_exercise_check
from .exercise_layout import normalize_workspace_exercise_metadata
from .paths import EXERCISES_DIR, PROGRESS_FILE, PROJECT_ROOT
from .progress import load_progress, record_attempt, save_progress
from .server import serve
from .validation import validate_exercises
from .workspace import list_workspaces


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python studio.py",
        description="Local-first Python learning studio.",
    )
    subparsers = parser.add_subparsers(dest="command")

    serve_parser = subparsers.add_parser("serve", help="Start the visual dashboard.")
    serve_parser.add_argument("--port", type=int, default=8765)
    serve_parser.add_argument("--open", action="store_true", help="Open a browser.")

    subparsers.add_parser("doctor", help="Check the local learning environment.")
    subparsers.add_parser("list", help="List all exercises.")
    subparsers.add_parser("next", help="Show the next unfinished exercise.")
    subparsers.add_parser("progress", help="Show progress summary.")
    subparsers.add_parser("validate", help="Validate every exercise definition.")
    subparsers.add_parser(
        "normalize-layout",
        help="Write course/module/level metadata for every exercise.",
    )

    check_parser = subparsers.add_parser("check", help="Run one exercise.")
    check_parser.add_argument("exercise_id")

    hint_parser = subparsers.add_parser("hint", help="Show a graded hint.")
    hint_parser.add_argument("exercise_id")
    hint_parser.add_argument("--level", type=int, default=1)
    return parser


def _next_exercise():
    progress = load_progress(PROGRESS_FILE)
    completed = set(progress.get("completed", []))
    for exercise in load_exercises():
        if exercise["id"] not in completed:
            return exercise
    return None


def _print_exercise(exercise) -> None:
    print(f"{exercise['id']}  {exercise['title']}")
    print(f"预算: {exercise['minutes']} 分钟")
    print(f"说明: {exercise['summary']}")
    print(f"路径: {exercise['directory']}")
    print(f"概念: {', '.join(exercise.get('concepts', []))}")


def command_doctor() -> int:
    python_ok = sys.version_info >= (3, 11)
    tools = {
        "git": shutil.which("git"),
        "uv": shutil.which("uv"),
        "code": shutil.which("code"),
    }
    print("Python Studio doctor")
    print(f"Python: {sys.version.split()[0]} {'OK' if python_ok else 'NEEDS >= 3.11'}")
    print(f"Project: {PROJECT_ROOT}")
    for name, path in tools.items():
        print(f"{name}: {'OK' if path else 'not found'} {path or ''}".rstrip())
    print(f"Exercises: {len(load_exercises())}")
    return 0 if python_ok else 1


def command_list() -> int:
    progress = load_progress(PROGRESS_FILE)
    completed = set(progress.get("completed", []))
    for exercise in load_exercises():
        marker = "[x]" if exercise["id"] in completed else "[ ]"
        print(
            f"{marker} {exercise['order']:02d} "
            f"{exercise['id']:<28} {exercise['title']}"
        )
    return 0


def command_next() -> int:
    exercise = _next_exercise()
    if exercise is None:
        print("当前练习已全部通过。下一步请推进 projects/ 中的项目。")
        return 0
    _print_exercise(exercise)
    return 0


def command_check(exercise_id: str) -> int:
    try:
        result = run_exercise_check(exercise_id)
    except KeyError as error:
        print(str(error), file=sys.stderr)
        return 2

    progress = load_progress(PROGRESS_FILE)
    progress = record_attempt(progress, exercise_id, result)
    save_progress(PROGRESS_FILE, progress)
    print(result["output"])
    print(
        f"\n{'PASSED' if result['passed'] else 'FAILED'} "
        f"in {result['duration_seconds']:.2f}s"
    )
    return 0 if result["passed"] else 1


def command_hint(exercise_id: str, level: int) -> int:
    try:
        exercise = find_exercise(exercise_id)
    except KeyError as error:
        print(str(error), file=sys.stderr)
        return 2
    hints = exercise.get("hints", [])
    if not hints:
        print("这道题没有额外提示。")
        return 0
    index = min(max(level, 1), len(hints)) - 1
    print(f"提示 {index + 1}/{len(hints)}: {hints[index]}")
    return 0


def command_progress() -> int:
    progress = load_progress(PROGRESS_FILE)
    payload = catalog_payload(progress)
    stats = payload["stats"]
    print(
        f"完成 {stats['completed']}/{stats['total']} "
        f"({stats['percent']}%), "
        f"练习预算 {stats['practice_minutes']}/{stats['total_minutes']} 分钟"
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command in (None, "serve"):
        port = getattr(args, "port", 8765)
        open_browser = getattr(args, "open", False)
        serve(PROJECT_ROOT, port, open_browser)
        return 0
    if args.command == "doctor":
        return command_doctor()
    if args.command == "list":
        return command_list()
    if args.command == "next":
        return command_next()
    if args.command == "check":
        return command_check(args.exercise_id)
    if args.command == "hint":
        return command_hint(args.exercise_id, args.level)
    if args.command == "progress":
        return command_progress()
    if args.command == "validate":
        return command_validate()
    if args.command == "normalize-layout":
        return command_normalize_layout()

    parser.print_help()
    return 2


def command_validate() -> int:
    result = validate_exercises()
    print(
        f"Validated {result['exercises']} exercises: "
        f"{'OK' if result['ok'] else 'FAILED'}"
    )
    for error in result["errors"]:
        print(f"ERROR: {error}")
    for warning in result["warnings"]:
        print(f"WARNING: {warning}")
    return 0 if result["ok"] else 1


def command_normalize_layout() -> int:
    total = 0
    updated = 0
    for workspace in list_workspaces():
        if not workspace.exercises_dir.exists():
            continue
        result = normalize_workspace_exercise_metadata(workspace)
        total += result["exercises"]
        updated += result["updated"]
        print(
            f"{workspace.id}: {result['updated']}/{result['exercises']} "
            "exercise metadata files updated"
        )
    print(f"Updated {updated}/{total} exercise metadata files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
