from sqlalchemy import String, Float, Boolean, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from app.db.base import Base


class BusStatus(str, enum.Enum):
    RUNNING = "running"
    DELAYED = "delayed"
    STOPPED = "stopped"
    DEPOT = "depot"
    OUT_OF_SERVICE = "out_of_service"


class BusType(str, enum.Enum):
    ORDINARY = "ordinary"
    EXPRESS = "express"
    SUPER_EXPRESS = "super_express"
    AC = "ac"
    MINI = "mini"


class Bus(Base):
    __tablename__ = "buses"

    # ── Identity ─────────────────────────────────────────
    bus_number: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    registration_number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False
    )
    bus_type: Mapped[BusType] = mapped_column(
        SAEnum(BusType), default=BusType.ORDINARY, nullable=False
    )

    # ── Capacity ─────────────────────────────────────────
    seating_capacity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=52
    )
    standing_capacity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=20
    )

    # ── Route Assignment ─────────────────────────────────
    route_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("routes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Live Location ────────────────────────────────────
    current_latitude: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    current_longitude: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    last_location_update: Mapped[datetime | None] = mapped_column(
        nullable=True
    )
    current_speed_kmh: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    heading_degrees: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    # ── Current Journey ──────────────────────────────────
    current_stop: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    next_stop: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    # Distance covered on current route (km)
    distance_covered_km: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    # Delay in minutes (positive = late, negative = early)
    delay_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # ── Status ───────────────────────────────────────────
    status: Mapped[BusStatus] = mapped_column(
        SAEnum(BusStatus), default=BusStatus.DEPOT, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    # ── Driver / Conductor ───────────────────────────────
    driver_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    conductor_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    conductor_mobile: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # ── Tracking Source ──────────────────────────────────
    # "gps" = dedicated GPS device, "etm" = ETM machine feed
    tracking_source: Mapped[str] = mapped_column(
        String(10), default="gps", nullable=False
    )

    # ── Relationships ─────────────────────────────────────
    route: Mapped["Route | None"] = relationship(     # noqa: F821
        "Route", back_populates="buses"
    )
    tickets: Mapped[list["Ticket"]] = relationship(   # noqa: F821
        "Ticket", back_populates="bus", lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<Bus {self.bus_number} "
            f"status={self.status} "
            f"route={self.route_id}>"
        )

    @property
    def is_location_stale(self) -> bool:
        """True if last GPS update is older than threshold."""
        if self.last_location_update is None:
            return True
        from datetime import timezone
        from app.core.config import settings
        now = datetime.now(timezone.utc)
        delta = (now - self.last_location_update).total_seconds()
        return delta > settings.BUS_LOCATION_STALE_SECONDS

    @property
    def eta_display(self) -> str:
        """Human-readable delay string for passengers."""
        if self.status == BusStatus.DEPOT:
            return "At depot"
        if self.delay_minutes == 0:
            return "On time"
        if self.delay_minutes > 0:
            return f"~{self.delay_minutes} min late"
        return f"~{abs(self.delay_minutes)} min early"