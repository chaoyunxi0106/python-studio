from __future__ import annotations

from python_studio import knowledge_graph, store


def test_knowledge_graph_syncs_skills_and_prerequisites(tmp_path, monkeypatch) -> None:
    database = tmp_path / "study.db"
    monkeypatch.setattr(store, "DATABASE_FILE", database)
    monkeypatch.setattr(
        knowledge_graph,
        "load_exercises",
        lambda include_inactive=False: [
            {
                "id": "first",
                "stage": "module_1",
                "order": 1,
                "summary": "基础",
                "concepts": ["变量"],
            },
            {
                "id": "second",
                "stage": "module_1",
                "order": 2,
                "summary": "进阶",
                "concepts": ["条件"],
            },
        ],
    )

    result = knowledge_graph.sync_knowledge_graph()
    knowledge_graph.refresh_student_skill_state()
    summary = knowledge_graph.knowledge_graph_summary()

    assert result["skills"] > 0
    assert result["links"] > 0
    assert summary["skills"] == result["skills"]
    assert summary["exercise_links"] == result["links"]
