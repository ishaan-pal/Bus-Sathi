from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
import re


# ── Validators ────────────────────────────────────────────────────────────────
def validate_mobile(v: str) -> str:
    v = v.strip()
    if not re.fullmatch(r"[6-9]\d{9}", v):
        raise ValueError(
            "Enter a valid 10-digit Indian mobile number starting with 6-9"
        )
    return v


def validate_dob(v: str) -> str:
    from datetime import date
    try:
        dob = date.fromisoformat(v)
    except ValueError:
        raise ValueError("Date of birth must be in YYYY-MM-DD format")
    if dob >= date.today():
        raise ValueError("Date of birth must be in the past")
    age = (
        date.today().year - dob.year
        - ((date.today().month, date.today().day) < (dob.month, dob.day))
    )
    if age > 120:
        raise ValueError("Invalid date of birth")
    return v


# ── Request Schemas ───────────────────────────────────────────────────────────
class SendOTPRequest(BaseModel):
    mobile: str

    @field_validator("mobile")
    @classmethod
    def check_mobile(cls, v):
        return validate_mobile(v)


class VerifyOTPRequest(BaseModel):
    mobile: str
    otp: str

    @field_validator("mobile")
    @classmethod
    def check_mobile(cls, v):
        return validate_mobile(v)

    @field_validator("otp")
    @classmethod
    def check_otp(cls, v):
        v = v.strip()
        if not re.fullmatch(r"\d{6}", v):
            raise ValueError("OTP must be exactly 6 digits")
        return v


class AadhaarVerifyRequest(BaseModel):
    aadhaar_number: str

    @field_validator("aadhaar_number")
    @classmethod
    def check_aadhaar(cls, v):
        v = v.strip().replace(" ", "").replace("-", "")
        if not re.fullmatch(r"\d{12}", v):
            raise ValueError("Aadhaar number must be exactly 12 digits")
        return v


class CompleteProfileRequest(BaseModel):
    name: str
    date_of_birth: str

    @field_validator("name")
    @classmethod
    def check_name(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        if len(v) > 100:
            raise ValueError("Name must be under 100 characters")
        if not re.match(r"^[a-zA-Z\s\.]+$", v):
            raise ValueError("Name can only contain letters, spaces, and dots")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def check_dob(cls, v):
        return validate_dob(v)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ── Response Schemas ──────────────────────────────────────────────────────────
class UserProfileResponse(BaseModel):
    id: str
    mobile: str
    name: Optional[str]
    date_of_birth: Optional[str]
    aadhaar_verified: bool
    profile_complete: bool
    is_admin: bool
    is_staff: bool
    age: Optional[int] = None
    is_senior_citizen: bool = False
    is_child: bool = False

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user_id: str
    is_new_user: bool
    profile_complete: bool
    aadhaar_verified: bool


class OTPSentResponse(BaseModel):
    success: bool
    message: str
    mobile: str
    dev_mode: bool = False
    # Only populated in dev mode for testing convenience
    dev_otp: Optional[str] = None


class OTPVerifyResponse(BaseModel):
    success: bool
    message: str
    is_new_user: bool
    tokens: TokenResponse
    user: UserProfileResponse


class AadhaarVerifyResponse(BaseModel):
    success: bool
    message: str
    user: UserProfileResponse


class ProfileCompleteResponse(BaseModel):
    success: bool
    message: str
    user: UserProfileResponse


# ── Admin Schemas ─────────────────────────────────────────────────────────────
class UserListResponse(BaseModel):
    id: str
    mobile: str
    name: Optional[str]
    aadhaar_verified: bool
    profile_complete: bool
    is_active: bool
    is_admin: bool
    created_at: str

    model_config = {"from_attributes": True}


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def check_name(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) < 2:
                raise ValueError("Name must be at least 2 characters")
        return v