from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.box import StorageBox
from app.models.item import BoxItem, BoxItemTag
from app.models.user import User
from app.schemas.transfer import TransferRequest, TransferResponse
from app.utils.audit import log_action


async def transfer_item(db: AsyncSession, data: TransferRequest, user: User) -> TransferResponse:
    # Verify both boxes belong to the user
    from_box_result = await db.execute(
        select(StorageBox)
        .where(StorageBox.id == data.from_box_id)
        .where(StorageBox.owner_id == user.id)
    )
    from_box = from_box_result.scalar_one_or_none()
    if not from_box:
        raise ValueError("Source box not found or access denied")

    to_box_result = await db.execute(
        select(StorageBox)
        .where(StorageBox.id == data.to_box_id)
        .where(StorageBox.owner_id == user.id)
    )
    to_box = to_box_result.scalar_one_or_none()
    if not to_box:
        raise ValueError("Destination box not found or access denied")

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

    # Check if item exists in destination
    dest_result = await db.execute(
        select(BoxItem)
        .where(BoxItem.box_id == data.to_box_id, BoxItem.item_id == data.item_id)
    )
    dest_bi = dest_result.scalar_one_or_none()

    if dest_bi:
        dest_bi.quantity += data.quantity
        dest_bi.updated_by = user.id
    else:
        dest_bi = BoxItem(
            box_id=data.to_box_id,
            item_id=data.item_id,
            quantity=data.quantity,
            created_by=user.id,
            updated_by=user.id,
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
        "user_id": user.id,
    })
    await log_action(db, data.to_box_id, "ITEM_RECEIVED", {
        "item_name": item_name,
        "quantity": data.quantity,
        "from_box": from_box.box_code,
        "to_box": to_box.box_code,
        "user_id": user.id,
    })

    await db.commit()

    return TransferResponse(
        message=f"Transferred {data.quantity}x {item_name}",
        from_box_code=from_box.box_code,
        to_box_code=to_box.box_code,
        item_name=item_name,
        quantity=data.quantity,
    )
