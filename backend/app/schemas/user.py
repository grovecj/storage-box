from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: int
    google_id: str
    email: str
    name: str
    picture_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
