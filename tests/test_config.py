from __future__ import annotations

from python_studio import config


def test_update_settings_preserves_existing_key(tmp_path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DEEPSEEK_API_KEY=old-key\nDEEPSEEK_MODEL=old-model\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DEEPSEEK_API_KEY", "old-key")
    monkeypatch.setenv("DEEPSEEK_MODEL", "old-model")

    result = config.update_ai_settings(
        api_key=None,
        base_url="https://api.deepseek.com",
        model="deepseek-chat",
        timeout_seconds=60,
        history_limit=40,
        path=env_file,
    )

    content = env_file.read_text(encoding="utf-8")
    assert "DEEPSEEK_API_KEY=old-key" in content
    assert "DEEPSEEK_MODEL=deepseek-chat" in content
    assert result["configured"] is True


def test_clear_api_key_and_reject_invalid_url(tmp_path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    config.update_ai_settings(
        api_key=None,
        base_url="https://api.deepseek.com",
        model="deepseek-chat",
        timeout_seconds=60,
        history_limit=40,
        clear_api_key=True,
        path=env_file,
    )
    assert "DEEPSEEK_API_KEY=" in env_file.read_text(encoding="utf-8")

    try:
        config.update_ai_settings(
            api_key="key",
            base_url="http://example.com",
            model="deepseek-chat",
            timeout_seconds=60,
            history_limit=40,
            path=env_file,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Remote http URL must be rejected")

