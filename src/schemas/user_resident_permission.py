from pydantic import BaseModel, ConfigDict, Field


class UserResidentPermissionBase(BaseModel):
    """Shared properties for User-Resident permission association."""

    user_id: int = Field(
        ...,
        description="ID of the user granted permission",
        examples=[1],
    )
    resident_id: int = Field(
        ...,
        description="ID of the resident accessible to the user",
        examples=[1],
    )


class UserResidentPermissionCreate(UserResidentPermissionBase):
    """Schema for assigning resident access permission to a user."""

    pass


class UserResidentPermissionResponse(UserResidentPermissionBase):
    """Schema for returning user-resident permission link."""

    model_config = ConfigDict(from_attributes=True)
