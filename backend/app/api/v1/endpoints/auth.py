from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.auth import (
    login_with_mobile,
    verify_aadhaar,
    issue_tokens,
    refresh_access_token,
    user_to_profile,
)
from app.schemas.user import (
    LoginRequest,
    LoginResponse,
    AadhaarVerifyRequest,
    AadhaarVerifyResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserProfileResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Login (mobile only — no OTP) ─────────────────────────────────────────────
@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Sign in with mobile number",
)
async def login_endpoint(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Sign in or register using mobile number only.
    Returns JWT tokens immediately — no OTP required.

    Aadhaar verification is required separately for booking tickets
    and applying for bus passes.
    """
    try:
        user, is_new, tokens = await login_with_mobile(body.mobile, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )

    return LoginResponse(
        success=True,
        message="Signed in successfully",
        is_new_user=is_new,
        tokens=TokenResponse(**tokens),
        user=UserProfileResponse(**user_to_profile(user)),
    )


# ── Aadhaar Verification ──────────────────────────────────────────────────────
@router.post(
    "/verify-aadhaar",
    response_model=AadhaarVerifyResponse,
    summary="Verify Aadhaar number",
)
async def verify_aadhaar_endpoint(
    body: AadhaarVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify Aadhaar and auto-populate name and DOB.
    Uses a mock stub until DigiLocker/UIDAI credentials are obtained.
    Required before booking tickets or applying for passes.
    """
    success, message, _ = await verify_aadhaar(
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
        user=UserProfileResponse(**user_to_profile(current_user)),
    )


# ── Refresh Token ─────────────────────────────────────────────────────────────
@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
async def refresh_token_endpoint(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
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


# ── Current User ──────────────────────────────────────────────────────────────
@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current user profile",
)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserProfileResponse(**user_to_profile(current_user))


# ── Logout ────────────────────────────────────────────────────────────────────
@router.post("/logout", summary="Logout")
async def logout():
    return {
        "success": True,
        "message": "Logged out successfully. Please discard your tokens.",
    }
