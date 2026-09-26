from pydantic import BaseModel, Field

from src.schemas.user import EmailStr


class Token(BaseModel):
    """Schema for returning an access token to the client."""

    access_token: str = Field(..., description="JWT Bearer access token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenPayload(BaseModel):
    """Schema representing the decoded JWT payload data."""

    sub: str | None = None
    user_id: int | None = None
    role: str | None = None


class LoginRequest(BaseModel):
    """Schema for JSON-based login request payload."""

    email: EmailStr = Field(..., description="Registered user email")
    password: str = Field(..., description="Plaintext account password")
