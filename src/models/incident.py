from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from utils.utils import _utcnow

if TYPE_CHECKING:
    from src.models.resident import Resident


class Incident(Base):
    """SQLAlchemy model representing the incidents table."""

    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    resident_id: Mapped[int] = mapped_column(ForeignKey("residents.id"), nullable=False)
    incident_date: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, nullable=False
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    resident: Mapped["Resident"] = relationship("Resident", back_populates="incidents")
