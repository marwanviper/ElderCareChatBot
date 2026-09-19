from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from utils.utils import _utcnow

if TYPE_CHECKING:
    from src.models.resident import Resident
    from src.models.user import User


class CareReport(Base):
    """SQLAlchemy model representing the care_reports table."""

    __tablename__ = "care_reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    resident_id: Mapped[int] = mapped_column(ForeignKey("residents.id"), nullable=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    report_date: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="care_reports")
    resident: Mapped["Resident"] = relationship(
        "Resident", back_populates="care_reports"
    )
