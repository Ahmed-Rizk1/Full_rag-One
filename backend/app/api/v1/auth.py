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
    UpdateSettingsRequest,
)
from app.models.user import User
from app.services.auth_service import auth_service
from app.services.llm_client import LLMClient

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


from fastapi.responses import HTMLResponse
from sqlalchemy import select


@router.get(
    "/verify",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
)
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Verify user registration token and mark account as active/verified."""
    stmt = select(User).where(User.verification_token == token)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    
    if not user:
        return """
        <html>
            <body style="font-family: sans-serif; background-color: #09090b; color: #ef4444; text-align: center; padding-top: 100px;">
                <h2>❌ Invalid or expired verification token.</h2>
            </body>
        </html>
        """
    
    user.is_verified = True
    user.verification_token = None
    await db.commit()
    
    return """
    <html>
        <body style="font-family: sans-serif; background-color: #09090b; color: #10b981; text-align: center; padding-top: 100px;">
            <h2>🎉 Email verified successfully!</h2>
            <p style="color: #a1a1aa;">You can now close this tab and sign in through the workspace portal.</p>
        </body>
    </html>
    """


@router.put(
    "/settings",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def update_settings(
    settings_data: UpdateSettingsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update user API keys and preferred provider, validating any new keys first."""
    if settings_data.openai_api_key is not None:
        if settings_data.openai_api_key.strip():
            await LLMClient.validate_key(settings_data.openai_api_key, "openai")
            current_user.openai_api_key = settings_data.openai_api_key.strip()
        else:
            current_user.openai_api_key = None

    if settings_data.groq_api_key is not None:
        if settings_data.groq_api_key.strip():
            await LLMClient.validate_key(settings_data.groq_api_key, "groq")
            current_user.groq_api_key = settings_data.groq_api_key.strip()
        else:
            current_user.groq_api_key = None

    if settings_data.preferred_provider is not None:
        if settings_data.preferred_provider not in ("openai", "groq"):
            from app.core.exceptions import ValidationError
            raise ValidationError(detail="Preferred provider must be 'openai' or 'groq'.")
        current_user.preferred_provider = settings_data.preferred_provider

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user

