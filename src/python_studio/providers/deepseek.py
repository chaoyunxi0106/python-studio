from __future__ import annotations

import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request

from ..config import DeepSeekConfig, open_url


class ProviderError(RuntimeError):
    pass


def chat_completion(
    config: DeepSeekConfig,
    messages: list[dict[str, Any]],
    *,
    temperature: float,
    max_tokens: int,
    response_format: bool = True,
    tools: list[dict[str, Any]] | None = None,
    tool_choice: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": config.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        body["response_format"] = {"type": "json_object"}
    if tools:
        body["tools"] = tools
        body["tool_choice"] = tool_choice or "auto"

    request = Request(
        config.base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "PythonStudio/0.1",
        },
        method="POST",
    )
    try:
        with open_url(request, timeout=config.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise ProviderError(f"DeepSeek request failed with HTTP {error.code}.") from error
    except URLError as error:
        raise ProviderError(f"Unable to reach DeepSeek: {error.reason}") from error
    except TimeoutError as error:
        raise ProviderError("DeepSeek request timed out.") from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ProviderError("DeepSeek returned malformed JSON.") from error

    try:
        return dict(payload["choices"][0]["message"])
    except (KeyError, IndexError, TypeError) as error:
        raise ProviderError("DeepSeek returned an unexpected response.") from error


def extract_json_object(content: str) -> dict[str, Any]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", str(content).strip())
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as first_error:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            raise ProviderError("DeepSeek did not return a JSON object.") from first_error
        try:
            payload = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as error:
            raise ProviderError("DeepSeek returned malformed JSON.") from error
    if not isinstance(payload, dict):
        raise ProviderError("DeepSeek JSON response must be an object.")
    return payload


def chat_json(
    config: DeepSeekConfig,
    messages: list[dict[str, Any]],
    *,
    temperature: float,
    max_tokens: int,
) -> dict[str, Any]:
    message = chat_completion(
        config,
        messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format=True,
    )
    return extract_json_object(str(message.get("content") or ""))
