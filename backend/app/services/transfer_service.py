from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.box import StorageBox
from app.models.item import BoxItem, BoxItemTag
from app.schemas.transfer import TransferRequest, TransferResponse
from app.utils.audit import log_action


async def transfer_item(db: AsyncSession, data: TransferRequest) -> TransferResponse:
    # Get source box_item
    source_result = await db.execute(
        select(BoxItem)
        .where(BoxItem.box_id == data.from_box_id, BoxItem.item_id == data.item_id)
        .options(selectinload(BoxItem.item), selectinload(BoxItem.tags).selectinload(BoxItemTag.tag))
    )
    source_bi = source_result.scalar_one_or_none()
    if not source_bi:
        raise ValueError("Item not found in source box")

    if data.quantity > source_bi.quantity:
        raise ValueError(f"Cannot transfer {data.quantity}, only {source_bi.quantity} available")

    # Get box codes for response
    from_box = await db.execute(select(StorageBox).where(StorageBox.id == data.from_box_id))
    from_box = from_box.scalar_one()
    to_box = await db.execute(select(StorageBox).where(StorageBox.id == data.to_box_id))
    to_box = to_box.scalar_one_or_none()
    if not to_box:
        raise ValueError("Destination box not found")

    # Check if item exists in destination
    dest_result = await db.execute(
        select(BoxItem)
        .where(BoxItem.box_id == data.to_box_id, BoxItem.item_id == data.item_id)
    )
    dest_bi = dest_result.scalar_one_or_none()

    if dest_bi:
        dest_bi.quantity += data.quantity
    else:
        dest_bi = BoxItem(
            box_id=data.to_box_id,
            item_id=data.item_id,
            quantity=data.quantity,
        )
        db.add(dest_bi)
        await db.flush()

        # Copy tags from source
        for bit in source_bi.tags:
            db.add(BoxItemTag(box_item_id=dest_bi.id, tag_id=bit.tag_id))

    # Reduce source quantity or remove
    if data.quantity == source_bi.quantity:
        await db.delete(source_bi)
    else:
        source_bi.quantity -= data.quantity

    item_name = source_bi.item.name

    await log_action(db, data.from_box_id, "ITEM_TRANSFERRED", {
        "item_name": item_name,
        "quantity": data.quantity,
        "from_box": from_box.box_code,
        "to_box": to_box.box_code,
    })
    await log_action(db, data.to_box_id, "ITEM_RECEIVED", {
        "item_name": item_name,
        "quantity": data.quantity,
        "from_box": from_box.box_code,
        "to_box": to_box.box_code,
    })

    await db.commit()

    return TransferResponse(
        message=f"Transferred {data.quantity}x {item_name}",
        from_box_code=from_box.box_code,
        to_box_code=to_box.box_code,
        item_name=item_name,
        quantity=data.quantity,
    )
