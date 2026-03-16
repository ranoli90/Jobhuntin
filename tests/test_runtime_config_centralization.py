from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from shared.config import get_settings
from shared.redirect_validation import _get_allowed_redirect_origins


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_local_redirect_origins_are_loaded_from_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENV", "local")
    monkeypatch.setenv("APP_BASE_URL", "https://app.example.com")
    monkeypatch.setenv(
        "LOCAL_REDIRECT_ORIGINS",
        "http://localhost:4321,http://127.0.0.1:4444/",
    )

    origins = _get_allowed_redirect_origins()

    assert origins == [
        "https://app.example.com",
        "http://localhost:4321",
        "http://127.0.0.1:4444",
    ]


@pytest.mark.asyncio
async def test_local_redis_fallback_uses_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    from shared.redis_client import RedisManager

    monkeypatch.setenv("ENV", "local")
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setenv("LOCAL_REDIS_URL", "redis://cache.internal:6380")

    manager = RedisManager()

    with patch("shared.redis_client.redis.from_url", return_value=object()) as mock_from_url:
        await manager.get_client()

    assert mock_from_url.call_args.args[0] == "redis://cache.internal:6380"


def test_api_cache_disk_path_is_loaded_from_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_CACHE_DISK_PATH", "C:/runtime-cache/api")

    settings = get_settings()

    assert Path(settings.api_cache_disk_path) == Path("C:/runtime-cache/api")
