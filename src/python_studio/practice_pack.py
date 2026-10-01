from __future__ import annotations

import ast
import json
import re
import time
from pathlib import Path
from typing import Any

from .exercise_layout import normalize_scope, resolve_exercise_location
from .workspace import get_workspace


FUNCTION_NAME_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")
PARAMETER_NAME_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")


class PracticePackError(ValueError):
    pass


def _clean_text(value: Any, fallback: str, limit: int = 500) -> str:
    text = str(value or "").strip()
    return (text or fallback)[:limit]


def _validate_case(case: dict[str, Any]) -> dict[str, Any]:
    args = case.get("args", [])
    if not isinstance(args, list):
        raise PracticePackError("Each case args value must be a list.")
    expected = case.get("expected")
    try:
        json.dumps(expected, ensure_ascii=False)
    except TypeError as error:
        raise PracticePackError("Case expected values must be JSON serializable.") from error
    return {
        "args": args,
        "expected": expected,
    }


def _clean_code(value: Any, limit: int = 2500) -> str:
    code = str(value or "").strip()
    code = re.sub(r"^```(?:python)?\s*|\s*```$", "", code)
    return code[:limit]


def normalize_practice_pack(
    payload: dict[str, Any],
    *,
    knowledge_point: str,
    source_exercise_id: str | None = None,
) -> dict[str, Any]:
    raw_tasks = payload.get("tasks")
    if not isinstance(raw_tasks, list) or not raw_tasks:
        raise PracticePackError("Practice pack requires at least one task.")

    tasks = []
    function_names: set[str] = set()
    for index, raw_task in enumerate(raw_tasks[:6], start=1):
        if not isinstance(raw_task, dict):
            raise PracticePackError("Each task must be an object.")
        function_name = str(raw_task.get("function_name", "")).strip()
        if not FUNCTION_NAME_PATTERN.fullmatch(function_name):
            raise PracticePackError(f"Invalid function name: {function_name}")
        if function_name in function_names:
            raise PracticePackError(f"Duplicate function name: {function_name}")
        function_names.add(function_name)

        raw_cases = raw_task.get("cases")
        if not isinstance(raw_cases, list) or not raw_cases:
            raise PracticePackError(f"Task {function_name} requires test cases.")
        cases = [_validate_case(case) for case in raw_cases[:8] if isinstance(case, dict)]
        if not cases:
            raise PracticePackError(f"Task {function_name} has no valid cases.")
        max_argument_count = max(len(case["args"]) for case in cases)
        raw_parameters = raw_task.get("parameters", [])
        if not isinstance(raw_parameters, list):
            raw_parameters = []
        parameters = [
            str(parameter).strip()
            for parameter in raw_parameters
            if PARAMETER_NAME_PATTERN.fullmatch(str(parameter).strip())
        ]
        while len(parameters) < max_argument_count:
            parameters.append(f"argument{len(parameters) + 1}")

        tasks.append(
            {
                "title": _clean_text(raw_task.get("title"), f"补练小题 {index}", 120),
                "instruction": _clean_text(
                    raw_task.get("instruction"),
                    f"完成函数 {function_name}。",
                    800,
                ),
                "function_name": function_name,
                "parameters": parameters,
                "cases": cases,
                "reference": _clean_code(raw_task.get("reference")),
                "hint": _clean_text(raw_task.get("hint"), "先写出输入和预期输出。", 300),
            }
        )

    knowledge = payload.get("knowledge")
    if not isinstance(knowledge, dict):
        knowledge = {}
    normalized_knowledge = {
        "title": _clean_text(knowledge.get("title"), knowledge_point, 120),
        "summary": _clean_text(
            knowledge.get("summary"),
            f"围绕「{knowledge_point}」完成一组同类练习。",
            500,
        ),
        "syntax": _clean_text(knowledge.get("syntax"), "", 500),
        "points": [
            _clean_text(point, "", 240)
            for point in knowledge.get("points", [])[:6]
            if str(point).strip()
        ],
        "pitfall": _clean_text(knowledge.get("pitfall"), "先处理边界，再运行检查。", 400),
    }
    hints = [
        _clean_text(hint, "", 300)
        for hint in payload.get("hints", [])
        if str(hint).strip()
    ][:6]
    if not hints:
        hints = [task["hint"] for task in tasks][:5]

    return {
        "title": _clean_text(payload.get("title"), f"补练：{knowledge_point}", 120),
        "summary": _clean_text(
            payload.get("summary"),
            f"围绕「{knowledge_point}」的综合补练。",
            500,
        ),
        "minutes": max(10, min(int(payload.get("minutes", 25)), 60)),
        "concepts": [knowledge_point],
        "knowledge": normalized_knowledge,
        "hints": hints,
        "tasks": tasks,
        "source_exercise_id": source_exercise_id,
    }


def _starter_code(tasks: list[dict[str, Any]]) -> str:
    blocks = []
    for task in tasks:
        blocks.append(
            f"def {task['function_name']}({', '.join(task['parameters'])}):\n"
            "    raise NotImplementedError\n"
        )
    return "\n\n".join(blocks) + "\n"


def _solution_code(tasks: list[dict[str, Any]]) -> str | None:
    references = [task["reference"] for task in tasks if task.get("reference")]
    if len(references) != len(tasks):
        return None
    code = "\n\n".join(references).strip() + "\n"
    try:
        ast.parse(code)
    except SyntaxError:
        return None
    return code


def _test_code(tasks: list[dict[str, Any]]) -> str:
    methods = []
    for index, task in enumerate(tasks, start=1):
        methods.append(
            f"    def test_{index:02d}_{task['function_name']}(self):\n"
            f"        self._run_task({index - 1}, {task['function_name']!r})\n"
        )
    return (
        "from __future__ import annotations\n\n"
        "import importlib.util\n"
        "import json\n"
        "import unittest\n"
        "from pathlib import Path\n\n\n"
        "def load_student_code():\n"
        "    path = Path(__file__).with_name(\"starter.py\")\n"
        "    spec = importlib.util.spec_from_file_location(\"student_generated_practice\", path)\n"
        "    if spec is None or spec.loader is None:\n"
        "        raise RuntimeError(\"Unable to load starter.py\")\n"
        "    module = importlib.util.module_from_spec(spec)\n"
        "    spec.loader.exec_module(module)\n"
        "    return module\n\n\n"
        "class GeneratedPracticeTests(unittest.TestCase):\n"
        "    @classmethod\n"
        "    def setUpClass(cls):\n"
        "        cls.module = load_student_code()\n"
        "        cls.tasks = json.loads(Path(__file__).with_name(\"cases.json\").read_text(\n"
        "            encoding=\"utf-8\"\n"
        "        ))\n\n"
        "    def _run_task(self, task_index, function_name):\n"
        "        function = getattr(self.module, function_name)\n"
        "        task = self.tasks[task_index]\n"
        "        for case_index, case in enumerate(task[\"cases\"], start=1):\n"
        "            with self.subTest(case=case_index):\n"
        "                result = function(*case[\"args\"])\n"
        "                self.assertEqual(result, case[\"expected\"])\n\n"
        + "\n".join(methods)
        + "\n\n"
        "if __name__ == \"__main__\":\n"
        "    unittest.main()\n"
    )


def _readme(pack: dict[str, Any]) -> str:
    lines = [
        f"# {pack['title']}",
        "",
        pack["summary"],
        "",
        "## 操作题",
        "",
    ]
    for index, task in enumerate(pack["tasks"], start=1):
        lines.extend(
            [
                f"### {index}. `{task['function_name']}`",
                "",
                task["instruction"],
                "",
            ]
        )
    lines.extend(
        [
            "## 完成方式",
            "",
            "只需要修改 `starter.py`，然后在网页端点击“运行检查”。",
            "本练习由伴学系统围绕当前薄弱知识点动态生成。",
            "",
        ]
    )
    return "\n".join(lines)


def create_practice_exercise(
    pack: dict[str, Any],
    *,
    generated_root: Path | None = None,
    origin: str = "course",
    stage: str | None = None,
    scope: str | None = None,
    level_index: int | None = None,
) -> dict[str, Any]:
    workspace = get_workspace()
    resolved_origin = "workshop" if origin == "workshop" else "course"
    resolved_stage = stage or (
        "workshop" if resolved_origin == "workshop" else "ai_practice"
    )
    resolved_scope = normalize_scope(
        scope
        or (
            "workshop"
            if resolved_origin == "workshop"
            else ("tutoring" if resolved_stage == "ai_practice" else "course")
        )
    )
    location = resolve_exercise_location(
        scope=resolved_scope,
        stage=resolved_stage,
        workspace=workspace,
        level_index=level_index,
    )
    generated_root = generated_root or location.directory
    generated_root.mkdir(parents=True, exist_ok=True)
    prefix = {
        "course": "course",
        "workshop": "workshop",
        "tutoring": "tutoring",
    }[resolved_scope]
    pack_id = f"{prefix}_{int(time.time())}_{abs(hash(pack['title'])) % 10000:04d}"
    exercise_id = f"{pack_id}_{pack['knowledge']['title']}"[:70]
    exercise_id = re.sub(r"[^a-zA-Z0-9_]+", "_", exercise_id).strip("_").lower()
    exercise_dir = generated_root / exercise_id
    exercise_dir.mkdir(parents=True, exist_ok=False)

    meta = {
        "id": exercise_id,
        "active": True,
        "generated": True,
        "pack_id": pack_id,
        "subject_id": workspace.id,
        "course_id": location.course_id,
        "course_slug": location.course_slug,
        "course_title": location.course_title,
        "scope": resolved_scope,
        "storage_scope": resolved_scope,
        "relative_directory": location.relative_directory,
        "storage_path": (
            f"{location.relative_directory}/{exercise_id}"
            if location.relative_directory
            else exercise_id
        ),
        "origin": resolved_origin,
        "title": pack["title"],
        "stage": resolved_stage,
        "module_id": location.module_id,
        "module_number": location.module_number,
        "module_title": location.module_title,
        "level_index": location.level_index,
        "level_id": location.level_id,
        "order": 1000 + int(time.time()),
        "minutes": pack["minutes"],
        "summary": pack["summary"],
        "concepts": pack["concepts"],
        "hints": pack["hints"],
        "knowledge": pack["knowledge"],
        "source_exercise_id": pack.get("source_exercise_id"),
        "task_skills": {
            task["function_name"]: pack["knowledge"]["title"] for task in pack["tasks"]
        },
    }
    cases = [
        {
            "function_name": task["function_name"],
            "cases": task["cases"],
        }
        for task in pack["tasks"]
    ]

    (exercise_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (exercise_dir / "README.md").write_text(_readme(pack), encoding="utf-8")
    (exercise_dir / "starter.py").write_text(
        _starter_code(pack["tasks"]),
        encoding="utf-8",
    )
    (exercise_dir / "test_exercise.py").write_text(
        _test_code(pack["tasks"]),
        encoding="utf-8",
    )
    (exercise_dir / "cases.json").write_text(
        json.dumps(cases, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    solution = _solution_code(pack["tasks"])
    if solution:
        (exercise_dir / "solution.py").write_text(solution, encoding="utf-8")
        meta["solution_generated"] = True
        (exercise_dir / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return {
        "id": exercise_id,
        "directory": str(exercise_dir),
        "pack_id": pack_id,
    }
