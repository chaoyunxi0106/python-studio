from __future__ import annotations

import json
from datetime import datetime

from python_studio import materializer, workshop, workspace
from python_studio.catalog import catalog_payload
from python_studio.config import DeepSeekConfig
from python_studio.store import _connect


def _no_ai_config():
    return DeepSeekConfig(
        api_key="",
        base_url="https://api.deepseek.com",
        model="deepseek-chat",
        timeout_seconds=10,
        history_limit=20,
    )


def test_workshop_grows_nodes_and_materializes_practice(tmp_path, monkeypatch) -> None:
    subjects_dir = tmp_path / "subjects"
    monkeypatch.setattr(workspace, "SUBJECTS_DIR", subjects_dir)
    monkeypatch.setattr(workspace, "SUBJECT_REGISTRY", subjects_dir / "registry.json")
    target = workspace.create_subject_workspace(
        title="Workshop Test",
        mode="conceptual",
        blueprint={"mode": "conceptual", "modules": []},
        source_material="test",
    )
    token = workspace.set_current_subject(target.id)
    monkeypatch.setattr(workshop, "get_deepseek_config", _no_ai_config)
    monkeypatch.setattr(materializer, "get_deepseek_config", _no_ai_config)
    captured = {}

    def fake_assessment(module, blueprint, config, extra_context=None):
        captured["extra_context"] = extra_context
        return [
            {
                "id": "mc1",
                "type": "multiple_choice",
                "question": "上下文相关选择题",
                "options": ["A", "B", "C", "D"],
                "answer_index": 0,
                "explanation": "解释",
            },
            {
                "id": "sa1",
                "type": "short_answer",
                "question": "上下文相关文本题",
                "rubric": ["评分点"],
                "reference_answer": "参考答案",
            },
        ]

    monkeypatch.setattr(
        materializer,
        "_call_deepseek_assessment",
        fake_assessment,
    )
    try:
        first = workshop.ask_workshop(question="什么是线性空间？")
        assert len(first["nodes"]) == 1
        parent = first["nodes"][0]["id"]
        second = workshop.ask_workshop(
            question="继续展开基与维数",
            selected_node_id=parent,
        )
        assert len(second["nodes"]) == 2
        assert len(second["edges"]) == 1
        child_node = next(
            node for node in second["nodes"] if node.get("parent_id")
        )
        result = workshop.materialize_node_practice(child_node["id"])
        assert result["exercise_id"]
        assert (
            target.exercises_dir
            / "workshop"
            / result["exercise_id"]
            / "assessment.json"
        ).exists()
        assert captured["extra_context"]["node"]["id"]
        assert captured["extra_context"]["ancestors"]
        assert captured["extra_context"]["recent_messages"]
        meta = json.loads(
            (
                target.exercises_dir
                / "workshop"
                / result["exercise_id"]
                / "meta.json"
            ).read_text(encoding="utf-8")
        )
        assert meta["origin"] == "workshop"
        assert meta["workshop_node_id"]
        assert meta["stage"] == "workshop"
        catalog = catalog_payload({}, origin="course")
        assert any(
            stage["id"] == "workshop"
            for stage in catalog["roadmap"]["stages"]
        )
        assert not any(
            exercise["id"] == result["exercise_id"]
            for exercise in catalog["exercises"]
        )
        workshop_catalog = catalog_payload({}, origin="workshop")
        assert any(
            exercise["id"] == result["exercise_id"]
            for exercise in workshop_catalog["exercises"]
        )
    finally:
        workspace.reset_current_subject(token)


def test_workshop_sessions_keep_graphs_isolated(tmp_path, monkeypatch) -> None:
    subjects_dir = tmp_path / "subjects"
    monkeypatch.setattr(workspace, "SUBJECTS_DIR", subjects_dir)
    monkeypatch.setattr(workspace, "SUBJECT_REGISTRY", subjects_dir / "registry.json")
    target = workspace.create_subject_workspace(
        title="Workshop Sessions",
        mode="conceptual",
        blueprint={"mode": "conceptual", "modules": []},
        source_material="test",
    )
    token = workspace.set_current_subject(target.id)
    monkeypatch.setattr(workshop, "get_deepseek_config", _no_ai_config)
    try:
        first = workshop.ask_workshop(question="第一条分支")
        first_session_id = int(first["session_id"])
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        with _connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO workshop_sessions (title, created_at, updated_at)
                VALUES (?, ?, ?)
                """,
                ("第二条分支", now, now),
            )
            second_session_id = int(cursor.lastrowid)

        second = workshop.ask_workshop(
            question="另一张图",
            session_id=second_session_id,
        )
        assert first_session_id != second_session_id
        assert len(second["nodes"]) == 1
        assert len(second["edges"]) == 0

        first_payload = workshop.workshop_payload(first_session_id)
        assert len(first_payload["nodes"]) == 1
        assert first_payload["nodes"][0]["title"] == "第一条分支"
        assert all(
            node["session_id"] == first_session_id
            for node in first_payload["nodes"]
        )
    finally:
        workspace.reset_current_subject(token)
