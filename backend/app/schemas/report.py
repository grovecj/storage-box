from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    box_ids: list[int] | None = None  # None = all boxes
    tag_filter: list[str] = Field(default_factory=list)
    location_filter: str | None = None  # Filter by location_name contains
    format: str = Field(default="html", pattern="^(html|pdf|csv|text)$")


class AuditLogResponse(BaseModel):
    id: int
    action: str
    details: dict
    created_at: str

    model_config = {"from_attributes": True}
