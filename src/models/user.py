from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, Enum as SQLEnum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.models.care_report import CareReport
    from src.models.user_resident_permission import UserResidentPermission


class Role(str, Enum):
    """User roles defining system access tiers."""

    ADMIN = "admin"
    CAREGIVER = "caregiver"

    def __str__(self) -> str:
        return self.value


class User(Base):
    """SQLAlchemy model representing the users table."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[Role] = mapped_column(
        SQLEnum(
            Role,
            native_enum=False,
            length=20,
            values_callable=lambda obj: [e.value for e in obj],
            validate_strings=True,
        ),
        default=Role.CAREGIVER,
        nullable=False,
    )
    deleted_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    care_reports: Mapped[List["CareReport"]] = relationship(
        "CareReport", back_populates="user"
    )
    user_resident_permissions: Mapped[List["UserResidentPermission"]] = relationship(
        "UserResidentPermission", back_populates="user"
    )
