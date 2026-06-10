import uuid
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import (
    create_access_token,
    create_refresh_token,
    mock_aadhaar_verify,
)
from app.models.user import User


async def login_with_mobile(
    mobile: str,
    db: AsyncSession,
) -> Tuple[User, bool, dict]:
    """
    Sign in or register with mobile number only (no OTP).
    Returns (user, is_new_user, tokens).
    """
    user, is_new = await get_or_create_user(mobile, db)
    if not user.is_active:
        raise ValueError("Account is deactivated")
    tokens = issue_tokens(user)
    return user, is_new, tokens


async def get_or_create_user(
    mobile: str,
    db: AsyncSession,
) -> Tuple[User, bool]:
    """Fetch existing user or create a new one. Returns (user, is_new_user)."""
    result = await db.execute(select(User).where(User.mobile == mobile))
    user = result.scalar_one_or_none()

    if user:
        return user, False

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


async def verify_aadhaar(
    user: User,
    aadhaar_number: str,
    db: AsyncSession,
) -> Tuple[bool, str, Optional[dict]]:
    """
    Verify Aadhaar and populate user profile.
    Uses mock stub until government API credentials are obtained.
    """
    if user.aadhaar_verified:
        return False, "Aadhaar already verified for this account", None

    result = await db.execute(
        select(User).where(
            User.aadhaar_number == aadhaar_number,
            User.id != user.id,
        )
    )
    if result.scalar_one_or_none():
        return False, "This Aadhaar is linked to another account", None

    success, aadhaar_data = mock_aadhaar_verify(aadhaar_number)
    if not success:
        return False, "Aadhaar verification failed. Please check the number.", None

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


def issue_tokens(user: User) -> dict:
    """Create access + refresh JWT pair."""
    extra = {
        "mobile": user.mobile,
        "is_admin": user.is_admin,
        "is_staff": user.is_staff,
        "aadhaar_verified": user.aadhaar_verified,
    }
    access_token = create_access_token(subject=user.id, extra=extra)
    refresh_token = create_refresh_token(subject=user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user.id,
        "is_new_user": not user.aadhaar_verified,
        "profile_complete": user.profile_complete,
        "aadhaar_verified": user.aadhaar_verified,
    }


async def refresh_access_token(
    refresh_token: str,
    db: AsyncSession,
) -> Tuple[bool, str, Optional[dict]]:
    """Validate refresh token and issue new access token."""
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


def user_to_profile(user: User) -> dict:
    """Build UserProfileResponse-compatible dict."""
    return {
        "id": user.id,
        "mobile": user.mobile,
        "name": user.name,
        "date_of_birth": user.date_of_birth,
        "aadhaar_verified": user.aadhaar_verified,
        "profile_complete": user.profile_complete,
        "is_admin": user.is_admin,
        "is_staff": user.is_staff,
        "age": user.age,
        "is_senior_citizen": user.is_senior_citizen,
        "is_child": user.is_child,
    }
