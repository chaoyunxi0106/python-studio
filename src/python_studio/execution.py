from __future__ import annotations

import os
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


DEFAULT_OUTPUT_LIMIT = 200_000
DEFAULT_MEMORY_LIMIT_MB = 512


@dataclass(frozen=True)
class ProcessResult:
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False


def _output_limit() -> int:
    try:
        value = int(os.environ.get("STUDIO_MAX_OUTPUT_BYTES", ""))
    except ValueError:
        value = DEFAULT_OUTPUT_LIMIT
    return max(10_000, min(value, 2_000_000))


def _memory_limit_bytes() -> int:
    try:
        value = int(os.environ.get("STUDIO_MAX_MEMORY_MB", ""))
    except ValueError:
        value = DEFAULT_MEMORY_LIMIT_MB
    value = max(128, min(value, 4096))
    return value * 1024 * 1024


def _preexec_limits(timeout_seconds: int) -> None:
    """Apply POSIX best-effort limits; Windows relies on timeout and ACLs."""
    if os.name != "posix":
        return
    try:
        import resource

        cpu = max(1, int(timeout_seconds) + 1)
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 1))
        resource.setrlimit(resource.RLIMIT_FSIZE, (_output_limit() * 2, _output_limit() * 2))
        resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
        resource.setrlimit(
            resource.RLIMIT_AS,
            (_memory_limit_bytes(), _memory_limit_bytes()),
        )
    except (ImportError, OSError, ValueError):
        return


def _read_limited(path: Path, limit: int) -> str:
    data = path.read_bytes()
    if len(data) <= limit:
        return data.decode("utf-8", errors="replace")
    suffix = "\n...[output truncated by Python Studio]"
    return data[:limit].decode("utf-8", errors="replace") + suffix


def run_process(
    command: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    timeout_seconds: int,
) -> ProcessResult:
    """Run a local command without a shell and with bounded output/time."""
    if not command:
        raise ValueError("Command must not be empty.")
    limit = _output_limit()
    started = time.perf_counter()
    creationflags = 0
    start_new_session = False
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    else:
        start_new_session = True

    with tempfile.TemporaryDirectory(prefix="python-studio-run-") as temp_dir:
        stdout_path = Path(temp_dir) / "stdout.txt"
        stderr_path = Path(temp_dir) / "stderr.txt"
        with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
            process = subprocess.Popen(
                list(command),
                cwd=cwd,
                env=dict(env),
                stdin=subprocess.DEVNULL,
                stdout=stdout_file,
                stderr=stderr_file,
                shell=False,
                creationflags=creationflags,
                start_new_session=start_new_session,
                preexec_fn=(
                    (lambda: _preexec_limits(timeout_seconds))
                    if os.name == "posix"
                    else None
                ),
            )
            timed_out = False
            try:
                returncode = process.wait(timeout=max(1, timeout_seconds))
            except subprocess.TimeoutExpired:
                timed_out = True
                _terminate_process(process)
                returncode = -1
        stdout = _read_limited(stdout_path, limit)
        stderr = _read_limited(stderr_path, limit)

    return ProcessResult(
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        duration_seconds=round(time.perf_counter() - started, 2),
        timed_out=timed_out,
    )


def _terminate_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    try:
        if os.name == "posix":
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        else:
            process.kill()
    except (OSError, ProcessLookupError):
        try:
            process.kill()
        except OSError:
            pass
    finally:
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass
