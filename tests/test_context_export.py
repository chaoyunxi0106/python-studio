from __future__ import annotations

from python_studio.context_export import compact_chat_contexts


def test_compact_contexts_limits_items_and_fields() -> None:
    items = [
        {
            "attempt_id": index,
            "exercise_id": f"exercise-{index}",
            "title": f"Exercise {index}",
            "instructions": "x" * 3000,
            "my_code": "y" * 4000,
            "task_results": list(range(20)),
            "ai_review": {"code_issues": ["a", "b", "c", "d"]},
        }
        for index in range(6)
    ]
    compacted = compact_chat_contexts({"items": items})
    assert len(compacted) == 4
    assert len(compacted[0]["instructions"]) == 1000
    assert len(compacted[0]["my_code"]) == 1600
    assert compacted[0]["ai_review"]["code_issues"] == ["a", "b"]

