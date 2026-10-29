import pytest
from app.config import Settings


def test_cors_origins_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    settings = Settings()
    assert "http://localhost:5173" in settings.cors_allowed_origins
    assert "http://localhost:8080" in settings.cors_allowed_origins


def test_cors_origins_comma_separated(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "CORS_ALLOWED_ORIGINS",
        "https://my-app.vercel.app, https://custom-domain.com",
    )
    settings = Settings()
    assert settings.cors_allowed_origins == [
        "https://my-app.vercel.app",
        "https://custom-domain.com",
    ]


def test_cors_origins_wildcard(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "*")
    settings = Settings()
    assert settings.cors_allowed_origins == ["*"]


def test_cors_origins_json_list(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", '["https://a.com", "https://b.com"]')
    settings = Settings()
    assert settings.cors_allowed_origins == ["https://a.com", "https://b.com"]


def test_cors_origins_empty_string(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "   ")
    settings = Settings()
    assert settings.cors_allowed_origins == []

