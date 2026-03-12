from pydantic import BaseModel, Field


class TransferRequest(BaseModel):
    from_box_id: int
    to_box_id: int
    item_id: int
    quantity: int = Field(gt=0)


class TransferResponse(BaseModel):
    message: str
    from_box_code: str
    to_box_code: str
    item_name: str
    quantity: int
