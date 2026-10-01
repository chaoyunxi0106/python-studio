from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .assessment import normalize_assessment_items
from .companion import generate_and_create_practice
from .config import DeepSeekConfig, get_deepseek_config
from .exercise_layout import resolve_exercise_location
from .providers.deepseek import ProviderError, chat_json
from .workspace import get_workspace, reset_current_subject, set_current_subject


ACCENTS = ["#2ea043", "#2f81f7", "#d29922", "#a371f7", "#db61a2", "#f0883e"]


def _local_assessment(module: dict[str, Any]) -> list[dict[str, Any]]:
    concepts = list(module.get("concepts") or [module.get("title", "知识点")])
    items = []
    for index, concept in enumerate(concepts[:4], start=1):
        items.append(
            {
                "id": f"item_{index}",
                "type": "multiple_choice",
                "question": f"关于“{concept}”，下列说法最准确的是哪一项？",
                "options": [
                    "它只用于记忆定义，不需要理解适用条件",
                    "需要同时理解定义、条件和典型应用",
                    "掌握名称就等同于掌握知识点",
                    "出现异常时不需要检查前提条件",
                ],
                "answer_index": 1,
                "explanation": "概念学习需要同时理解定义、条件和应用。",
            }
        )
    items.append(
        {
            "id": "item_text",
            "type": "short_answer",
            "question": f"用自己的话解释“{module.get('title')}”的核心思想，并举一个应用例子。",
            "rubric": [
                "说明核心定义",
                "解释适用条件",
                "给出具体例子",
            ],
            "reference_answer": "参考模块知识点和材料说明。",
        }
    )
    return items


def _call_deepseek_assessment(
    module: dict[str, Any],
    blueprint: dict[str, Any],
    config: DeepSeekConfig,
    extra_context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    system_prompt = """
你是概念型课程练习设计器。请根据模块知识点设计评估题。
至少包含 2 道选择题和 1 道文本题。文本题必须有评分标准。
如果提供了 extra_context，必须优先使用其中的节点、父节点、分支和近期对话，
题目要检验当前具体问题，而不是输出通用的“什么是某概念”。
选择题的干扰项应来自常见误区或相近概念。
只输出 JSON：
{
  "items": [
    {
      "id": "item_id",
      "type": "multiple_choice",
      "question": "题干",
      "options": ["A", "B", "C", "D"],
      "answer_index": 0,
      "explanation": "解释"
    },
    {
      "id": "text_id",
      "type": "short_answer",
      "question": "题干",
      "rubric": ["评分点"],
      "reference_answer": "参考答案"
    }
  ]
}
最多 8 道题。不要输出 Markdown。
""".strip()
    payload = {
        "course": blueprint.get("title"),
        "module": module,
        "mode": blueprint.get("mode"),
        "extra_context": extra_context or {},
    }
    result = chat_json(
        config,
        [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(payload, ensure_ascii=False),
            },
        ],
        temperature=0.2,
        max_tokens=1800,
    )
    return normalize_assessment_items(result.get("items"))


def _write_assessment_exercise(
    workspace_root: Path,
    *,
    module: dict[str, Any],
    module_index: int,
    items: list[dict[str, Any]],
    exercise_id: str,
    scope: str = "course",
) -> str:
    items = normalize_assessment_items(items)
    location = resolve_exercise_location(
        scope=scope,
        stage=str(module.get("id") or "workshop"),
    )
    exercise_dir = location.directory / exercise_id
    exercise_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "id": exercise_id,
        "active": True,
        "generated": True,
        "subject_id": location.course_id,
        "course_id": location.course_id,
        "course_slug": location.course_slug,
        "course_title": location.course_title,
        "scope": location.scope,
        "storage_scope": location.scope,
        "relative_directory": location.relative_directory,
        "storage_path": (
            f"{location.relative_directory}/{exercise_id}"
            if location.relative_directory
            else exercise_id
        ),
        "origin": "workshop" if location.scope == "workshop" else "course",
        "exercise_type": "assessment",
        "title": f"{module.get('title', '概念模块')} · 概念与思维训练",
        "stage": module.get("id", f"module_{module_index}"),
        "module_id": location.module_id,
        "module_number": location.module_number,
        "module_title": location.module_title,
        "level_index": location.level_index,
        "level_id": location.level_id,
        "order": module_index * 100 + 1,
        "minutes": 25,
        "summary": module.get("goal", "概念理解与应用练习。"),
        "concepts": list(module.get("concepts") or []),
        "hints": ["先解释概念，再检查适用条件和边界。"],
        "domain": "command",
        "starter_file": "answers.json",
        "test_file": "check.py",
        "solution_file": "solution.json",
        "analysis_mode": "generic",
        "test_command": ["{python}", "check.py"],
    }
    (exercise_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (exercise_dir / "assessment.json").write_text(
        json.dumps({"items": items}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (exercise_dir / "answers.json").write_text("{}\n", encoding="utf-8")
    solution = {
        item["id"]: {
            "answer_index": item.get("answer_index"),
            "reference_answer": item.get("reference_answer"),
            "rubric": item.get("rubric", []),
        }
        for item in items
    }
    (exercise_dir / "solution.json").write_text(
        json.dumps(solution, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (exercise_dir / "check.py").write_text(
        'print("Concept assessment is evaluated by the platform.")\n',
        encoding="utf-8",
    )
    lines = [
        f"# {meta['title']}",
        "",
        meta["summary"],
        "",
        "## 题目",
        "",
    ]
    for index, item in enumerate(items, start=1):
        lines.append(f"{index}. {item.get('question', '')}")
    (exercise_dir / "README.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    return str(exercise_dir)


def _write_roadmap(workspace_root: Path, blueprint: dict[str, Any]) -> None:
    stages = []
    for index, module in enumerate(blueprint.get("modules") or []):
        stages.append(
            {
                "id": module.get("id", f"module_{index + 1}"),
                "module": index + 1,
                "title": module.get("title", f"模块 {index + 1}"),
                "description": module.get("goal", ""),
                "availability": "active",
                "accent": ACCENTS[index % len(ACCENTS)],
            }
        )
    curriculum_dir = workspace_root / "curriculum"
    curriculum_dir.mkdir(parents=True, exist_ok=True)
    (curriculum_dir / "roadmap.json").write_text(
        json.dumps({"stages": stages}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    outline = [f"# {blueprint.get('title')}", "", blueprint.get("summary", "")]
    for module in blueprint.get("modules") or []:
        outline.extend(
            [
                "",
                f"## {module.get('title')}",
                "",
                module.get("goal", ""),
                "",
                *[f"- {concept}" for concept in module.get("concepts") or []],
            ]
        )
    (curriculum_dir / "KNOWLEDGE_OUTLINE.md").write_text(
        "\n".join(outline) + "\n",
        encoding="utf-8",
    )


def ensure_workshop_stage() -> None:
    workspace = get_workspace()
    roadmap_path = workspace.curriculum_dir / "roadmap.json"
    if roadmap_path.exists():
        roadmap = json.loads(roadmap_path.read_text(encoding="utf-8"))
    else:
        roadmap = {"stages": []}
    if not any(stage.get("id") == "workshop" for stage in roadmap["stages"]):
        roadmap["stages"].append(
            {
                "id": "workshop",
                "module": len(roadmap["stages"]) + 1,
                "title": "创造工坊",
                "description": "由伴读 AI 对话生成、持续生长的知识节点和练习。",
                "availability": "active",
                "accent": "#db61a2",
            }
        )
    roadmap_path.parent.mkdir(parents=True, exist_ok=True)
    roadmap_path.write_text(
        json.dumps(roadmap, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def ensure_course_practice_stage() -> None:
    """Ensure the current course has a visible bucket for scoped AI practice."""
    workspace = get_workspace()
    roadmap_path = workspace.curriculum_dir / "roadmap.json"
    if roadmap_path.exists():
        roadmap = json.loads(roadmap_path.read_text(encoding="utf-8"))
    else:
        roadmap = {"stages": []}
    if not any(stage.get("id") == "ai_practice" for stage in roadmap["stages"]):
        roadmap["stages"].append(
            {
                "id": "ai_practice",
                "module": len(roadmap["stages"]) + 1,
                "title": "AI 专属补练",
                "description": "由伴学 AI 针对当前科目生成的正式补练。",
                "availability": "active",
                "accent": "#6f8cff",
            }
        )
    roadmap_path.parent.mkdir(parents=True, exist_ok=True)
    roadmap_path.write_text(
        json.dumps(roadmap, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _mark_workshop_origin(exercise_id: str) -> None:
    """Tag a generated exercise so course views can keep it out of their records."""
    from .catalog import find_exercise

    try:
        exercise = find_exercise(exercise_id, include_inactive=True)
    except KeyError:
        return
    meta_path = Path(exercise["directory"]) / "meta.json"
    if not meta_path.exists():
        return
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["origin"] = "workshop"
    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def materialize_assessment_node(
    *,
    node_id: str,
    title: str,
    summary: str,
    node_type: str = "concept",
    context: dict[str, Any] | None = None,
) -> str:
    workspace = get_workspace()
    module = {
        "id": "workshop",
        "title": title,
        "goal": summary,
        "concepts": [title],
        "activities": [
            {
                "title": title,
                "type": (
                    "proof" if node_type == "proof" else "short_answer"
                ),
                "objective": summary,
                "deliverable": "完整答案和推理过程。",
            }
        ],
    }
    config = get_deepseek_config()
    try:
        items = _call_deepseek_assessment(
            module,
            {
                "title": title,
                "summary": summary,
                "mode": "conceptual",
                "materials": (context or {}).get("source_material_excerpt", ""),
            },
            config,
            extra_context=context,
        )
    except (ProviderError, ValueError, KeyError, json.JSONDecodeError):
        items = _local_assessment(module)
    exercise_id = f"workshop_{node_id}_concept"
    _write_assessment_exercise(
        workspace.root,
        module=module,
        module_index=90,
        items=items,
        exercise_id=exercise_id,
        scope="workshop",
    )
    _mark_workshop_origin(exercise_id)
    ensure_workshop_stage()
    return exercise_id


def materialize_subject(subject_id: str) -> dict[str, Any]:
    workspace = get_workspace(subject_id)
    manifest_path = workspace.root / "subject.json"
    if not manifest_path.exists():
        raise KeyError("Subject manifest not found.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    blueprint = manifest.get("blueprint") or {}
    _write_roadmap(workspace.root, blueprint)

    token = set_current_subject(subject_id)
    created_exercises = []
    config = get_deepseek_config()
    if not config.configured:
        reset_current_subject(token)
        raise ValueError(
            "AI 服务尚未配置，无法生成课程题目。请先在“设置 > 模型”保存 API 密钥。"
        )
    try:
        mode = str(blueprint.get("mode", "programming"))
        for module_index, module in enumerate(blueprint.get("modules") or [], start=1):
            stage_id = module.get("id", f"module_{module_index}")
            activity_titles = [
                activity.get("title", "")
                for activity in module.get("activities") or []
            ]
            if mode in {"programming", "hybrid"}:
                try:
                    created = generate_and_create_practice(
                        [],
                        knowledge_point=module.get("title", "综合实操"),
                        source_exercise_id=None,
                        source_task="；".join(activity_titles),
                        config=config,
                        origin="course",
                        stage=stage_id,
                        scope="course",
                    )
                    meta_path = Path(created["directory"]) / "meta.json"
                    generated_meta = json.loads(
                        meta_path.read_text(encoding="utf-8")
                    )
                    generated_meta["stage"] = stage_id
                    generated_meta["order"] = module_index * 100
                    generated_meta["title"] = (
                        f"{module.get('title', '模块')} · 综合实操"
                    )
                    generated_meta["materialized"] = True
                    meta_path.write_text(
                        json.dumps(generated_meta, ensure_ascii=False, indent=2)
                        + "\n",
                        encoding="utf-8",
                    )
                    created_exercises.append(created["id"])
                except (ValueError, OSError):
                    pass
            if mode in {"conceptual", "hybrid"}:
                try:
                    items = _call_deepseek_assessment(module, blueprint, config)
                except (ProviderError, ValueError, KeyError, json.JSONDecodeError):
                    items = _local_assessment(module)
                exercise_id = f"{workspace.slug}_{stage_id}_concept"
                _write_assessment_exercise(
                    workspace.root,
                    module=module,
                    module_index=module_index,
                    items=items,
                    exercise_id=exercise_id,
                    scope="course",
                )
                created_exercises.append(exercise_id)
    finally:
        reset_current_subject(token)

    manifest["materialized"] = True
    manifest["exercise_count"] = len(created_exercises)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "subject_id": subject_id,
        "workspace": str(workspace.root),
        "exercises": created_exercises,
    }
