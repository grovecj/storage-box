from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.group import GroupCreate, GroupListResponse, GroupResponse, GroupUpdate
from app.services import group_service

router = APIRouter(prefix="/groups", tags=["groups"])


@router.post("", response_model=GroupResponse, status_code=201)
async def create_group(
    data: GroupCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await group_service.create_group(db, data, user)


@router.get("", response_model=GroupListResponse)
async def list_groups(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await group_service.list_groups(db, user)


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    group = await group_service.get_group(db, group_id, user)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: int,
    data: GroupUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    group = await group_service.update_group(db, group_id, data, user)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@router.delete("/{group_id}")
async def delete_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await group_service.delete_group(db, group_id, user)
    if not result:
        raise HTTPException(status_code=404, detail="Group not found")
    return result
