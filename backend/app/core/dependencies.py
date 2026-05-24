import uuid
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.exceptions import AuthError, NotFoundError
from app.core.security import decode_token
from app.models.user import User
from app.repositories.user_repo import user_repository

# Standard bearer scheme
security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency to retrieve the currently authenticated user from the JWT access token."""
    if credentials is None:
        raise AuthError("Authentication credentials are required.")

    token = credentials.credentials
    # Decode and validate the access token
    payload = decode_token(token, expected_type="access")
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthError("Token payload is missing user identification.")

    # Convert string subject back to UUID object for database compatibility
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError as e:
        raise AuthError("Token subject is not a valid UUID identifier.") from e

    # Retrieve the user from database
    user = await user_repository.get(db, id=user_id)
    if not user:
        raise NotFoundError("User account was not found.")

    return user


def require_roles(*roles: str):
    """Dependency factory that returns a role validation dependency."""
    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in roles:
            raise AuthError(
                detail="You do not have permission to perform this action.",
                status_code=403,
            )
        return current_user

    return role_checker
