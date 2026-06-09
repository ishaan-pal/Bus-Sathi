from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Route(Base):
    __tablename__ = "routes"

    # ── Identity ─────────────────────────────────────────
    route_number: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # ── Endpoints ────────────────────────────────────────
    origin: Mapped[str] = mapped_column(String(100), nullable=False)
    destination: Mapped[str] = mapped_column(String(100), nullable=False)

    # ── Distance & Duration ──────────────────────────────
    total_distance_km: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    estimated_duration_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # ── Status ───────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    # ── Relationships ─────────────────────────────────────
    stops: Mapped[list["RouteStop"]] = relationship(
        "RouteStop",
        back_populates="route",
        order_by="RouteStop.stop_order",
        cascade="all, delete-orphan",
        lazy="select",
    )
    buses: Mapped[list["Bus"]] = relationship(        # noqa: F821
        "Bus", back_populates="route", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Route {self.route_number}: {self.origin} → {self.destination}>"


class RouteStop(Base):
    __tablename__ = "route_stops"

    # ── Foreign Key ──────────────────────────────────────
    route_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("routes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Stop Details ─────────────────────────────────────
    stop_name: Mapped[str] = mapped_column(String(100), nullable=False)
    stop_order: Mapped[int] = mapped_column(Integer, nullable=False)

    # ── Distance from origin (for fare calculation) ───────
    distance_from_origin_km: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )

    # ── Coordinates ──────────────────────────────────────
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Timing ───────────────────────────────────────────
    # Minutes from departure at origin
    scheduled_minutes_from_origin: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    is_major_stop: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # ── Relationships ─────────────────────────────────────
    route: Mapped["Route"] = relationship(
        "Route", back_populates="stops"
    )

    def __repr__(self) -> str:
        return (
            f"<RouteStop order={self.stop_order} "
            f"name={self.stop_name} "
            f"dist={self.distance_from_origin_km}km>"
        )