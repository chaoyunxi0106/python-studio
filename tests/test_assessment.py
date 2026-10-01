from __future__ import annotations

import json

from python_studio.assessment import evaluate_assessment, normalize_assessment_items


def test_multiple_choice_assessment(tmp_path) -> None:
    exercise_dir = tmp_path / "exercise"
    exercise_dir.mkdir()
    (exercise_dir / "assessment.json").write_text(
        json.dumps(
            {
                "items": [
                    {
                        "id": "q1",
                        "type": "multiple_choice",
                        "question": "1 + 1 = ?",
                        "options": ["1", "2", "3"],
                        "explanation": "基础加法",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (exercise_dir / "solution.json").write_text(
        json.dumps({"q1": {"answer_index": 1}}),
        encoding="utf-8",
    )
    exercise = {"directory": str(exercise_dir)}

    passed = evaluate_assessment(exercise, {"q1": 1})
    failed = evaluate_assessment(exercise, {"q1": 0})

    assert passed["passed"] is True
    assert failed["passed"] is False


def test_assessment_normalization_rejects_invalid_model_items() -> None:
    items = normalize_assessment_items(
        [
            {
                "id": "bad",
                "type": "multiple_choice",
                "question": "invalid answer index",
                "options": ["A", "B"],
                "answer_index": 9,
            },
            {
                "id": "ok",
                "type": "unknown",
                "question": "explain this",
                "rubric": ["point", ""],
                "reference_answer": "answer",
            },
        ]
    )

    assert len(items) == 1
    assert items[0]["id"] == "ok"
    assert items[0]["type"] == "short_answer"
    assert items[0]["rubric"] == ["point"]
