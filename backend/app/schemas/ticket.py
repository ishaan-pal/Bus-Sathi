from pydantic import BaseModel, field_validator
from typing import Optional
from app.models.ticket import TicketStatus, PaymentMethod


# ── Booking Request Schemas ───────────────────────────────────────────────────
class InitiateBookingRequest(BaseModel):
    bus_id: str
    boarding_stop: str
    destination_stop: str
    adult_count: int = 1
    child_count: int = 0
    senior_count: int = 0

    @field_validator("boarding_stop", "destination_stop")
    @classmethod
    def check_stop(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Stop name must be at least 2 characters")
        return v

    @field_validator("adult_count", "child_count", "senior_count")
    @classmethod
    def check_count(cls, v):
        if v < 0:
            raise ValueError("Passenger count cannot be negative")
        if v > 10:
            raise ValueError("Maximum 10 passengers per category per booking")
        return v

    @field_validator("adult_count")
    @classmethod
    def check_adult_count(cls, v):
        # At least validation done at model level
        return v

    def total_passengers(self) -> int:
        return self.adult_count + self.child_count + self.senior_count


class ConfirmPaymentRequest(BaseModel):
    ticket_id: str
    payment_id: str
    razorpay_signature: str


# ── Fare Breakdown Schemas ────────────────────────────────────────────────────
class PassengerFareResponse(BaseModel):
    category: str
    count: int
    unit_fare_rupees: float
    total_fare_rupees: float
    concession_percent: int


class FareBreakdownResponse(BaseModel):
    boarding_stop: str
    destination_stop: str
    distance_km: float
    total_fare_rupees: float
    total_fare_paise: int
    breakdown: dict


# ── Payment Order Schema ──────────────────────────────────────────────────────
class PaymentOrderResponse(BaseModel):
    id: str
    amount: int                     # in paise
    currency: str
    receipt: str
    status: str


class BookingInitiatedResponse(BaseModel):
    success: bool
    message: str
    ticket_id: str
    ticket_number: str
    fare: FareBreakdownResponse
    payment_order: Optional[dict]
    razorpay_key_id: Optional[str] = None


# ── Active Ticket Schemas ─────────────────────────────────────────────────────
class ActiveTicketItem(BaseModel):
    ticket_id: str
    ticket_number: str
    bus_number: str
    boarding_stop: str
    destination_stop: str
    journey_date: str
    journey_time: str
    adult_count: int
    child_count: int
    senior_count: int
    total_passengers: int
    total_fare_rupees: float
    status: str
    paid_at: Optional[str]

    model_config = {"from_attributes": True}


class ActiveTicketsResponse(BaseModel):
    success: bool
    total: int
    tickets: list[ActiveTicketItem]


# ── Ticket Detail Schema ──────────────────────────────────────────────────────
class TicketDetailResponse(BaseModel):
    """
    Full ticket detail shown on the ticket screen.
    Contains all info needed for conductor visual verification.
    """
    ticket_id: str
    ticket_number: str

    # Passenger
    passenger_name: str
    passenger_mobile: str

    # Journey
    bus_number: str
    route_number: Optional[str]
    boarding_stop: str
    destination_stop: str
    journey_date: str
    journey_time: str

    # Passengers
    adult_count: int
    child_count: int
    senior_count: int
    total_passengers: int

    # Fare
    adult_fare_rupees: float
    child_fare_rupees: float
    senior_fare_rupees: float
    total_fare_rupees: float
    payment_method: Optional[str]
    paid_at: Optional[str]

    # Status
    status: str
    is_valid_for_travel: bool
    expires_at: Optional[str]

    # Verification — rotates every 60s
    verification_token: Optional[str]
    verification_token_expires: Optional[str]
    current_timestamp: str

    # Verification banner text
    verification_banner: str = "LIVE VERIFIED • HARYANA ROADWAYS"


# ── Verification Token Refresh ────────────────────────────────────────────────
class TokenRefreshResponse(BaseModel):
    success: bool
    verification_token: str
    expires_at: str


# ── Fare Calculator Schema ────────────────────────────────────────────────────
class FareCalculateRequest(BaseModel):
    route_id: str
    boarding_stop: str
    destination_stop: str
    adult_count: int = 1
    child_count: int = 0
    senior_count: int = 0

    @field_validator("adult_count", "child_count", "senior_count")
    @classmethod
    def check_count(cls, v):
        if v < 0:
            raise ValueError("Count cannot be negative")
        if v > 10:
            raise ValueError("Maximum 10 per category")
        return v


class FareCalculateResponse(BaseModel):
    success: bool
    fare: FareBreakdownResponse


# ── Admin Ticket Schemas ──────────────────────────────────────────────────────
class AdminTicketListItem(BaseModel):
    ticket_id: str
    ticket_number: str
    user_mobile: str
    bus_number: str
    boarding_stop: str
    destination_stop: str
    journey_date: str
    total_passengers: int
    total_fare_rupees: float
    status: str
    payment_verified: bool
    created_at: str

    model_config = {"from_attributes": True}


class ConductorVerifyRequest(BaseModel):
    ticket_number: str
    bus_number: str


class ConductorVerifyResponse(BaseModel):
    success: bool
    message: str
    is_valid: bool
    ticket_number: Optional[str]
    passenger_name: Optional[str]
    total_passengers: Optional[int]
    boarding_stop: Optional[str]
    destination_stop: Optional[str]
    fare_paid: Optional[float]