from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

# Robust EmailStr supporting environments with or without email-validator package
try:
    import email_validator  # noqa: F401
    from pydantic import EmailStr
except ImportError:
    EmailStr = Annotated[
        str,
        StringConstraints(
            pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
            strip_whitespace=True,
            to_lower=True,
            max_length=255,
        ),
    ]


class UserBase(BaseModel):
    """Shared properties for a User."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Full name of the user",
        examples=["Ahmed Hassan"],
    )
    email: EmailStr = Field(
        ...,
        max_length=255,
        description="Unique email address of the user",
        examples=["ahmed@eldercare.test"],
    )
    role: str = Field(
        default="caregiver",
        min_length=1,
        max_length=20,
        description="User role (e.g., 'admin', 'caregiver')",
        examples=["caregiver"],
    )


class UserCreate(UserBase):
    """Schema for creating a new User."""

    password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="Plaintext password provided during registration",
        examples=["SecurePass123!"],
    )


class UserUpdate(BaseModel):
    """Schema for updating an existing User. All fields are optional."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Updated full name",
    )
    email: EmailStr | None = Field(
        default=None,
        max_length=255,
        description="Updated email address",
    )
    role: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
        description="Updated role",
    )
    password: str | None = Field(
        default=None,
        min_length=6,
        max_length=128,
        description="Updated password",
    )


class UserResponse(BaseModel):
    """Schema for returning user data. Excludes sensitive fields like password_hash."""

    id: int = Field(..., description="Unique user ID")
    name: str = Field(..., description="Full name of the user")
    email: EmailStr = Field(..., description="Unique email address")
    role: str = Field(..., description="Role of the user")
    deleted_date: datetime | None = Field(
        default=None,
        description="Timestamp of soft deletion, or None if active",
    )

    model_config = ConfigDict(from_attributes=True)
