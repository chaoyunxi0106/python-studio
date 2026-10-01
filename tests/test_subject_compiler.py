from __future__ import annotations

import pytest

from python_studio import store, subject_compiler, workspace
from python_studio.config import DeepSeekConfig


def test_local_blueprint_selects_conceptual_mode() -> None:
    blueprint = subject_compiler._local_blueprint(
        "数学优化理论",
        "凸集、凸函数和 KKT 条件",
        "auto",
    )
    activity_types = {
        activity["type"]
        for module in blueprint["modules"]
        for activity in module["activities"]
    }
    assert blueprint["mode"] == "conceptual"
    assert "multiple_choice" in activity_types
    assert "short_answer" in activity_types


def test_compile_subject_saves_ai_blueprint(tmp_path, monkeypatch) -> None:
    database = tmp_path / "study.db"
    monkeypatch.setattr(store, "DATABASE_FILE", database)
    subjects_dir = tmp_path / "subjects"
    monkeypatch.setattr(workspace, "SUBJECTS_DIR", subjects_dir)
    monkeypatch.setattr(workspace, "SUBJECT_REGISTRY", subjects_dir / "registry.json")
    monkeypatch.setattr(
        subject_compiler,
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
        subject_compiler,
        "_call_deepseek_subject",
        lambda *args, **kwargs: {
            "title": "数据结构",
            "mode": "programming",
            "summary": "从零生成的数据结构课程",
            "duration_weeks": 4,
            "objectives": ["掌握基础数据结构"],
            "assessment_strategy": "代码练习与测试",
            "modules": [
                {
                    "id": "module_1",
                    "title": "线性结构",
                    "goal": "理解栈与队列",
                    "concepts": ["栈", "队列"],
                    "activities": [
                        {
                            "title": "实现栈",
                            "type": "code_task",
                            "objective": "实现基础操作",
                            "deliverable": "通过自动测试",
                        }
                    ],
                }
            ],
            "capstone": "完成一个小型数据结构项目",
            "source_excerpt": "",
        },
    )

    result = subject_compiler.compile_subject(
        subject="数据结构",
        material="栈、队列、树和图",
        requested_mode="programming",
    )
    assert result["blueprint"]["mode"] == "programming"
    subjects = subject_compiler.list_subjects()
    assert len(subjects) == 1
    assert subjects[0]["title"] == "数据结构"


def test_compile_subject_requires_ai_configuration(tmp_path, monkeypatch) -> None:
    database = tmp_path / "study.db"
    monkeypatch.setattr(store, "DATABASE_FILE", database)
    subjects_dir = tmp_path / "subjects"
    monkeypatch.setattr(workspace, "SUBJECTS_DIR", subjects_dir)
    monkeypatch.setattr(workspace, "SUBJECT_REGISTRY", subjects_dir / "registry.json")
    monkeypatch.setattr(
        subject_compiler,
        "get_deepseek_config",
        lambda: DeepSeekConfig(
            api_key="",
            base_url="https://api.deepseek.com",
            model="deepseek-chat",
            timeout_seconds=10,
            history_limit=20,
        ),
    )

    with pytest.raises(ValueError, match="API"):
        subject_compiler.compile_subject(
            subject="数据结构",
            material="栈、队列、树和图",
            requested_mode="programming",
        )
