from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

from .ai_jobs import run_ai_operation
from .config import DeepSeekConfig, get_deepseek_config
from .paths import DATABASE_FILE
from .providers.deepseek import ProviderError, chat_json
from .workspace import create_subject_workspace, get_workspace, list_workspaces


MODES = {"auto", "programming", "conceptual", "hybrid"}
ACTIVITY_TYPES = {
    "code_task",
    "code_debug",
    "code_refactor",
    "mini_project",
    "multiple_choice",
    "short_answer",
    "proof",
    "numeric_exercise",
    "concept_map",
    "reflection",
}


def _slug(value: str, fallback: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower()).strip("_")
    return slug[:60] or fallback


def _local_blueprint(
    subject: str,
    material: str,
    requested_mode: str,
) -> dict[str, Any]:
    math_keywords = ("数学", "优化", "证明", "定理", "概率", "统计", "线性代数")
    mode = requested_mode
    if mode == "auto":
        mode = "conceptual" if any(
            keyword in subject for keyword in math_keywords
        ) else "programming"
    activity_type = (
        "multiple_choice"
        if mode == "conceptual"
        else "code_task"
    )
    second_activity = "short_answer" if mode == "conceptual" else "code_debug"
    return {
        "title": subject,
        "mode": mode,
        "summary": f"围绕“{subject}”生成的本地学习蓝图。",
        "duration_weeks": 4,
        "objectives": [
            f"理解 {subject} 的核心概念",
            f"通过练习应用 {subject} 的知识",
            "能够检查和解释自己的答案",
        ],
        "assessment_strategy": (
            "选择题检查概念，文本回答检查解释与推理。"
            if mode == "conceptual"
            else "自动测试检查代码，代码审查检查未覆盖问题。"
        ),
        "modules": [
            {
                "id": "foundation",
                "title": "基础概念",
                "goal": f"建立 {subject} 的基本认识。",
                "concepts": [f"{subject} 基本概念"],
                "activities": [
                    {
                        "title": "概念诊断",
                        "type": activity_type,
                        "objective": "识别核心概念和常见误区。",
                        "deliverable": "完成一组基础练习。",
                    },
                    {
                        "title": "知识运用",
                        "type": second_activity,
                        "objective": "把概念应用到简单场景。",
                        "deliverable": "给出答案并说明理由。",
                    },
                ],
            },
            {
                "id": "application",
                "title": "综合应用",
                "goal": f"在综合问题中使用 {subject}。",
                "concepts": [f"{subject} 综合应用"],
                "activities": [
                    {
                        "title": "综合训练",
                        "type": (
                            "mini_project"
                            if mode == "programming"
                            else "proof"
                        ),
                        "objective": "组合多个知识点完成完整任务。",
                        "deliverable": "可检查的综合答案或项目。",
                    }
                ],
            },
        ],
        "capstone": f"完成一个能够展示 {subject} 学习成果的作品或解释报告。",
        "source_excerpt": material[:1000],
    }


def _normalize_blueprint(
    payload: dict[str, Any],
    *,
    subject: str,
    material: str,
    requested_mode: str,
) -> dict[str, Any]:
    mode = str(payload.get("mode") or requested_mode or "programming")
    if mode not in MODES or mode == "auto":
        mode = "programming"
    modules = []
    for module_index, raw_module in enumerate(
        list(payload.get("modules") or [])[:6],
        start=1,
    ):
        if not isinstance(raw_module, dict):
            continue
        activities = []
        for activity_index, raw_activity in enumerate(
            list(raw_module.get("activities") or [])[:6],
            start=1,
        ):
            if not isinstance(raw_activity, dict):
                continue
            activity_type = str(raw_activity.get("type") or "short_answer")
            if activity_type not in ACTIVITY_TYPES:
                activity_type = "short_answer"
            activities.append(
                {
                    "title": str(
                        raw_activity.get("title")
                        or f"练习 {module_index}.{activity_index}"
                    )[:120],
                    "type": activity_type,
                    "objective": str(raw_activity.get("objective") or "")[:500],
                    "deliverable": str(raw_activity.get("deliverable") or "")[:500],
                }
            )
        modules.append(
            {
                "id": _slug(
                    str(raw_module.get("id") or raw_module.get("title") or ""),
                    f"module_{module_index}",
                ),
                "title": str(
                    raw_module.get("title") or f"第 {module_index} 章"
                )[:120],
                "goal": str(raw_module.get("goal") or "")[:500],
                "concepts": [
                    str(item)[:120]
                    for item in list(raw_module.get("concepts") or [])[:10]
                ],
                "activities": activities,
            }
        )
    if not modules:
        return _local_blueprint(subject, material, requested_mode)
    return {
        "title": str(payload.get("title") or subject)[:120],
        "mode": mode,
        "summary": str(payload.get("summary") or "")[:1000],
        "duration_weeks": max(
            1,
            min(int(payload.get("duration_weeks", 4)), 52),
        ),
        "objectives": [
            str(item)[:300]
            for item in list(payload.get("objectives") or [])[:8]
        ],
        "assessment_strategy": str(
            payload.get("assessment_strategy") or ""
        )[:1000],
        "modules": modules,
        "capstone": str(payload.get("capstone") or "")[:1000],
        "source_excerpt": material[:1000],
    }


def _call_deepseek_subject(
    subject: str,
    material: str,
    requested_mode: str,
    config: DeepSeekConfig,
) -> dict[str, Any]:
    system_prompt = """
你是学习平台课程编译器。把用户输入的学习主题或知识材料转换成可执行学习蓝图。

模式判断：
- programming：以编写、调试、重构和项目实操为核心。
- conceptual：以概念理解、推理、证明、计算和文本解释为核心。
- hybrid：同时包含编程实操和理论理解。

练习类型只能使用：
code_task, code_debug, code_refactor, mini_project,
multiple_choice, short_answer, proof, numeric_exercise,
concept_map, reflection。

输出 JSON：
{
  "title": "课程名称",
  "mode": "programming|conceptual|hybrid",
  "summary": "课程概述",
  "duration_weeks": 4,
  "objectives": ["目标"],
  "assessment_strategy": "检查和评价策略",
  "modules": [
    {
      "id": "module_id",
      "title": "章节名称",
      "goal": "章节目标",
      "concepts": ["知识点"],
      "activities": [
        {
          "title": "练习名称",
          "type": "练习类型",
          "objective": "训练目标",
          "deliverable": "学生需要提交的结果"
        }
      ]
    }
  ],
  "capstone": "综合项目或综合证明"
}

最多 6 个模块，每章最多 6 个练习。不要输出 Markdown。
""".strip()
    request_body = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "subject": subject,
                        "requested_mode": requested_mode,
                        "material": material[:12000],
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        "temperature": 0.2,
        "max_tokens": 3200,
        "response_format": {"type": "json_object"},
    }
    try:
        return chat_json(
            config,
            request_body["messages"],
            temperature=float(request_body["temperature"]),
            max_tokens=int(request_body["max_tokens"]),
        )
    except ProviderError as error:
        raise RuntimeError("Subject compilation failed.") from error


def compile_subject(
    *,
    subject: str,
    material: str,
    requested_mode: str = "auto",
) -> dict[str, Any]:
    clean_subject = subject.strip()
    clean_material = material.strip()
    if not clean_subject and not clean_material:
        raise ValueError("Subject or material is required.")
    if requested_mode not in MODES:
        raise ValueError("Unsupported learning mode.")
    if not clean_subject:
        clean_subject = clean_material[:60].strip()

    config = get_deepseek_config()
    if not config.configured:
        raise ValueError(
            "AI 服务尚未配置。请先到“设置 > 模型”填写并保存 API 密钥，"
            "再回来从零生成学习科目。"
        )

    def operation() -> dict[str, Any]:
        if config.configured:
            try:
                return _call_deepseek_subject(
                    clean_subject,
                    clean_material,
                    requested_mode,
                    config,
                )
            except RuntimeError:
                return _local_blueprint(
                    clean_subject,
                    clean_material,
                    requested_mode,
                )
        return _local_blueprint(
            clean_subject,
            clean_material,
            requested_mode,
        )

    payload = run_ai_operation(
        "subject_blueprint",
        {
            "subject": clean_subject,
            "mode": requested_mode,
            "material": clean_material[:12000],
        },
        operation,
        use_cache=True,
    )
    blueprint = _normalize_blueprint(
        payload,
        subject=clean_subject,
        material=clean_material,
        requested_mode=requested_mode,
    )
    workspace = create_subject_workspace(
        title=blueprint["title"],
        mode=blueprint["mode"],
        blueprint=blueprint,
        source_material=clean_material,
    )
    return {
        "id": workspace.id,
        "slug": workspace.slug,
        "blueprint": blueprint,
    }


def list_subjects() -> list[dict[str, Any]]:
    if len(list_workspaces()) == 1 and DATABASE_FILE.exists():
        try:
            connection = sqlite3.connect(DATABASE_FILE)
            connection.row_factory = sqlite3.Row
            legacy_rows = connection.execute(
                """
                SELECT title, mode, source_material, blueprint_json
                FROM subjects
                ORDER BY id
                """
            ).fetchall()
            connection.close()
        except sqlite3.Error:
            legacy_rows = []
        for row in legacy_rows:
            blueprint = json.loads(row["blueprint_json"])
            create_subject_workspace(
                title=str(row["title"]),
                mode=str(row["mode"]),
                blueprint=blueprint,
                source_material=str(row["source_material"] or ""),
            )
    subjects = []
    for workspace in list_workspaces():
        if workspace.is_default:
            continue
        manifest_path = workspace.root / "subject.json"
        manifest = {}
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                manifest = {}
        subjects.append(
            {
                "id": workspace.id,
                "slug": workspace.slug,
                "title": workspace.title,
                "summary": manifest.get("blueprint", {}).get("summary", ""),
                "mode": workspace.mode,
                "created_at": manifest.get("created_at"),
            }
        )
    return sorted(subjects, key=lambda item: item["created_at"] or "", reverse=True)


def get_subject(subject_id: int | str) -> dict[str, Any] | None:
    try:
        workspace = get_workspace(str(subject_id))
    except KeyError:
        return None
    manifest_path = workspace.root / "subject.json"
    if not manifest_path.exists():
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {
        "id": workspace.id,
        "slug": workspace.slug,
        "title": workspace.title,
        "summary": manifest.get("blueprint", {}).get("summary", ""),
        "mode": workspace.mode,
        "source_material": manifest.get("source_material", ""),
        "blueprint": manifest.get("blueprint", {}),
        "created_at": manifest.get("created_at"),
        "updated_at": manifest.get("created_at"),
    }
