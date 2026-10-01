from __future__ import annotations

from python_studio import ai_jobs, store


def test_ai_operation_cache_and_usage(tmp_path, monkeypatch) -> None:
    database = tmp_path / "study.db"
    monkeypatch.setattr(store, "DATABASE_FILE", database)
    calls = []

    def operation():
        calls.append(1)
        return {"answer": 42}

    first = ai_jobs.run_ai_operation(
        "example",
        {"value": 1},
        operation,
        use_cache=True,
    )
    second = ai_jobs.run_ai_operation(
        "example",
        {"value": 1},
        operation,
        use_cache=True,
    )

    assert first == second == {"answer": 42}
    assert calls == [1]
    usage = ai_jobs.ai_usage_summary()
    assert usage["jobs"] == 2
    assert usage["cache_hits"] == 1
    assert usage["cache_entries"] == 1

