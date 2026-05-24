import pytest
from app.config import Settings
from app.core.exceptions import AppError, AuthError, NotFoundError, ValidationError


def test_settings_default_values():
    """Verify that Settings loads expected default values when no environment variables are set."""
    settings = Settings(_env_file=None)  # Avoid loading from any existing .env file
    assert settings.APP_NAME == "AI Workspace OS"
    assert settings.ENVIRONMENT == "development"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.CHROMA_PORT == 8000


def test_settings_env_overrides(monkeypatch):
    """Verify that settings can be overridden using environment variables."""
    monkeypatch.setenv("APP_NAME", "Test App Override")
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("CHROMA_PORT", "9000")
    monkeypatch.setenv("GROQ_API_KEY", "test_groq_key")

    settings = Settings(_env_file=None)
    assert settings.APP_NAME == "Test App Override"
    assert settings.ENVIRONMENT == "testing"
    assert settings.CHROMA_PORT == 9000
    assert settings.GROQ_API_KEY == "test_groq_key"


@pytest.mark.parametrize(
    "exception_class,expected_status_code,expected_default_detail",
    [
        (AppError, 500, "An unexpected application error occurred."),
        (NotFoundError, 404, "The requested resource was not found."),
        (AuthError, 401, "Authentication credentials are invalid or missing."),
        (ValidationError, 422, "The request parameters or body failed validation."),
    ]
)
def test_exceptions_expose_status_and_detail(exception_class, expected_status_code, expected_default_detail):
    """Verify that each custom exception has the correct default status_code and detail."""
    # Test default values
    exc = exception_class()
    assert exc.status_code == expected_status_code
    assert exc.detail == expected_default_detail

    # Test custom detail override
    custom_detail = "Custom error message"
    exc_custom = exception_class(detail=custom_detail)
    assert exc_custom.status_code == expected_status_code
    assert exc_custom.detail == custom_detail

    # Test custom status code override
    custom_status = 418
    exc_status = exception_class(status_code=custom_status)
    assert exc_status.status_code == custom_status
    assert exc_status.detail == expected_default_detail
