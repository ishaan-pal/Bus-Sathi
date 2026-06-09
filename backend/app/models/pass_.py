from sqlalchemy import String, Boolean, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from app.db.base import Base


class PassType(str, enum.Enum):
    STUDENT = "student"
    SENIOR_CITIZEN = "senior_citizen"
    MONTHLY = "monthly"
    DIFFERENTLY_ABLED = "differently_abled"
    FREEDOM_FIGHTER = "freedom_fighter"
    PRESS = "press"


class PassStatus(str, enum.Enum):
    DRAFT = "draft"                   # not yet submitted
    SUBMITTED = "submitted"           # under review
    VERIFICATION_PENDING = "verification_pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVOKED = "revoked"


class PassCategory(str, enum.Enum):
    ORDINARY = "ordinary"
    EXPRESS = "express"
    ALL_ROUTES = "all_routes"


class BusPass(Base):
    __tablename__ = "bus_passes"

    # ── Ownership ────────────────────────────────────────
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Pass Identity ─────────────────────────────────────
    pass_number: Mapped[str | None] = mapped_column(
        String(20), unique=True, nullable=True, index=True
    )
    pass_type: Mapped[PassType] = mapped_column(
        SAEnum(PassType), nullable=False
    )
    pass_category: Mapped[PassCategory] = mapped_column(
        SAEnum(PassCategory),
        default=PassCategory.ORDINARY,
        nullable=False,
    )

    # ── Route Coverage ────────────────────────────────────
    # Null means all-routes pass
    route_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("routes.id", ondelete="SET NULL"),
        nullable=True,
    )
    from_stop: Mapped[str | None] = mapped_column(String(100), nullable=True)
    to_stop: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # ── Validity ──────────────────────────────────────────
    valid_from: Mapped[str | None] = mapped_column(
        String(10), nullable=True           # YYYY-MM-DD
    )
    valid_until: Mapped[str | None] = mapped_column(
        String(10), nullable=True           # YYYY-MM-DD
    )

    # ── Status ────────────────────────────────────────────
    status: Mapped[PassStatus] = mapped_column(
        SAEnum(PassStatus),
        default=PassStatus.DRAFT,
        nullable=False,
        index=True,
    )

    # ── Application Details ───────────────────────────────
    applicant_name: Mapped[str] = mapped_column(String(100), nullable=False)
    applicant_mobile: Mapped[str] = mapped_column(String(10), nullable=False)
    applicant_dob: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Student-specific
    institution_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    institution_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    student_id_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # ── Document Uploads ──────────────────────────────────
    # S3 / local paths to uploaded documents
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    id_proof_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    address_proof_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    institution_cert_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True         # for student pass
    )

    # ── Admin Review ──────────────────────────────────────
    reviewed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Verification Banner ───────────────────────────────
    # Rotating token shown on pass screen for conductor verification
    verification_token: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    verification_token_expires: Mapped[datetime | None] = mapped_column(
        nullable=True
    )

    # ── Relationships ──────────────────────────────────────
    user: Mapped["User"] = relationship(              # noqa: F821
        "User", back_populates="passes"
    )
    route: Mapped["Route | None"] = relationship(     # noqa: F821
        "Route", lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<BusPass {self.pass_number} "
            f"type={self.pass_type} "
            f"status={self.status}>"
        )

    @property
    def is_valid(self) -> bool:
        """True only when approved and within validity period."""
        if self.status != PassStatus.APPROVED:
            return False
        if not self.valid_from or not self.valid_until:
            return False
        from datetime import date
        today = date.today().isoformat()
        return self.valid_from <= today <= self.valid_until

    @property
    def days_remaining(self) -> int | None:
        """Days left before pass expires. None if not approved."""
        if not self.is_valid or not self.valid_until:
            return None
        from datetime import date
        expiry = date.fromisoformat(self.valid_until)
        return (expiry - date.today()).days