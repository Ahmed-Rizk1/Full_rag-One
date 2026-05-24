import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.repositories.user_repo import user_repository


def test_password_hashing():
    """Verify that password hashing and verification works correctly."""
    password = "supersecretpassword123"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_jwt_token_flow():
    """Verify access and refresh token creation, decoding, and validation."""
    user_id = "550e8400-e29b-41d4-a716-446655440000"

    # Test access token
    access_token = create_access_token(user_id)
    payload = decode_token(access_token, expected_type="access")
    assert payload.get("sub") == user_id

    # Test refresh token
    refresh_token = create_refresh_token(user_id)
    payload_refresh = decode_token(refresh_token, expected_type="refresh")
    assert payload_refresh.get("sub") == user_id


def test_jwt_invalid_type_raises_error():
    """Verify decoding a token with mismatching expected type raises AuthError."""
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    access_token = create_access_token(user_id)

    with pytest.raises(AuthError) as exc_info:
        decode_token(access_token, expected_type="refresh")
    assert "Invalid token type" in str(exc_info.value)


@pytest.mark.asyncio
async def test_api_auth_flow(client: AsyncClient, db_session: AsyncSession):
    """Test full integration API flow for signup, login, refresh, and /me."""
    email = "auth_flow_test@example.com"
    password = "testpassword123"
    name = "Auth Flow User"

    # 1. Test POST /signup
    signup_payload = {"email": email, "password": password, "full_name": name}
    response = await client.post("/api/v1/auth/signup", json=signup_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == email
    assert data["full_name"] == name
    assert "id" in data

    # Try duplicate signup
    dup_response = await client.post("/api/v1/auth/signup", json=signup_payload)
    assert dup_response.status_code == 409
    assert "already exists" in dup_response.json()["detail"]

    # 2. Test POST /login
    login_payload = {"email": email, "password": password}
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"

    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]

    # Test invalid login credentials
    bad_login_response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "wrongpassword"}
    )
    assert bad_login_response.status_code == 401

    # 3. Test GET /me (unauthenticated first)
    unauth_me = await client.get("/api/v1/auth/me")
    assert unauth_me.status_code == 401

    # Test GET /me (authenticated)
    headers = {"Authorization": f"Bearer {access_token}"}
    me_response = await client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["email"] == email
    assert me_data["full_name"] == name

    # 4. Test POST /refresh
    refresh_response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_response.status_code == 200
    refreshed_tokens = refresh_response.json()
    assert "access_token" in refreshed_tokens
    assert "refresh_token" in refreshed_tokens


@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient):
    """Test health check route."""
    # Since Postgres is a test SQLite engine in memory (mocked), and Redis/Chroma are not running,
    # it might return 503 degraded depending on environment, which is expected and valid.
    response = await client.get("/api/v1/health")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "postgres" in data["services"]
    assert "redis" in data["services"]
    assert "chromadb" in data["services"]
