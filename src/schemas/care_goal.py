from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CareGoalBase(BaseModel):
    """Shared properties for a CareGoal."""

    resident_id: int = Field(
        ...,
        description="ID of the resident for whom this goal is set",
        examples=[1],
    )
    goal: str = Field(
        ...,
        min_length=1,
        description="Description of the care goal",
        examples=["Walk 200 meters daily with walker assistance."],
    )
    status: str = Field(
        default="active",
        min_length=1,
        max_length=30,
        description="Status of the goal (e.g., 'active', 'achieved', 'cancelled')",
        examples=["active"],
    )


class CareGoalCreate(CareGoalBase):
    """Schema for creating a new care goal."""

    pass


class CareGoalUpdate(BaseModel):
    """Schema for updating an existing care goal. All fields are optional."""

    goal: str | None = Field(
        default=None,
        min_length=1,
        description="Updated goal description",
    )
    status: str | None = Field(
        default=None,
        min_length=1,
        max_length=30,
        description="Updated goal status",
    )


class CareGoalResponse(CareGoalBase):
    """Schema for returning care goal data."""

    id: int = Field(..., description="Unique care goal ID")
    created_at: datetime = Field(..., description="Timestamp when goal was established")

    model_config = ConfigDict(from_attributes=True)
