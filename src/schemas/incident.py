from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class IncidentBase(BaseModel):
    """Shared properties for an Incident."""

    resident_id: int = Field(
        ...,
        description="ID of the resident involved in the incident",
        examples=[1],
    )
    type: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Category of the incident (e.g., 'Fall', 'Medication', 'Behavioral')",
        examples=["Fall"],
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Detailed description of what occurred and actions taken",
        examples=["Resident slipped near bathroom entrance. No fractures detected."],
    )


class IncidentCreate(IncidentBase):
    """Schema for reporting a new incident."""

    incident_date: datetime | None = Field(
        default=None,
        description="Incident timestamp; defaults to current UTC time if not provided",
    )


class IncidentUpdate(BaseModel):
    """Schema for updating an existing incident record. All fields are optional."""

    type: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="Updated incident category",
    )
    description: str | None = Field(
        default=None,
        min_length=1,
        description="Updated incident description",
    )
    incident_date: datetime | None = Field(
        default=None,
        description="Updated incident timestamp",
    )


class IncidentResponse(IncidentBase):
    """Schema for returning incident data."""

    id: int = Field(..., description="Unique incident ID")
    incident_date: datetime = Field(..., description="Timestamp of the incident")

    model_config = ConfigDict(from_attributes=True)
