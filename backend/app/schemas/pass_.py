from pydantic import BaseModel, field_validator
from typing import Optional
from app.models.pass_ import PassType, PassStatus, PassCategory


# ── Application Request Schemas ───────────────────────────────────────────────
class ApplyPassRequest(BaseModel):
    pass_type: PassType
    pass_category: PassCategory = PassCategory.ORDINARY
    applicant_name: str
    applicant_dob: str
    route_id: Optional[str] = None
    from_stop: Optional[str] = None
    to_stop: Optional[str] = None

    # Student-specific fields
    institution_name: Optional[str] = None
    institution_address: Optional[str] = None
    student_id_number: Optional[str] = None

    @field_validator("applicant_name")
    @classmethod
    def check_name(cls, v):
        import re
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        if len(v) > 100:
            raise ValueError("Name must be under 100 characters")
        if not re.match(r"^[a-zA-Z\s\.]+$", v):
            raise ValueError("Name can only contain letters, spaces, and dots")
        return v

    @field_validator("applicant_dob")
    @classmethod
    def check_dob(cls, v):
        from datetime import date
        try:
            dob = date.fromisoformat(v)
        except ValueError:
            raise ValueError("Date of birth must be in YYYY-MM-DD format")
        if dob >= date.today():
            raise ValueError("Date of birth must be in the past")
        return v

    @field_validator("institution_name")
    @classmethod
    def check_institution(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) < 2:
                raise ValueError("Institution name too short")
            if len(v) > 200:
                raise ValueError("Institution name too long")
        return v


class RenewPassRequest(BaseModel):
    pass_id: str


class RejectPassRequest(BaseModel):
    rejection_reason: str

    @field_validator("rejection_reason")
    @classmethod
    def check_reason(cls, v):
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Rejection reason must be at least 10 characters")
        if len(v) > 500:
            raise ValueError("Rejection reason must be under 500 characters")
        return v


# ── Pass Response Schemas ─────────────────────────────────────────────────────
class PassApplicationResponse(BaseModel):
    success: bool
    message: str
    pass_id: str
    pass_type: str
    status: str
    required_documents: list[str]


class PassDocumentUploadResponse(BaseModel):
    success: bool
    message: str
    doc_type: str
    status: str
    all_docs_uploaded: bool


# ── Active Pass Display ───────────────────────────────────────────────────────
class ActivePassResponse(BaseModel):
    """
    Full pass detail shown on the pass screen.
    Contains all info needed for conductor visual verification.
    """
    pass_id: str
    pass_number: str
    pass_type: str
    pass_category: str

    # Holder
    applicant_name: str
    applicant_mobile: str
    applicant_dob: Optional[str]

    # Route
    route_number: Optional[str]
    route_name: Optional[str]
    from_stop: Optional[str]
    to_stop: Optional[str]

    # Validity
    valid_from: str
    valid_until: str
    days_remaining: Optional[int]
    is_valid: bool

    # Status
    status: str

    # Verification — rotates every 60s
    verification_token: Optional[str]
    verification_token_expires: Optional[str]
    current_timestamp: str

    # Verification banner
    verification_banner: str = "LIVE VERIFIED • HARYANA ROADWAYS"


# ── Pass List Item ────────────────────────────────────────────────────────────
class PassListItem(BaseModel):
    pass_id: str
    pass_number: Optional[str]
    pass_type: str
    pass_category: str
    status: str
    valid_from: Optional[str]
    valid_until: Optional[str]
    is_valid: bool
    days_remaining: Optional[int]
    created_at: str

    model_config = {"from_attributes": True}


class PassHistoryResponse(BaseModel):
    success: bool
    total: int
    passes: list[PassListItem]


# ── Pass Status Response ──────────────────────────────────────────────────────
class PassStatusResponse(BaseModel):
    pass_id: str
    pass_number: Optional[str]
    pass_type: str
    status: str
    rejection_reason: Optional[str]
    reviewed_at: Optional[str]
    valid_from: Optional[str]
    valid_until: Optional[str]
    required_documents: list[str]
    uploaded_documents: dict[str, bool]

    model_config = {"from_attributes": True}


# ── Token Refresh ─────────────────────────────────────────────────────────────
class PassTokenRefreshResponse(BaseModel):
    success: bool
    verification_token: str
    expires_at: str


# ── Admin Pass Schemas ────────────────────────────────────────────────────────
class AdminPassListItem(BaseModel):
    pass_id: str
    pass_number: Optional[str]
    pass_type: str
    status: str
    applicant_name: str
    applicant_mobile: str
    route_number: Optional[str]
    valid_until: Optional[str]
    created_at: str
    reviewed_by: Optional[str]
    reviewed_at: Optional[str]

    model_config = {"from_attributes": True}


class AdminPassDetailResponse(BaseModel):
    pass_id: str
    pass_number: Optional[str]
    pass_type: str
    pass_category: str
    status: str
    applicant_name: str
    applicant_mobile: str
    applicant_dob: Optional[str]
    route_number: Optional[str]
    from_stop: Optional[str]
    to_stop: Optional[str]
    institution_name: Optional[str]
    institution_address: Optional[str]
    student_id_number: Optional[str]
    photo_url: Optional[str]
    id_proof_url: Optional[str]
    address_proof_url: Optional[str]
    institution_cert_url: Optional[str]
    valid_from: Optional[str]
    valid_until: Optional[str]
    rejection_reason: Optional[str]
    admin_notes: Optional[str]
    reviewed_by: Optional[str]
    reviewed_at: Optional[str]
    created_at: str

    model_config = {"from_attributes": True}


class AdminUpdatePassNotesRequest(BaseModel):
    admin_notes: str

    @field_validator("admin_notes")
    @classmethod
    def check_notes(cls, v):
        v = v.strip()
        if len(v) > 1000:
            raise ValueError("Notes must be under 1000 characters")
        return v