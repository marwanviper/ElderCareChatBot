from datetime import datetime

from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from src.database import Base
from utils.utils import _utcnow


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)

    deleted_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    care_reports: Mapped[list["CareReport"]] = relationship(
        "CareReport", back_populates="user"
    )

    user_resident_permissions: Mapped[list["UserResidentPermission"]] = relationship(
        "UserResidentPermission", back_populates="user"
    )


class CareReport(Base):
    __tablename__ = "care_reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    resident_id: Mapped[int] = mapped_column(ForeignKey("residents.id"), nullable=False)

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    report_date: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, nullable=False
    )

    content: Mapped[str] = mapped_column(String(1000), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="care_reports")

    resident: Mapped["Resident"] = relationship(
        "Resident", back_populates="care_reports"
    )


class Resident(Base):
    __tablename__ = "residents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)

    room_number: Mapped[str | None] = mapped_column(String(20), nullable=True)

    date_of_birth: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    care_reports: Mapped[list["CareReport"]] = relationship(
        "CareReport", back_populates="resident"
    )

    care_goals: Mapped[list["CareGoal"]] = relationship(
        "CareGoal", back_populates="resident"
    )

    incidents: Mapped[list["Incident"]] = relationship(
        "Incident", back_populates="resident"
    )

    user_resident_permissions: Mapped[list["UserResidentPermission"]] = relationship(
        "UserResidentPermission", back_populates="resident"
    )


class CareGoal(Base):
    __tablename__ = "care_goals"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    resident_id: Mapped[int] = mapped_column(ForeignKey("residents.id"), nullable=False)

    goal: Mapped[str] = mapped_column(String(1000), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, nullable=False
    )

    resident: Mapped["Resident"] = relationship("Resident", back_populates="care_goals")


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    resident_id: Mapped[int] = mapped_column(ForeignKey("residents.id"), nullable=False)

    incident_date: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, nullable=False
    )

    description: Mapped[str] = mapped_column(String(1000), nullable=False)

    type: Mapped[str] = mapped_column(String(50), nullable=False)

    resident: Mapped["Resident"] = relationship("Resident", back_populates="incidents")


class UserResidentPermission(Base):
    __tablename__ = "user_resident_permissions"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)

    resident_id: Mapped[int] = mapped_column(
        ForeignKey("residents.id"), primary_key=True
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="user_resident_permissions"
    )

    resident: Mapped["Resident"] = relationship(
        "Resident", back_populates="user_resident_permissions"
    )


if __name__ == "__main__":
    from database import get_db

    db = next(get_db())
    users: list[User] = db.query(User).all()
    for user in users:
        print(user.id, user.name, user.email, user.role)
    db.close()
