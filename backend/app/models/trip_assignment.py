from datetime import date, time

from sqlalchemy import String, ForeignKey, Date, Time, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TripAssignment(Base):
    __tablename__ = "trip_assignments"

    assignment_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    bus_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("buses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    driver_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("drivers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    conductor_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("drivers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    route_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("routes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    scheduled_departure: Mapped[time | None] = mapped_column(Time, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)

    bus: Mapped["Bus"] = relationship("Bus", back_populates="trip_assignments")  # noqa: F821
    driver: Mapped["Driver"] = relationship(  # noqa: F821
        "Driver",
        foreign_keys=[driver_id],
        back_populates="trip_assignments_as_driver",
    )
    conductor: Mapped["Driver | None"] = relationship(  # noqa: F821
        "Driver",
        foreign_keys=[conductor_id],
        back_populates="trip_assignments_as_conductor",
    )
    route: Mapped["Route"] = relationship("Route")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<TripAssignment {self.assignment_date} "
            f"bus={self.bus_id} driver={self.driver_id}>"
        )
