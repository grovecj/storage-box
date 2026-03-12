from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.box import BoxCreate, BoxUpdate, BoxResponse, BoxListResponse
from app.services import box_service

router = APIRouter(prefix="/boxes", tags=["boxes"])


@router.post("", response_model=BoxResponse, status_code=201)
async def create_box(data: BoxCreate, db: AsyncSession = Depends(get_db)):
    return await box_service.create_box(db, data)


@router.get("", response_model=BoxListResponse)
async def list_boxes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query("recent", pattern="^(recent|proximity)$"),
    lat: float | None = Query(None),
    lng: float | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await box_service.list_boxes(db, page, page_size, sort, lat, lng)


@router.get("/{box_id}", response_model=BoxResponse)
async def get_box(box_id: int, db: AsyncSession = Depends(get_db)):
    box = await box_service.get_box(db, box_id)
    if not box:
        raise HTTPException(status_code=404, detail="Box not found")
    return box


@router.get("/code/{box_code}", response_model=BoxResponse)
async def get_box_by_code(box_code: str, db: AsyncSession = Depends(get_db)):
    box = await box_service.get_box_by_code(db, box_code)
    if not box:
        raise HTTPException(status_code=404, detail="Box not found")
    return box


@router.put("/{box_id}", response_model=BoxResponse)
async def update_box(box_id: int, data: BoxUpdate, db: AsyncSession = Depends(get_db)):
    box = await box_service.update_box(db, box_id, data)
    if not box:
        raise HTTPException(status_code=404, detail="Box not found")
    return box


@router.delete("/{box_id}")
async def delete_box(box_id: int, db: AsyncSession = Depends(get_db)):
    result = await box_service.delete_box(db, box_id)
    if not result:
        raise HTTPException(status_code=404, detail="Box not found")
    return result
