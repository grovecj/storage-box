from datetime import datetime

from pydantic import BaseModel, Field


class LocationSchema(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class BoxCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    location: LocationSchema | None = None


class BoxUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    location: LocationSchema | None = None


class BoxResponse(BaseModel):
    id: int
    box_code: str
    name: str
    latitude: float | None = None
    longitude: float | None = None
    item_count: int = 0
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None
    updated_by: int | None = None

    model_config = {"from_attributes": True}


class BoxListResponse(BaseModel):
    boxes: list[BoxResponse]
    total: int
    page: int
    page_size: int
