from __future__ import annotations

import pytest

from python_studio.providers.deepseek import ProviderError, extract_json_object


def test_extract_json_object_accepts_fenced_json() -> None:
    payload = extract_json_object('```json\n{"ok": true}\n```')
    assert payload == {"ok": True}


def test_extract_json_object_rejects_non_object() -> None:
    with pytest.raises(ProviderError):
        extract_json_object("[1, 2, 3]")
