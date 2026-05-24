from datetime import datetime, timedelta, timezone
from typing import Any
import bcrypt
import jwt

from app.config import settings
from app.core.exceptions import AuthError

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    """Hash a plaintext password using raw bcrypt."""
    # Bcrypt requires bytes. Encode the password to UTF-8
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def create_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    """Generic function to create a JWT token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(subject: str | Any) -> str:
    """Create a short-lived access token."""
    return create_token(
        data={"sub": str(subject), "type": "access"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(subject: str | Any) -> str:
    """Create a long-lived refresh token."""
    return create_token(
        data={"sub": str(subject), "type": "refresh"},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    """Decode and validate a JWT token.

    Raises AuthError if the token is expired or invalid.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        token_type = payload.get("type")
        if token_type != expected_type:
            raise AuthError(f"Invalid token type. Expected '{expected_type}' token.")
        return payload
    except jwt.ExpiredSignatureError as e:
        raise AuthError("Token has expired.") from e
    except jwt.InvalidTokenError as e:
        raise AuthError("Token is invalid.") from e
