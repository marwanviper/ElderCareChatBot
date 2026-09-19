from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CareReportBase(BaseModel):
    """Shared properties for a CareReport."""

    resident_id: int = Field(
        ...,
        description="ID of the resident this report pertains to",
        examples=[1],
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Detailed observation or care notes",
        examples=["Resident completed physical therapy exercises successfully."],
    )
    created_by: int | None = Field(
        default=None,
        description="ID of the user who authored this report",
        examples=[1],
    )


class CareReportCreate(CareReportBase):
    """Schema for creating a new care report."""

    report_date: datetime | None = Field(
        default=None,
        description="Report timestamp; defaults to current UTC time if not provided",
    )


class CareReportUpdate(BaseModel):
    """Schema for updating an existing care report. All fields are optional."""

    content: str | None = Field(
        default=None,
        min_length=1,
        description="Updated report content",
    )
    report_date: datetime | None = Field(
        default=None,
        description="Updated report timestamp",
    )


class CareReportResponse(CareReportBase):
    """Schema for returning care report data."""

    id: int = Field(..., description="Unique care report ID")
    report_date: datetime = Field(..., description="Report creation timestamp")

    model_config = ConfigDict(from_attributes=True)
