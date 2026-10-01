from __future__ import annotations

from python_studio.services import chat_service
from python_studio.store import (
    append_chat_message,
    clear_chat_messages,
    create_chat_session,
    delete_chat_session,
    list_chat_messages,
    list_chat_sessions,
    update_chat_session,
)


def test_chat_sessions_are_isolated(tmp_path) -> None:
    database = tmp_path / "study.db"
    first = create_chat_session("First", db_path=database)
    second = create_chat_session("Second", db_path=database)

    append_chat_message(first["id"], "user", "hello first", db_path=database)
    update_chat_session(
        first["id"],
        context={"items": [{"title": "Question A"}]},
        db_path=database,
    )
    append_chat_message(first["id"], "context", "Loaded A", db_path=database)

    assert len(list_chat_messages(first["id"], db_path=database)) == 2
    assert list_chat_messages(second["id"], db_path=database) == []
    assert len(list_chat_sessions(db_path=database)) == 2

    clear_chat_messages(first["id"], db_path=database)
    assert list_chat_messages(first["id"], db_path=database) == []
    assert delete_chat_session(second["id"], db_path=database)
    assert len(list_chat_sessions(db_path=database)) == 1


def test_chat_passes_origin_to_companion(tmp_path, monkeypatch) -> None:
    session = {"id": 1, "title": "Scoped chat", "context": None}
    captured = {}

    def fake_chat(messages, *, context, config, actions, origin):
        captured["origin"] = origin
        return "ok"

    monkeypatch.setattr(chat_service, "chat_with_companion", fake_chat)
    monkeypatch.setattr(chat_service, "get_deepseek_config", lambda: object())
    monkeypatch.setattr(chat_service, "get_chat_session", lambda session_id: session)
    monkeypatch.setattr(
        chat_service,
        "append_chat_message",
        lambda *args, **kwargs: {
            "id": 1,
            "session_id": session["id"],
            "role": "assistant",
            "content": "ok",
        },
    )
    monkeypatch.setattr(chat_service, "list_chat_messages", lambda *args, **kwargs: [])
    chat_service.send_chat_message(
        session["id"],
        "question",
        origin="workshop",
    )
    assert captured["origin"] == "workshop"
