from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.core.schemas.user import (
    LoginRequest,
    RefreshRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)
from app.models.user import User
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def signup(
    signup_data: SignupRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user account."""
    return await auth_service.signup(db, signup_data)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate and obtain JWT access and refresh tokens."""
    return await auth_service.login(db, login_data)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def refresh(
    refresh_data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Rotate expired access token using a valid refresh token."""
    return await auth_service.refresh(db, refresh_token=refresh_data.refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def read_current_user(
    current_user: User = Depends(get_current_user),
):
    """Retrieve the currently authenticated user's profile details."""
    return current_user
