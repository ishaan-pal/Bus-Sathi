from sqlalchemy import String, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.base import Base


class StaffRole(str, enum.Enum):
    DRIVER = "driver"
    CONDUCTOR = "conductor"
    BOTH = "both"


class Driver(Base):
    __tablename__ = "drivers"

    employee_id: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    mobile: Mapped[str | None] = mapped_column(String(10), nullable=True)
    license_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    depot_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("depots.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    role: Mapped[StaffRole] = mapped_column(
        SAEnum(StaffRole), default=StaffRole.DRIVER, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    depot: Mapped["Depot | None"] = relationship(  # noqa: F821
        "Depot", back_populates="drivers"
    )
    trip_assignments_as_driver: Mapped[list["TripAssignment"]] = relationship(  # noqa: F821
        "TripAssignment",
        foreign_keys="TripAssignment.driver_id",
        back_populates="driver",
        lazy="select",
    )
    trip_assignments_as_conductor: Mapped[list["TripAssignment"]] = relationship(  # noqa: F821
        "TripAssignment",
        foreign_keys="TripAssignment.conductor_id",
        back_populates="conductor",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Driver {self.employee_id} {self.name}>"
