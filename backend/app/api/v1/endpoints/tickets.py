from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import redis.asyncio as aioredis

from app.core.dependencies import (
    get_db,
    get_redis,
    get_current_user,
    require_aadhaar_verified,
    get_current_admin,
)
from app.models.user import User
from app.models.ticket import Ticket, TicketStatus
from app.models.bus import Bus
from app.models.route import Route, RouteStop
from app.services.ticket import (
    initiate_booking,
    confirm_payment,
    get_active_tickets,
    refresh_verification_token,
    expire_stale_tickets,
)
from app.services.fare_engine import fare_engine
from app.schemas.ticket import (
    InitiateBookingRequest,
    ConfirmPaymentRequest,
    BookingInitiatedResponse,
    ActiveTicketsResponse,
    ActiveTicketItem,
    TicketDetailResponse,
    TokenRefreshResponse,
    FareCalculateRequest,
    FareCalculateResponse,
    FareBreakdownResponse,
    AdminTicketListItem,
    ConductorVerifyRequest,
    ConductorVerifyResponse,
)

router = APIRouter(prefix="/tickets", tags=["Tickets"])


# ── Initiate Booking ──────────────────────────────────────────────────────────
@router.post(
    "/book",
    response_model=BookingInitiatedResponse,
    summary="Initiate ticket booking and create payment order",
)
async def initiate_booking_endpoint(
    body: InitiateBookingRequest,
    current_user: User = Depends(require_aadhaar_verified),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """
    Step 1 of ticket booking:
    - Validates bus and route
    - Calculates fare with concessions
    - Creates a PAYMENT_PENDING ticket
    - Returns Razorpay payment order for client to process

    Requires authentication.
    """
    if body.total_passengers() == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one passenger is required",
        )

    success, message, data = await initiate_booking(
        user=current_user,
        bus_id=body.bus_id,
        boarding_stop=body.boarding_stop,
        destination_stop=body.destination_stop,
        adult_count=body.adult_count,
        child_count=body.child_count,
        senior_count=body.senior_count,
        db=db,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    return BookingInitiatedResponse(
        success=True,
        message=message,
        ticket_id=data["ticket_id"],
        ticket_number=data["ticket_number"],
        fare=FareBreakdownResponse(**data["fare"]),
        payment_order=data["payment_order"],
        razorpay_key_id=data["razorpay_key_id"],
    )


# ── Confirm Payment ───────────────────────────────────────────────────────────
@router.post(
    "/confirm-payment",
    summary="Confirm Razorpay payment and activate ticket",
)
async def confirm_payment_endpoint(
    body: ConfirmPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """
    Step 2 of ticket booking:
    - Verifies Razorpay payment signature
    - Activates the ticket
    - Generates rotating verification token
    - Caches ticket for offline access

    In demo mode, any payment_id and signature are accepted.
    """
    success, message, ticket = await confirm_payment(
        ticket_id=body.ticket_id,
        user_id=current_user.id,
        payment_id=body.payment_id,
        razorpay_signature=body.razorpay_signature,
        db=db,
        redis=redis,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    return {
        "success": True,
        "message": message,
        "ticket_id": ticket.id,
        "ticket_number": ticket.ticket_number,
        "status": ticket.status.value,
    }


# ── Active Tickets ────────────────────────────────────────────────────────────
@router.get(
    "/active",
    response_model=ActiveTicketsResponse,
    summary="Get all active tickets for current user",
)
async def get_active_tickets_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """
    Returns all currently active (paid and valid) tickets for the user.
    Auto-expires any tickets past their journey date.
    Tickets are cached for offline access.
    """
    tickets = await get_active_tickets(current_user.id, db, redis)

    items = []
    for t in tickets:
        # Get bus number
        bus_result = await db.execute(
            select(Bus.bus_number).where(Bus.id == t.bus_id)
        )
        bus_number = bus_result.scalar_one_or_none() or "Unknown"

        items.append(
            ActiveTicketItem(
                ticket_id=t.id,
                ticket_number=t.ticket_number,
                bus_number=bus_number,
                boarding_stop=t.boarding_stop,
                destination_stop=t.destination_stop,
                journey_date=t.journey_date,
                journey_time=t.journey_time,
                adult_count=t.adult_count,
                child_count=t.child_count,
                senior_count=t.senior_count,
                total_passengers=t.total_passengers,
                total_fare_rupees=t.total_fare_rupees,
                status=t.status.value,
                paid_at=(
                    t.paid_at.isoformat() if t.paid_at else None
                ),
            )
        )

    return ActiveTicketsResponse(
        success=True,
        total=len(items),
        tickets=items,
    )


# ── Ticket Detail ─────────────────────────────────────────────────────────────
@router.get(
    "/{ticket_id}",
    response_model=TicketDetailResponse,
    summary="Get full ticket detail with verification token",
)
async def get_ticket_detail(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """
    Returns full ticket detail screen data including:
    - Passenger info
    - Journey details
    - Fare breakdown
    - Rotating verification token (for conductor visual check)
    - Current timestamp

    Token auto-refreshes if expired.
    No QR code, no PDF, no download — app-only display.
    """
    result = await db.execute(
        select(Ticket).where(
            and_(
                Ticket.id == ticket_id,
                Ticket.user_id == current_user.id,
            )
        )
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    # Auto-refresh token if expired
    now = datetime.now(timezone.utc)
    if (
        ticket.status == TicketStatus.ACTIVE
        and (
            ticket.verification_token is None
            or ticket.verification_token_expires is None
            or ticket.verification_token_expires <= now
        )
    ):
        _, _, new_token = await refresh_verification_token(
            ticket_id=ticket_id,
            user_id=current_user.id,
            db=db,
            redis=redis,
        )

    # Fetch bus and route info
    bus_result = await db.execute(
        select(Bus).where(Bus.id == ticket.bus_id)
    )
    bus = bus_result.scalar_one_or_none()
    bus_number = bus.bus_number if bus else "Unknown"

    route_number = None
    if ticket.route_id:
        route_result = await db.execute(
            select(Route.route_number).where(Route.id == ticket.route_id)
        )
        route_number = route_result.scalar_one_or_none()

    # IST timestamp
    ist_offset = timedelta(hours=5, minutes=30)
    ist_now = now + ist_offset

    return TicketDetailResponse(
        ticket_id=ticket.id,
        ticket_number=ticket.ticket_number,
        passenger_name=current_user.name or "Passenger",
        passenger_mobile=current_user.mobile,
        bus_number=bus_number,
        route_number=route_number,
        boarding_stop=ticket.boarding_stop,
        destination_stop=ticket.destination_stop,
        journey_date=ticket.journey_date,
        journey_time=ticket.journey_time,
        adult_count=ticket.adult_count,
        child_count=ticket.child_count,
        senior_count=ticket.senior_count,
        total_passengers=ticket.total_passengers,
        adult_fare_rupees=ticket.adult_fare_rupees,
        child_fare_rupees=round(ticket.child_fare_paise / 100, 2),
        senior_fare_rupees=round(ticket.senior_fare_paise / 100, 2),
        total_fare_rupees=ticket.total_fare_rupees,
        payment_method=(
            ticket.payment_method.value if ticket.payment_method else None
        ),
        paid_at=(ticket.paid_at.isoformat() if ticket.paid_at else None),
        status=ticket.status.value,
        is_valid_for_travel=ticket.is_valid_for_travel,
        expires_at=(
            ticket.expires_at.isoformat() if ticket.expires_at else None
        ),
        verification_token=ticket.verification_token,
        verification_token_expires=(
            ticket.verification_token_expires.isoformat()
            if ticket.verification_token_expires else None
        ),
        current_timestamp=ist_now.strftime("%d %b %Y  %I:%M:%S %p IST"),
        verification_banner="LIVE VERIFIED • HARYANA ROADWAYS",
    )


# ── Refresh Verification Token ────────────────────────────────────────────────
@router.post(
    "/{ticket_id}/refresh-token",
    response_model=TokenRefreshResponse,
    summary="Rotate ticket verification token",
)
async def refresh_token_endpoint(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """
    Rotate the verification token displayed on the ticket screen.
    Called every 60 seconds by the Flutter app to prevent
    screenshot reuse. Conductor sees a live, changing token.
    """
    success, message, token = await refresh_verification_token(
        ticket_id=ticket_id,
        user_id=current_user.id,
        db=db,
        redis=redis,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message,
        )

    from datetime import timedelta
    expires = datetime.now(timezone.utc) + timedelta(seconds=60)
    return TokenRefreshResponse(
        success=True,
        verification_token=token,
        expires_at=expires.isoformat(),
    )


# ── Fare Calculator ───────────────────────────────────────────────────────────
@router.post(
    "/fare/calculate",
    response_model=FareCalculateResponse,
    summary="Calculate fare for a journey",
)
async def calculate_fare_endpoint(
    body: FareCalculateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate fare for a journey without booking.
    Used on the booking screen to show fare before payment.
    Available to guests and registered users.
    """
    stops_result = await db.execute(
        select(RouteStop)
        .where(RouteStop.route_id == body.route_id)
        .order_by(RouteStop.stop_order)
    )
    route_stops = stops_result.scalars().all()

    if not route_stops:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found",
        )

    try:
        fare = fare_engine.calculate_from_stops(
            route_stops=route_stops,
            boarding_stop_name=body.boarding_stop,
            destination_stop_name=body.destination_stop,
            adult_count=body.adult_count,
            child_count=body.child_count,
            senior_count=body.senior_count,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return FareCalculateResponse(
        success=True,
        fare=FareBreakdownResponse(**fare.to_dict()),
    )


# ── Conductor Verify ──────────────────────────────────────────────────────────
@router.post(
    "/conductor/verify",
    response_model=ConductorVerifyResponse,
    summary="Conductor visual ticket verification",
)
async def conductor_verify(
    body: ConductorVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Used by conductors to verify a ticket number visually.
    No QR scanner needed — conductor enters ticket number
    and bus number to confirm validity.
    """
    result = await db.execute(
        select(Ticket).where(
            Ticket.ticket_number == body.ticket_number
        )
    )
    ticket = result.scalar_one_or_none()

    if not ticket:
        return ConductorVerifyResponse(
            success=False,
            message="Ticket not found",
            is_valid=False,
            ticket_number=None,
            passenger_name=None,
            total_passengers=None,
            boarding_stop=None,
            destination_stop=None,
            fare_paid=None,
        )

    # Verify bus matches
    bus_result = await db.execute(
        select(Bus).where(Bus.id == ticket.bus_id)
    )
    bus = bus_result.scalar_one_or_none()
    if not bus or bus.bus_number != body.bus_number:
        return ConductorVerifyResponse(
            success=False,
            message="Ticket not valid for this bus",
            is_valid=False,
            ticket_number=body.ticket_number,
            passenger_name=None,
            total_passengers=None,
            boarding_stop=None,
            destination_stop=None,
            fare_paid=None,
        )

    # Get passenger name
    user_result = await db.execute(
        select(User).where(User.id == ticket.user_id)
    )
    user = user_result.scalar_one_or_none()

    is_valid = ticket.is_valid_for_travel
    return ConductorVerifyResponse(
        success=True,
        message="Valid ticket" if is_valid else "Ticket is not active",
        is_valid=is_valid,
        ticket_number=ticket.ticket_number,
        passenger_name=user.name if user else "Unknown",
        total_passengers=ticket.total_passengers,
        boarding_stop=ticket.boarding_stop,
        destination_stop=ticket.destination_stop,
        fare_paid=ticket.total_fare_rupees,
    )


# ── Admin: All Tickets ────────────────────────────────────────────────────────
@router.get(
    "/admin/all",
    response_model=list[AdminTicketListItem],
    summary="[Admin] List all tickets",
)
async def admin_list_tickets(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    ticket_status: str = Query(None),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Admin endpoint to list all tickets with filters."""
    query = select(Ticket).order_by(Ticket.created_at.desc())

    if ticket_status:
        try:
            ts = TicketStatus(ticket_status)
            query = query.where(Ticket.status == ts)
        except ValueError:
            pass

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    tickets = result.scalars().all()

    items = []
    for t in tickets:
        bus_result = await db.execute(
            select(Bus.bus_number).where(Bus.id == t.bus_id)
        )
        bus_number = bus_result.scalar_one_or_none() or "Unknown"

        user_result = await db.execute(
            select(User.mobile).where(User.id == t.user_id)
        )
        user_mobile = user_result.scalar_one_or_none() or "Unknown"

        items.append(
            AdminTicketListItem(
                ticket_id=t.id,
                ticket_number=t.ticket_number,
                user_mobile=user_mobile,
                bus_number=bus_number,
                boarding_stop=t.boarding_stop,
                destination_stop=t.destination_stop,
                journey_date=t.journey_date,
                total_passengers=t.total_passengers,
                total_fare_rupees=t.total_fare_rupees,
                status=t.status.value,
                payment_verified=t.payment_verified,
                created_at=t.created_at.isoformat(),
            )
        )
    return items