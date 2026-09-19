from datetime import date
from typing import TYPE_CHECKING, List

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.models.care_goal import CareGoal
    from src.models.care_report import CareReport
    from src.models.incident import Incident
    from src.models.user_resident_permission import UserResidentPermission


class Resident(Base):
    """SQLAlchemy model representing the residents table."""

    __tablename__ = "residents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    room_number: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Relationships
    care_reports: Mapped[List["CareReport"]] = relationship(
        "CareReport", back_populates="resident"
    )
    care_goals: Mapped[List["CareGoal"]] = relationship(
        "CareGoal", back_populates="resident"
    )
    incidents: Mapped[List["Incident"]] = relationship(
        "Incident", back_populates="resident"
    )
    user_resident_permissions: Mapped[List["UserResidentPermission"]] = relationship(
        "UserResidentPermission", back_populates="resident"
    )
