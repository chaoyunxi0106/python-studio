from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from .paths import DATABASE_FILE
from . import paths as path_config
from .migrations import column_names, run_migrations
from .test_analysis import analyze_test_results
from .workspace import get_workspace


SCHEMA = """
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_id TEXT NOT NULL,
    title TEXT NOT NULL,
    concepts TEXT NOT NULL DEFAULT '[]',
    checked_at TEXT NOT NULL,
    passed INTEGER NOT NULL,
    duration_seconds REAL NOT NULL,
    output TEXT NOT NULL,
    code_snapshot TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_attempts_checked_at
ON attempts(checked_at DESC);

CREATE INDEX IF NOT EXISTS idx_attempts_exercise
ON attempts(exercise_id);

CREATE TABLE IF NOT EXISTS task_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    exercise_id TEXT NOT NULL,
    task_name TEXT NOT NULL,
    test_name TEXT NOT NULL,
    knowledge_point TEXT NOT NULL,
    passed INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(attempt_id) REFERENCES attempts(id)
);

CREATE INDEX IF NOT EXISTS idx_task_results_attempt
ON task_results(attempt_id);

CREATE INDEX IF NOT EXISTS idx_task_results_skill
ON task_results(knowledge_point);

CREATE TABLE IF NOT EXISTS attempt_analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL UNIQUE,
    source TEXT NOT NULL,
    model TEXT NOT NULL DEFAULT '',
    generated_at TEXT NOT NULL,
    summary TEXT NOT NULL,
    requirement_gaps TEXT NOT NULL DEFAULT '[]',
    code_issues TEXT NOT NULL DEFAULT '[]',
    hidden_risks TEXT NOT NULL DEFAULT '[]',
    strengths TEXT NOT NULL DEFAULT '[]',
    FOREIGN KEY(attempt_id) REFERENCES attempts(id)
);

CREATE TABLE IF NOT EXISTS mistakes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    knowledge_point TEXT NOT NULL,
    source_exercise_id TEXT,
    question TEXT NOT NULL,
    expected_answer TEXT NOT NULL DEFAULT '',
    hint TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    source TEXT NOT NULL DEFAULT 'local',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(knowledge_point, question)
);

CREATE INDEX IF NOT EXISTS idx_mistakes_status
ON mistakes(status);

CREATE TABLE IF NOT EXISTS analysis_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    payload TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_analysis_runs_generated_at
ON analysis_runs(generated_at DESC);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    context_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    context_json TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES chat_sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session
ON chat_messages(session_id, id);

CREATE TABLE IF NOT EXISTS ai_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    cache_key TEXT,
    status TEXT NOT NULL,
    input_chars INTEGER NOT NULL DEFAULT 0,
    output_chars INTEGER NOT NULL DEFAULT 0,
    duration_ms INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    created_at TEXT NOT NULL,
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS ai_cache (
    cache_key TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    response_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    mode TEXT NOT NULL,
    source_material TEXT NOT NULL DEFAULT '',
    blueprint_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workshop_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workshop_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES workshop_sessions(id)
);

CREATE TABLE IF NOT EXISTS thought_nodes (
    id TEXT PRIMARY KEY,
    session_id INTEGER NOT NULL,
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

CREATE TABLE IF NOT EXISTS thought_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation TEXT NOT NULL DEFAULT 'branch',
    created_at TEXT NOT NULL,
    UNIQUE(source_id, target_id)
);

"""


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def exercise_origin(exercise: dict[str, Any]) -> str:
    """Workshop-generated practice is tracked apart from course practice."""
    origin = str(exercise.get("origin") or "").strip()
    if origin:
        return origin
    return "workshop" if str(exercise.get("stage") or "") == "workshop" else "course"


def _migration_baseline(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA)


def _migration_chat_context(connection: sqlite3.Connection) -> None:
    if "context_json" not in column_names(connection, "chat_sessions"):
        connection.execute("ALTER TABLE chat_sessions ADD COLUMN context_json TEXT")


def _migration_ai_jobs(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS ai_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            cache_key TEXT,
            status TEXT NOT NULL,
            input_chars INTEGER NOT NULL DEFAULT 0,
            output_chars INTEGER NOT NULL DEFAULT 0,
            duration_ms INTEGER NOT NULL DEFAULT 0,
            error TEXT,
            created_at TEXT NOT NULL,
            finished_at TEXT
        );

        CREATE TABLE IF NOT EXISTS ai_cache (
            cache_key TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            response_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )


def _migration_knowledge_graph(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS skills (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS exercise_skills (
            exercise_id TEXT NOT NULL,
            skill_id TEXT NOT NULL,
            weight REAL NOT NULL DEFAULT 1.0,
            PRIMARY KEY(exercise_id, skill_id),
            FOREIGN KEY(skill_id) REFERENCES skills(id)
        );

        CREATE TABLE IF NOT EXISTS skill_prerequisites (
            skill_id TEXT NOT NULL,
            prerequisite_id TEXT NOT NULL,
            PRIMARY KEY(skill_id, prerequisite_id),
            FOREIGN KEY(skill_id) REFERENCES skills(id),
            FOREIGN KEY(prerequisite_id) REFERENCES skills(id)
        );

        CREATE TABLE IF NOT EXISTS student_skill_state (
            skill_id TEXT PRIMARY KEY,
            mastery INTEGER NOT NULL DEFAULT 0,
            checks INTEGER NOT NULL DEFAULT 0,
            failures INTEGER NOT NULL DEFAULT 0,
            trend TEXT NOT NULL DEFAULT 'insufficient',
            recent_results TEXT NOT NULL DEFAULT '[]',
            last_seen TEXT,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(skill_id) REFERENCES skills(id)
        );
        """
    )


def _migration_subject_compiler(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            summary TEXT NOT NULL DEFAULT '',
            mode TEXT NOT NULL,
            source_material TEXT NOT NULL DEFAULT '',
            blueprint_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
    )


def _migration_creative_workshop(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS workshop_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS workshop_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES workshop_sessions(id)
        );

        CREATE TABLE IF NOT EXISTS thought_nodes (
            id TEXT PRIMARY KEY,
            session_id INTEGER NOT NULL,
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

        CREATE TABLE IF NOT EXISTS thought_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            relation TEXT NOT NULL DEFAULT 'branch',
            created_at TEXT NOT NULL,
            UNIQUE(source_id, target_id)
        );
        """
    )


def _migration_origin_scope(connection: sqlite3.Connection) -> None:
    """Separate course records from creative-workshop records."""
    for table in ("attempts", "mistakes", "analysis_runs"):
        if "origin" not in column_names(connection, table):
            connection.execute(
                f"ALTER TABLE {table} ADD COLUMN origin TEXT NOT NULL DEFAULT 'course'"
            )
    connection.execute(
        "UPDATE attempts SET origin = 'workshop' WHERE exercise_id GLOB 'workshop_node_*'"
    )
    connection.execute(
        "UPDATE mistakes SET origin = 'workshop' "
        "WHERE source_exercise_id GLOB 'workshop_node_*'"
    )


def _migration_workshop_session_scope(connection: sqlite3.Connection) -> None:
    """Attach graph nodes and edges to a concrete workshop session."""
    for table in ("thought_nodes", "thought_edges"):
        if "session_id" not in column_names(connection, table):
            connection.execute(
                f"ALTER TABLE {table} ADD COLUMN session_id INTEGER"
            )

    row = connection.execute(
        "SELECT id FROM workshop_sessions ORDER BY id LIMIT 1"
    ).fetchone()
    if row:
        default_session_id = int(row[0])
    else:
        now = _now()
        cursor = connection.execute(
            """
            INSERT INTO workshop_sessions (title, created_at, updated_at)
            VALUES (?, ?, ?)
            """,
            ("创造工坊", now, now),
        )
        default_session_id = int(cursor.lastrowid)

    for table in ("thought_nodes", "thought_edges"):
        connection.execute(
            f"UPDATE {table} SET session_id = ? WHERE session_id IS NULL",
            (default_session_id,),
        )
    connection.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_thought_nodes_session
        ON thought_nodes(session_id, created_at);

        CREATE INDEX IF NOT EXISTS idx_thought_edges_session
        ON thought_edges(session_id, id);
        """
    )


@contextmanager
def _connect(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    if db_path is not None:
        resolved_path = db_path
    elif DATABASE_FILE != path_config.DATABASE_FILE:
        resolved_path = DATABASE_FILE
    else:
        resolved_path = get_workspace().database_file
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(resolved_path, timeout=10)
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        run_migrations(
            connection,
            [
                (1, "baseline_schema", _migration_baseline),
                (2, "chat_context", _migration_chat_context),
                (3, "ai_jobs_and_cache", _migration_ai_jobs),
                (4, "knowledge_graph", _migration_knowledge_graph),
                (5, "subject_compiler", _migration_subject_compiler),
                (6, "creative_workshop", _migration_creative_workshop),
                (7, "origin_scope", _migration_origin_scope),
                (8, "workshop_session_scope", _migration_workshop_session_scope),
            ],
        )
        _backfill_task_results(connection)
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _backfill_task_results(connection: sqlite3.Connection) -> None:
    from .catalog import find_exercise

    rows = connection.execute(
        """
        SELECT a.id, a.exercise_id, a.checked_at, a.passed, a.output
        FROM attempts AS a
        WHERE NOT EXISTS (
            SELECT 1 FROM task_results AS t WHERE t.attempt_id = a.id
        )
        """
    ).fetchall()
    for row in rows:
        try:
            exercise = find_exercise(row["exercise_id"])
        except KeyError:
            continue
        tasks = analyze_test_results(
            exercise,
            row["output"],
            passed_overall=bool(row["passed"]),
        )
        for task in tasks:
            connection.execute(
                """
                INSERT INTO task_results (
                    attempt_id,
                    exercise_id,
                    task_name,
                    test_name,
                    knowledge_point,
                    passed,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["id"],
                    row["exercise_id"],
                    task["task_name"],
                    task["test_name"],
                    task["knowledge_point"],
                    int(task["passed"]),
                    row["checked_at"],
                ),
            )


def record_learning_attempt(
    attempt: dict[str, Any],
    exercise: dict[str, Any],
    *,
    db_path: Path | None = None,
) -> int:
    with _connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO attempts (
                exercise_id,
                title,
                concepts,
                checked_at,
                passed,
                duration_seconds,
                output,
                code_snapshot,
                origin
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                attempt["exercise_id"],
                exercise["title"],
                json.dumps(exercise.get("concepts", []), ensure_ascii=False),
                attempt["checked_at"],
                int(bool(attempt["passed"])),
                float(attempt.get("duration_seconds", 0)),
                str(attempt.get("output", ""))[-30000:],
                str(attempt.get("code_snapshot", ""))[-30000:],
                exercise_origin(exercise),
            ),
        )
        attempt_id = int(cursor.lastrowid)
        for task in attempt.get("task_results", []):
            connection.execute(
                """
                INSERT INTO task_results (
                    attempt_id,
                    exercise_id,
                    task_name,
                    test_name,
                    knowledge_point,
                    passed,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    attempt_id,
                    attempt["exercise_id"],
                    str(task["task_name"]),
                    str(task["test_name"]),
                    str(task["knowledge_point"]),
                    int(bool(task["passed"])),
                    attempt["checked_at"],
                ),
            )
        return attempt_id


def list_learning_attempts(
    limit: int = 100,
    *,
    origin: str | None = None,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    query = """
        SELECT id, exercise_id, title, concepts, checked_at, passed,
               duration_seconds, output, code_snapshot, origin
        FROM attempts
    """
    parameters: list[Any] = []
    if origin:
        query += " WHERE origin = ?"
        parameters.append(origin)
    query += " ORDER BY id DESC LIMIT ?"
    parameters.append(max(1, min(limit, 500)))

    with _connect(db_path) as connection:
        rows = connection.execute(query, parameters).fetchall()
        attempt_ids = [int(row["id"]) for row in rows]
        tasks_by_attempt: dict[int, list[dict[str, Any]]] = {
            attempt_id: [] for attempt_id in attempt_ids
        }
        if attempt_ids:
            placeholders = ",".join("?" for _ in attempt_ids)
            task_rows = connection.execute(
                f"""
                SELECT attempt_id, task_name, test_name, knowledge_point, passed
                FROM task_results
                WHERE attempt_id IN ({placeholders})
                ORDER BY id
                """,
                attempt_ids,
            ).fetchall()
            for row in task_rows:
                tasks_by_attempt[int(row["attempt_id"])].append(
                    {
                        "task_name": row["task_name"],
                        "test_name": row["test_name"],
                        "knowledge_point": row["knowledge_point"],
                        "passed": bool(row["passed"]),
                    }
                )
            analysis_rows = connection.execute(
                f"""
                SELECT attempt_id, source, model, generated_at, summary,
                       requirement_gaps, code_issues, hidden_risks, strengths
                FROM attempt_analyses
                WHERE attempt_id IN ({placeholders})
                """,
                attempt_ids,
            ).fetchall()
            analyses_by_attempt = {
                int(row["attempt_id"]): {
                    "source": row["source"],
                    "model": row["model"],
                    "generated_at": row["generated_at"],
                    "summary": row["summary"],
                    "requirement_gaps": json.loads(row["requirement_gaps"] or "[]"),
                    "code_issues": json.loads(row["code_issues"] or "[]"),
                    "hidden_risks": json.loads(row["hidden_risks"] or "[]"),
                    "strengths": json.loads(row["strengths"] or "[]"),
                }
                for row in analysis_rows
            }
        else:
            analyses_by_attempt = {}
    return [
        {
            **dict(row),
            "passed": bool(row["passed"]),
            "concepts": json.loads(row["concepts"] or "[]"),
            "task_results": tasks_by_attempt.get(int(row["id"]), []),
            "ai_analysis": analyses_by_attempt.get(int(row["id"])),
        }
        for row in rows
    ]


def learning_history_summary(
    *,
    origin: str | None = None,
    db_path: Path | None = None,
) -> dict[str, Any]:
    scope = " WHERE origin = ?" if origin else ""
    scope_args: tuple[Any, ...] = (origin,) if origin else ()
    with _connect(db_path) as connection:
        totals = connection.execute(
            f"""
            SELECT COUNT(*) AS attempts,
                   SUM(CASE WHEN passed = 1 THEN 1 ELSE 0 END) AS passed,
                   SUM(CASE WHEN passed = 0 THEN 1 ELSE 0 END) AS failed
            FROM attempts
            {scope}
            """,
            scope_args,
        ).fetchone()
        latest = connection.execute(
            f"SELECT checked_at FROM attempts{scope} ORDER BY id DESC LIMIT 1",
            scope_args,
        ).fetchone()
        failed_tasks = connection.execute(
            f"""
            SELECT COUNT(*) AS count
            FROM task_results AS t
            JOIN attempts AS a ON a.id = t.attempt_id
            WHERE t.passed = 0{" AND a.origin = ?" if origin else ""}
            """,
            scope_args,
        ).fetchone()

    attempts = int(totals["attempts"] or 0)
    passed = int(totals["passed"] or 0)
    return {
        "attempts": attempts,
        "passed": passed,
        "failed": int(totals["failed"] or 0),
        "pass_rate": round((passed / attempts) * 100) if attempts else 0,
        "latest_attempt_at": latest["checked_at"] if latest else None,
        "failed_tasks": int(failed_tasks["count"] or 0),
    }


def get_learning_attempt(
    attempt_id: int,
    *,
    db_path: Path | None = None,
) -> dict[str, Any] | None:
    return next(
        (
            attempt
            for attempt in list_learning_attempts(limit=500, db_path=db_path)
            if int(attempt["id"]) == attempt_id
        ),
        None,
    )


def save_attempt_analysis(
    attempt_id: int,
    analysis: dict[str, Any],
    *,
    db_path: Path | None = None,
) -> None:
    with _connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO attempt_analyses (
                attempt_id,
                source,
                model,
                generated_at,
                summary,
                requirement_gaps,
                code_issues,
                hidden_risks,
                strengths
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(attempt_id) DO UPDATE SET
                source = excluded.source,
                model = excluded.model,
                generated_at = excluded.generated_at,
                summary = excluded.summary,
                requirement_gaps = excluded.requirement_gaps,
                code_issues = excluded.code_issues,
                hidden_risks = excluded.hidden_risks,
                strengths = excluded.strengths
            """,
            (
                attempt_id,
                str(analysis.get("source", "local")),
                str(analysis.get("model", "")),
                str(analysis.get("generated_at") or _now()),
                str(analysis.get("summary", "")),
                json.dumps(analysis.get("requirement_gaps", []), ensure_ascii=False),
                json.dumps(analysis.get("code_issues", []), ensure_ascii=False),
                json.dumps(analysis.get("hidden_risks", []), ensure_ascii=False),
                json.dumps(analysis.get("strengths", []), ensure_ascii=False),
            ),
        )


def skill_summary(
    *,
    origin: str | None = None,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    with _connect(db_path) as connection:
        rows = connection.execute(
            f"""
            SELECT t.knowledge_point,
                   COUNT(*) AS checks,
                   SUM(CASE WHEN t.passed = 0 THEN 1 ELSE 0 END) AS failures,
                   MAX(t.created_at) AS last_seen
            FROM task_results AS t
            JOIN attempts AS a ON a.id = t.attempt_id
            {"WHERE a.origin = ?" if origin else ""}
            GROUP BY t.knowledge_point
            ORDER BY failures DESC, checks DESC
            """,
            (origin,) if origin else (),
        ).fetchall()
        trends = {
            str(row["knowledge_point"]): _skill_trend(
                connection,
                str(row["knowledge_point"]),
                origin=origin,
            )
            for row in rows
        }

    summary = []
    for row in rows:
        checks = int(row["checks"] or 0)
        failures = int(row["failures"] or 0)
        mastery = max(0, 100 - round((failures / checks) * 100)) if checks else 0
        summary.append(
            {
                "knowledge_point": row["knowledge_point"],
                "checks": checks,
                "failures": failures,
                "mastery": mastery,
                "last_seen": row["last_seen"],
                **trends[str(row["knowledge_point"])],
            }
        )
    return summary


def _skill_trend(
    connection: sqlite3.Connection,
    knowledge_point: str,
    *,
    origin: str | None = None,
) -> dict[str, Any]:
    rows = connection.execute(
        f"""
        SELECT t.passed
        FROM task_results AS t
        JOIN attempts AS a ON a.id = t.attempt_id
        WHERE t.knowledge_point = ?{" AND a.origin = ?" if origin else ""}
        ORDER BY t.created_at DESC, t.id DESC
        LIMIT 6
        """,
        (knowledge_point, origin) if origin else (knowledge_point,),
    ).fetchall()
    recent = [bool(row["passed"]) for row in rows]
    if len(recent) < 2:
        trend = "insufficient"
    elif recent[0] and not recent[1]:
        trend = "improving"
    elif not recent[0] and recent[1]:
        trend = "slipping"
    elif all(recent[:2]):
        trend = "stable"
    else:
        trend = "needs_attention"
    return {
        "recent_results": recent,
        "trend": trend,
    }


def upsert_mistake(
    item: dict[str, Any],
    *,
    source: str,
    db_path: Path | None = None,
) -> int:
    knowledge_point = str(item.get("knowledge_point", "")).strip()
    question = str(item.get("question", "")).strip()
    if not knowledge_point or not question:
        raise ValueError("Mistake items require knowledge_point and question.")

    now = _now()
    with _connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO mistakes (
                knowledge_point,
                source_exercise_id,
                question,
                expected_answer,
                hint,
                status,
                source,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?)
            ON CONFLICT(knowledge_point, question) DO UPDATE SET
                source_exercise_id = excluded.source_exercise_id,
                expected_answer = excluded.expected_answer,
                hint = excluded.hint,
                source = excluded.source,
                status = 'active',
                updated_at = excluded.updated_at
            """,
            (
                knowledge_point,
                item.get("source_exercise_id"),
                question,
                str(item.get("expected_answer", "")),
                str(item.get("hint", "")),
                source,
                now,
                now,
            ),
        )
        row = connection.execute(
            """
            SELECT id FROM mistakes
            WHERE knowledge_point = ? AND question = ?
            """,
            (knowledge_point, question),
        ).fetchone()
        return int(row["id"])


def replace_mistakes(
    items: list[dict[str, Any]],
    *,
    source: str,
    origin: str = "course",
    db_path: Path | None = None,
) -> int:
    now = _now()
    with _connect(db_path) as connection:
        connection.execute("DELETE FROM mistakes WHERE origin = ?", (origin,))
        inserted = 0
        for item in items[:2]:
            knowledge_point = str(item.get("knowledge_point", "")).strip()
            question = str(item.get("question", "")).strip()
            if not knowledge_point or not question:
                continue
            connection.execute(
                """
                INSERT INTO mistakes (
                    knowledge_point,
                    source_exercise_id,
                    question,
                    expected_answer,
                    hint,
                    status,
                    source,
                    origin,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?, ?)
                """,
                (
                    knowledge_point,
                    item.get("source_exercise_id"),
                    question,
                    str(item.get("expected_answer", "")),
                    str(item.get("hint", "")),
                    source,
                    origin,
                    now,
                    now,
                ),
            )
            inserted += 1
        return inserted


def list_mistakes(
    *,
    active_only: bool = True,
    origin: str | None = None,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    query = """
        SELECT id, knowledge_point, source_exercise_id, question,
               expected_answer, hint, status, source, origin, created_at, updated_at
        FROM mistakes
    """
    conditions: list[str] = []
    parameters: list[Any] = []
    if active_only:
        conditions.append("status = 'active'")
    if origin:
        conditions.append("origin = ?")
        parameters.append(origin)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY updated_at DESC, id DESC"

    with _connect(db_path) as connection:
        rows = connection.execute(query, parameters).fetchall()
    return [dict(row) for row in rows]


def update_mistake_status(
    mistake_id: int,
    status: str,
    *,
    db_path: Path | None = None,
) -> bool:
    if status not in {"active", "mastered"}:
        raise ValueError("status must be active or mastered")
    with _connect(db_path) as connection:
        cursor = connection.execute(
            "UPDATE mistakes SET status = ?, updated_at = ? WHERE id = ?",
            (status, _now(), mistake_id),
        )
        return cursor.rowcount > 0


def save_analysis(
    analysis: dict[str, Any],
    *,
    origin: str = "course",
    db_path: Path | None = None,
) -> int:
    generated_at = str(analysis.get("generated_at") or _now())
    with _connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO analysis_runs (source, generated_at, payload, origin)
            VALUES (?, ?, ?, ?)
            """,
            (
                str(analysis.get("source", "unknown")),
                generated_at,
                json.dumps(analysis, ensure_ascii=False),
                origin,
            ),
        )
        return int(cursor.lastrowid)


def latest_analysis(
    *,
    origin: str | None = None,
    db_path: Path | None = None,
) -> dict[str, Any] | None:
    with _connect(db_path) as connection:
        row = connection.execute(
            f"""
            SELECT payload
            FROM analysis_runs
            {"WHERE origin = ?" if origin else ""}
            ORDER BY id DESC
            LIMIT 1
            """,
            (origin,) if origin else (),
        ).fetchone()
    if not row:
        return None
    try:
        return json.loads(row["payload"])
    except json.JSONDecodeError:
        return None


def cleanup_attempts_before(
    cutoff: str,
    *,
    db_path: Path | None = None,
) -> int:
    with _connect(db_path) as connection:
        old_ids = [
            int(row["id"])
            for row in connection.execute(
                "SELECT id FROM attempts WHERE checked_at < ?",
                (cutoff,),
            ).fetchall()
        ]
        if not old_ids:
            return 0
        placeholders = ",".join("?" for _ in old_ids)
        connection.execute(
            f"DELETE FROM task_results WHERE attempt_id IN ({placeholders})",
            old_ids,
        )
        connection.execute(
            f"DELETE FROM attempts WHERE id IN ({placeholders})",
            old_ids,
        )
        return len(old_ids)


def cleanup_mastered_mistakes(*, db_path: Path | None = None) -> int:
    with _connect(db_path) as connection:
        cursor = connection.execute("DELETE FROM mistakes WHERE status = 'mastered'")
        return int(cursor.rowcount)


def attempt_counts_for_exercises(*, db_path: Path | None = None) -> dict[str, int]:
    with _connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT exercise_id, COUNT(*) AS count
            FROM attempts
            GROUP BY exercise_id
            """
        ).fetchall()
    return {str(row["exercise_id"]): int(row["count"]) for row in rows}


def get_latest_attempt_for_exercise(
    exercise_id: str,
    *,
    db_path: Path | None = None,
) -> dict[str, Any] | None:
    return next(
        (
            attempt
            for attempt in list_learning_attempts(limit=500, db_path=db_path)
            if str(attempt["exercise_id"]) == exercise_id
        ),
        None,
    )


def get_or_create_chat_session(*, db_path: Path | None = None) -> dict[str, Any]:
    with _connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT id, title, context_json, created_at, updated_at
            FROM chat_sessions
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
        if row:
            return {
                **dict(row),
                "context": json.loads(row["context_json"] or "null"),
            }
        now = _now()
        cursor = connection.execute(
            """
            INSERT INTO chat_sessions (title, context_json, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            ("伴学对话", None, now, now),
        )
        return {
            "id": int(cursor.lastrowid),
            "title": "伴学对话",
            "context": None,
            "created_at": now,
            "updated_at": now,
        }


def create_chat_session(
    title: str = "新的伴学对话",
    *,
    context: dict[str, Any] | None = None,
    db_path: Path | None = None,
) -> dict[str, Any]:
    now = _now()
    with _connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO chat_sessions (title, context_json, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                title[:120],
                json.dumps(context, ensure_ascii=False) if context else None,
                now,
                now,
            ),
        )
        return {
            "id": int(cursor.lastrowid),
            "title": title[:120],
            "context": context,
            "created_at": now,
            "updated_at": now,
        }


def list_chat_sessions(*, db_path: Path | None = None) -> list[dict[str, Any]]:
    with _connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT id, title, context_json, created_at, updated_at
            FROM chat_sessions
            ORDER BY updated_at DESC, id DESC
            """
        ).fetchall()
    return [
        {
            **dict(row),
            "context": json.loads(row["context_json"] or "null"),
        }
        for row in rows
    ]


def get_chat_session(
    session_id: int,
    *,
    db_path: Path | None = None,
) -> dict[str, Any] | None:
    with _connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT id, title, context_json, created_at, updated_at
            FROM chat_sessions
            WHERE id = ?
            """,
            (session_id,),
        ).fetchone()
    if not row:
        return None
    return {
        **dict(row),
        "context": json.loads(row["context_json"] or "null"),
    }


def update_chat_session(
    session_id: int,
    *,
    title: str | None = None,
    context: dict[str, Any] | None = None,
    clear_context: bool = False,
    db_path: Path | None = None,
) -> bool:
    now = _now()
    updates = ["updated_at = ?"]
    parameters: list[Any] = [now]
    if title is not None:
        updates.append("title = ?")
        parameters.append(title[:120])
    if clear_context:
        updates.append("context_json = NULL")
    elif context is not None:
        updates.append("context_json = ?")
        parameters.append(json.dumps(context, ensure_ascii=False))
    parameters.append(session_id)
    with _connect(db_path) as connection:
        cursor = connection.execute(
            f"UPDATE chat_sessions SET {', '.join(updates)} WHERE id = ?",
            parameters,
        )
        return cursor.rowcount > 0


def clear_chat_messages(
    session_id: int,
    *,
    db_path: Path | None = None,
) -> int:
    with _connect(db_path) as connection:
        cursor = connection.execute(
            "DELETE FROM chat_messages WHERE session_id = ?",
            (session_id,),
        )
        connection.execute(
            "UPDATE chat_sessions SET updated_at = ? WHERE id = ?",
            (_now(), session_id),
        )
        return int(cursor.rowcount)


def delete_chat_session(
    session_id: int,
    *,
    db_path: Path | None = None,
) -> bool:
    with _connect(db_path) as connection:
        connection.execute(
            "DELETE FROM chat_messages WHERE session_id = ?",
            (session_id,),
        )
        cursor = connection.execute(
            "DELETE FROM chat_sessions WHERE id = ?",
            (session_id,),
        )
        return cursor.rowcount > 0


def list_chat_messages(
    session_id: int,
    *,
    limit: int = 100,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    with _connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT id, session_id, role, content, context_json, created_at
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY id ASC
            LIMIT ?
            """,
            (session_id, max(1, min(limit, 500))),
        ).fetchall()
    return [
        {
            **dict(row),
            "context": json.loads(row["context_json"] or "null"),
        }
        for row in rows
    ]


def append_chat_message(
    session_id: int,
    role: str,
    content: str,
    *,
    context: dict[str, Any] | None = None,
    db_path: Path | None = None,
) -> dict[str, Any]:
    now = _now()
    with _connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO chat_messages (
                session_id,
                role,
                content,
                context_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session_id,
                role,
                content,
                json.dumps(context, ensure_ascii=False) if context else None,
                now,
            ),
        )
        connection.execute(
            "UPDATE chat_sessions SET updated_at = ? WHERE id = ?",
            (now, session_id),
        )
        return {
            "id": int(cursor.lastrowid),
            "session_id": session_id,
            "role": role,
            "content": content,
            "context": context,
            "created_at": now,
        }
