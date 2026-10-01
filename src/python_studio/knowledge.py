from __future__ import annotations

from typing import Any


def knowledge_for_exercise(exercise: dict[str, Any]) -> dict[str, Any]:
    """Return AI-authored lesson content, then metadata, then a generic stub."""
    from .authoring import authored_lesson

    authored = authored_lesson(exercise)
    if authored:
        return authored

    embedded = exercise.get("knowledge")
    if isinstance(embedded, dict) and embedded.get("title"):
        return embedded

    return {
        "title": exercise.get("title", "当前知识点"),
        "summary": exercise.get("summary", ""),
        "syntax": "",
        "points": list(exercise.get("concepts") or []),
        "pitfall": "先阅读题目契约，再开始修改代码。",
    }
