from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import search_service
from app.services import item_service

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search(
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    return await search_service.search(db, q)


@router.get("/autocomplete/items")
async def autocomplete_items(
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    return await item_service.autocomplete_items(db, q)
