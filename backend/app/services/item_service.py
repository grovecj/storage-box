from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.box import StorageBox
from app.models.item import Item, BoxItem, BoxItemTag
from app.models.tag import Tag
from app.models.user import User
from app.schemas.item import (
    ItemAddRequest,
    ItemUpdateRequest,
    BoxItemResponse,
    BoxItemListResponse,
)
from app.utils.audit import log_action

MAX_ITEMS_PER_BOX = 500


async def _verify_box_owner(db: AsyncSession, box_id: int, user: User) -> bool:
    """Verify that the box belongs to the user."""
    result = await db.execute(
        select(StorageBox)
        .where(StorageBox.id == box_id)
        .where(StorageBox.owner_id == user.id)
    )
    return result.scalar_one_or_none() is not None


async def _get_or_create_item(db: AsyncSession, name: str, user: User) -> Item:
    result = await db.execute(select(Item).where(func.lower(Item.name) == name.lower()))
    item = result.scalar_one_or_none()
    if not item:
        item = Item(name=name, created_by=user.id, updated_by=user.id)
        db.add(item)
        await db.flush()
    return item


async def _get_or_create_tag(db: AsyncSession, name: str, user: User) -> Tag:
    result = await db.execute(select(Tag).where(func.lower(Tag.name) == name.lower()))
    tag = result.scalar_one_or_none()
    if not tag:
        tag = Tag(name=name, created_by=user.id, updated_by=user.id)
        db.add(tag)
        await db.flush()
    return tag


def _box_item_to_response(box_item: BoxItem) -> BoxItemResponse:
    return BoxItemResponse(
        id=box_item.id,
        item_id=box_item.item_id,
        name=box_item.item.name,
        quantity=box_item.quantity,
        tags=[bit.tag.name for bit in box_item.tags],
        created_at=box_item.created_at,
        updated_at=box_item.updated_at,
        created_by=box_item.created_by,
        updated_by=box_item.updated_by,
    )


async def list_items(
    db: AsyncSession, box_id: int, user: User, page: int = 1, page_size: int | None = 10
) -> BoxItemListResponse | None:
    if not await _verify_box_owner(db, box_id, user):
        return None

    count_result = await db.execute(
        select(func.count(BoxItem.id)).where(BoxItem.box_id == box_id)
    )
    total = count_result.scalar()

    query = (
        select(BoxItem)
        .where(BoxItem.box_id == box_id)
        .options(selectinload(BoxItem.item), selectinload(BoxItem.tags).selectinload(BoxItemTag.tag))
        .order_by(BoxItem.created_at.desc())
    )

    if page_size is not None:
        query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    box_items = result.scalars().all()

    return BoxItemListResponse(
        items=[_box_item_to_response(bi) for bi in box_items],
        total=total,
        page=page,
        page_size=page_size or total,
    )


async def add_item(db: AsyncSession, box_id: int, data: ItemAddRequest, user: User) -> BoxItemResponse:
    if not await _verify_box_owner(db, box_id, user):
        raise ValueError("Box not found or access denied")

    # Check 500 item limit
    count_result = await db.execute(
        select(func.count(BoxItem.id)).where(BoxItem.box_id == box_id)
    )
    current_count = count_result.scalar()
    if current_count >= MAX_ITEMS_PER_BOX:
        raise ValueError(f"Box has reached the maximum limit of {MAX_ITEMS_PER_BOX} items")

    item = await _get_or_create_item(db, data.name, user)

    # Check if item already exists in this box
    existing = await db.execute(
        select(BoxItem)
        .where(BoxItem.box_id == box_id, BoxItem.item_id == item.id)
        .options(selectinload(BoxItem.item), selectinload(BoxItem.tags).selectinload(BoxItemTag.tag))
    )
    box_item = existing.scalar_one_or_none()

    if box_item:
        box_item.quantity += data.quantity
        box_item.updated_by = user.id
    else:
        box_item = BoxItem(
            box_id=box_id,
            item_id=item.id,
            quantity=data.quantity,
            created_by=user.id,
            updated_by=user.id,
        )
        db.add(box_item)
        await db.flush()

    # Handle tags
    await db.execute(
        BoxItemTag.__table__.delete().where(BoxItemTag.box_item_id == box_item.id)
    )
    for tag_name in data.tags:
        tag = await _get_or_create_tag(db, tag_name, user)
        db.add(BoxItemTag(box_item_id=box_item.id, tag_id=tag.id))

    await db.flush()

    await log_action(db, box_id, "ITEM_ADDED", {
        "item_name": item.name,
        "quantity": data.quantity,
        "tags": data.tags,
        "user_id": user.id,
    })
    await db.commit()

    # Re-fetch with relationships
    result = await db.execute(
        select(BoxItem)
        .where(BoxItem.id == box_item.id)
        .options(selectinload(BoxItem.item), selectinload(BoxItem.tags).selectinload(BoxItemTag.tag))
    )
    box_item = result.scalar_one()
    return _box_item_to_response(box_item)


async def update_item(
    db: AsyncSession, box_id: int, item_id: int, data: ItemUpdateRequest, user: User
) -> BoxItemResponse | None:
    if not await _verify_box_owner(db, box_id, user):
        return None

    result = await db.execute(
        select(BoxItem)
        .where(BoxItem.box_id == box_id, BoxItem.item_id == item_id)
        .options(selectinload(BoxItem.item), selectinload(BoxItem.tags).selectinload(BoxItemTag.tag))
    )
    box_item = result.scalar_one_or_none()
    if not box_item:
        return None

    if data.quantity is not None:
        box_item.quantity = data.quantity

    box_item.updated_by = user.id

    if data.tags is not None:
        await db.execute(
            BoxItemTag.__table__.delete().where(BoxItemTag.box_item_id == box_item.id)
        )
        for tag_name in data.tags:
            tag = await _get_or_create_tag(db, tag_name, user)
            db.add(BoxItemTag(box_item_id=box_item.id, tag_id=tag.id))

    await db.flush()
    await log_action(db, box_id, "ITEM_UPDATED", {
        "item_name": box_item.item.name,
        "changes": data.model_dump(exclude_none=True),
        "user_id": user.id,
    })
    await db.commit()

    result = await db.execute(
        select(BoxItem)
        .where(BoxItem.id == box_item.id)
        .options(selectinload(BoxItem.item), selectinload(BoxItem.tags).selectinload(BoxItemTag.tag))
    )
    box_item = result.scalar_one()
    return _box_item_to_response(box_item)


async def remove_item(db: AsyncSession, box_id: int, item_id: int, user: User) -> bool:
    if not await _verify_box_owner(db, box_id, user):
        return False

    result = await db.execute(
        select(BoxItem)
        .where(BoxItem.box_id == box_id, BoxItem.item_id == item_id)
        .options(selectinload(BoxItem.item))
    )
    box_item = result.scalar_one_or_none()
    if not box_item:
        return False

    await log_action(db, box_id, "ITEM_REMOVED", {
        "item_name": box_item.item.name,
        "quantity": box_item.quantity,
        "user_id": user.id,
    })

    await db.delete(box_item)
    await db.commit()
    return True


async def autocomplete_items(db: AsyncSession, query: str, limit: int = 10) -> list[dict]:
    result = await db.execute(
        select(Item)
        .where(func.lower(Item.name).contains(query.lower()))
        .limit(limit)
    )
    items = result.scalars().all()
    return [{"id": i.id, "name": i.name} for i in items]
