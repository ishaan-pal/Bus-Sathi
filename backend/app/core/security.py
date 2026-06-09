from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import random
import string

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ── Password Hashing ─────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── OTP ──────────────────────────────────────────────────────────────────────
def generate_otp() -> str:
    """Generate a secure numeric OTP."""
    if settings.OTP_DEV_MODE:
        return settings.OTP_DEV_FIXED
    return "".join(random.choices(string.digits, k=settings.OTP_LENGTH))


def get_otp_redis_key(mobile: str) -> str:
    return f"otp:{mobile}"


def get_otp_attempts_key(mobile: str) -> str:
    return f"otp_attempts:{mobile}"


# ── JWT ──────────────────────────────────────────────────────────────────────
def create_access_token(subject: str, extra: dict = {}) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
        **extra,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT. Returns payload or None."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def decode_access_token(token: str) -> Optional[str]:
    """Returns user_id (sub) from a valid access token, else None."""
    payload = decode_token(token)
    if payload is None:
        return None
    if payload.get("type") != "access":
        return None
    return payload.get("sub")


def decode_refresh_token(token: str) -> Optional[str]:
    """Returns user_id (sub) from a valid refresh token, else None."""
    payload = decode_token(token)
    if payload is None:
        return None
    if payload.get("type") != "refresh":
        return None
    return payload.get("sub")


# ── Aadhaar Stub ─────────────────────────────────────────────────────────────
def mock_aadhaar_verify(aadhaar_number: str) -> Tuple[bool, dict]:
    """
    Stub for Aadhaar KYC verification.
    Replace with actual UIDAI / DigiLocker API call when government
    credentials are obtained.
    Returns (success, user_data)
    """
    # Simulate Aadhaar data for demo purposes
    mock_data = {
        "name": "Demo User",
        "dob": "1990-01-01",
        "gender": "M",
        "verified": True,
    }
    # Basic format check: 12 digits
    if len(aadhaar_number) == 12 and aadhaar_number.isdigit():
        return True, mock_data
    return False, {}