from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.core.config import settings
from app.core.dependencies import get_db, get_redis, get_current_user
from app.models.user import User
from app.services.auth import (
    send_otp,
    verify_otp,
    get_or_create_user,
    verify_aadhaar,
    complete_profile_manual,
    issue_tokens,
    refresh_access_token,
)
from app.schemas.user import (
    SendOTPRequest,
    VerifyOTPRequest,
    AadhaarVerifyRequest,
    CompleteProfileRequest,
    RefreshTokenRequest,
    OTPSentResponse,
    OTPVerifyResponse,
    AadhaarVerifyResponse,
    ProfileCompleteResponse,
    TokenResponse,
    UserProfileResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Send OTP ──────────────────────────────────────────────────────────────────
@router.post(
    "/send-otp",
    response_model=OTPSentResponse,
    summary="Send OTP to mobile number",
)
async def send_otp_endpoint(
    body: SendOTPRequest,
    redis: aioredis.Redis = Depends(get_redis),
):
    """
    Send a 6-digit OTP to the given mobile number.
    In dev mode (OTP_DEV_MODE=True), OTP is always 123456
    and is returned in the response for convenience.
    """
    success, message = await send_otp(body.mobile, redis)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=message,
        )
    return OTPSentResponse(
        success=True,
        message=message,
        mobile=body.mobile,
        dev_mode=settings.OTP_DEV_MODE,
        dev_otp=settings.OTP_DEV_FIXED if settings.OTP_DEV_MODE else None,
    )


# ── Verify OTP ────────────────────────────────────────────────────────────────
@router.post(
    "/verify-otp",
    response_model=OTPVerifyResponse,
    summary="Verify OTP and issue JWT tokens",
)
async def verify_otp_endpoint(
    body: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """
    Verify the OTP sent to mobile number.
    - Existing user → returns tokens immediately
    - New user → returns tokens with is_new_user=True,
      client should redirect to Aadhaar/profile setup
    """
    # Verify OTP
    otp_success, otp_message = await verify_otp(body.mobile, body.otp, redis)
    if not otp_success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=otp_message,
        )

    # Get or create user
    user, is_new = await get_or_create_user(body.mobile, db)

    # Issue tokens
    tokens = issue_tokens(user)

    return OTPVerifyResponse(
        success=True,
        message="OTP verified successfully",
        is_new_user=is_new,
        tokens=TokenResponse(**tokens),
        user=UserProfileResponse(
            id=user.id,
            mobile=user.mobile,
            name=user.name,
            date_of_birth=user.date_of_birth,
            aadhaar_verified=user.aadhaar_verified,
            profile_complete=user.profile_complete,
            is_admin=user.is_admin,
            is_staff=user.is_staff,
            age=user.age,
            is_senior_citizen=user.is_senior_citizen,
            is_child=user.is_child,
        ),
    )


# ── Aadhaar Verification ──────────────────────────────────────────────────────
@router.post(
    "/verify-aadhaar",
    response_model=AadhaarVerifyResponse,
    summary="Verify Aadhaar number (stub for demo)",
)
async def verify_aadhaar_endpoint(
    body: AadhaarVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify Aadhaar number and auto-populate name and DOB.
    Currently uses a mock stub — replace with DigiLocker/UIDAI
    when government API credentials are obtained.

    Any valid 12-digit number works in demo mode.
    """
    success, message, aadhaar_data = await verify_aadhaar(
        user=current_user,
        aadhaar_number=body.aadhaar_number,
        db=db,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    return AadhaarVerifyResponse(
        success=True,
        message=message,
        user=UserProfileResponse(
            id=current_user.id,
            mobile=current_user.mobile,
            name=current_user.name,
            date_of_birth=current_user.date_of_birth,
            aadhaar_verified=current_user.aadhaar_verified,
            profile_complete=current_user.profile_complete,
            is_admin=current_user.is_admin,
            is_staff=current_user.is_staff,
            age=current_user.age,
            is_senior_citizen=current_user.is_senior_citizen,
            is_child=current_user.is_child,
        ),
    )


# ── Complete Profile Manually ─────────────────────────────────────────────────
@router.post(
    "/complete-profile",
    response_model=ProfileCompleteResponse,
    summary="Complete profile without Aadhaar (demo mode)",
)
async def complete_profile_endpoint(
    body: CompleteProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Allow profile completion by manually entering name and DOB.
    Used in demo mode when Aadhaar API is not yet available.
    Aadhaar can be verified later from the profile screen.
    """
    user = await complete_profile_manual(
        user=current_user,
        name=body.name,
        date_of_birth=body.date_of_birth,
        db=db,
    )
    return ProfileCompleteResponse(
        success=True,
        message="Profile completed successfully",
        user=UserProfileResponse(
            id=user.id,
            mobile=user.mobile,
            name=user.name,
            date_of_birth=user.date_of_birth,
            aadhaar_verified=user.aadhaar_verified,
            profile_complete=user.profile_complete,
            is_admin=user.is_admin,
            is_staff=user.is_staff,
            age=user.age,
            is_senior_citizen=user.is_senior_citizen,
            is_child=user.is_child,
        ),
    )


# ── Refresh Token ─────────────────────────────────────────────────────────────
@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token using refresh token",
)
async def refresh_token_endpoint(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Exchange a valid refresh token for a new access token.
    Refresh tokens are valid for 30 days.
    """
    success, message, token_data = await refresh_access_token(
        refresh_token=body.refresh_token,
        db=db,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
        )
    return TokenResponse(**token_data)


# ── Get Current User Profile ──────────────────────────────────────────────────
@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current authenticated user profile",
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """Return the profile of the currently authenticated user."""
    return UserProfileResponse(
        id=current_user.id,
        mobile=current_user.mobile,
        name=current_user.name,
        date_of_birth=current_user.date_of_birth,
        aadhaar_verified=current_user.aadhaar_verified,
        profile_complete=current_user.profile_complete,
        is_admin=current_user.is_admin,
        is_staff=current_user.is_staff,
        age=current_user.age,
        is_senior_citizen=current_user.is_senior_citizen,
        is_child=current_user.is_child,
    )


# ── Logout ────────────────────────────────────────────────────────────────────
@router.post(
    "/logout",
    summary="Logout (client-side token discard)",
)
async def logout():
    """
    Stateless logout — client must discard tokens.
    For production, implement a token blacklist in Redis.
    """
    return {
        "success": True,
        "message": "Logged out successfully. Please discard your tokens.",
    }