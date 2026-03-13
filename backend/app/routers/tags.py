from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.tag import Tag
from app.models.user import User
from app.schemas.item import TagResponse

router = APIRouter(prefix="/tags", tags=["tags"])


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


@router.get("", response_model=list[TagResponse])
async def list_tags(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Tag).order_by(Tag.name))
    return result.scalars().all()


@router.post("", response_model=TagResponse, status_code=201)
async def create_tag(
    data: TagCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    existing = await db.execute(select(Tag).where(Tag.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Tag already exists")
    tag = Tag(name=data.name, created_by=user.id, updated_by=user.id)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag
