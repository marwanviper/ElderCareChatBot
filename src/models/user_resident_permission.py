from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.models.resident import Resident
    from src.models.user import User


class UserResidentPermission(Base):
    """SQLAlchemy model representing the user_resident_permissions junction table."""

    __tablename__ = "user_resident_permissions"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    resident_id: Mapped[int] = mapped_column(
        ForeignKey("residents.id"), primary_key=True
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", back_populates="user_resident_permissions"
    )
    resident: Mapped["Resident"] = relationship(
        "Resident", back_populates="user_resident_permissions"
    )
