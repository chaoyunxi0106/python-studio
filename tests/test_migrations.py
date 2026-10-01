from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor

from python_studio.migrations import column_names, run_migrations


def test_migrations_are_recorded_once() -> None:
    connection = sqlite3.connect(":memory:")
    calls = []

    def migration(connection: sqlite3.Connection) -> None:
        calls.append(1)
        connection.execute("CREATE TABLE example (id INTEGER PRIMARY KEY)")

    migrations = [(1, "create_example", migration)]
    assert run_migrations(connection, migrations) == 1
    assert run_migrations(connection, migrations) == 1
    assert calls == [1]
    assert "id" in column_names(connection, "example")


def test_concurrent_migrations_are_serialized(tmp_path) -> None:
    database = tmp_path / "concurrent.db"
    calls = []

    def migration(connection: sqlite3.Connection) -> None:
        calls.append(1)
        connection.execute("CREATE TABLE example (id INTEGER PRIMARY KEY)")

    migrations = [(1, "create_example", migration)]

    def worker():
        connection = sqlite3.connect(database, timeout=10)
        try:
            return run_migrations(connection, migrations)
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: worker(), range(8)))

    assert results == [1] * 8
    assert calls == [1]
