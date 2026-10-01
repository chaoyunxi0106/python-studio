from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .ai_jobs import run_ai_operation
from .config import DeepSeekConfig, get_deepseek_config
from .providers.deepseek import ProviderError, chat_json


ITEM_TYPES = {"multiple_choice", "short_answer", "proof"}


def normalize_assessment_items(
    items: Any,
    *,
    require_answers: bool = True,
) -> list[dict[str, Any]]:
    """Constrain model-produced assessment data before it reaches the UI."""
    if not isinstance(items, list):
        raise ValueError("Assessment items must be a list.")
    normalized = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(items[:8], start=1):
        if not isinstance(raw, dict):
            continue
        item_id = str(raw.get("id") or f"item_{index}").strip()[:80]
        question = str(raw.get("question") or "").strip()[:2000]
        if not item_id or not question or item_id in seen_ids:
            continue
        item_type = str(raw.get("type") or "short_answer").strip().lower()
        if item_type not in ITEM_TYPES:
            item_type = "short_answer"
        if item_type == "multiple_choice":
            options = [
                str(option).strip()[:500]
                for option in list(raw.get("options") or [])[:8]
                if str(option).strip()
            ]
            try:
                answer_index = int(raw.get("answer_index"))
            except (TypeError, ValueError):
                answer_index = None
            if len(options) < 2:
                continue
            if answer_index is not None and not 0 <= answer_index < len(options):
                if require_answers:
                    continue
                answer_index = None
            if answer_index is None and require_answers:
                continue
            item = {
                "id": item_id,
                "type": "multiple_choice",
                "question": question,
                "options": options,
                "answer_index": answer_index,
                "explanation": str(raw.get("explanation") or "").strip()[:1200],
            }
        else:
            item = {
                "id": item_id,
                "type": item_type,
                "question": question,
                "rubric": [
                    str(point).strip()[:300]
                    for point in list(raw.get("rubric") or [])[:8]
                    if str(point).strip()
                ],
                "reference_answer": str(
                    raw.get("reference_answer") or ""
                ).strip()[:4000],
            }
        seen_ids.add(item_id)
        normalized.append(item)
    if not normalized:
        raise ValueError("Assessment does not contain any valid items.")
    return normalized


def load_assessment(exercise: dict[str, Any]) -> dict[str, Any] | None:
    path = Path(exercise["directory"]) / "assessment.json"
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        **payload,
        "items": normalize_assessment_items(
            payload.get("items", []),
            require_answers=False,
        ),
    }


def _grade_text_with_ai(
    *,
    item: dict[str, Any],
    answer: str,
    config: DeepSeekConfig,
) -> dict[str, Any]:
    system_prompt = """
你是严格的学科文本答案评审员。根据题目、参考答案和评分标准评价学生回答。
只输出 JSON：
{"score": 0到100整数, "feedback": "简短反馈", "missing": ["缺失点"]}
不要泄露完整参考作文，只给针对当前回答的反馈。
""".strip()
    return chat_json(
        config,
        [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "item": item,
                        "student_answer": answer,
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        temperature=0.1,
        max_tokens=700,
    )


def evaluate_assessment(
    exercise: dict[str, Any],
    answers: dict[str, Any],
) -> dict[str, Any]:
    payload = load_assessment(exercise)
    if payload is None:
        raise ValueError("Assessment data is missing.")
    solution_path = Path(exercise["directory"]) / "solution.json"
    solution = (
        json.loads(solution_path.read_text(encoding="utf-8"))
        if solution_path.exists()
        else {}
    )
    config = get_deepseek_config()
    results = []
    passed_count = 0
    for item in payload.get("items", []):
        item_id = str(item.get("id"))
        answer = answers.get(item_id)
        if item.get("type") == "multiple_choice":
            expected = solution.get(item_id, {}).get("answer_index")
            passed = answer == expected
            results.append(
                {
                    "item_id": item_id,
                    "type": "multiple_choice",
                    "passed": passed,
                    "answer": answer,
                    "expected": expected,
                    "feedback": (
                        item.get("explanation", "")
                        if not passed
                        else "选择正确。"
                    ),
                }
            )
        else:
            text = str(answer or "").strip()
            if not text:
                evaluation = {
                    "score": 0,
                    "feedback": "没有填写文本答案。",
                    "missing": list(item.get("rubric") or []),
                }
            elif config.configured:
                try:
                    evaluation = run_ai_operation(
                        "assessment_text_grading",
                        {"item_id": item_id, "answer": text, "item": item},
                        lambda: _grade_text_with_ai(
                            item=item,
                            answer=text,
                            config=config,
                        ),
                        use_cache=True,
                    )
                except ProviderError:
                    evaluation = {
                        "score": min(100, 40 + len(text)),
                        "feedback": "模型评分失败，使用基础完成度评价。",
                        "missing": [],
                    }
            else:
                evaluation = {
                    "score": min(100, 40 + len(text)),
                    "feedback": "已记录文本答案；未配置模型，使用基础完成度评价。",
                    "missing": [],
                }
            passed = int(evaluation.get("score", 0)) >= 60
            results.append(
                {
                    "item_id": item_id,
                    "type": item.get("type", "short_answer"),
                    "passed": passed,
                    **evaluation,
                }
            )
        if results[-1]["passed"]:
            passed_count += 1

    total = len(results)
    return {
        "passed": total > 0 and passed_count == total,
        "passed_count": passed_count,
        "total": total,
        "results": results,
    }
