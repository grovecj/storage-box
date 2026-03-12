from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    box_ids: list[int] | None = None  # None = all boxes
    tag_filter: list[str] = Field(default_factory=list)
    format: str = Field(default="html", pattern="^(html|pdf|csv)$")


class AuditLogResponse(BaseModel):
    id: int
    action: str
    details: dict
    created_at: str

    model_config = {"from_attributes": True}
