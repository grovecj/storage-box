from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.item import (
    BoxItemListResponse,
    BoxItemResponse,
    ItemAddRequest,
    ItemUpdateRequest,
)
from app.services import item_service

router = APIRouter(prefix="/boxes/{box_id}/items", tags=["items"])


@router.get("", response_model=BoxItemListResponse)
async def list_items(
    box_id: int,
    page: int = Query(1, ge=1),
    page_size: int | None = Query(10, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # page_size=0 means ALL
    if page_size == 0:
        page_size = None
    result = await item_service.list_items(db, box_id, user, page, page_size)
    if result is None:
        raise HTTPException(status_code=404, detail="Box not found")
    return result


@router.post("", response_model=BoxItemResponse, status_code=201)
async def add_item(
    box_id: int,
    data: ItemAddRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return await item_service.add_item(db, box_id, data, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.put("/{item_id}", response_model=BoxItemResponse)
async def update_item(
    box_id: int,
    item_id: int,
    data: ItemUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await item_service.update_item(db, box_id, item_id, data, user)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found in this box")
    return result


@router.delete("/{item_id}")
async def remove_item(
    box_id: int,
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    success = await item_service.remove_item(db, box_id, item_id, user)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found in this box")
    return {"message": "Item removed"}
