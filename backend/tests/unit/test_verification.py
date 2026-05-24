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
