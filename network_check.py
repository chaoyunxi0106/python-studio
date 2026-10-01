"""Standalone network diagnostic for the companion AI connection.

Run it in the same terminal you use to start the studio:

    python network_check.py

It walks the connection one layer at a time and tells you which layer is
blocked, so a WinError 10013 can be traced to its real cause.
"""

from __future__ import annotations

import json
import socket
import ssl
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8")

from python_studio.config import get_deepseek_config  # noqa: E402


def line(title: str) -> None:
    print()
    print(f"--- {title} ---")


def ok(message: str) -> None:
    print(f"  [OK]   {message}")


def bad(message: str) -> None:
    print(f"  [FAIL] {message}")


def info(message: str) -> None:
    print(f"  [info] {message}")


def check_runtime() -> None:
    line("1. 运行环境")
    info(f"解释器：{sys.executable}")
    info(f"版本：{sys.version.split()[0]}")


def check_env() -> tuple[str, str]:
    line("2. 配置")
    config = get_deepseek_config()
    info(f"Base URL：{config.base_url}")
    info(f"模型：{config.model}")
    info(f"密钥：{'已设置' if config.api_key else '未设置'}")
    return config.base_url, config.api_key


def check_dns(host: str) -> list[str]:
    line("3. 域名解析")
    try:
        addresses = sorted({item[4][0] for item in socket.getaddrinfo(host, 443)})
    except socket.gaierror as error:
        bad(f"解析失败：{error}")
        return []
    ok(f"{host} -> {', '.join(addresses[:4])}")
    return addresses


def check_tcp(host: str) -> bool:
    line("4. TCP 连接 443（这一步失败就是 10013 的来源）")
    try:
        with socket.create_connection((host, 443), timeout=10) as sock:
            local = sock.getsockname()
            ok(f"已连接，本地端口 {local[1]}")
        return True
    except OSError as error:
        code = getattr(error, "winerror", None) or error.errno
        bad(f"{type(error).__name__} winerror={code} {error}")
        if code == 10013:
            print()
            print("  WinError 10013 表示发起这次连接时被系统拒绝，常见原因按概率排序：")
            print("   a) 防火墙或安全软件拦截了该 python.exe 的出站连接")
            print("   b) WSL / Hyper-V / Docker 占用并保留了动态端口段")
            print("   c) 服务器安全策略或端点防护禁止该进程联网")
        return False


def check_tls(host: str) -> bool:
    line("5. TLS 握手")
    context = ssl.create_default_context()
    try:
        with socket.create_connection((host, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=host) as tls:
                ok(f"协议 {tls.version()}，证书主体 {tls.getpeercert().get('subject')}")
        return True
    except OSError as error:
        code = getattr(error, "winerror", None) or error.errno
        bad(f"{type(error).__name__} winerror={code} {error}")
        return False


def check_http(base_url: str, api_key: str) -> bool:
    line("6. 真实接口请求")
    if not api_key:
        info("未配置密钥，跳过。")
        return False
    request = Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(
            {
                "model": get_deepseek_config().model,
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 2,
            }
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "PythonStudio/0.1",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            ok(f"HTTP {response.status}，模型已响应。")
        return True
    except HTTPError as error:
        if error.code in {401, 403}:
            bad(f"HTTP {error.code}：网络是通的，是密钥或权限问题。")
        else:
            bad(f"HTTP {error.code}：网络是通的，接口返回了业务错误。")
        return False
    except URLError as error:
        code = getattr(error.reason, "winerror", None) or getattr(
            error.reason, "errno", None
        )
        bad(f"{type(error.reason).__name__} winerror={code} {error.reason}")
        return False
    except Exception as error:  # noqa: BLE001
        bad(f"{type(error).__name__} {error}")
        return False


def check_port_ranges() -> None:
    line("7. 动态端口与保留段（WSL/Hyper-V 相关）")
    try:
        excluded = subprocess.run(
            ["netsh", "int", "ipv4", "show", "excludedportrange", "protocol=tcp"],
            capture_output=True,
            text=True,
            timeout=15,
        ).stdout
    except (OSError, subprocess.SubprocessError) as error:
        info(f"无法读取：{error}")
        return
    for raw in excluded.splitlines():
        parts = raw.split()
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            info(f"保留段 {parts[0]}-{parts[1]}")
    info("如果保留段与你看到的失败端口重合，说明是 WSL/Hyper-V 的端口保留。")


def main() -> int:
    print("Python Studio 伴学 AI 连接诊断")
    check_runtime()
    base_url, api_key = check_env()
    host = urlparse(base_url).hostname or "api.deepseek.com"
    if not check_dns(host):
        return 1
    if not check_tcp(host):
        check_port_ranges()
        print()
        print("结论：连接在 TCP 层就被拒绝，与 API 密钥无关。")
        return 1
    if not check_tls(host):
        return 1
    if not check_http(base_url, api_key):
        return 1
    print()
    print("结论：网络链路完全正常，若应用内仍失败，请重启 python studio.py serve。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
