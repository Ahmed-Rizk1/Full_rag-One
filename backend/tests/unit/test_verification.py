from unittest.mock import patch
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.user import User


@pytest.mark.asyncio
async def test_email_verification_flow(client: AsyncClient, db_session: AsyncSession):
    """Test signup creates unverified user, login fails with 403, verification succeeds, and then login succeeds."""
    # Force environment to development to require verification
    original_env = settings.ENVIRONMENT
    settings.ENVIRONMENT = "development"
    try:
        email = "verify_test@example.com"
        password = "testpassword123"
        name = "Verify Test User"

        # 1. Signup
        signup_payload = {"email": email, "password": password, "full_name": name}
        res = await client.post("/api/v1/auth/signup", json=signup_payload)
        assert res.status_code == 201
        
        # Verify user is created as unverified and has token in DB
        db_res = await db_session.execute(select(User).where(User.email == email))
        user = db_res.scalar_one()
        assert user.is_verified is False
        assert user.verification_token is not None
        token = user.verification_token

        # 2. Login fails with 403 Forbidden
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_res.status_code == 403
        assert "Email not verified" in login_res.json()["detail"]

        # 3. Requesting verification via the endpoint succeeds
        verify_res = await client.get(f"/api/v1/auth/verify?token={token}")
        assert verify_res.status_code == 200
        assert "verified successfully" in verify_res.text

        # 4. Login now succeeds
        login_res2 = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_res2.status_code == 200
        assert "access_token" in login_res2.json()
    finally:
        settings.ENVIRONMENT = original_env


@pytest.mark.asyncio
async def test_update_settings_and_validation(client: AsyncClient, db_session: AsyncSession):
    """Test updating user preferred provider and API keys with validation checks."""
    email = "settings_test@example.com"
    password = "settingspassword123"
    name = "Settings Test User"
    
    original_env = settings.ENVIRONMENT
    settings.ENVIRONMENT = "testing"
    try:
        # Signup
        signup_payload = {"email": email, "password": password, "full_name": name}
        res = await client.post("/api/v1/auth/signup", json=signup_payload)
        assert res.status_code == 201
        
        # Login
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_res.status_code == 200
        token_data = login_res.json()
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}

        # 2. Try updating preferred provider and keys with invalid key mock failing
        from app.core.exceptions import ValidationError
        with patch("app.services.llm_client.LLMClient.validate_key", side_effect=ValidationError("Invalid API key")):
            settings_payload = {
                "openai_api_key": "bad_key",
                "groq_api_key": "bad_key",
                "preferred_provider": "openai"
            }
            res = await client.put("/api/v1/auth/settings", json=settings_payload, headers=headers)
            assert res.status_code == 422
            assert "Invalid API key" in res.json()["detail"]

        # 3. Update with valid mock succeeding
        with patch("app.services.llm_client.LLMClient.validate_key", return_value=True):
            settings_payload = {
                "openai_api_key": "sk-validkey",
                "groq_api_key": "gsk_validkey",
                "preferred_provider": "openai"
            }
            res = await client.put("/api/v1/auth/settings", json=settings_payload, headers=headers)
            assert res.status_code == 200
            user_data = res.json()
            assert user_data["preferred_provider"] == "openai"
            assert user_data["has_openai_key"] is True
            assert user_data["has_groq_key"] is True

        # 4. Check that /auth/me returns computed attributes
        me_res = await client.get("/api/v1/auth/me", headers=headers)
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["preferred_provider"] == "openai"
        assert me_data["has_openai_key"] is True
        assert me_data["has_groq_key"] is True

    finally:
        settings.ENVIRONMENT = original_env

