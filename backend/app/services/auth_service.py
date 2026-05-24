from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, AuthError
from app.core.schemas.user import LoginRequest, SignupRequest, TokenResponse
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repo import user_repository


class AuthService:
    """Service layer coordinating user registration, authentication, and session refreshment."""

    async def signup(self, db: AsyncSession, signup_data: SignupRequest) -> User:
        """Register a new user after verifying that the email is not duplicate."""
        existing_user = await user_repository.get_by_email(db, email=signup_data.email)
        if existing_user:
            raise AppError(
                detail="A user with this email address already exists.",
                status_code=409,
            )

        hashed_password = hash_password(signup_data.password)
        user_data = {
            "email": signup_data.email,
            "hashed_password": hashed_password,
            "full_name": signup_data.full_name,
            "role": "user",  # Default role
        }
        return await user_repository.create(db, obj_in=user_data)

    async def login(self, db: AsyncSession, login_data: LoginRequest) -> TokenResponse:
        """Authenticate user credentials and return a new session token pair."""
        user = await user_repository.get_by_email(db, email=login_data.email)
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise AuthError("Invalid email or password.")

        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh(self, db: AsyncSession, refresh_token: str) -> TokenResponse:
        """Validate the refresh token and return rotated access and refresh tokens."""
        payload = decode_token(refresh_token, expected_type="refresh")
        import uuid
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise AuthError("Invalid refresh token payload.")

        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError as e:
            raise AuthError("Invalid user ID in token.") from e

        user = await user_repository.get(db, id=user_id)
        if not user:
            raise AuthError("User not found or inactive.")

        access_token = create_access_token(subject=user.id)
        new_refresh_token = create_refresh_token(subject=user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
        )


auth_service = AuthService()
