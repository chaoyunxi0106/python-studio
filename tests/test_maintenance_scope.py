from __future__ import annotations

import json

from python_studio import maintenance, workspace


def test_maintenance_uses_current_subject_workspace(tmp_path, monkeypatch) -> None:
    subjects_dir = tmp_path / "subjects"
    monkeypatch.setattr(workspace, "SUBJECTS_DIR", subjects_dir)
    monkeypatch.setattr(workspace, "SUBJECT_REGISTRY", subjects_dir / "registry.json")
    target = workspace.create_subject_workspace(
        title="Maintenance Scope",
        mode="programming",
        blueprint={"mode": "programming", "modules": []},
        source_material="test",
    )
    generated = target.exercises_dir / "ai" / "generated_demo"
    generated.mkdir(parents=True)
    (generated / "meta.json").write_text(
        json.dumps(
            {
                "id": "generated_demo",
                "generated": True,
                "title": "Generated demo",
                "stage": "ai_practice",
                "order": 1,
                "minutes": 20,
                "summary": "Generated demo",
                "concepts": ["demo"],
                "active": True,
            }
        ),
        encoding="utf-8",
    )

    token = workspace.set_current_subject(target.id)
    try:
        summary = maintenance.maintenance_summary()
        assert summary["workspace"]["id"] == target.id
        assert summary["generated_exercises"]["total"] == 1
        assert target.database_file.exists()

        maintenance.update_generated_exercise("generated_demo", "archive")
        archived = json.loads((generated / "meta.json").read_text(encoding="utf-8"))
        assert archived["archived"] is True
        assert archived["active"] is False
    finally:
        workspace.reset_current_subject(token)
