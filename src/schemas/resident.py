from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class ResidentBase(BaseModel):
    """Shared properties for a Resident."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Full name of the resident",
        examples=["Anna Müller"],
    )
    date_of_birth: date | None = Field(
        default=None,
        description="Date of birth of the resident",
        examples=["1942-03-14"],
    )
    room_number: str | None = Field(
        default=None,
        max_length=20,
        description="Assigned room or suite number",
        examples=["101"],
    )


class ResidentCreate(ResidentBase):
    """Schema for creating a new resident record."""

    pass


class ResidentUpdate(BaseModel):
    """Schema for updating an existing resident. All fields are optional."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Updated full name",
    )
    date_of_birth: date | None = Field(
        default=None,
        description="Updated date of birth",
    )
    room_number: str | None = Field(
        default=None,
        max_length=20,
        description="Updated room number",
    )


class ResidentResponse(ResidentBase):
    """Schema for returning resident data."""

    id: int = Field(..., description="Unique resident ID")

    model_config = ConfigDict(from_attributes=True)
