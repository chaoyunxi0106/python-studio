from __future__ import annotations

from typing import Any

from ..companion import chat_with_companion
from ..config import get_deepseek_config
from ..context_export import compact_chat_contexts
from ..store import (
    append_chat_message,
    clear_chat_messages,
    create_chat_session,
    delete_chat_session,
    get_chat_session,
    get_or_create_chat_session,
    list_chat_messages,
    list_chat_sessions,
    update_chat_session,
)


def sessions_payload() -> dict[str, Any]:
    sessions = list_chat_sessions()
    if not sessions:
        sessions = [get_or_create_chat_session()]
    return {"sessions": sessions}


def chat_payload(session_id: int | None = None) -> dict[str, Any]:
    session = get_chat_session(session_id) if session_id else None
    if session is None:
        session = get_or_create_chat_session()
    return {
        "session": session,
        "session_id": int(session["id"]),
        "messages": list_chat_messages(int(session["id"])),
    }


def new_chat(
    title: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    session = create_chat_session(title, context=context)
    return {
        "session": session,
        "session_id": session["id"],
        "messages": [],
    }


def send_chat_message(
    session_id: int | None,
    message: str,
    context: Any = None,
    *,
    origin: str = "course",
) -> dict[str, Any]:
    session = get_chat_session(session_id) if session_id else None
    if session is None:
        session = get_or_create_chat_session()
    session_id = int(session["id"])
    if not isinstance(context, (dict, list)):
        context = session.get("context") or {}
    contexts = compact_chat_contexts(context)
    append_chat_message(
        session_id,
        "user",
        message,
        context={"items": contexts} if contexts else None,
    )
    history = list_chat_messages(session_id, limit=24)
    actions: list[dict[str, Any]] = []
    answer = chat_with_companion(
        history,
        context={"items": contexts},
        config=get_deepseek_config(),
        actions=actions,
        origin=origin,
    )
    saved = append_chat_message(session_id, "assistant", answer)
    return {"session_id": session_id, "message": saved, "actions": actions}


def manage_chat_session(
    session_id: int,
    action: str,
    *,
    title: str | None = None,
    context: Any = None,
    marker: str | None = None,
) -> bool:
    if action == "rename":
        if not title:
            raise ValueError("Title is required.")
        return update_chat_session(session_id, title=title)
    if action == "set_context":
        clear_context = context is None
        if isinstance(context, dict) and isinstance(context.get("items"), list):
            normalized_context = {"items": compact_chat_contexts(context)}
        elif isinstance(context, list):
            normalized_context = {"items": compact_chat_contexts(context)}
        else:
            normalized_context = None
        updated = update_chat_session(
            session_id,
            context=normalized_context,
            clear_context=clear_context,
        )
        if updated and marker:
            append_chat_message(session_id, "context", marker)
        return updated
    if action == "clear":
        clear_chat_messages(session_id)
        return True
    if action == "delete":
        return delete_chat_session(session_id)
    raise ValueError("Unsupported action.")
