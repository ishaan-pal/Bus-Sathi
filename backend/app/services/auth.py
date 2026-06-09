import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.security import (
    generate_otp,
    get_otp_redis_key,
    get_otp_attempts_key,
    create_access_token,
    create_refresh_token,
    mock_aadhaar_verify,
)
from app.models.user import User


# ── OTP Send ──────────────────────────────────────────────────────────────────
async def send_otp(
    mobile: str,
    redis: aioredis.Redis,
) -> Tuple[bool, str]:
    """
    Generate and store OTP in Redis.
    In dev mode, OTP is always settings.OTP_DEV_FIXED ("123456").
    In production, sends via Fast2SMS API.

    Returns (success, message)
    """
    otp = generate_otp()
    otp_key = get_otp_redis_key(mobile)
    attempts_key = get_otp_attempts_key(mobile)

    # Store OTP with expiry
    await redis.setex(otp_key, settings.OTP_EXPIRE_SECONDS, otp)
    # Reset attempt counter
    await redis.setex(attempts_key, settings.OTP_EXPIRE_SECONDS, "0")

    if settings.OTP_DEV_MODE:
        print(f"[DEV] OTP for {mobile}: {otp}")
        return True, "OTP sent successfully (dev mode)"

    # ── Production SMS via Fast2SMS (free tier) ───────────────────────────
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.fast2sms.com/dev/bulkV2",
                headers={"authorization": settings.SMS_API_KEY},
                json={
                    "route": "otp",
                    "variables_values": otp,
                    "numbers": mobile,
                },
                timeout=10.0,
            )
            data = response.json()
            if data.get("return"):
                return True, "OTP sent successfully"
            return False, "Failed to send OTP via SMS"
    except Exception as e:
        print(f"SMS error: {e}")
        return False, "SMS service unavailable"


# ── OTP Verify ────────────────────────────────────────────────────────────────
async def verify_otp(
    mobile: str,
    otp_input: str,
    redis: aioredis.Redis,
) -> Tuple[bool, str]:
    """
    Verify OTP from Redis.
    Tracks attempt count — blocks after OTP_MAX_ATTEMPTS.

    Returns (success, message)
    """
    otp_key = get_otp_redis_key(mobile)
    attempts_key = get_otp_attempts_key(mobile)

    stored_otp = await redis.get(otp_key)
    if stored_otp is None:
        return False, "OTP expired or not found. Please request a new OTP."

    # Increment attempts
    attempts = await redis.incr(attempts_key)
    if attempts > settings.OTP_MAX_ATTEMPTS:
        await redis.delete(otp_key)
        await redis.delete(attempts_key)
        return False, "Too many incorrect attempts. Please request a new OTP."

    if stored_otp != otp_input.strip():
        remaining = settings.OTP_MAX_ATTEMPTS - attempts
        return False, f"Incorrect OTP. {remaining} attempt(s) remaining."

    # OTP matched — clean up Redis
    await redis.delete(otp_key)
    await redis.delete(attempts_key)
    return True, "OTP verified successfully"


# ── Get or Create User ────────────────────────────────────────────────────────
async def get_or_create_user(
    mobile: str,
    db: AsyncSession,
) -> Tuple[User, bool]:
    """
    Fetch existing user or create a new one after OTP verification.

    Returns (user, is_new_user)
    """
    result = await db.execute(
        select(User).where(User.mobile == mobile)
    )
    user = result.scalar_one_or_none()

    if user:
        return user, False

    # New user — create with mobile only; profile filled after Aadhaar
    user = User(
        id=str(uuid.uuid4()),
        mobile=mobile,
        is_active=True,
        is_admin=False,
        profile_complete=False,
        aadhaar_verified=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user, True


# ── Aadhaar Verification ──────────────────────────────────────────────────────
async def verify_aadhaar(
    user: User,
    aadhaar_number: str,
    db: AsyncSession,
) -> Tuple[bool, str, Optional[dict]]:
    """
    Verify Aadhaar and populate user profile.
    Uses mock stub until government API credentials obtained.

    Returns (success, message, aadhaar_data)
    """
    # Check if already verified
    if user.aadhaar_verified:
        return False, "Aadhaar already verified for this account", None

    # Check if Aadhaar linked to another account
    result = await db.execute(
        select(User).where(
            User.aadhaar_number == aadhaar_number,
            User.id != user.id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return False, "This Aadhaar is linked to another account", None

    # Verify via stub / real API
    success, aadhaar_data = mock_aadhaar_verify(aadhaar_number)
    if not success:
        return False, "Aadhaar verification failed. Please check the number.", None

    # Update user profile with Aadhaar data
    user.aadhaar_number = aadhaar_number
    user.aadhaar_verified = True
    if aadhaar_data.get("name"):
        user.name = aadhaar_data["name"]
    if aadhaar_data.get("dob"):
        user.date_of_birth = aadhaar_data["dob"]
    user.profile_complete = True

    await db.commit()
    await db.refresh(user)
    return True, "Aadhaar verified successfully", aadhaar_data


# ── Complete Profile (without Aadhaar) ───────────────────────────────────────
async def complete_profile_manual(
    user: User,
    name: str,
    date_of_birth: str,
    db: AsyncSession,
) -> User:
    """
    Allow profile completion without Aadhaar for demo mode.
    Aadhaar verification can be done later.
    """
    user.name = name.strip()
    user.date_of_birth = date_of_birth
    user.profile_complete = True
    await db.commit()
    await db.refresh(user)
    return user


# ── Issue Tokens ──────────────────────────────────────────────────────────────
def issue_tokens(user: User) -> dict:
    """
    Create and return access + refresh JWT pair.
    Embeds role flags in access token for quick middleware checks.
    """
    extra = {
        "mobile": user.mobile,
        "is_admin": user.is_admin,
        "is_staff": user.is_staff,
        "profile_complete": user.profile_complete,
    }
    access_token = create_access_token(subject=user.id, extra=extra)
    refresh_token = create_refresh_token(subject=user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user.id,
        "is_new_user": not user.profile_complete,
        "profile_complete": user.profile_complete,
        "aadhaar_verified": user.aadhaar_verified,
    }


# ── Refresh Token ─────────────────────────────────────────────────────────────
async def refresh_access_token(
    refresh_token: str,
    db: AsyncSession,
) -> Tuple[bool, str, Optional[dict]]:
    """
    Validate refresh token and issue new access token.

    Returns (success, message, token_data)
    """
    from app.core.security import decode_refresh_token
    user_id = decode_refresh_token(refresh_token)
    if not user_id:
        return False, "Invalid or expired refresh token", None

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        return False, "User not found or deactivated", None

    tokens = issue_tokens(user)
    return True, "Token refreshed", tokens