from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.transfer import TransferRequest, TransferResponse
from app.services import transfer_service

router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.post("", response_model=TransferResponse)
async def transfer_item(
    data: TransferRequest, db: AsyncSession = Depends(get_db)
):
    try:
        return await transfer_service.transfer_item(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
