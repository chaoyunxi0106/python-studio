from __future__ import annotations

import json

from python_studio import authoring, companion, config, workspace
from python_studio.catalog import catalog_payload
from python_studio.config import DeepSeekConfig


def enable_fake_ai(monkeypatch) -> None:
    monkeypatch.setattr(
        config,
        "get_deepseek_config",
        lambda: DeepSeekConfig(
            api_key="test-key",
            base_url="https://api.deepseek.com",
            model="deepseek-chat",
            timeout_seconds=10,
            history_limit=20,
        ),
    )
    monkeypatch.setattr(
        companion,
        "_call_deepseek_practice",
        lambda *args, **kwargs: {
            "title": "Generated practice",
            "summary": "Generated from test context.",
            "minutes": 20,
            "knowledge": {
                "title": "generated",
                "summary": "Generated knowledge.",
                "syntax": "",
                "points": ["Use the generated contract."],
                "pitfall": "Do not return a placeholder.",
            },
            "hints": ["Resolve the task."],
            "tasks": [
                {
                    "title": "Generated task",
                    "instruction": "Return the expected value.",
                    "function_name": "resolve_task",
                    "parameters": [],
                    "cases": [{"args": [], "expected": "done"}],
                    "reference": "def resolve_task():\n    return 'done'",
                    "hint": "Return a literal value.",
                }
            ],
        },
    )


def make_subject(tmp_path, monkeypatch):
    subjects_dir = tmp_path / "subjects"
    monkeypatch.setattr(workspace, "SUBJECTS_DIR", subjects_dir)
    monkeypatch.setattr(workspace, "SUBJECT_REGISTRY", subjects_dir / "registry.json")
    target = workspace.create_subject_workspace(
        title="Generation Scope",
        mode="programming",
        blueprint={"mode": "programming", "modules": []},
        source_material="test",
    )
    (target.curriculum_dir / "roadmap.json").write_text(
        json.dumps(
            {
                "stages": [
                    {
                        "id": "loops",
                        "module": 3,
                        "title": "循环",
                        "description": "循环训练",
                        "availability": "active",
                    },
                    {
                        "id": "ai_practice",
                        "module": 11,
                        "title": "AI 专属补练",
                        "description": "补练",
                        "availability": "active",
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return target


def test_companion_creation_records_subject_origin_and_resolved_stage(
    tmp_path,
    monkeypatch,
) -> None:
    target = make_subject(tmp_path, monkeypatch)
    enable_fake_ai(monkeypatch)
    token = workspace.set_current_subject(target.id)
    try:
        result = authoring.execute_tool(
            "create_practice",
            {"knowledge_point": "for 循环", "module_id": "module_3"},
            origin="course",
        )
        assert result["created"] is True
        assert result["subject_id"] == target.id
        assert result["origin"] == "course"
        assert result["scope"] == "course"
        assert result["stage"] == "loops"
        assert result["level_index"] == 1

        meta = json.loads(
            (
                target.exercises_dir
                / result["exercise_id"]
                / "meta.json"
            ).read_text(encoding="utf-8")
        )
        assert meta["subject_id"] == target.id
        assert meta["origin"] == "course"
        assert meta["scope"] == "course"
        assert meta["stage"] == "loops"
        assert meta["level_id"] == "loops-L01"
        assert meta["storage_path"] == result["exercise_id"]

        lesson = authoring.execute_tool(
            "write_lesson",
            {"title": "Auto lesson", "summary": "Resolve exercise id automatically."},
            origin="course",
        )
        assert lesson["ok"] is True
        assert lesson["exercise_id"] == result["exercise_id"]

        catalog = catalog_payload({}, origin="course")
        loops = next(
            stage
            for stage in catalog["roadmap"]["stages"]
            if stage["id"] == "loops"
        )
        assert loops["exercise_count"] == 1
    finally:
        workspace.reset_current_subject(token)


def test_workshop_creation_is_separate_from_course_scope(
    tmp_path,
    monkeypatch,
) -> None:
    target = make_subject(tmp_path, monkeypatch)
    enable_fake_ai(monkeypatch)
    token = workspace.set_current_subject(target.id)
    try:
        result = authoring.execute_tool(
            "create_practice",
            {"knowledge_point": "栈与队列", "module_id": "module_99"},
            origin="workshop",
        )
        assert result["origin"] == "workshop"
        assert result["scope"] == "workshop"
        assert result["stage"] == "workshop"
        assert result["subject_id"] == target.id
        assert (
            target.exercises_dir
            / "workshop"
            / result["exercise_id"]
        ).exists()

        course_catalog = catalog_payload({}, origin="course")
        workshop_catalog = catalog_payload({}, origin="workshop")
        assert all(
            exercise["id"] != result["exercise_id"]
            for exercise in course_catalog["exercises"]
        )
        assert any(
            exercise["id"] == result["exercise_id"]
            for exercise in workshop_catalog["exercises"]
        )
    finally:
        workspace.reset_current_subject(token)


def test_catalog_keeps_unknown_stage_visible_as_unassigned(tmp_path, monkeypatch) -> None:
    target = make_subject(tmp_path, monkeypatch)
    exercise_dir = target.exercises_dir / "orphan"
    exercise_dir.mkdir(parents=True)
    (exercise_dir / "meta.json").write_text(
        json.dumps(
            {
                "id": "orphan",
                "title": "Orphan",
                "stage": "module_3",
                "order": 1,
                "minutes": 20,
                "summary": "orphan",
                "concepts": ["loop"],
            }
        ),
        encoding="utf-8",
    )
    token = workspace.set_current_subject(target.id)
    try:
        catalog = catalog_payload({}, origin="course")
        assert any(
            stage["id"] == "module_3" and stage["title"].startswith("未归类")
            for stage in catalog["roadmap"]["stages"]
        )
        assert any(
            exercise["id"] == "orphan"
            for exercise in catalog["exercises"]
        )
    finally:
        workspace.reset_current_subject(token)
