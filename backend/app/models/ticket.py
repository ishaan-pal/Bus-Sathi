from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from app.db.base import Base


class TicketStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"
    PAYMENT_PENDING = "payment_pending"
    PAYMENT_FAILED = "payment_failed"


class PaymentMethod(str, enum.Enum):
    UPI = "upi"
    DEBIT_CARD = "debit_card"
    CREDIT_CARD = "credit_card"
    NET_BANKING = "net_banking"


class Ticket(Base):
    __tablename__ = "tickets"

    # ── Ownership ────────────────────────────────────────
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    bus_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("buses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    route_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("routes.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # ── Ticket Identity ───────────────────────────────────
    ticket_number: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )

    # ── Journey Details ──────────────────────────────────
    boarding_stop: Mapped[str] = mapped_column(String(100), nullable=False)
    destination_stop: Mapped[str] = mapped_column(String(100), nullable=False)
    journey_date: Mapped[str] = mapped_column(
        String(10), nullable=False           # YYYY-MM-DD
    )
    journey_time: Mapped[str] = mapped_column(
        String(5), nullable=False            # HH:MM
    )

    # ── Passenger Breakdown ──────────────────────────────
    adult_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    child_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    senior_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    @property
    def total_passengers(self) -> int:
        return self.adult_count + self.child_count + self.senior_count

    # ── Fare Breakdown ───────────────────────────────────
    adult_fare_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    child_fare_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    senior_fare_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_fare_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    @property
    def total_fare_rupees(self) -> float:
        return round(self.total_fare_paise / 100, 2)

    @property
    def adult_fare_rupees(self) -> float:
        return round(self.adult_fare_paise / 100, 2)

    # ── Payment ──────────────────────────────────────────
    payment_method: Mapped[PaymentMethod | None] = mapped_column(
        SAEnum(PaymentMethod), nullable=True
    )
    payment_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True           # Razorpay payment ID
    )
    razorpay_order_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    payment_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    paid_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # ── Lifecycle ────────────────────────────────────────
    status: Mapped[TicketStatus] = mapped_column(
        SAEnum(TicketStatus),
        default=TicketStatus.PAYMENT_PENDING,
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(nullable=True)
    expired_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # ── Security ─────────────────────────────────────────
    # Verification token shown on ticket screen (rotates every 60s)
    verification_token: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    verification_token_expires: Mapped[datetime | None] = mapped_column(
        nullable=True
    )

    # ── Conductor Notes ──────────────────────────────────
    conductor_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────────
    user: Mapped["User"] = relationship(              # noqa: F821
        "User", back_populates="tickets"
    )
    bus: Mapped["Bus"] = relationship(                # noqa: F821
        "Bus", back_populates="tickets"
    )

    def __repr__(self) -> str:
        return (
            f"<Ticket {self.ticket_number} "
            f"status={self.status} "
            f"{self.boarding_stop}→{self.destination_stop}>"
        )

    @property
    def is_valid_for_travel(self) -> bool:
        """True only when ticket is active and payment verified."""
        return (
            self.status == TicketStatus.ACTIVE
            and self.payment_verified
        )