from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import ProxyHandler, Request, build_opener, install_opener, urlopen

from .paths import PROJECT_ROOT


ENV_FILE = PROJECT_ROOT / ".env"


def load_local_env(path: Path = ENV_FILE) -> None:
    """Load simple KEY=VALUE lines without overriding process variables."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


@dataclass(frozen=True)
class DeepSeekConfig:
    api_key: str
    base_url: str
    model: str
    timeout_seconds: int
    history_limit: int

    @property
    def configured(self) -> bool:
        return bool(self.api_key)


def get_deepseek_config() -> DeepSeekConfig:
    load_local_env()
    # Keeps every outbound call proxy-aware when .env sets DEEPSEEK_PROXY.
    apply_proxy()
    return DeepSeekConfig(
        api_key=os.environ.get("DEEPSEEK_API_KEY", "").strip(),
        base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip(),
        model=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat").strip(),
        timeout_seconds=int(os.environ.get("DEEPSEEK_TIMEOUT_SECONDS", "60")),
        history_limit=int(os.environ.get("COMPANION_HISTORY_LIMIT", "40")),
    )


def ai_settings_payload() -> dict[str, object]:
    config = get_deepseek_config()
    return {
        "configured": config.configured,
        "base_url": config.base_url,
        "model": config.model,
        "timeout_seconds": config.timeout_seconds,
        "history_limit": config.history_limit,
    }


def describe_network_error(error: BaseException) -> str:
    """Turn low-level socket failures into something a learner can act on."""
    reason = getattr(error, "reason", error)
    code = getattr(reason, "winerror", None) or getattr(reason, "errno", None)
    if code == 10013:
        return (
            "系统拒绝了这次对外连接（WinError 10013）。这通常不是密钥问题，"
            "而是运行环境不允许联网：如果服务是在沙箱或受限容器里启动的，"
            "请在普通终端重新运行 python studio.py serve；"
            "否则请检查防火墙或杀毒软件是否拦截了 python.exe 的出站连接。"
        )
    if isinstance(reason, TimeoutError) or code in {10060, 110}:
        return "连接超时。请检查网络，或确认 Base URL 是否需要代理。"
    if code in {11001, 8}:
        return "域名解析失败。请检查 DNS 或 Base URL 拼写。"
    return f"连接失败：{reason}"


def get_proxy_url() -> str:
    load_local_env()
    for key in ("DEEPSEEK_PROXY", "HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
        value = os.environ.get(key, "").strip()
        if value:
            return value
    return ""


def apply_proxy() -> str:
    """Install a global proxy opener when .env configures one.

    Routing through a local proxy is the practical way around an OS-level
    ``WinError 10013``: the process then only talks to the proxy's loopback
    port, which is normally permitted. Installing the opener globally keeps
    every existing ``urlopen`` call site proxy-aware without touching them.
    """
    proxy = get_proxy_url()
    if proxy:
        install_opener(build_opener(ProxyHandler({"http": proxy, "https": proxy})))
    return proxy


def open_url(request: Request, *, timeout: int):
    apply_proxy()
    return urlopen(request, timeout=timeout)


def _validate_base_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Base URL must be a valid http(s) URL.")
    if parsed.scheme == "http" and parsed.hostname not in {
        "127.0.0.1",
        "localhost",
        "::1",
    }:
        raise ValueError("Only localhost may use http; remote URLs must use https.")
    return value.rstrip("/")


def update_ai_settings(
    *,
    api_key: str | None,
    base_url: str,
    model: str,
    timeout_seconds: int,
    history_limit: int,
    clear_api_key: bool = False,
    path: Path = ENV_FILE,
) -> dict[str, object]:
    normalized_url = _validate_base_url(base_url.strip())
    normalized_model = model.strip()
    if not normalized_model:
        raise ValueError("Model is required.")
    if not 5 <= timeout_seconds <= 180:
        raise ValueError("Timeout must be between 5 and 180 seconds.")
    if not 5 <= history_limit <= 100:
        raise ValueError("History limit must be between 5 and 100.")

    current = get_deepseek_config()
    new_key = ""
    if clear_api_key:
        new_key = ""
    elif api_key is not None and api_key.strip():
        new_key = api_key.strip()
    else:
        new_key = current.api_key

    values = {
        "DEEPSEEK_API_KEY": new_key,
        "DEEPSEEK_BASE_URL": normalized_url,
        "DEEPSEEK_MODEL": normalized_model,
        "DEEPSEEK_TIMEOUT_SECONDS": str(timeout_seconds),
        "COMPANION_HISTORY_LIMIT": str(history_limit),
    }
    existing_lines = (
        path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    )
    seen: set[str] = set()
    output: list[str] = []
    for line in existing_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            output.append(line)
            continue
        key = stripped.split("=", 1)[0].strip()
        if key in values:
            output.append(f"{key}={values[key]}")
            seen.add(key)
        else:
            output.append(line)
    for key, value in values.items():
        if key not in seen:
            output.append(f"{key}={value}")

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text("\n".join(output).strip() + "\n", encoding="utf-8")
    temporary.replace(path)
    try:
        path.chmod(0o600)
    except OSError:
        pass

    os.environ.update(values)
    return ai_settings_payload()


def test_ai_connection() -> dict[str, object]:
    config = get_deepseek_config()
    if not config.configured:
        raise ValueError("API key is not configured.")
    request = Request(
        config.base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(
            {
                "model": config.model,
                "messages": [{"role": "user", "content": "只回复 OK"}],
                "temperature": 0,
                "max_tokens": 8,
            },
            ensure_ascii=False,
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "PythonStudio/0.1",
        },
        method="POST",
    )
    started = time.perf_counter()
    try:
        with open_url(request, timeout=config.timeout_seconds) as response:
            response.read()
    except HTTPError as error:
        raise ValueError(f"Connection failed with HTTP {error.code}.") from error
    except URLError as error:
        raise ValueError(describe_network_error(error)) from error
    except TimeoutError as error:
        raise ValueError(describe_network_error(error)) from error
    return {
        "ok": True,
        "model": config.model,
        "latency_ms": round((time.perf_counter() - started) * 1000),
    }
