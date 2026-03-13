from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.box import BoxCreate, BoxListResponse, BoxResponse, BoxUpdate
from app.services import box_service

router = APIRouter(prefix="/boxes", tags=["boxes"])


@router.post("", response_model=BoxResponse, status_code=201)
async def create_box(
    data: BoxCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await box_service.create_box(db, data, user)


@router.get("", response_model=BoxListResponse)
async def list_boxes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query("recent", pattern="^(recent|proximity)$"),
    lat: float | None = Query(None),
    lng: float | None = Query(None),
    group_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await box_service.list_boxes(db, user, page, page_size, sort, lat, lng, group_id)


@router.get("/{box_id}", response_model=BoxResponse)
async def get_box(
    box_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    box = await box_service.get_box(db, box_id, user)
    if not box:
        raise HTTPException(status_code=404, detail="Box not found")
    return box


@router.get("/code/{box_code}", response_model=BoxResponse)
async def get_box_by_code(
    box_code: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    box = await box_service.get_box_by_code(db, box_code, user)
    if not box:
        raise HTTPException(status_code=404, detail="Box not found")
    return box


@router.put("/{box_id}", response_model=BoxResponse)
async def update_box(
    box_id: int,
    data: BoxUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    box = await box_service.update_box(db, box_id, data, user)
    if not box:
        raise HTTPException(status_code=404, detail="Box not found")
    return box


@router.delete("/{box_id}")
async def delete_box(
    box_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await box_service.delete_box(db, box_id, user)
    if not result:
        raise HTTPException(status_code=404, detail="Box not found")
    return result
