from __future__ import annotations

import sqlite3
import threading
from collections.abc import Callable
from datetime import datetime


MigrationFunction = Callable[[sqlite3.Connection], None]
_MIGRATION_LOCK = threading.Lock()


def run_migrations(
    connection: sqlite3.Connection,
    migrations: list[tuple[int, str, MigrationFunction]],
) -> int:
    with _MIGRATION_LOCK:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
            """,
        )
        applied = {
            int(row[0])
            for row in connection.execute(
                "SELECT version FROM schema_migrations"
            ).fetchall()
        }
        current_version = max(applied, default=0)
        try:
            for version, name, migration in sorted(migrations):
                if version in applied:
                    continue
                migration(connection)
                connection.execute(
                    """
                    INSERT INTO schema_migrations (version, name, applied_at)
                    VALUES (?, ?, ?)
                    """,
                    (
                        version,
                        name,
                        datetime.now().astimezone().isoformat(timespec="seconds"),
                    ),
                )
                current_version = version
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        return current_version


def column_names(
    connection: sqlite3.Connection,
    table_name: str,
) -> set[str]:
    return {
        str(row[1])
        for row in connection.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()
    }
