from datetime import datetime

from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TrackingApiKey(Base):
    __tablename__ = "tracking_api_keys"

    label: Mapped[str] = mapped_column(String(100), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    depot_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("depots.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(nullable=True)

    depot: Mapped["Depot | None"] = relationship(  # noqa: F821
        "Depot", back_populates="tracking_keys"
    )

    def __repr__(self) -> str:
        return f"<TrackingApiKey {self.label} ({self.key_prefix}…)>"
