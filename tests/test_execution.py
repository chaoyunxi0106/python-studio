from __future__ import annotations

import os
import sys

from python_studio.execution import run_process


def test_run_process_captures_output(tmp_path) -> None:
    result = run_process(
        [sys.executable, "-c", "print('hello')"],
        cwd=tmp_path,
        env=os.environ.copy(),
        timeout_seconds=5,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "hello"
    assert result.timed_out is False


def test_run_process_timeout_is_bounded(tmp_path) -> None:
    result = run_process(
        [sys.executable, "-c", "import time; time.sleep(3)"],
        cwd=tmp_path,
        env=os.environ.copy(),
        timeout_seconds=1,
    )

    assert result.timed_out is True
    assert result.returncode == -1


def test_run_process_truncates_large_output(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("STUDIO_MAX_OUTPUT_BYTES", "10000")
    result = run_process(
        [sys.executable, "-c", "print('x' * 30000)"],
        cwd=tmp_path,
        env=os.environ.copy(),
        timeout_seconds=5,
    )

    assert "output truncated" in result.stdout
    assert len(result.stdout) < 11000
