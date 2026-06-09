import uuid
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.config import settings
from app.models.ticket import Ticket, TicketStatus, PaymentMethod
from app.models.bus import Bus
from app.models.route import Route, RouteStop
from app.models.user import User
from app.services.fare_engine import fare_engine


# ── Ticket Number Generator ───────────────────────────────────────────────────
def generate_ticket_number() -> str:
    """
    Generate a human-readable ticket number.
    Format: HR-YYYYMMDD-XXXXX (e.g. HR-20240615-A3F9K)
    """
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_part = secrets.token_hex(3).upper()[:5]
    return f"HR-{date_part}-{random_part}"


# ── Verification Token ────────────────────────────────────────────────────────
def generate_verification_token() -> Tuple[str, datetime]:
    """
    Generate a rotating verification token for conductor visual check.
    Token rotates every 60 seconds — makes screenshots invalid.
    """
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(seconds=60)
    return token, expires


# ── Create Razorpay Order ─────────────────────────────────────────────────────
async def create_payment_order(
    amount_paise: int,
    ticket_number: str,
) -> Tuple[bool, str, Optional[dict]]:
    """
    Create a Razorpay order for payment.
    Uses sandbox credentials for demo.
    Returns (success, message, order_data)
    """
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        # Demo mode — return mock order
        mock_order = {
            "id": f"order_demo_{secrets.token_hex(8)}",
            "amount": amount_paise,
            "currency": settings.RAZORPAY_CURRENCY,
            "receipt": ticket_number,
            "status": "created",
        }
        return True, "Demo payment order created", mock_order

    try:
        import httpx
        import base64

        credentials = base64.b64encode(
            f"{settings.RAZORPAY_KEY_ID}:{settings.RAZORPAY_KEY_SECRET}".encode()
        ).decode()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.razorpay.com/v1/orders",
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/json",
                },
                json={
                    "amount": amount_paise,
                    "currency": settings.RAZORPAY_CURRENCY,
                    "receipt": ticket_number,
                    "notes": {"ticket_number": ticket_number},
                },
                timeout=10.0,
            )
            if response.status_code == 200:
                return True, "Payment order created", response.json()
            return False, "Failed to create payment order", None
    except Exception as e:
        print(f"Razorpay error: {e}")
        return False, "Payment service unavailable", None


# ── Verify Razorpay Payment ───────────────────────────────────────────────────
def verify_razorpay_signature(
    order_id: str,
    payment_id: str,
    signature: str,
) -> bool:
    """
    Verify Razorpay payment signature using HMAC-SHA256.
    """
    if not settings.RAZORPAY_KEY_SECRET:
        # Demo mode — always passes
        return True

    import hmac
    import hashlib

    message = f"{order_id}|{payment_id}"
    expected = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


# ── Initiate Ticket Booking ───────────────────────────────────────────────────
async def initiate_booking(
    user: User,
    bus_id: str,
    boarding_stop: str,
    destination_stop: str,
    adult_count: int,
    child_count: int,
    senior_count: int,
    db: AsyncSession,
) -> Tuple[bool, str, Optional[dict]]:
    """
    Step 1 of booking:
    - Validate bus and route
    - Calculate fare
    - Create PAYMENT_PENDING ticket
    - Create Razorpay order

    Returns (success, message, booking_data)
    """
    # Validate bus
    result = await db.execute(
        select(Bus).where(and_(Bus.id == bus_id, Bus.is_active == True))
    )
    bus = result.scalar_one_or_none()
    if not bus:
        return False, "Bus not found or inactive", None
    if not bus.route_id:
        return False, "Bus has no assigned route", None

    # Fetch route stops
    stops_result = await db.execute(
        select(RouteStop)
        .where(RouteStop.route_id == bus.route_id)
        .order_by(RouteStop.stop_order)
    )
    route_stops = stops_result.scalars().all()

    # Calculate fare
    try:
        fare = fare_engine.calculate_from_stops(
            route_stops=route_stops,
            boarding_stop_name=boarding_stop,
            destination_stop_name=destination_stop,
            adult_count=adult_count,
            child_count=child_count,
            senior_count=senior_count,
        )
    except ValueError as e:
        return False, str(e), None

    # Get journey date/time in IST
    ist_offset = timedelta(hours=5, minutes=30)
    ist_now = datetime.now(timezone.utc) + ist_offset
    journey_date = ist_now.strftime("%Y-%m-%d")
    journey_time = ist_now.strftime("%H:%M")

    # Create ticket in PAYMENT_PENDING state
    ticket_number = generate_ticket_number()
    ticket = Ticket(
        id=str(uuid.uuid4()),
        user_id=user.id,
        bus_id=bus_id,
        route_id=bus.route_id,
        ticket_number=ticket_number,
        boarding_stop=boarding_stop,
        destination_stop=destination_stop,
        journey_date=journey_date,
        journey_time=journey_time,
        adult_count=adult_count,
        child_count=child_count,
        senior_count=senior_count,
        adult_fare_paise=fare.adult.total_fare_paise,
        child_fare_paise=fare.child.total_fare_paise,
        senior_fare_paise=fare.senior.total_fare_paise,
        total_fare_paise=fare.total_fare_paise,
        status=TicketStatus.PAYMENT_PENDING,
        payment_verified=False,
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)

    # Create payment order
    pay_success, pay_msg, order_data = await create_payment_order(
        amount_paise=fare.total_fare_paise,
        ticket_number=ticket_number,
    )
    if not pay_success:
        return False, pay_msg, None

    # Store Razorpay order ID
    if order_data:
        ticket.razorpay_order_id = order_data.get("id")
        await db.commit()

    return True, "Booking initiated", {
        "ticket_id": ticket.id,
        "ticket_number": ticket_number,
        "fare": fare.to_dict(),
        "payment_order": order_data,
        "razorpay_key_id": settings.RAZORPAY_KEY_ID or "demo_mode",
    }


# ── Confirm Payment ───────────────────────────────────────────────────────────
async def confirm_payment(
    ticket_id: str,
    user_id: str,
    payment_id: str,
    razorpay_signature: str,
    db: AsyncSession,
    redis: aioredis.Redis,
) -> Tuple[bool, str, Optional[Ticket]]:
    """
    Step 2 of booking:
    - Verify Razorpay payment signature
    - Activate ticket
    - Generate verification token

    Returns (success, message, ticket)
    """
    result = await db.execute(
        select(Ticket).where(
            and_(
                Ticket.id == ticket_id,
                Ticket.user_id == user_id,
                Ticket.status == TicketStatus.PAYMENT_PENDING,
            )
        )
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        return False, "Ticket not found or already processed", None

    # Verify signature
    if not verify_razorpay_signature(
        order_id=ticket.razorpay_order_id or "",
        payment_id=payment_id,
        signature=razorpay_signature,
    ):
        ticket.status = TicketStatus.PAYMENT_FAILED
        await db.commit()
        return False, "Payment verification failed", None

    # Activate ticket
    now = datetime.now(timezone.utc)
    token, token_expires = generate_verification_token()

    ticket.status = TicketStatus.ACTIVE
    ticket.payment_verified = True
    ticket.payment_id = payment_id
    ticket.paid_at = now
    ticket.verification_token = token
    ticket.verification_token_expires = token_expires
    # Ticket expires at end of journey date (midnight IST)
    ist_offset = timedelta(hours=5, minutes=30)
    ist_midnight = (now + ist_offset).replace(
        hour=23, minute=59, second=59, microsecond=0
    ) - ist_offset
    ticket.expires_at = ist_midnight

    await db.commit()
    await db.refresh(ticket)

    # Cache active ticket in Redis
    await _cache_active_ticket(ticket, redis)

    return True, "Payment confirmed. Ticket is now active.", ticket


# ── Refresh Verification Token ────────────────────────────────────────────────
async def refresh_verification_token(
    ticket_id: str,
    user_id: str,
    db: AsyncSession,
    redis: aioredis.Redis,
) -> Tuple[bool, str, Optional[str]]:
    """
    Rotate the verification token on the ticket detail screen.
    Called every 60 seconds to prevent screenshot reuse.
    """
    result = await db.execute(
        select(Ticket).where(
            and_(
                Ticket.id == ticket_id,
                Ticket.user_id == user_id,
                Ticket.status == TicketStatus.ACTIVE,
            )
        )
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        return False, "Active ticket not found", None

    token, expires = generate_verification_token()
    ticket.verification_token = token
    ticket.verification_token_expires = expires
    await db.commit()
    await _cache_active_ticket(ticket, redis)

    return True, "Token refreshed", token


# ── Expire Stale Tickets ──────────────────────────────────────────────────────
async def expire_stale_tickets(db: AsyncSession) -> int:
    """
    Called periodically to move expired tickets to EXPIRED state.
    Returns count of tickets expired.
    """
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Ticket).where(
            and_(
                Ticket.status == TicketStatus.ACTIVE,
                Ticket.expires_at <= now,
            )
        )
    )
    tickets = result.scalars().all()

    for ticket in tickets:
        ticket.status = TicketStatus.EXPIRED
        ticket.expired_at = now

    if tickets:
        await db.commit()

    return len(tickets)


# ── Get Active Tickets ────────────────────────────────────────────────────────
async def get_active_tickets(
    user_id: str,
    db: AsyncSession,
    redis: aioredis.Redis,
) -> list[Ticket]:
    """
    Fetch all active tickets for a user.
    Checks for expired tickets and updates them first.
    """
    # Auto-expire any stale tickets
    await expire_stale_tickets(db)

    result = await db.execute(
        select(Ticket).where(
            and_(
                Ticket.user_id == user_id,
                Ticket.status == TicketStatus.ACTIVE,
            )
        ).order_by(Ticket.created_at.desc())
    )
    return result.scalars().all()


# ── Cache Active Ticket ───────────────────────────────────────────────────────
async def _cache_active_ticket(
    ticket: Ticket,
    redis: aioredis.Redis,
) -> None:
    """Cache ticket data for offline access."""
    import json
    key = f"ticket:active:{ticket.user_id}:{ticket.id}"
    data = {
        "ticket_id": ticket.id,
        "ticket_number": ticket.ticket_number,
        "bus_id": ticket.bus_id,
        "boarding_stop": ticket.boarding_stop,
        "destination_stop": ticket.destination_stop,
        "journey_date": ticket.journey_date,
        "journey_time": ticket.journey_time,
        "adult_count": ticket.adult_count,
        "child_count": ticket.child_count,
        "senior_count": ticket.senior_count,
        "total_fare_rupees": ticket.total_fare_rupees,
        "status": ticket.status.value,
        "verification_token": ticket.verification_token,
        "verification_token_expires": (
            ticket.verification_token_expires.isoformat()
            if ticket.verification_token_expires else None
        ),
    }
    await redis.setex(
        key,
        settings.TICKET_CACHE_SECONDS,
        json.dumps(data),
    )