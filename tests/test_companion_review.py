from __future__ import annotations

from python_studio import companion
from python_studio.config import DeepSeekConfig


def test_review_prompt_builds_with_json_example(monkeypatch) -> None:
    captured = {}

    def fake_chat_json(config, messages, *, temperature, max_tokens):
        captured["messages"] = messages
        return {
            "summary": "ok",
            "requirement_gaps": [],
            "code_issues": [],
            "hidden_risks": [],
            "strengths": [],
        }

    monkeypatch.setattr(companion, "chat_json", fake_chat_json)
    analysis = companion._call_deepseek_attempt(
        {
            "title": "示例题",
            "concepts": ["return"],
            "passed": False,
            "task_results": [{"task_name": "value", "passed": False}],
            "requirements": "必须返回结果。",
            "code_snapshot": "def value():\n    print('x')",
            "output": "AssertionError",
            "domain_name": "Python",
            "domain_context": "基础语法",
        },
        DeepSeekConfig(
            api_key="test-key",
            base_url="https://api.deepseek.com",
            model="deepseek-chat",
            timeout_seconds=10,
            history_limit=20,
        ),
    )

    assert analysis["summary"] == "ok"
    assert "只输出 JSON" in captured["messages"][0]["content"]
