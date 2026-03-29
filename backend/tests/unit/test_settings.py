"""Settings parsing tests (no destructive global env mutation)."""

from __future__ import annotations

import pytest
from app.core.settings import Settings, get_settings


def test_cors_origins_validator_parses_comma_separated_string() -> None:
    s = Settings.model_validate(
        {
            "cors_origins": "http://localhost:3000, https://example.edu",
        }
    )
    assert s.cors_origins == ["http://localhost:3000", "https://example.edu"]


@pytest.mark.usefixtures("clear_settings_cache")
def test_get_settings_respects_log_level_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    get_settings.cache_clear()
    assert get_settings().log_level == "DEBUG"
