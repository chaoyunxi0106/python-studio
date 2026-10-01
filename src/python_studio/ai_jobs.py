from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any, TypeVar

from .store import _connect, _now


T = TypeVar("T")


def _cache_key(kind: str, payload: Any) -> str:
    canonical = json.dumps(
        {"kind": kind, "payload": payload},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def get_cached_response(kind: str, payload: Any) -> Any | None:
    key = _cache_key(kind, payload)
    with _connect() as connection:
        row = connection.execute(
            "SELECT response_json FROM ai_cache WHERE cache_key = ?",
            (key,),
        ).fetchone()
    return json.loads(row["response_json"]) if row else None


def save_cached_response(kind: str, payload: Any, response: Any) -> None:
    key = _cache_key(kind, payload)
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO ai_cache (cache_key, kind, response_json, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET
                response_json = excluded.response_json,
                created_at = excluded.created_at
            """,
            (
                key,
                kind,
                json.dumps(response, ensure_ascii=False),
                _now(),
            ),
        )


def run_ai_operation(
    kind: str,
    payload: Any,
    operation: Callable[[], T],
    *,
    use_cache: bool = True,
) -> T:
    key = _cache_key(kind, payload)
    if use_cache:
        cached = get_cached_response(kind, payload)
        if cached is not None:
            with _connect() as connection:
                connection.execute(
                    """
                    INSERT INTO ai_jobs (
                        kind, cache_key, status, input_chars, output_chars,
                        duration_ms, created_at, finished_at
                    )
                    VALUES (?, ?, 'cache_hit', ?, ?, 0, ?, ?)
                    """,
                    (
                        kind,
                        key,
                        len(json.dumps(payload, ensure_ascii=False)),
                        len(json.dumps(cached, ensure_ascii=False)),
                        _now(),
                        _now(),
                    ),
                )
            return cached

    input_chars = len(json.dumps(payload, ensure_ascii=False))
    started = time.perf_counter()
    with _connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO ai_jobs (
                kind, cache_key, status, input_chars, created_at
            )
            VALUES (?, ?, 'running', ?, ?)
            """,
            (kind, key, input_chars, _now()),
        )
        job_id = int(cursor.lastrowid)

    try:
        result = operation()
    except Exception as error:
        duration_ms = round((time.perf_counter() - started) * 1000)
        with _connect() as connection:
            connection.execute(
                """
                UPDATE ai_jobs
                SET status = 'failed', duration_ms = ?, error = ?, finished_at = ?
                WHERE id = ?
                """,
                (duration_ms, str(error)[:1000], _now(), job_id),
            )
        raise

    duration_ms = round((time.perf_counter() - started) * 1000)
    output_chars = len(json.dumps(result, ensure_ascii=False))
    with _connect() as connection:
        connection.execute(
            """
            UPDATE ai_jobs
            SET status = 'completed', output_chars = ?, duration_ms = ?,
                finished_at = ?
            WHERE id = ?
            """,
            (output_chars, duration_ms, _now(), job_id),
        )
    if use_cache:
        save_cached_response(kind, payload, result)
    return result


def ai_usage_summary() -> dict[str, Any]:
    with _connect() as connection:
        totals = connection.execute(
            """
            SELECT COUNT(*) AS jobs,
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed,
                   SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed,
                   SUM(CASE WHEN status = 'cache_hit' THEN 1 ELSE 0 END) AS cache_hits,
                   COALESCE(SUM(input_chars), 0) AS input_chars,
                   COALESCE(SUM(output_chars), 0) AS output_chars,
                   COALESCE(SUM(duration_ms), 0) AS duration_ms
            FROM ai_jobs
            """
        ).fetchone()
        cache = connection.execute(
            "SELECT COUNT(*) AS count FROM ai_cache"
        ).fetchone()
    return {
        "jobs": int(totals["jobs"] or 0),
        "completed": int(totals["completed"] or 0),
        "failed": int(totals["failed"] or 0),
        "cache_hits": int(totals["cache_hits"] or 0),
        "cache_entries": int(cache["count"] or 0),
        "input_chars": int(totals["input_chars"] or 0),
        "output_chars": int(totals["output_chars"] or 0),
        "duration_ms": int(totals["duration_ms"] or 0),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }

