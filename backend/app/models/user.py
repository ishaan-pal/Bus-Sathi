from sqlalchemy import String, Boolean, Date, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.base import Base


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class User(Base):
    __tablename__ = "users"

    # ── Identity ─────────────────────────────────────────
    mobile: Mapped[str] = mapped_column(
        String(10), unique=True, index=True, nullable=False
    )
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    date_of_birth: Mapped[str | None] = mapped_column(
        String(10), nullable=True          # stored as YYYY-MM-DD string
    )
    gender: Mapped[Gender | None] = mapped_column(
        SAEnum(Gender), nullable=True
    )

    # ── Aadhaar ──────────────────────────────────────────
    aadhaar_number: Mapped[str | None] = mapped_column(
        String(12), nullable=True, unique=True
    )
    aadhaar_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # ── Profile ──────────────────────────────────────────
    profile_complete: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # ── Roles & Status ───────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    is_staff: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # ── Relationships ─────────────────────────────────────
    tickets: Mapped[list["Ticket"]] = relationship(      # noqa: F821
        "Ticket", back_populates="user", lazy="select"
    )
    passes: Mapped[list["BusPass"]] = relationship(      # noqa: F821
        "BusPass", back_populates="user", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} mobile={self.mobile} name={self.name}>"

    @property
    def age(self) -> int | None:
        """Calculate age from DOB string (YYYY-MM-DD)."""
        if not self.date_of_birth:
            return None
        from datetime import date
        try:
            dob = date.fromisoformat(self.date_of_birth)
            today = date.today()
            return (
                today.year - dob.year
                - ((today.month, today.day) < (dob.month, dob.day))
            )
        except ValueError:
            return None

    @property
    def is_senior_citizen(self) -> bool:
        age = self.age
        return age is not None and age >= 60

    @property
    def is_child(self) -> bool:
        age = self.age
        return age is not None and age < 12