from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from .ai_jobs import run_ai_operation
from .companion import generate_and_create_practice
from .config import DeepSeekConfig, get_deepseek_config
from .materializer import ensure_workshop_stage, materialize_assessment_node
from .providers.deepseek import ProviderError, chat_json
from .store import _connect, _now
from .workspace import get_workspace


NODE_TYPES = {
    "concept",
    "question",
    "method",
    "example",
    "counterexample",
    "project",
    "practice",
}
RELATIONS = {"branches_to", "explains", "example_of", "contradicts", "practice_for"}


def _timeline_node_id(index: int) -> str:
    return f"node_{uuid.uuid4().hex[:12]}_{index}"


def get_or_create_workshop_session() -> dict[str, Any]:
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT id, title, created_at, updated_at
            FROM workshop_sessions
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
        if row:
            return dict(row)
        now = _now()
        cursor = connection.execute(
            """
            INSERT INTO workshop_sessions (title, created_at, updated_at)
            VALUES (?, ?, ?)
            """,
            ("创造工坊", now, now),
        )
        return {
            "id": int(cursor.lastrowid),
            "title": "创造工坊",
            "created_at": now,
            "updated_at": now,
        }


def get_workshop_session(session_id: int) -> dict[str, Any] | None:
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT id, title, created_at, updated_at
            FROM workshop_sessions
            WHERE id = ?
            """,
            (session_id,),
        ).fetchone()
    return dict(row) if row else None


def resolve_workshop_session(session_id: int | None = None) -> dict[str, Any]:
    if session_id is None:
        return get_or_create_workshop_session()
    session = get_workshop_session(session_id)
    if session is None:
        raise KeyError(f"Unknown workshop session: {session_id}")
    return session


def _normalize_workshop_response(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Workshop response must be an object.")
    nodes = []
    for index, raw in enumerate(list(payload.get("nodes") or [])[:4], start=1):
        if not isinstance(raw, dict):
            continue
        node_type = str(raw.get("node_type") or "concept").strip().lower()
        if node_type not in NODE_TYPES:
            node_type = "concept"
        relation = str(raw.get("relation") or "branches_to").strip().lower()
        if relation not in RELATIONS:
            relation = "branches_to"
        title = str(raw.get("title") or "").strip()[:120]
        if not title:
            continue
        nodes.append(
            {
                "key": str(raw.get("key") or f"node_{index}")[:100],
                "parent_key": (
                    str(raw["parent_key"])[:160]
                    if raw.get("parent_key") is not None
                    else None
                ),
                "title": title,
                "summary": str(raw.get("summary") or "").strip()[:800],
                "node_type": node_type,
                "relation": relation,
            }
        )
    if not nodes:
        raise ValueError("Workshop response did not contain valid nodes.")
    return {
        "answer": str(payload.get("answer") or "已完成思考。")[:2000],
        "nodes": nodes,
    }


def _layout_graph(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not nodes:
        return []
    by_id = {node["id"]: dict(node) for node in nodes}
    children: dict[str, list[str]] = {node_id: [] for node_id in by_id}
    has_parent: set[str] = set()
    for edge in edges:
        source = str(edge["source_id"])
        target = str(edge["target_id"])
        if source in by_id and target in by_id:
            children[source].append(target)
            has_parent.add(target)
    roots = [
        node_id
        for node_id in by_id
        if node_id not in has_parent
    ] or [next(iter(by_id))]

    leaf_x = 140.0

    def assign(node_id: str, depth: int) -> float:
        nonlocal leaf_x
        child_ids = children.get(node_id, [])
        if child_ids:
            child_xs = [assign(child_id, depth + 1) for child_id in child_ids]
            x = sum(child_xs) / len(child_xs)
        else:
            x = leaf_x
            leaf_x += 180.0
        by_id[node_id]["x"] = x
        by_id[node_id]["y"] = 120.0 + depth * 150.0
        return x

    for root in roots:
        assign(root, 0)
        leaf_x += 100.0
    return list(by_id.values())


def workshop_payload(session_id: int | None = None) -> dict[str, Any]:
    session = resolve_workshop_session(session_id)
    resolved_id = int(session["id"])
    with _connect() as connection:
        messages = [
            dict(row)
            for row in connection.execute(
                """
                SELECT id, role, content, created_at
                FROM workshop_messages
                WHERE session_id = ?
                ORDER BY id
                """,
                (resolved_id,),
            ).fetchall()
        ]
        nodes = [
            dict(row)
            for row in connection.execute(
                """
                SELECT id, session_id, title, summary, node_type, parent_id,
                       exercise_id, x, y, created_at, updated_at
                FROM thought_nodes
                WHERE session_id = ?
                ORDER BY created_at, id
                """,
                (resolved_id,),
            ).fetchall()
        ]
        edges = [
            dict(row)
            for row in connection.execute(
                """
                SELECT id, session_id, source_id, target_id, relation, created_at
                FROM thought_edges
                WHERE session_id = ?
                ORDER BY id
                """,
                (resolved_id,),
            ).fetchall()
        ]
    return {
        "session": session,
        "session_id": resolved_id,
        "messages": messages,
        "nodes": _layout_graph(nodes, edges),
        "edges": edges,
    }


def _local_workshop_response(
    question: str,
    selected_node: dict[str, Any] | None,
) -> dict[str, Any]:
    title = question.strip()[:60] or "新的思考方向"
    return {
        "answer": (
            "先把问题拆成一个可验证的支点，再从定义、条件、例子和反例四个方向继续扩展。"
        ),
        "nodes": [
            {
                "key": "root",
                "parent_key": selected_node["id"] if selected_node else None,
                "title": title,
                "summary": f"围绕“{title}”建立可继续提问的知识支点。",
                "node_type": "concept",
                "relation": "branches_to",
            }
        ],
    }


def _call_deepseek_workshop(
    question: str,
    selected_node: dict[str, Any] | None,
    nodes: list[dict[str, Any]],
    config: DeepSeekConfig,
) -> dict[str, Any]:
    system_prompt = """
你是创造式学习工坊的思维导图设计师。
根据用户当前问题和已有节点，输出一个简洁回答和 1 到 4 个新思维节点。
节点可以代表概念、问题、方法、反例、项目或个人困惑。
节点类型使用：concept, question, method, example, counterexample, project, practice。

只输出 JSON：
{
  "answer": "直接回答当前问题，简洁，不重复已有节点",
  "nodes": [
    {
      "key": "本次输出内的唯一键",
      "parent_key": "已有节点 id 或本次节点的 key；根节点可为空",
      "title": "短标题",
      "summary": "这个支点的含义",
      "node_type": "concept",
      "relation": "branches_to"
    }
  ]
}
最多 4 个节点。不要输出 Markdown。
""".strip()
    payload = chat_json(
        config,
        [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "question": question,
                        "selected_node": selected_node,
                        "existing_nodes": nodes[-30:],
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        temperature=0.35,
        max_tokens=1400,
    )
    return _normalize_workshop_response(payload)


def ask_workshop(
    *,
    question: str,
    session_id: int | None = None,
    selected_node_id: str | None = None,
) -> dict[str, Any]:
    clean_question = question.strip()
    if not clean_question:
        raise ValueError("Question is required.")
    session = resolve_workshop_session(session_id)
    resolved_session_id = int(session["id"])
    payload = workshop_payload(resolved_session_id)
    selected_node = next(
        (
            node
            for node in payload["nodes"]
            if node["id"] == selected_node_id
        ),
        None,
    )
    config = get_deepseek_config()

    def operation() -> dict[str, Any]:
        if config.configured:
            try:
                return _call_deepseek_workshop(
                    clean_question,
                    selected_node,
                    payload["nodes"],
                    config,
                )
            except (ProviderError, KeyError, json.JSONDecodeError):
                return _local_workshop_response(clean_question, selected_node)
        return _local_workshop_response(clean_question, selected_node)

    result = run_ai_operation(
        "creative_workshop",
        {
            "question": clean_question,
            "selected_node": selected_node_id,
            "graph_version": len(payload["nodes"]),
        },
        operation,
        use_cache=False,
    )
    now = _now()
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO workshop_messages (session_id, role, content, created_at)
            VALUES (?, 'user', ?, ?)
            """,
            (resolved_session_id, clean_question, now),
        )
        connection.execute(
            """
            INSERT INTO workshop_messages (session_id, role, content, created_at)
            VALUES (?, 'assistant', ?, ?)
            """,
            (
                resolved_session_id,
                str(result.get("answer") or "已完成思考。"),
                now,
            ),
        )

        existing_nodes = {
            node["id"]: node for node in payload["nodes"]
        }
        parent_default = selected_node_id or (
            payload["nodes"][-1]["id"] if payload["nodes"] else None
        )
        created_nodes = []
        raw_nodes = list(result.get("nodes") or [])[:4]
        key_map: dict[str, str] = {}
        for index, raw_node in enumerate(raw_nodes, start=1):
            node_id = _timeline_node_id(index)
            key = str(raw_node.get("key") or f"node_{index}")
            key_map[key] = node_id
            parent_key = raw_node.get("parent_key")
            parent_id = key_map.get(str(parent_key)) if parent_key else parent_default
            if parent_id not in existing_nodes and parent_id not in created_nodes:
                parent_id = parent_default
            parent = existing_nodes.get(parent_id)
            base_x = float(parent["x"]) if parent else 600
            base_y = float(parent["y"]) if parent else 380
            x = base_x + (index - (len(raw_nodes) + 1) / 2) * 190
            y = base_y + 130
            node = {
                "id": node_id,
                "title": str(raw_node.get("title") or clean_question)[:120],
                "summary": str(raw_node.get("summary") or "")[:800],
                "node_type": str(raw_node.get("node_type") or "concept"),
                "parent_id": parent_id,
                "x": x,
                "y": y,
            }
            connection.execute(
                """
                INSERT INTO thought_nodes (
                    id, session_id, title, summary, node_type, parent_id,
                    x, y, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    node_id,
                    resolved_session_id,
                    node["title"],
                    node["summary"],
                    node["node_type"],
                    parent_id,
                    x,
                    y,
                    now,
                    now,
                ),
            )
            if parent_id:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO thought_edges (
                        session_id, source_id, target_id, relation, created_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        resolved_session_id,
                        parent_id,
                        node_id,
                        str(raw_node.get("relation") or "branches_to"),
                        now,
                    ),
                )
            created_nodes.append(node_id)
    return {
        **workshop_payload(resolved_session_id),
        "created_node_ids": created_nodes,
    }


def materialize_node_practice(node_id: str) -> dict[str, Any]:
    with _connect() as connection:
        node = connection.execute(
            """
            SELECT id, session_id, title, summary, node_type, exercise_id
            FROM thought_nodes
            WHERE id = ?
            """,
            (node_id,),
        ).fetchone()
    if not node:
        raise KeyError("Thought node not found.")
    if node["exercise_id"]:
        return {
            "node_id": node_id,
            "exercise_id": node["exercise_id"],
            "created": False,
        }

    graph = workshop_payload(int(node["session_id"]))
    nodes_by_id = {item["id"]: item for item in graph["nodes"]}
    current = nodes_by_id.get(node_id, dict(node))
    ancestors = []
    cursor = current.get("parent_id")
    while cursor and cursor in nodes_by_id and len(ancestors) < 8:
        parent = nodes_by_id[cursor]
        ancestors.append(
            {
                "id": parent["id"],
                "title": parent["title"],
                "summary": parent["summary"],
            }
        )
        cursor = parent.get("parent_id")
    child_nodes = [
        {
            "id": item["id"],
            "title": item["title"],
            "summary": item["summary"],
            "node_type": item["node_type"],
        }
        for item in graph["nodes"]
        if item.get("parent_id") == node_id
    ]
    recent_messages = [
        {"role": item["role"], "content": item["content"]}
        for item in graph["messages"][-8:]
    ]
    workspace = get_workspace()
    manifest_path = workspace.root / "subject.json"
    manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.exists()
        else {}
    )
    context = {
        "subject": manifest.get("title", workspace.title),
        "blueprint": manifest.get("blueprint", {}),
        "node": {
            "id": current.get("id"),
            "title": current.get("title"),
            "summary": current.get("summary"),
            "node_type": current.get("node_type"),
        },
        "ancestors": ancestors,
        "children": child_nodes,
        "recent_messages": recent_messages,
        "source_material_excerpt": str(
            manifest.get("source_material", "")
        )[:6000],
    }

    if node["node_type"] in {
        "concept",
        "question",
        "counterexample",
        "method",
    } and node["node_type"] != "project":
        exercise_id = materialize_assessment_node(
            node_id=node_id,
            title=str(node["title"]),
            summary=str(node["summary"]),
            node_type=str(node["node_type"]),
            context=context,
        )
    else:
        config = get_deepseek_config()
        created = generate_and_create_practice(
            [],
            knowledge_point=str(node["title"]),
            source_task=str(node["summary"]),
            creative_context=context,
            config=config,
            origin="workshop",
            stage="workshop",
            scope="workshop",
        )
        exercise_id = str(created["id"])
        ensure_workshop_stage()

    from .catalog import find_exercise

    meta_path = (
        Path(find_exercise(exercise_id, include_inactive=True)["directory"])
        / "meta.json"
    )
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["stage"] = "workshop"
        meta["order"] = 9000 + len(graph["nodes"])
        meta["origin"] = "workshop"
        meta["scope"] = "workshop"
        meta["storage_scope"] = "workshop"
        meta["workshop_node_id"] = node_id
        meta["source_node_title"] = str(node["title"])
        meta["title"] = f"{node['title']} · 工坊练习"
        meta["workshop_context"] = {
            "ancestor_titles": [item["title"] for item in ancestors],
            "source_messages": recent_messages[-4:],
        }
        meta_path.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    with _connect() as connection:
        connection.execute(
            """
            UPDATE thought_nodes
            SET exercise_id = ?, updated_at = ?
            WHERE id = ?
            """,
            (exercise_id, _now(), node_id),
        )
    return {
        "node_id": node_id,
        "exercise_id": exercise_id,
        "created": True,
    }
