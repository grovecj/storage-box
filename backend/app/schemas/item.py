from datetime import datetime

from pydantic import BaseModel, Field


class ItemAddRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    quantity: int = Field(gt=0)
    tags: list[str] = Field(default_factory=list)


class ItemUpdateRequest(BaseModel):
    quantity: int | None = Field(default=None, gt=0)
    tags: list[str] | None = None


class TagResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class BoxItemResponse(BaseModel):
    id: int
    item_id: int
    name: str
    quantity: int
    tags: list[str]
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None
    updated_by: int | None = None

    model_config = {"from_attributes": True}


class BoxItemListResponse(BaseModel):
    items: list[BoxItemResponse]
    total: int
    page: int
    page_size: int


class ItemAutocompleteResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}
