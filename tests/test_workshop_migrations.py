from __future__ import annotations

import sqlite3

from python_studio.migrations import column_names
from python_studio.store import _connect


def test_workshop_session_scope_backfills_existing_graph(tmp_path) -> None:
    database = tmp_path / "study.db"
    connection = sqlite3.connect(database)
    connection.executescript(
        """
        CREATE TABLE workshop_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE workshop_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE thought_nodes (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            summary TEXT NOT NULL DEFAULT '',
            node_type TEXT NOT NULL DEFAULT 'concept',
            parent_id TEXT,
            exercise_id TEXT,
            x REAL NOT NULL DEFAULT 0,
            y REAL NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE thought_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            relation TEXT NOT NULL DEFAULT 'branch',
            created_at TEXT NOT NULL,
            UNIQUE(source_id, target_id)
        );
        INSERT INTO workshop_sessions (title, created_at, updated_at)
        VALUES ('legacy', '2026-10-01T00:00:00+08:00', '2026-10-01T00:00:00+08:00');
        INSERT INTO thought_nodes (
            id, title, summary, node_type, parent_id, exercise_id,
            x, y, created_at, updated_at
        )
        VALUES (
            'node_1', 'legacy node', '', 'concept', NULL, NULL,
            0, 0, '2026-10-01T00:00:00+08:00', '2026-10-01T00:00:00+08:00'
        );
        INSERT INTO thought_edges (
            source_id, target_id, relation, created_at
        )
        VALUES ('node_0', 'node_1', 'branches_to', '2026-10-01T00:00:00+08:00');
        """
    )
    connection.commit()
    connection.close()

    with _connect(database):
        pass

    connection = sqlite3.connect(database)
    try:
        assert "session_id" in column_names(connection, "thought_nodes")
        assert "session_id" in column_names(connection, "thought_edges")
        node_session = connection.execute(
            "SELECT session_id FROM thought_nodes WHERE id = 'node_1'"
        ).fetchone()[0]
        edge_session = connection.execute(
            "SELECT session_id FROM thought_edges WHERE source_id = 'node_0'"
        ).fetchone()[0]
    finally:
        connection.close()
    assert node_session == edge_session == 1
