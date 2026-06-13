from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Depot(Base):
    __tablename__ = "depots"

    code: Mapped[str] = mapped_column(
        String(10), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str | None] = mapped_column(String(80), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    drivers: Mapped[list["Driver"]] = relationship(  # noqa: F821
        "Driver", back_populates="depot", lazy="select"
    )
    tracking_keys: Mapped[list["TrackingApiKey"]] = relationship(  # noqa: F821
        "TrackingApiKey", back_populates="depot", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Depot {self.code} {self.name}>"
