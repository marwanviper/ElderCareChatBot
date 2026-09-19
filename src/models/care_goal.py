from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from utils.utils import _utcnow

if TYPE_CHECKING:
    from src.models.resident import Resident


class CareGoal(Base):
    """SQLAlchemy model representing the care_goals table."""

    __tablename__ = "care_goals"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    resident_id: Mapped[int] = mapped_column(ForeignKey("residents.id"), nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, nullable=False
    )

    # Relationships
    resident: Mapped["Resident"] = relationship("Resident", back_populates="care_goals")
