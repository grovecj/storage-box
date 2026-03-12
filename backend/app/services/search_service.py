from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.box import StorageBox
from app.models.item import Item, BoxItem, BoxItemTag
from app.models.tag import Tag


async def search(db: AsyncSession, query: str) -> dict:
    q = query.strip()
    if not q:
        return {"boxes": [], "items": []}

    # Search boxes by code or name
    geom = func.ST_GeomFromWKB(func.ST_AsBinary(StorageBox.location))
    box_result = await db.execute(
        select(
            StorageBox,
            func.count(BoxItem.id).label("item_count"),
            func.ST_Y(geom).label("lat"),
            func.ST_X(geom).label("lng"),
        )
        .outerjoin(BoxItem, BoxItem.box_id == StorageBox.id)
        .where(
            or_(
                StorageBox.box_code.ilike(f"%{q}%"),
                StorageBox.name.ilike(f"%{q}%"),
            )
        )
        .group_by(StorageBox.id)
        .limit(20)
    )

    boxes = []
    for row in box_result.all():
        box, item_count, lat, lng = row
        boxes.append({
            "id": box.id,
            "box_code": box.box_code,
            "name": box.name,
            "latitude": lat,
            "longitude": lng,
            "item_count": item_count,
            "match_type": "box",
        })

    # Search items by name or tag
    item_result = await db.execute(
        select(BoxItem)
        .join(Item, BoxItem.item_id == Item.id)
        .outerjoin(BoxItemTag, BoxItemTag.box_item_id == BoxItem.id)
        .outerjoin(Tag, BoxItemTag.tag_id == Tag.id)
        .where(
            or_(
                Item.name.ilike(f"%{q}%"),
                Tag.name.ilike(f"%{q}%"),
            )
        )
        .options(
            selectinload(BoxItem.item),
            selectinload(BoxItem.box),
            selectinload(BoxItem.tags).selectinload(BoxItemTag.tag),
        )
        .distinct()
        .limit(50)
    )

    items = []
    seen_box_ids = {b["id"] for b in boxes}
    for bi in item_result.scalars().all():
        items.append({
            "id": bi.id,
            "item_id": bi.item_id,
            "name": bi.item.name,
            "quantity": bi.quantity,
            "tags": [bit.tag.name for bit in bi.tags],
            "box_id": bi.box_id,
            "box_code": bi.box.box_code,
            "box_name": bi.box.name,
        })
        # Also include the parent box in box results if not already there
        if bi.box_id not in seen_box_ids:
            seen_box_ids.add(bi.box_id)
            boxes.append({
                "id": bi.box.id,
                "box_code": bi.box.box_code,
                "name": bi.box.name,
                "item_count": 0,
                "match_type": "contains_match",
            })

    return {"boxes": boxes, "items": items}
