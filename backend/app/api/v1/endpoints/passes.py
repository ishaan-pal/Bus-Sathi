import os
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import redis.asyncio as aioredis

from app.core.config import settings
from app.core.dependencies import (
    get_db,
    get_redis,
    get_current_user,
    get_current_admin,
)
from app.models.user import User
from app.models.pass_ import BusPass, PassType, PassStatus, PassCategory
from app.models.route import Route
from app.services.pass_ import (
    apply_for_pass,
    upload_pass_document,
    approve_pass,
    reject_pass,
    renew_pass,
    get_active_pass,
    refresh_pass_token,
    _get_required_docs,
)
from app.schemas.pass_ import (
    ApplyPassRequest,
    RejectPassRequest,
    PassApplicationResponse,
    PassDocumentUploadResponse,
    ActivePassResponse,
    PassListItem,
    PassHistoryResponse,
    PassStatusResponse,
    PassTokenRefreshResponse,
    AdminPassListItem,
    AdminPassDetailResponse,
    AdminUpdatePassNotesRequest,
)

router = APIRouter(prefix="/passes", tags=["Bus Passes"])


# ── Apply for Pass ────────────────────────────────────────────────────────────
@router.post(
    "/apply",
    response_model=PassApplicationResponse,
    summary="Apply for a new bus pass",
)
async def apply_pass_endpoint(
    body: ApplyPassRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a new bus pass application.
    After submission, upload required documents via /passes/{pass_id}/upload.
    Pass types: student, senior_citizen, monthly, differently_abled,
                freedom_fighter, press
    """
    success, message, bus_pass = await apply_for_pass(
        user=current_user,
        pass_type=body.pass_type,
        pass_category=body.pass_category,
        applicant_name=body.applicant_name,
        applicant_dob=body.applicant_dob,
        route_id=body.route_id,
        from_stop=body.from_stop,
        to_stop=body.to_stop,
        institution_name=body.institution_name,
        institution_address=body.institution_address,
        student_id_number=body.student_id_number,
        db=db,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    required_docs = _get_required_docs(body.pass_type)
    return PassApplicationResponse(
        success=True,
        message=message,
        pass_id=bus_pass.id,
        pass_type=bus_pass.pass_type.value,
        status=bus_pass.status.value,
        required_documents=required_docs,
    )


# ── Upload Document ───────────────────────────────────────────────────────────
@router.post(
    "/{pass_id}/upload",
    response_model=PassDocumentUploadResponse,
    summary="Upload document for pass application",
)
async def upload_document_endpoint(
    pass_id: str,
    doc_type: str = Form(..., description="photo | id_proof | address_proof | institution_cert"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a required document for a pass application.
    Accepted formats: JPEG, PNG, WebP. Max size: 5MB.
    """
    # Validate file type
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: JPEG, PNG, WebP",
        )

    # Validate file size
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    # Save file locally (replace with S3 in production)
    upload_dir = os.path.join(settings.UPLOAD_DIR, "passes", pass_id)
    os.makedirs(upload_dir, exist_ok=True)

    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    filename = f"{doc_type}_{uuid.uuid4().hex[:8]}.{ext}"
    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # Update pass record
    success, message = await upload_pass_document(
        pass_id=pass_id,
        user_id=current_user.id,
        doc_type=doc_type,
        file_path=file_path,
        db=db,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    # Check overall status after upload
    result = await db.execute(
        select(BusPass).where(BusPass.id == pass_id)
    )
    bus_pass = result.scalar_one_or_none()
    required_docs = _get_required_docs(bus_pass.pass_type)
    uploaded = all(
        getattr(bus_pass, f"{d}_url") is not None
        for d in required_docs
        if hasattr(bus_pass, f"{d}_url")
    )

    return PassDocumentUploadResponse(
        success=True,
        message=message,
        doc_type=doc_type,
        status=bus_pass.status.value,
        all_docs_uploaded=uploaded,
    )


# ── Active Pass ───────────────────────────────────────────────────────────────
@router.get(
    "/active",
    response_model=ActivePassResponse,
    summary="Get active bus pass with verification token",
)
async def get_active_pass_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the user's currently valid bus pass.
    Includes rotating verification token for conductor visual check.
    No QR code, no PDF — app-only display.
    """
    bus_pass = await get_active_pass(current_user.id, db)
    if not bus_pass:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active pass found",
        )

    # Auto-refresh token if expired
    now = datetime.now(timezone.utc)
    if (
        bus_pass.verification_token is None
        or bus_pass.verification_token_expires is None
        or bus_pass.verification_token_expires <= now
    ):
        await refresh_pass_token(bus_pass.id, current_user.id, db)
        result = await db.execute(
            select(BusPass).where(BusPass.id == bus_pass.id)
        )
        bus_pass = result.scalar_one_or_none()

    # Fetch route info
    route_number = None
    route_name = None
    if bus_pass.route_id:
        route_result = await db.execute(
            select(Route).where(Route.id == bus_pass.route_id)
        )
        route = route_result.scalar_one_or_none()
        if route:
            route_number = route.route_number
            route_name = route.name

    # IST timestamp
    ist_offset = timedelta(hours=5, minutes=30)
    ist_now = now + ist_offset

    return ActivePassResponse(
        pass_id=bus_pass.id,
        pass_number=bus_pass.pass_number,
        pass_type=bus_pass.pass_type.value,
        pass_category=bus_pass.pass_category.value,
        applicant_name=bus_pass.applicant_name,
        applicant_mobile=bus_pass.applicant_mobile,
        applicant_dob=bus_pass.applicant_dob,
        route_number=route_number,
        route_name=route_name,
        from_stop=bus_pass.from_stop,
        to_stop=bus_pass.to_stop,
        valid_from=bus_pass.valid_from,
        valid_until=bus_pass.valid_until,
        days_remaining=bus_pass.days_remaining,
        is_valid=bus_pass.is_valid,
        status=bus_pass.status.value,
        verification_token=bus_pass.verification_token,
        verification_token_expires=(
            bus_pass.verification_token_expires.isoformat()
            if bus_pass.verification_token_expires else None
        ),
        current_timestamp=ist_now.strftime("%d %b %Y  %I:%M:%S %p IST"),
        verification_banner="LIVE VERIFIED • HARYANA ROADWAYS",
    )


# ── Refresh Pass Token ────────────────────────────────────────────────────────
@router.post(
    "/{pass_id}/refresh-token",
    response_model=PassTokenRefreshResponse,
    summary="Rotate pass verification token",
)
async def refresh_pass_token_endpoint(
    pass_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Rotate the verification token on the active pass screen.
    Called every 60 seconds to prevent screenshot reuse.
    """
    success, message, token = await refresh_pass_token(
        pass_id=pass_id,
        user_id=current_user.id,
        db=db,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message,
        )

    expires = datetime.now(timezone.utc) + timedelta(seconds=60)
    return PassTokenRefreshResponse(
        success=True,
        verification_token=token,
        expires_at=expires.isoformat(),
    )


# ── Pass History ──────────────────────────────────────────────────────────────
@router.get(
    "/history",
    response_model=PassHistoryResponse,
    summary="Get all pass applications and history",
)
async def get_pass_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns all pass applications for the current user."""
    result = await db.execute(
        select(BusPass)
        .where(BusPass.user_id == current_user.id)
        .order_by(BusPass.created_at.desc())
    )
    passes = result.scalars().all()

    items = [
        PassListItem(
            pass_id=p.id,
            pass_number=p.pass_number,
            pass_type=p.pass_type.value,
            pass_category=p.pass_category.value,
            status=p.status.value,
            valid_from=p.valid_from,
            valid_until=p.valid_until,
            is_valid=p.is_valid,
            days_remaining=p.days_remaining,
            created_at=p.created_at.isoformat(),
        )
        for p in passes
    ]
    return PassHistoryResponse(
        success=True,
        total=len(items),
        passes=items,
    )


# ── Pass Status ───────────────────────────────────────────────────────────────
@router.get(
    "/{pass_id}/status",
    response_model=PassStatusResponse,
    summary="Check status of a pass application",
)
async def get_pass_status(
    pass_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check the current status of a pass application including uploaded docs."""
    result = await db.execute(
        select(BusPass).where(
            and_(
                BusPass.id == pass_id,
                BusPass.user_id == current_user.id,
            )
        )
    )
    bus_pass = result.scalar_one_or_none()
    if not bus_pass:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pass not found",
        )

    required_docs = _get_required_docs(bus_pass.pass_type)
    uploaded_documents = {
        "photo": bus_pass.photo_url is not None,
        "id_proof": bus_pass.id_proof_url is not None,
        "address_proof": bus_pass.address_proof_url is not None,
        "institution_cert": bus_pass.institution_cert_url is not None,
    }

    return PassStatusResponse(
        pass_id=bus_pass.id,
        pass_number=bus_pass.pass_number,
        pass_type=bus_pass.pass_type.value,
        status=bus_pass.status.value,
        rejection_reason=bus_pass.rejection_reason,
        reviewed_at=(
            bus_pass.reviewed_at.isoformat()
            if bus_pass.reviewed_at else None
        ),
        valid_from=bus_pass.valid_from,
        valid_until=bus_pass.valid_until,
        required_documents=required_docs,
        uploaded_documents=uploaded_documents,
    )


# ── Renew Pass ────────────────────────────────────────────────────────────────
@router.post(
    "/{pass_id}/renew",
    summary="Submit renewal application for an existing pass",
)
async def renew_pass_endpoint(
    pass_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a renewal for an existing approved or expired pass.
    Copies document URLs from original — re-upload only if needed.
    """
    success, message, renewal = await renew_pass(
        pass_id=pass_id,
        user_id=current_user.id,
        db=db,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )
    return {
        "success": True,
        "message": message,
        "new_pass_id": renewal.id,
        "status": renewal.status.value,
    }


# ── Admin: List All Passes ────────────────────────────────────────────────────
@router.get(
    "/admin/all",
    response_model=list[AdminPassListItem],
    summary="[Admin] List all pass applications",
)
async def admin_list_passes(
    pass_status: str = Query(None),
    pass_type: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Admin endpoint to list and filter all pass applications."""
    query = select(BusPass).order_by(BusPass.created_at.desc())

    if pass_status:
        try:
            ps = PassStatus(pass_status)
            query = query.where(BusPass.status == ps)
        except ValueError:
            pass

    if pass_type:
        try:
            pt = PassType(pass_type)
            query = query.where(BusPass.pass_type == pt)
        except ValueError:
            pass

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    passes = result.scalars().all()

    items = []
    for p in passes:
        route_number = None
        if p.route_id:
            r = await db.execute(
                select(Route.route_number).where(Route.id == p.route_id)
            )
            route_number = r.scalar_one_or_none()

        items.append(
            AdminPassListItem(
                pass_id=p.id,
                pass_number=p.pass_number,
                pass_type=p.pass_type.value,
                status=p.status.value,
                applicant_name=p.applicant_name,
                applicant_mobile=p.applicant_mobile,
                route_number=route_number,
                valid_until=p.valid_until,
                created_at=p.created_at.isoformat(),
                reviewed_by=p.reviewed_by,
                reviewed_at=(
                    p.reviewed_at.isoformat() if p.reviewed_at else None
                ),
            )
        )
    return items


# ── Admin: Pass Detail ────────────────────────────────────────────────────────
@router.get(
    "/admin/{pass_id}",
    response_model=AdminPassDetailResponse,
    summary="[Admin] Get full pass application detail",
)
async def admin_get_pass_detail(
    pass_id: str,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Admin endpoint to view full pass application with documents."""
    result = await db.execute(
        select(BusPass).where(BusPass.id == pass_id)
    )
    bus_pass = result.scalar_one_or_none()
    if not bus_pass:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pass not found",
        )

    route_number = None
    if bus_pass.route_id:
        r = await db.execute(
            select(Route.route_number).where(Route.id == bus_pass.route_id)
        )
        route_number = r.scalar_one_or_none()

    return AdminPassDetailResponse(
        pass_id=bus_pass.id,
        pass_number=bus_pass.pass_number,
        pass_type=bus_pass.pass_type.value,
        pass_category=bus_pass.pass_category.value,
        status=bus_pass.status.value,
        applicant_name=bus_pass.applicant_name,
        applicant_mobile=bus_pass.applicant_mobile,
        applicant_dob=bus_pass.applicant_dob,
        route_number=route_number,
        from_stop=bus_pass.from_stop,
        to_stop=bus_pass.to_stop,
        institution_name=bus_pass.institution_name,
        institution_address=bus_pass.institution_address,
        student_id_number=bus_pass.student_id_number,
        photo_url=bus_pass.photo_url,
        id_proof_url=bus_pass.id_proof_url,
        address_proof_url=bus_pass.address_proof_url,
        institution_cert_url=bus_pass.institution_cert_url,
        valid_from=bus_pass.valid_from,
        valid_until=bus_pass.valid_until,
        rejection_reason=bus_pass.rejection_reason,
        admin_notes=bus_pass.admin_notes,
        reviewed_by=bus_pass.reviewed_by,
        reviewed_at=(
            bus_pass.reviewed_at.isoformat()
            if bus_pass.reviewed_at else None
        ),
        created_at=bus_pass.created_at.isoformat(),
    )


# ── Admin: Approve Pass ───────────────────────────────────────────────────────
@router.post(
    "/admin/{pass_id}/approve",
    summary="[Admin] Approve a pass application",
)
async def admin_approve_pass(
    pass_id: str,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Approve a pending pass application and generate pass number."""
    success, message, bus_pass = await approve_pass(
        pass_id=pass_id,
        admin_name=admin.name or "Admin",
        db=db,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )
    return {
        "success": True,
        "message": message,
        "pass_number": bus_pass.pass_number,
        "valid_from": bus_pass.valid_from,
        "valid_until": bus_pass.valid_until,
    }


# ── Admin: Reject Pass ────────────────────────────────────────────────────────
@router.post(
    "/admin/{pass_id}/reject",
    summary="[Admin] Reject a pass application",
)
async def admin_reject_pass(
    pass_id: str,
    body: RejectPassRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Reject a pass application with a reason."""
    success, message = await reject_pass(
        pass_id=pass_id,
        admin_name=admin.name or "Admin",
        rejection_reason=body.rejection_reason,
        db=db,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )
    return {"success": True, "message": message}


# ── Admin: Update Notes ───────────────────────────────────────────────────────
@router.patch(
    "/admin/{pass_id}/notes",
    summary="[Admin] Add notes to a pass application",
)
async def admin_update_notes(
    pass_id: str,
    body: AdminUpdatePassNotesRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Admin endpoint to add internal notes to a pass application."""
    result = await db.execute(
        select(BusPass).where(BusPass.id == pass_id)
    )
    bus_pass = result.scalar_one_or_none()
    if not bus_pass:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pass not found",
        )
    bus_pass.admin_notes = body.admin_notes
    await db.commit()
    return {"success": True, "message": "Notes updated"}