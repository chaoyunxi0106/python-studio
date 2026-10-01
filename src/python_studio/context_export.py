from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .catalog import read_exercise_documentation, read_exercise_solution
from .domain_profiles import profile_for_exercise
from .knowledge import knowledge_for_exercise


def build_exercise_context(
    exercise: dict[str, Any],
    attempt: dict[str, Any] | None = None,
) -> dict[str, Any]:
    exercise_dir = Path(exercise["directory"])
    profile = profile_for_exercise(exercise)
    starter_path = exercise_dir / profile.starter_file
    starter_code = (
        starter_path.read_text(encoding="utf-8", errors="replace")
        if starter_path.exists()
        else ""
    )
    context = {
        "exercise_id": exercise["id"],
        "attempt_id": attempt.get("id") if attempt else None,
        "title": exercise["title"],
        "summary": exercise.get("summary", ""),
        "knowledge": knowledge_for_exercise(exercise),
        "instructions": read_exercise_documentation(exercise)[:6000],
        "starter_code": starter_code[:6000],
        "my_code": str(attempt.get("code_snapshot", ""))[:6000] if attempt else "",
        "task_results": attempt.get("task_results", []) if attempt else [],
        "test_output_excerpt": (
            str(attempt.get("output", ""))[-1800:] if attempt else ""
        ),
        "ai_review": attempt.get("ai_analysis") if attempt else None,
        "standard_solution": read_exercise_solution(exercise),
        "last_checked": attempt.get("checked_at") if attempt else None,
        "passed": attempt.get("passed") if attempt else None,
    }
    return context


def context_to_markdown(context: dict[str, Any]) -> str:
    knowledge = context.get("knowledge") or {}
    ai_review = context.get("ai_review") or {}
    lines = [
        f"# {context.get('title', '题目上下文')}",
        "",
        f"- 练习 ID：`{context.get('exercise_id', '')}`",
        f"- 最近运行：{context.get('last_checked') or '暂无'}",
        f"- 运行结果：{'通过' if context.get('passed') else '未通过或未运行'}",
        "",
        "## 题目说明",
        "",
        context.get("instructions") or context.get("summary") or "暂无",
        "",
        "## 知识点",
        "",
        knowledge.get("summary", ""),
        "",
        "## 我的代码",
        "",
        "```python",
        context.get("my_code") or context.get("starter_code") or "",
        "```",
        "",
        "## 测试结果",
        "",
        "```text",
        context.get("test_output_excerpt") or "暂无",
        "```",
        "",
        "## AI 审查",
        "",
    ]
    if ai_review:
        lines.append(ai_review.get("summary", "暂无摘要"))
        for label, key in (
            ("题目差距", "requirement_gaps"),
            ("代码问题", "code_issues"),
            ("隐藏风险", "hidden_risks"),
            ("已掌握", "strengths"),
        ):
            values = ai_review.get(key) or []
            if values:
                lines.append(f"\n### {label}")
                lines.extend(f"- {value}" for value in values)
    else:
        lines.append("尚未生成 AI 审查。")

    solution = context.get("standard_solution")
    if solution:
        lines.extend(
            [
                "",
                "## 标准答案",
                "",
                "```python",
                solution,
                "```",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def compact_context_json(context: dict[str, Any], limit: int = 12000) -> str:
    payload = json.dumps(context, ensure_ascii=False)
    if len(payload) <= limit:
        return payload
    return payload[:limit] + "...[truncated]"


def compact_chat_context(context: dict[str, Any]) -> dict[str, Any]:
    knowledge = context.get("knowledge") or {}
    ai_review = context.get("ai_review") or {}
    return {
        "exercise_id": context.get("exercise_id"),
        "attempt_id": context.get("attempt_id"),
        "title": context.get("title"),
        "summary": str(context.get("summary", ""))[:300],
        "knowledge": {
            "title": knowledge.get("title"),
            "summary": str(knowledge.get("summary", ""))[:500],
            "points": list(knowledge.get("points") or [])[:4],
            "pitfall": str(knowledge.get("pitfall", ""))[:300],
        },
        "instructions": str(context.get("instructions", ""))[:1500],
        "my_code": str(context.get("my_code", ""))[:2200],
        "task_results": list(context.get("task_results") or [])[:8],
        "test_output_excerpt": str(context.get("test_output_excerpt", ""))[:700],
        "ai_review": (
            {
                "summary": str(ai_review.get("summary", ""))[:700],
                "requirement_gaps": list(ai_review.get("requirement_gaps") or [])[:3],
                "code_issues": list(ai_review.get("code_issues") or [])[:3],
                "hidden_risks": list(ai_review.get("hidden_risks") or [])[:3],
                "strengths": list(ai_review.get("strengths") or [])[:3],
            }
            if ai_review
            else None
        ),
        "last_checked": context.get("last_checked"),
        "passed": context.get("passed"),
    }


def compact_chat_contexts(contexts: Any) -> list[dict[str, Any]]:
    if isinstance(contexts, dict) and isinstance(contexts.get("items"), list):
        raw_items = contexts["items"]
    elif isinstance(contexts, list):
        raw_items = contexts
    elif isinstance(contexts, dict):
        raw_items = [contexts]
    else:
        raw_items = []

    compacted = []
    seen = set()
    for context in raw_items[-4:]:
        if not isinstance(context, dict):
            continue
        identity = (context.get("attempt_id"), context.get("exercise_id"))
        if identity in seen:
            continue
        seen.add(identity)
        item = compact_chat_context(context)
        item["instructions"] = item["instructions"][:1000]
        item["my_code"] = item["my_code"][:1600]
        item["test_output_excerpt"] = item["test_output_excerpt"][:500]
        if item.get("ai_review"):
            for key in (
                "requirement_gaps",
                "code_issues",
                "hidden_risks",
                "strengths",
            ):
                item["ai_review"][key] = item["ai_review"][key][:2]
        compacted.append(item)
    return compacted
