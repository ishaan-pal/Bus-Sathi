import uuid
import secrets
from datetime import datetime, timezone, timedelta, date
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.pass_ import BusPass, PassType, PassStatus, PassCategory
from app.models.user import User


# ── Pass Number Generator ─────────────────────────────────────────────────────
def generate_pass_number(pass_type: PassType) -> str:
    """
    Format: HR-[TYPE_CODE]-YYYYMM-XXXXX
    e.g. HR-STU-202406-A3F9K
    """
    type_codes = {
        PassType.STUDENT: "STU",
        PassType.SENIOR_CITIZEN: "SEN",
        PassType.MONTHLY: "MON",
        PassType.DIFFERENTLY_ABLED: "DIF",
        PassType.FREEDOM_FIGHTER: "FRE",
        PassType.PRESS: "PRS",
    }
    code = type_codes.get(pass_type, "GEN")
    date_part = datetime.now(timezone.utc).strftime("%Y%m")
    random_part = secrets.token_hex(3).upper()[:5]
    return f"HR-{code}-{date_part}-{random_part}"


# ── Validity Period ───────────────────────────────────────────────────────────
def get_validity_dates(pass_type: PassType) -> Tuple[str, str]:
    """
    Return (valid_from, valid_until) as YYYY-MM-DD strings.
    - Student pass: 1 year from today
    - Monthly pass: 1 month from today
    - Senior / others: 1 year from today
    """
    today = date.today()
    valid_from = today.isoformat()

    if pass_type == PassType.MONTHLY:
        # Next month same date
        if today.month == 12:
            valid_until = today.replace(year=today.year + 1, month=1)
        else:
            try:
                valid_until = today.replace(month=today.month + 1)
            except ValueError:
                # Handle month-end edge cases
                import calendar
                last_day = calendar.monthrange(today.year, today.month + 1)[1]
                valid_until = today.replace(month=today.month + 1, day=last_day)
    else:
        # 1 year
        try:
            valid_until = today.replace(year=today.year + 1)
        except ValueError:
            valid_until = today.replace(year=today.year + 1, day=28)

    return valid_from, valid_until.isoformat()


# ── Apply for New Pass ────────────────────────────────────────────────────────
async def apply_for_pass(
    user: User,
    pass_type: PassType,
    pass_category: PassCategory,
    applicant_name: str,
    applicant_dob: str,
    route_id: Optional[str],
    from_stop: Optional[str],
    to_stop: Optional[str],
    institution_name: Optional[str],
    institution_address: Optional[str],
    student_id_number: Optional[str],
    db: AsyncSession,
) -> Tuple[bool, str, Optional[BusPass]]:
    """
    Create a new bus pass application in SUBMITTED state.
    Documents are uploaded separately via upload_pass_document().
    """
    # Check for existing active pass of same type
    result = await db.execute(
        select(BusPass).where(
            and_(
                BusPass.user_id == user.id,
                BusPass.pass_type == pass_type,
                BusPass.status.in_([
                    PassStatus.APPROVED,
                    PassStatus.SUBMITTED,
                    PassStatus.VERIFICATION_PENDING,
                ]),
            )
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        if existing.status == PassStatus.APPROVED and existing.is_valid:
            return False, "You already have an active pass of this type", None
        if existing.status in [PassStatus.SUBMITTED, PassStatus.VERIFICATION_PENDING]:
            return False, "You already have a pending application of this type", None

    bus_pass = BusPass(
        id=str(uuid.uuid4()),
        user_id=user.id,
        pass_type=pass_type,
        pass_category=pass_category,
        applicant_name=applicant_name.strip(),
        applicant_mobile=user.mobile,
        applicant_dob=applicant_dob,
        route_id=route_id,
        from_stop=from_stop,
        to_stop=to_stop,
        institution_name=institution_name,
        institution_address=institution_address,
        student_id_number=student_id_number,
        status=PassStatus.SUBMITTED,
    )
    db.add(bus_pass)
    await db.commit()
    await db.refresh(bus_pass)
    return True, "Pass application submitted successfully", bus_pass


# ── Upload Pass Document ──────────────────────────────────────────────────────
async def upload_pass_document(
    pass_id: str,
    user_id: str,
    doc_type: str,           # "photo" | "id_proof" | "address_proof" | "institution_cert"
    file_path: str,          # local path after saving upload
    db: AsyncSession,
) -> Tuple[bool, str]:
    """
    Attach an uploaded document URL to a pass application.
    """
    result = await db.execute(
        select(BusPass).where(
            and_(
                BusPass.id == pass_id,
                BusPass.user_id == user_id,
                BusPass.status.in_([
                    PassStatus.DRAFT,
                    PassStatus.SUBMITTED,
                    PassStatus.VERIFICATION_PENDING,
                ]),
            )
        )
    )
    bus_pass = result.scalar_one_or_none()
    if not bus_pass:
        return False, "Pass application not found or cannot be modified"

    doc_field_map = {
        "photo": "photo_url",
        "id_proof": "id_proof_url",
        "address_proof": "address_proof_url",
        "institution_cert": "institution_cert_url",
    }
    field = doc_field_map.get(doc_type)
    if not field:
        return False, f"Unknown document type: {doc_type}"

    setattr(bus_pass, field, file_path)

    # Move to verification pending if all required docs uploaded
    required_docs = _get_required_docs(bus_pass.pass_type)
    uploaded = all(
        getattr(bus_pass, doc_field_map[d]) is not None
        for d in required_docs
    )
    if uploaded and bus_pass.status == PassStatus.SUBMITTED:
        bus_pass.status = PassStatus.VERIFICATION_PENDING

    await db.commit()
    return True, "Document uploaded successfully"


def _get_required_docs(pass_type: PassType) -> list[str]:
    """Return list of required document types for each pass type."""
    base = ["photo", "id_proof"]
    if pass_type == PassType.STUDENT:
        return base + ["institution_cert"]
    if pass_type == PassType.SENIOR_CITIZEN:
        return base + ["address_proof"]
    if pass_type == PassType.DIFFERENTLY_ABLED:
        return base + ["id_proof"]
    return base


# ── Admin: Approve Pass ───────────────────────────────────────────────────────
async def approve_pass(
    pass_id: str,
    admin_name: str,
    db: AsyncSession,
) -> Tuple[bool, str, Optional[BusPass]]:
    """
    Admin approves a pass application.
    Generates pass number and sets validity period.
    """
    result = await db.execute(
        select(BusPass).where(BusPass.id == pass_id)
    )
    bus_pass = result.scalar_one_or_none()
    if not bus_pass:
        return False, "Pass not found", None

    if bus_pass.status not in [
        PassStatus.SUBMITTED,
        PassStatus.VERIFICATION_PENDING,
    ]:
        return False, f"Cannot approve pass in {bus_pass.status} state", None

    valid_from, valid_until = get_validity_dates(bus_pass.pass_type)
    token, token_expires = _generate_pass_token()

    bus_pass.status = PassStatus.APPROVED
    bus_pass.pass_number = generate_pass_number(bus_pass.pass_type)
    bus_pass.valid_from = valid_from
    bus_pass.valid_until = valid_until
    bus_pass.reviewed_by = admin_name
    bus_pass.reviewed_at = datetime.now(timezone.utc)
    bus_pass.verification_token = token
    bus_pass.verification_token_expires = token_expires

    await db.commit()
    await db.refresh(bus_pass)
    return True, "Pass approved successfully", bus_pass


# ── Admin: Reject Pass ────────────────────────────────────────────────────────
async def reject_pass(
    pass_id: str,
    admin_name: str,
    rejection_reason: str,
    db: AsyncSession,
) -> Tuple[bool, str]:
    """Admin rejects a pass application with a reason."""
    result = await db.execute(
        select(BusPass).where(BusPass.id == pass_id)
    )
    bus_pass = result.scalar_one_or_none()
    if not bus_pass:
        return False, "Pass not found"

    bus_pass.status = PassStatus.REJECTED
    bus_pass.reviewed_by = admin_name
    bus_pass.reviewed_at = datetime.now(timezone.utc)
    bus_pass.rejection_reason = rejection_reason.strip()

    await db.commit()
    return True, "Pass rejected"


# ── Renew Pass ────────────────────────────────────────────────────────────────
async def renew_pass(
    pass_id: str,
    user_id: str,
    db: AsyncSession,
) -> Tuple[bool, str, Optional[BusPass]]:
    """
    Create a renewal application for an existing pass.
    Copies details from original pass into new SUBMITTED application.
    """
    result = await db.execute(
        select(BusPass).where(
            and_(BusPass.id == pass_id, BusPass.user_id == user_id)
        )
    )
    original = result.scalar_one_or_none()
    if not original:
        return False, "Pass not found", None

    if original.status not in [PassStatus.APPROVED, PassStatus.EXPIRED]:
        return False, "Only approved or expired passes can be renewed", None

    renewal = BusPass(
        id=str(uuid.uuid4()),
        user_id=user_id,
        pass_type=original.pass_type,
        pass_category=original.pass_category,
        applicant_name=original.applicant_name,
        applicant_mobile=original.applicant_mobile,
        applicant_dob=original.applicant_dob,
        route_id=original.route_id,
        from_stop=original.from_stop,
        to_stop=original.to_stop,
        institution_name=original.institution_name,
        institution_address=original.institution_address,
        student_id_number=original.student_id_number,
        # Copy existing document URLs
        photo_url=original.photo_url,
        id_proof_url=original.id_proof_url,
        address_proof_url=original.address_proof_url,
        institution_cert_url=original.institution_cert_url,
        status=PassStatus.SUBMITTED,
    )
    db.add(renewal)
    await db.commit()
    await db.refresh(renewal)
    return True, "Renewal application submitted", renewal


# ── Refresh Pass Token ────────────────────────────────────────────────────────
async def refresh_pass_token(
    pass_id: str,
    user_id: str,
    db: AsyncSession,
) -> Tuple[bool, str, Optional[str]]:
    """Rotate verification token on active pass screen."""
    result = await db.execute(
        select(BusPass).where(
            and_(
                BusPass.id == pass_id,
                BusPass.user_id == user_id,
                BusPass.status == PassStatus.APPROVED,
            )
        )
    )
    bus_pass = result.scalar_one_or_none()
    if not bus_pass:
        return False, "Active pass not found", None

    token, expires = _generate_pass_token()
    bus_pass.verification_token = token
    bus_pass.verification_token_expires = expires
    await db.commit()
    return True, "Token refreshed", token


# ── Get Active Pass ───────────────────────────────────────────────────────────
async def get_active_pass(
    user_id: str,
    db: AsyncSession,
) -> Optional[BusPass]:
    """Get the most recent approved and valid pass for a user."""
    result = await db.execute(
        select(BusPass).where(
            and_(
                BusPass.user_id == user_id,
                BusPass.status == PassStatus.APPROVED,
            )
        ).order_by(BusPass.created_at.desc())
    )
    passes = result.scalars().all()
    # Return first valid one
    for p in passes:
        if p.is_valid:
            return p
    return None


# ── Internal Helpers ──────────────────────────────────────────────────────────
def _generate_pass_token() -> Tuple[str, datetime]:
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(seconds=60)
    return token, expires