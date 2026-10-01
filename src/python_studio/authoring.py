"""Authoring tools the companion AI can call to read and write site content.

Every page that currently shows model-authored prose (lesson notes, collaboration
guidance, diagnosis summaries) is written through this module, so the chat can
control the same content a human would edit by hand.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .catalog import find_exercise, load_exercises, load_roadmap
from .progress import load_progress
from .workspace import get_workspace


LESSON_FILE = "lesson.json"
MENTOR_FILE = "mentor.json"
DIAGNOSIS_FILE = "diagnosis.json"
README_BACKUP_SUFFIX = ".md.bak"

MAX_TEXT = 4000


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _trim(value: Any, limit: int = MAX_TEXT) -> str:
    return str(value or "").strip()[:limit]


def _exercise_dir(exercise_id: str) -> Path:
    exercise = find_exercise(exercise_id, include_inactive=True)
    return Path(exercise["directory"])


def _resolve_exercise_id(arguments: dict[str, Any]) -> str:
    requested = _trim(arguments.get("exercise_id"), 200)
    if requested:
        return requested

    workspace = get_workspace()
    exercises = load_exercises(include_inactive=True)
    by_id = {str(exercise["id"]): exercise for exercise in exercises}
    progress = load_progress(workspace.progress_file)
    last_exercise = str(progress.get("last_exercise") or "")
    if last_exercise in by_id:
        return last_exercise
    if exercises:
        return str(
            sorted(
                exercises,
                key=lambda item: (int(item.get("order", 0)), str(item["title"])),
            )[-1]["id"]
        )
    raise ValueError(
        "No exercise is available. Create a practice before writing lesson content."
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return payload if isinstance(payload, dict) else None


# --------------------------------------------------------------------------
# Readers used by the page payloads
# --------------------------------------------------------------------------


def authored_lesson(exercise: dict[str, Any]) -> dict[str, Any] | None:
    directory = exercise.get("directory")
    if not directory:
        return None
    payload = _read_json(Path(directory) / LESSON_FILE)
    return payload if payload and payload.get("title") else None


def authored_mentor(exercise: dict[str, Any]) -> dict[str, Any] | None:
    directory = exercise.get("directory")
    if not directory:
        return None
    return _read_json(Path(directory) / MENTOR_FILE)


def authored_diagnosis() -> dict[str, Any] | None:
    return _read_json(get_workspace().root / DIAGNOSIS_FILE)


# --------------------------------------------------------------------------
# Tool schemas (OpenAI-compatible function definitions)
# --------------------------------------------------------------------------


TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_exercises",
            "description": (
                "列出当前科目的练习关卡，包含 id、标题、所属模块与类型。"
                "在补充题目或修改练习前，先用它确认现有结构。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "module_id": {
                        "type": "string",
                        "description": "只列出该模块下的关卡，留空表示全部。",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_exercise",
            "description": (
                "读取一个练习关卡的完整信息：题面说明、起始代码、测试文件与元数据。"
                "修改前必须先读，避免编造不存在的接口。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "exercise_id": {"type": "string", "description": "关卡 id。"}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_practice",
            "description": (
                "新建一道可运行的练习关卡。用于补充某个模块的题目，或新建针对性补练。"
                "平台会自行生成起始代码与测试，不需要你输出代码。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "knowledge_point": {
                        "type": "string",
                        "description": "这道题训练的知识点。",
                    },
                    "module_id": {
                        "type": "string",
                        "description": (
                            "必须使用当前路线中真实存在的 stage id；"
                            "不确定时先调用 list_exercises 查看。"
                            "留空或无法匹配时进入 AI 专属补练。"
                        ),
                    },
                    "instructions": {
                        "type": "string",
                        "description": "给出题模型的额外要求，例如难度、题型、边界条件。",
                    },
                },
                "required": ["knowledge_point"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_exercise_readme",
            "description": (
                "覆写一道练习的题面说明（README.md）。原文件会先备份为 .md.bak。"
                "用于完善题目描述、补充边界条件或修正过时说明。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "exercise_id": {"type": "string"},
                    "markdown": {
                        "type": "string",
                        "description": "完整的 Markdown 题面，会整体替换原文件。",
                    },
                },
                "required": ["markdown"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_lesson",
            "description": (
                "写入或更新一道练习的「讲义」内容，也就是练习页知识点面板显示的"
                "讲解。只要写了就覆盖内置讲义。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "exercise_id": {"type": "string"},
                    "title": {"type": "string", "description": "知识点名称。"},
                    "summary": {
                        "type": "string",
                        "description": "它在解决什么问题，两到三句。",
                    },
                    "syntax": {
                        "type": "string",
                        "description": "核心写法，可直接给代码片段。",
                    },
                    "points": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "关键点，按重要性排序。",
                    },
                    "pitfall": {"type": "string", "description": "常见误区。"},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_mentor",
            "description": (
                "写入或更新一道练习的「协作」面板内容，也就是练习页的 AI 协作建议。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "exercise_id": {"type": "string"},
                    "intro": {
                        "type": "string",
                        "description": "一句话点明这道题该怎么和 AI 配合。",
                    },
                    "steps": {
                        "type": "array",
                        "description": "两到六条协作步骤。",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "body": {"type": "string"},
                            },
                            "required": ["title"],
                        },
                    },
                },
                "required": ["intro"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_diagnosis",
            "description": (
                "写入学习诊断的分析总结，会显示在档案页的诊断子页面。"
                "用于把当前判断沉淀成一段可复读的结论。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "整体状态判断，三到五句。",
                    },
                    "weaknesses": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "需要巩固的知识点，按优先级排序。",
                    },
                    "next_steps": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "建议的下一步动作。",
                    },
                },
                "required": ["summary"],
            },
        },
    },
]


def tool_registry() -> list[dict[str, Any]]:
    """Public, JSON-serialisable description of every authoring tool."""
    return [
        {
            "name": schema["function"]["name"],
            "description": schema["function"]["description"],
            "parameters": schema["function"].get("parameters", {}),
        }
        for schema in TOOL_SCHEMAS
    ]


# --------------------------------------------------------------------------
# Executors
# --------------------------------------------------------------------------


def _tool_list_exercises(
    arguments: dict[str, Any],
    *,
    origin: str | None = None,
) -> dict[str, Any]:
    module_id = _trim(arguments.get("module_id"))
    exercises = load_exercises(origin=origin)
    items = [
        {
            "id": exercise["id"],
            "title": exercise["title"],
            "module": exercise["stage"],
            "minutes": exercise.get("minutes"),
            "type": exercise.get("exercise_type", "code"),
            "origin": exercise.get("origin", "course"),
        }
        for exercise in exercises
        if not module_id or exercise["stage"] == module_id
    ]
    return {"count": len(items), "exercises": items}


def _tool_read_exercise(arguments: dict[str, Any]) -> dict[str, Any]:
    exercise_id = _resolve_exercise_id(arguments)
    exercise = find_exercise(exercise_id, include_inactive=True)
    directory = Path(exercise["directory"])
    starter = exercise.get("starter_file", "starter.py")
    test_file = exercise.get("test_file", "test_exercise.py")
    readme_path = directory / "README.md"
    return {
        "id": exercise["id"],
        "title": exercise["title"],
        "module": exercise["stage"],
        "summary": exercise.get("summary", ""),
        "concepts": exercise.get("concepts", []),
        "minutes": exercise.get("minutes"),
        "readme": (
            readme_path.read_text(encoding="utf-8", errors="replace")[:6000]
            if readme_path.exists()
            else ""
        ),
        "starter_code": (
            (directory / starter).read_text(encoding="utf-8", errors="replace")[:4000]
            if (directory / starter).exists()
            else ""
        ),
        "test_file": test_file,
    }


def _resolve_stage(
    module_id: str,
    *,
    origin: str,
) -> tuple[str, str, int | None]:
    if origin == "workshop":
        from .materializer import ensure_workshop_stage

        ensure_workshop_stage()
        return "workshop", "workshop", None

    roadmap = load_roadmap()
    stages = list(roadmap.get("stages") or [])
    stage_ids = {str(stage.get("id")) for stage in stages}
    if module_id in stage_ids:
        from .exercise_layout import next_level_index

        return module_id, "course", next_level_index(module_id)

    module_match = re.fullmatch(r"module[_-]?(\d+)", module_id, re.IGNORECASE)
    if module_match:
        requested_module = int(module_match.group(1))
        for stage in stages:
            try:
                if int(stage.get("module")) == requested_module:
                    from .exercise_layout import next_level_index

                    stage_id = str(stage["id"])
                    return stage_id, "course", next_level_index(stage_id)
            except (TypeError, ValueError):
                continue

    from .materializer import ensure_course_practice_stage

    ensure_course_practice_stage()
    return "ai_practice", "tutoring", None


def _tool_create_practice(
    arguments: dict[str, Any],
    *,
    origin: str = "course",
) -> dict[str, Any]:
    from .companion import generate_and_create_practice
    from .config import get_deepseek_config

    knowledge_point = _trim(arguments.get("knowledge_point"), 200)
    if not knowledge_point:
        raise ValueError("knowledge_point is required.")
    instructions = _trim(arguments.get("instructions")) or knowledge_point
    resolved_origin = "workshop" if origin == "workshop" else "course"
    module_id = _trim(arguments.get("module_id"), 60)
    stage_id, scope, level_index = _resolve_stage(
        module_id,
        origin=resolved_origin,
    )
    created = generate_and_create_practice(
        [],
        knowledge_point=knowledge_point,
        source_task=instructions,
        config=get_deepseek_config(),
        origin=resolved_origin,
        stage=stage_id,
        scope=scope,
        level_index=level_index,
    )
    exercise_id = str(created.get("id", ""))
    if exercise_id:
        meta_path = _exercise_dir(exercise_id) / "meta.json"
        meta = _read_json(meta_path) or {}
        meta["stage"] = stage_id
        meta["module"] = stage_id
        meta["origin"] = resolved_origin
        meta["scope"] = scope
        meta["storage_scope"] = scope
        meta["subject_id"] = get_workspace().id
        meta["created_from"] = (
            "workshop_chat" if resolved_origin == "workshop" else "companion_chat"
        )
        _write_json(meta_path, meta)
    return {
        "created": bool(exercise_id),
        "exercise_id": exercise_id,
        "knowledge_point": knowledge_point,
        "subject_id": get_workspace().id,
        "origin": resolved_origin,
        "scope": scope,
        "stage": stage_id,
        "level_index": level_index,
    }


def _tool_update_readme(arguments: dict[str, Any]) -> dict[str, Any]:
    exercise_id = _resolve_exercise_id(arguments)
    markdown = str(arguments.get("markdown") or "")
    if not markdown.strip():
        raise ValueError("markdown is required.")
    directory = _exercise_dir(exercise_id)
    target = directory / "README.md"
    if target.exists():
        backup = directory / f"README{README_BACKUP_SUFFIX}"
        backup.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    target.write_text(markdown.strip() + "\n", encoding="utf-8")
    return {"exercise_id": exercise_id, "chars": len(markdown), "backup": True}


def _tool_write_lesson(arguments: dict[str, Any]) -> dict[str, Any]:
    exercise_id = _resolve_exercise_id(arguments)
    title = _trim(arguments.get("title"), 200)
    if not title:
        raise ValueError("title is required.")
    points = [
        _trim(point, 400)
        for point in (arguments.get("points") or [])
        if _trim(point, 400)
    ][:8]
    payload = {
        "title": title,
        "summary": _trim(arguments.get("summary")),
        "syntax": _trim(arguments.get("syntax"), 1500),
        "points": points,
        "pitfall": _trim(arguments.get("pitfall"), 800),
        "authored_at": _now(),
    }
    _write_json(_exercise_dir(exercise_id) / LESSON_FILE, payload)
    return {"exercise_id": exercise_id, "lesson": payload["title"]}


def _tool_write_mentor(arguments: dict[str, Any]) -> dict[str, Any]:
    exercise_id = _resolve_exercise_id(arguments)
    intro = _trim(arguments.get("intro"))
    if not intro:
        raise ValueError("intro is required.")
    steps = []
    for item in (arguments.get("steps") or [])[:6]:
        if not isinstance(item, dict):
            continue
        title = _trim(item.get("title"), 120)
        if not title:
            continue
        steps.append({"title": title, "body": _trim(item.get("body"), 600)})
    payload = {"intro": intro, "steps": steps, "authored_at": _now()}
    _write_json(_exercise_dir(exercise_id) / MENTOR_FILE, payload)
    return {"exercise_id": exercise_id, "steps": len(steps)}


def _tool_write_diagnosis(arguments: dict[str, Any]) -> dict[str, Any]:
    summary = _trim(arguments.get("summary"))
    if not summary:
        raise ValueError("summary is required.")
    payload = {
        "summary": summary,
        "weaknesses": [_trim(item, 200) for item in (arguments.get("weaknesses") or [])][:8],
        "next_steps": [_trim(item, 200) for item in (arguments.get("next_steps") or [])][:8],
        "authored_at": _now(),
        "source": "companion",
    }
    _write_json(get_workspace().root / DIAGNOSIS_FILE, payload)
    return {"summary_chars": len(summary), "weaknesses": len(payload["weaknesses"])}


EXECUTORS = {
    "list_exercises": _tool_list_exercises,
    "read_exercise": _tool_read_exercise,
    "create_practice": _tool_create_practice,
    "update_exercise_readme": _tool_update_readme,
    "write_lesson": _tool_write_lesson,
    "write_mentor": _tool_write_mentor,
    "write_diagnosis": _tool_write_diagnosis,
}


def execute_tool(
    name: str,
    arguments: dict[str, Any],
    *,
    origin: str = "course",
) -> dict[str, Any]:
    """Run one tool call. Errors are returned, never raised, so the chat survives."""
    executor = EXECUTORS.get(name)
    if executor is None:
        return {"ok": False, "error": f"Unknown tool: {name}"}
    try:
        clean_arguments = arguments if isinstance(arguments, dict) else {}
        if name == "list_exercises":
            result = _tool_list_exercises(clean_arguments, origin=origin)
        elif name == "create_practice":
            result = _tool_create_practice(clean_arguments, origin=origin)
        else:
            result = executor(clean_arguments)
    except KeyError as error:
        return {"ok": False, "error": f"Not found: {error}"}
    except (ValueError, OSError, RuntimeError) as error:
        return {"ok": False, "error": str(error)}
    return {"ok": True, **result}


def tool_summary_line(name: str, result: dict[str, Any]) -> str:
    """Short human-readable line describing what a tool call did."""
    labels = {
        "list_exercises": "列出关卡",
        "read_exercise": "读取关卡",
        "create_practice": "新建练习",
        "update_exercise_readme": "更新题面",
        "write_lesson": "写讲义",
        "write_mentor": "写协作建议",
        "write_diagnosis": "写诊断总结",
    }
    label = labels.get(name, name)
    if not result.get("ok"):
        return f"{label}失败：{result.get('error', 'unknown')}"
    if name == "create_practice":
        return (
            f"{label}（{result.get('scope', 'tutoring')}/"
            f"{result.get('stage', 'ai_practice')}）："
            f"{result.get('exercise_id', '')}"
        )
    target = (
        result.get("exercise_id")
        or result.get("knowledge_point")
        or result.get("lesson")
        or ""
    )
    return f"{label}：{target}" if target else f"{label}完成"
